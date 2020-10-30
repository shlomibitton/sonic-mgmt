from abc import ABC, abstractmethod


class RouteCliInterface(ABC):

    @staticmethod
    @abstractmethod
    def add_route(engine, dst, via, dst_mask, vrf):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def del_route(engine, dst, via, dst_mask, vrf):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
