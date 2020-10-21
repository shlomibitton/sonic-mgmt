from abc import ABC, abstractmethod


class LagLacpCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def create_lag_interface_and_assign_physical_ports(engine, lag_lacp_info):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def delete_lag_interface_and_unbind_physical_ports(engine, lag_lacp_info):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
