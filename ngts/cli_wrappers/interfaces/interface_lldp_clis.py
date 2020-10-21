from abc import ABC, abstractmethod


class LldpCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def show_lldp_info_for_specific_interface(engine, interface_name):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
