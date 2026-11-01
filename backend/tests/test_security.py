from app.config import Settings
import pytest
def test_invalid_queue():
    with pytest.raises(ValueError):Settings(queue_timeout=0).validate()
