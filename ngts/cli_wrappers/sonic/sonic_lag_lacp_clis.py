from ngts.cli_wrappers.common.lag_lacp_clis_common import LagLacpCliCommon


class SonicLagLacpCli(LagLacpCliCommon):

    @staticmethod
    def create_lag_interface_and_assign_physical_ports(engine, lag_lacp_info):
        """
        This method is applies LAG configuration, according to the parameters specified in the configuration dict
        :param engine: ssh engine object
        :param lag_lacp_info: configuration dictionary with all LAG/LACP related info
        Syntax: {'type': 'lag type', 'name':'port_name', 'members':[list of LAG members]}
        Example: {'type': 'lacp', 'name': 'PortChannel0001', 'members': [eth1]}
        """
        lag_lacp_iface_name = lag_lacp_info['name']
        lag_type = lag_lacp_info['type']

        if lag_type == 'lag':
            raise Exception('Static LAG mode is currently not supported in SONiC')
        elif lag_type == 'lacp':
            SonicLagLacpCli.create_lag_interface(engine, lag_lacp_iface_name)
        else:
            raise Exception('Unknown lag type was provided by the user: {}. The valid types are: lacp.'
                            .format(lag_type))

        for member_port in lag_lacp_info['members']:
            SonicLagLacpCli.add_port_to_port_channel(engine, member_port, lag_lacp_iface_name)

    @staticmethod
    def delete_lag_interface_and_unbind_physical_ports(engine, lag_lacp_info):
        """
        This method deletes LAG configuration, according to the parameters specified in the configuration dict
        :param engine: ssh engine object
        :param lag_lacp_info: configuration dictionary with all LAG/LACP related info
        Syntax: {'type': 'lag type', 'name':'port_name', 'members':[list of LAG members]}
        Example: {'type': 'lacp', 'name': 'PortChannel0001', 'members': [eth1]}
        """
        lag_lacp_iface_name = lag_lacp_info['name']
        lag_type = lag_lacp_info['type']

        for member_port in lag_lacp_info['members']:
            SonicLagLacpCli.delete_port_from_port_channel(engine, member_port, lag_lacp_iface_name)

        if lag_type == 'lag':
            raise Exception('Static LAG mode is currently not supported in SONiC')
        elif lag_type == 'lacp':
            SonicLagLacpCli.delete_lag_interface(engine, lag_lacp_iface_name)
        else:
            raise Exception('Unknown lag type was provided by the user: {}. The valid types are: lacp.'
                            .format(lag_type))

    @staticmethod
    def create_lag_interface(engine, lacp_interface_name):
        """
        This method create a portchannel interface
        :param engine: ssh engine object
        :param lacp_interface_name: LACP interface name which should be added
        :return: command output
        """
        return engine.run_cmd("sudo config portchannel add {}".format(lacp_interface_name))

    @staticmethod
    def delete_lag_interface(engine, lacp_interface_name):
        """
        Method which deleting LACP interface in SONiC
        :param engine: ssh engine object
        :param lacp_interface_name: LACP interface name which should be deleted
        :return: command output
        """
        return engine.run_cmd("sudo config portchannel del {}".format(lacp_interface_name))

    @staticmethod
    def add_port_to_port_channel(engine, interface, lacp_interface_name):
        """
        This methods assign l2 interface to port-channel
        :param engine: ssh engine object
        :param interface: interface name which should be added to LACP
        :param lacp_interface_name: LACP interface name to which we will add interface
        :return: command output
        """
        return engine.run_cmd("sudo config portchannel member add {} {}".format(lacp_interface_name, interface))

    @staticmethod
    def delete_port_from_port_channel(engine, interface, lacp_interface_name):
        """
        This methods deletes l2 interface from port-channel
        :param engine: ssh engine object
        :param interface: interface name which should be deleted from LACP
        :param lacp_interface_name: LACP interface name from which we will remove interface
        :return: command output
        """
        return engine.run_cmd("sudo config portchannel member del {} {}".format(lacp_interface_name, interface))

    @staticmethod
    def show_interfaces_port_channel(engine):
        """
        This method performs show portchannel command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd("show interfaces portchannel")
