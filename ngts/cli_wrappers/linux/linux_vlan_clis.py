from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli
from ngts.cli_wrappers.common.vlan_clis_common import VlanCliCommon


class LinuxVlanCli(VlanCliCommon):

    @staticmethod
    def configure_vlan_and_add_ports(engine, vlan_info):
        """
        This method create a list a vlan interfaces, according to the dictionary provided by the user
        :param engine: ssh engine object
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                LinuxVlanCli.add_vlan_interface(engine, vlan_port, vlan_info['vlan_id'])
                vlan_iface = '{}.{}'.format(vlan_port, vlan_info['vlan_id'])
                LinuxInterfaceCli.enable_interface(engine, vlan_iface)

    @staticmethod
    def delete_vlan_and_remove_ports(engine, vlan_info):
        """
        This method deletes a vlan interface
        :param engine: ssh engine object
        :param vlan_info: vlan info dictionary
        {'vlan_id': vlan id, 'vlan_members': [{port name: vlan mode}]}
        Example: {'vlan_id': 500, 'vlan_members': [{eth1: 'trunk'}]}
        :return: command output
        """
        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
            for vlan_port, mode in vlan_port_and_mode_dict.items():
                LinuxVlanCli.del_vlan_interface(engine, vlan_port, vlan_info['vlan_id'])

    @staticmethod
    def add_vlan_interface(engine, interface, vlan):
        """
        This method creates a VLAN interface on Linux host
        :param engine: ssh engine object
        :param interface: linux interface name on top of it we will create vlan interface
        :param vlan: vlan ID
        :return: command output
        """
        vlan_interface = '{}.{}'.format(interface, vlan)
        return engine.run_cmd("sudo ip link add link {} name {} type vlan id {}".format(interface, vlan_interface, vlan))

    @staticmethod
    def del_vlan_interface(engine, interface, vlan):
        """
        This method deletes a VLAN interface on Linux host
        :param engine: ssh engine object
        :param interface: linux interface name on top of it we will remove vlan interface
        :param vlan: vlan ID
        :return: command output
        """
        vlan_interface = '{}.{}'.format(interface, vlan)
        return engine.run_cmd("sudo ip link del {}".format(vlan_interface))
