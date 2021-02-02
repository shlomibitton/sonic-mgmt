from abc import ABC, abstractmethod


class IfconfigCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def get_ifconfig(engine, options):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
