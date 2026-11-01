from app.engines.nemotron import NemotronEngine
from app.config import Settings
def test_engine_not_ready():assert not NemotronEngine(Settings()).initialized
