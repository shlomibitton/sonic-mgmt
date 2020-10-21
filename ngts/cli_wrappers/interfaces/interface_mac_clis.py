from abc import ABC, abstractmethod


class MacCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def get_mac_address_for_interface(engine, interface):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
