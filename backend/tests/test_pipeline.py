from app.audio.postprocessing import normalize
def test_empty_result():assert normalize([],2)==[]
