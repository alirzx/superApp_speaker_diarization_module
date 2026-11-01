import asyncio,hmac,logging,tempfile,time
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import Depends,FastAPI,File,Form,Header,HTTPException,UploadFile
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import JSONResponse,PlainTextResponse,Response
from prometheus_client import Counter,Histogram,generate_latest,CONTENT_TYPE_LATEST
from .config import Settings
from .audio.validation import validate_name
from .audio.decoder import InvalidAudio
from .engines.nemotron import NemotronEngine,EngineError
from .services.diarization import run
from .services.export import rttm
from .schemas import Result
LOG=logging.getLogger('diarization')
COUNT=Counter('superapp_diar_requests_total','Total diarization requests',['status'])
LATENCY=Histogram('superapp_diar_request_seconds','Total seconds per request')
def create_app(settings=None,engine_factory=NemotronEngine):
    settings=settings or Settings();settings.validate()
    @asynccontextmanager
    async def lifespan(app):
        app.state.engine=engine_factory(settings)
        await run_in_threadpool(app.state.engine.initialize)
        app.state.queue=asyncio.Semaphore(settings.concurrency)
        yield
        app.state.engine=None
    app=FastAPI(title='SuperApp Speaker Diarization',version='0.1.0',docs_url='/docs' if settings.environment!='production' else None,redoc_url=None,lifespan=lifespan)
    @app.middleware('http')
    async def headers(request,call_next):
        res=await call_next(request);res.headers['Cache-Control']='no-store';res.headers['X-Content-Type-Options']='nosniff';return res
    def auth(x_api_key:str|None=Header(None)):
        if settings.api_token and not hmac.compare_digest(x_api_key or '',settings.api_token):raise HTTPException(401,'Invalid API key')
    @app.get('/health/live')
    async def live():return {'status':'alive'}
    @app.get('/health/ready')
    async def ready():
        if not getattr(getattr(app.state,'engine',None),'initialized',False):return JSONResponse(status_code=503,content={'status':'not_ready'})
        return {'status':'ready','engine':'nemotron-3','device':'cpu'}
    @app.get('/v1/models',dependencies=[Depends(auth)])
    async def models():return {'models':[{'id':'nvidia/Nemotron-3-Diarization','device':'cpu','max_speakers':8}]}
    @app.get('/metrics',dependencies=[Depends(auth)])
    async def metrics():return Response(generate_latest(),media_type=CONTENT_TYPE_LATEST)
    @app.post('/v1/diarize',dependencies=[Depends(auth)],response_model=None)
    async def diarize(file:UploadFile=File(...),output_format:str=Form('json'),request_id:str|None=Form(None)):
        if output_format not in ('json','rttm'):raise HTTPException(422,'Invalid output format')
        if request_id is not None and (len(request_id)>80 or not request_id.isascii() or not all(c.isalnum() or c in '_-' for c in request_id)):raise HTTPException(422,'Invalid request_id')
        try:validate_name(file.filename)
        except ValueError as e:raise HTTPException(415,str(e)) from e
        try:await asyncio.wait_for(app.state.queue.acquire(),timeout=settings.queue_timeout)
        except asyncio.TimeoutError as e:COUNT.labels('busy').inc();raise HTTPException(503,'Inference queue full',headers={'Retry-After':'3'}) from e
        start=time.perf_counter()
        try:
            with tempfile.TemporaryDirectory(prefix='diar-') as temp:
                source=Path(temp)/'upload.bin';wav=Path(temp)/'input.wav';total=0
                with source.open('wb') as destination:
                    while chunk:=await file.read(1048576):
                        total+=len(chunk)
                        if total>settings.max_upload_mb*1048576:raise HTTPException(413,'Upload too large')
                        destination.write(chunk)
                if total==0:raise HTTPException(422,'Empty audio')
                result=await run_in_threadpool(run,app.state.engine,settings,source,wav,request_id)
            COUNT.labels('ok').inc()
            return PlainTextResponse(rttm(result['segments'])) if output_format=='rttm' else Result(**result)
        except InvalidAudio as e:COUNT.labels('invalid').inc();raise HTTPException(422,str(e)) from e
        except (EngineError,ValueError) as e:COUNT.labels('failed').inc();LOG.error('Inference error: %s',type(e).__name__);raise HTTPException(500,'Inference failed') from e
        finally:await file.close();app.state.queue.release();LATENCY.observe(time.perf_counter()-start)
    return app
app=create_app()
