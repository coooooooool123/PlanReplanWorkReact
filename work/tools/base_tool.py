from abc import ABC, abstractmethod
from typing import Dict, Any


class BaseTool(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.parameters = {}
    
    @abstractmethod
    def execute(self, **kwargs) -> Dict[str, Any]:
        pass
    
    def validate_params(self, **kwargs) -> bool:
        return True
    
    def get_schema(self) -> Dict:
        return {
            "name": self.name,
            "description": self.description,
            "parameters": self.parameters
        }
