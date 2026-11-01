from pathlib import Path
EXT={'.wav','.mp3','.flac','.m4a','.ogg','.opus'}
def validate_name(name):
    if not name or Path(name).suffix.lower() not in EXT:raise ValueError('unsupported audio extension')
