import pytest
from app.audio.postprocessing import normalize
from app.services.export import rttm
from app.config import Settings
def test_overlapping_speakers():
    data=normalize([{'start':0,'end':2,'speaker':1},{'start':1,'end':3,'speaker':2},{'start':3.5,'end':4,'speaker':1}],4)
    assert [s['speaker_id'] for s in data]==['SPEAKER_00','SPEAKER_01','SPEAKER_00']
    assert len(rttm(data).splitlines())==3
def test_invalid_bounds():
    with pytest.raises(ValueError):normalize([{'start':2,'end':1,'speaker':1}],4)
def test_production_auth():
    with pytest.raises(ValueError):Settings(environment='production',api_token='short').validate()
