from abc import ABC, abstractmethod


class Action(ABC):

    @abstractmethod
    def get_action_name(self):
        pass

    @abstractmethod
    def get_prompt(self):
        pass

    @abstractmethod
    def parse(self, text: str):
        pass

    @abstractmethod
    def support(self, text: str):
        pass

    @abstractmethod
    def actions(self, text: str, index: int, expander):
        pass

