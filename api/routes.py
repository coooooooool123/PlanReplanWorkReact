from typing import Dict
from orchestrator import Orchestrator


class APIRoutes:
    def __init__(self):
        self.orchestrator = Orchestrator()
    
    def submit_task(self, task: str) -> Dict:
        pass
    
    def get_task_status(self, task_id: str) -> Dict:
        pass
    
    def get_task_result(self, task_id: str) -> Dict:
        pass
    
    def get_tools(self) -> Dict:
        pass
