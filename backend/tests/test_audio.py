from app.audio.validation import validate_name
import pytest
def test_types():
    validate_name('speech.flac')
    with pytest.raises(ValueError):validate_name('something.exe')
