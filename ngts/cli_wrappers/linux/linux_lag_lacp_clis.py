from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli
from ngts.cli_wrappers.common.lag_lacp_clis_common import LagLacpCliCommon


class LinuxLagLacpCli(LagLacpCliCommon):

    @staticmethod
    def create_lag_interface_and_assign_physical_ports(engine, lag_lacp_info):
        """
        This method applies LAG configuration, according to the parameters specified in the configuration dict
        :param engine: ssh engine object
        :param lag_lacp_info: configuration dictionary with all LAG/LACP related info
        Syntax: {'type': 'lag type', 'name':'port_name', 'members':[list of LAG members]}
        Example: {'type': 'lacp', 'name': 'PortChannel0001', 'members': [eth1]}
        """
        lag_lacp_iface_name = lag_lacp_info['name']
        lag_type = lag_lacp_info['type']

        LinuxInterfaceCli.add_interface(engine, lag_lacp_iface_name, iface_type='bond')

        if lag_type == 'lag':
            pass
        elif lag_type == 'lacp':
            LinuxLagLacpCli.set_bond_mode(engine, lag_lacp_iface_name, bond_mode='4')
        else:
            raise Exception('Unknown lag type was provided by the user: {}. The valid types are: lacp.'
                            .format(lag_type))

        for member_port in lag_lacp_info['members']:
            LinuxInterfaceCli.disable_interface(engine, member_port)
            LinuxInterfaceCli.add_port_to_bond(engine, member_port, lag_lacp_iface_name)
            LinuxInterfaceCli.enable_interface(engine, member_port)

        LinuxInterfaceCli.enable_interface(engine, lag_lacp_iface_name)

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
        LinuxInterfaceCli.del_interface(engine, lag_lacp_iface_name)
        for member_port in lag_lacp_info['members']:
            LinuxInterfaceCli.enable_interface(engine, member_port)

    @staticmethod
    def set_bond_mode(engine, bond_name, bond_mode):
        """
        This method sets bond mode for a given bond name
        :param engine: ssh engine object
        :param bond_name: bond interface name
        :param bond_mode: bond mode which will be set
        :return: command output
        """
        return engine.run_cmd("sudo ip link set dev {} type bond mode {}".format(bond_name, bond_mode))
