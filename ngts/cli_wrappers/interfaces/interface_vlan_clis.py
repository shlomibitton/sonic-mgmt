from abc import ABC, abstractmethod


class VlanCliInterface(ABC):
    @staticmethod
    @abstractmethod
    def configure_vlan_and_add_ports(engine, vlan_info):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    @staticmethod
    @abstractmethod
    def delete_vlan_and_remove_ports(engine, vlan_info):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass
