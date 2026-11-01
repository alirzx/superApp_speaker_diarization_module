from abc import ABC,abstractmethod
class DiarizationEngine(ABC):
    @abstractmethod
    def initialize(self):pass
    @abstractmethod
    def diarize(self,wav):pass
