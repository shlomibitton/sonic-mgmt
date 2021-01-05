from ngts.cli_wrappers.interfaces.interface_mac_clis import MacCliInterface


class MacCliCommon(MacCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """

    @staticmethod
    def get_mac_address_for_interface(engine, interface):
        """
        Method for get mac address for interface
        :param engine: ssh engine object
        :param interface: interface name
        :return: mac address
        """
        return engine.run_cmd("cat /sys/class/net/{}/address".format(interface))
