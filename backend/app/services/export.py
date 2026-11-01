def rttm(segments,recording_id='recording'):
    return ''.join(f"SPEAKER {recording_id} 1 {s['start']:.3f} {s['end']-s['start']:.3f} <NA> <NA> {s['speaker_id']} <NA> <NA>\n" for s in segments)
