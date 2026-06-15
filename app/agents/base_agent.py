from abc import ABC, abstractmethod


class BaseAgent(ABC):

    def __init__(self, name: str):
        self.name = name

    @abstractmethod
    def run(self, state: dict) -> dict:
        pass

    def success(self, result):
        return {
            "agent_name": self.name,
            "status": "success",
            "result": result
        }

    def failure(self, error):
        return {
            "agent_name": self.name,
            "status": "failed",
            "error": str(error)
        }