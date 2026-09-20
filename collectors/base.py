from abc import ABC, abstractmethod
from typing import List
from core.models import IncidentReport

class BaseCollector(ABC):
    @abstractmethod
    def fetch_recent(self) -> List[IncidentReport]:
        """Polls external source and normalizes entries into canonical IncidentReport objects."""
        pass