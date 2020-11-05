from abc import ABC, abstractmethod


class ChassisCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def get_hostname(engine):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
