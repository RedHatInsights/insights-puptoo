from abc import ABC, abstractmethod


class Modifier(ABC):
    @abstractmethod
    def run(self, host: dict, transformed_obj: dict, **kwargs) -> None:
        pass
