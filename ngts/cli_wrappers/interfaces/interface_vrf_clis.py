from abc import ABC, abstractmethod


class VrfCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def add_vrf(engine, vrf):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def del_vrf(engine, vrf):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def add_interface_to_vrf(engine, interface, vrf):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def del_interface_from_vrf(engine, interface, vrf):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
