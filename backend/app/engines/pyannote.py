from .base import DiarizationEngine
class PyannoteEngine(DiarizationEngine):
    def initialize(self):raise NotImplementedError('optional benchmark engine')
    def diarize(self,wav):raise NotImplementedError('optional benchmark engine')
