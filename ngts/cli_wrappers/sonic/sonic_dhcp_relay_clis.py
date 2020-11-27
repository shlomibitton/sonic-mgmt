class SonicDhcpRelayCli:
    """
    This class is for DHCP Relay cli commands for linux only
    """
    @staticmethod
    def add_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method adding DHCP relay entry for VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID for which DHCP relay should be added
        :param dhcp_server: DHCP server IP address
        :return: command output
        """
        return engine.run_cmd("sudo config vlan dhcp_relay add {} {}".format(vlan, dhcp_server))

    @staticmethod
    def del_dhcp_relay(engine, vlan, dhcp_server):
        """
        This method delete DHCP relay entry from VLAN interface
        :param engine: ssh engine object
        :param vlan: vlan interface ID from which DHCP relay should be deleted
        :param dhcp_server: DHCP server IP address
        :return: command output
        """
        return engine.run_cmd("sudo config vlan dhcp_relay del {} {}".format(vlan, dhcp_server))
