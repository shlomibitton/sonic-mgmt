from abc import ABC, abstractmethod


class IpCliInterface(ABC):

    @staticmethod
    @abstractmethod
    def add_ip_to_interface(engine, interface, ip, mask):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def del_ip_from_interface(engine, interface, ip, mask):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
