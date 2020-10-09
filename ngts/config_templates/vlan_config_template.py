import allure

from ngts.cli_wrappers import sonic_vlan_clis
from ngts.cli_wrappers import linux_vlan_clis
from ngts.cli_wrappers import linux_interface_clis


class VlanConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup VLAN related settings.
    """
    @staticmethod
    def configuration(topology_obj, vlan_config_dict):
        """
        Method which are doing VLAN configuration
        :param topology_obj: topology object fixture
        :param vlan_config_dict: configuration dictionary with all VLANs related info
        Example: {'dut': [{'vlan_id': 31, 'vlan_members': []},{'vlan_id': 500, 'vlan_members': [{dutha2: 'trunk'}]}]}
        """
        with allure.step('Doing VLAN configuration'):
            for host_alias, configuration in vlan_config_dict.items():
                engine = topology_obj.players[host_alias]['engine']
                for vlan_info in configuration:
                    if host_alias == 'dut':
                        sonic_vlan_clis.add_vlan(engine, vlan_info['vlan_id'])
                        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
                            for vlan_port, mode in vlan_port_and_mode_dict.items():
                                sonic_vlan_clis.add_port_to_vlan(engine, vlan_port, vlan_info['vlan_id'], mode)
                    else:
                        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
                            for vlan_port, mode in vlan_port_and_mode_dict.items():
                                linux_vlan_clis.add_vlan_interface(engine, vlan_port, vlan_info['vlan_id'])
                                vlan_iface = '{}.{}'.format(vlan_port, vlan_info['vlan_id'])
                                linux_interface_clis.enable_interface(engine, vlan_iface)

    @staticmethod
    def cleanup(topology_obj, vlan_config_dict):
        """
        Method which are doing VLAN cleanup
        :param topology_obj: topology object fixture
        :param vlan_config_dict: configuration dictionary with all VLANs related info
        Example: {'dut': [{'vlan_id': 31, 'vlan_members': []},{'vlan_id': 500, 'vlan_members': [{dutha2: 'trunk'}]}]}
        """
        with allure.step('Doing VLAN cleanup'):
            for host_alias, configuration in vlan_config_dict.items():
                engine = topology_obj.players[host_alias]['engine']
                for vlan_info in configuration:
                    if host_alias == 'dut':
                        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
                            for vlan_port, mode in vlan_port_and_mode_dict.items():
                                sonic_vlan_clis.del_port_from_vlan(engine, vlan_port, vlan_info['vlan_id'])
                        sonic_vlan_clis.del_vlan(engine, vlan_info['vlan_id'])
                    else:
                        for vlan_port_and_mode_dict in vlan_info['vlan_members']:
                            for vlan_port, mode in vlan_port_and_mode_dict.items():
                                vlan_iface = '{}.{}'.format(vlan_port, vlan_info['vlan_id'])
                                linux_interface_clis.del_interface(engine, vlan_iface)
