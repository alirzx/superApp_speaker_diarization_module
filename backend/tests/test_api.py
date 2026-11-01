from fastapi.testclient import TestClient
from app.main import create_app
from app.config import Settings
class Fake:
    def __init__(self,config):self.initialized=False
    def initialize(self):self.initialized=True
    def diarize(self,wav):return [{'start':0,'end':1,'speaker':1}]
def test_health_and_auth():
    app=create_app(Settings(environment='test',api_token='secret'),engine_factory=Fake)
    with TestClient(app) as c:
        assert c.get('/health/ready').status_code==200
        assert c.get('/v1/models').status_code==401
        assert c.get('/v1/models',headers={'X-API-Key':'secret'}).status_code==200
def test_upload_validation():
    app=create_app(Settings(environment='test'),engine_factory=Fake)
    with TestClient(app) as c:
        assert c.post('/v1/diarize',files={'file':('evil.exe',b'bad')}).status_code==415
        assert c.post('/v1/diarize',files={'file':('a.wav',b'')}).status_code==422
