from abc import ABC, abstractmethod


class CrmCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def parse_thresholds_table(engine):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def parse_resources_table(engine):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
