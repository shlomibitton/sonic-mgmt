from ngts.cli_wrappers.interfaces.interface_ip_clis import IpCliInterface


class IpCliCommon(IpCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass

    @staticmethod
    def add_ip_neigh(engine, neighbor, neigh_mac_addr, dev):
        """
        This method adds an neighbor entry to the ARP table
        :param engine: ssh engine object
        :param neighbor: neighbor IP address
        :param neigh_mac_addr: neighbor MAC address
        :param dev: interface to which neighbour is attached
        :return: command output
        """
        return engine.run_cmd("sudo ip neigh replace {} lladdr {} dev {}".format(neighbor, neigh_mac_addr, dev))

    @staticmethod
    def del_ip_neigh(engine, neighbor, neigh_mac_addr, dev):
        """
        This method adds an neighbor entry to the ARP table
        :param engine: ssh engine object
        :param neighbor: neighbor IP address
        :param neigh_mac_addr: neighbor MAC address
        :param dev: interface to which neighbour is attached
        :return: command output
        """
        return engine.run_cmd("sudo ip neigh del {} lladdr {} dev {}".format(neighbor, neigh_mac_addr, dev))
