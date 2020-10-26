from abc import ABC, abstractmethod


class InterfaceCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def add_interface(engine, interface, iface_type):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def del_interface(engine, interface):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def enable_interface(engine, interface):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def disable_interface(engine, interface):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def set_interface_speed(engine, interface, speed):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def set_interface_mtu(engine, interface, mtu):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
