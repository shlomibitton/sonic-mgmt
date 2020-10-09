import allure

from ngts.cli_wrappers import sonic_lag_lacp_clis
from ngts.cli_wrappers import linux_lag_lacp_clis
from ngts.cli_wrappers import linux_interface_clis


class LagLacpConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup LAG/LACP related settings.
    """
    @staticmethod
    def configuration(topology_obj, lag_lacp_config_dict):
        """
        Method which are doing LAG/LACP configuration
        :param topology_obj: topology object fixture
        :param lag_lacp_config_dict: configuration dictionary with all LAG/LACP related info
        Example: {'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [dutha1]}]}
        """
        with allure.step('Doing LAG/LACP configuration'):
            for host_alias, configuration in lag_lacp_config_dict.items():
                engine = topology_obj.players[host_alias]['engine']

                for lag_lacp_info in configuration:
                    lag_lacp_iface_name = lag_lacp_info['name']
                    if host_alias == 'dut':
                        if lag_lacp_info['type'] == 'lag':
                            raise Exception('LAG mode not supported in SONiC for now, only LACP supported')
                        elif lag_lacp_info['type'] == 'lacp':
                            sonic_lag_lacp_clis.add_lacp_interface(engine, lag_lacp_iface_name)
                        for member_port in lag_lacp_info['members']:
                            sonic_lag_lacp_clis.add_port_to_lacp(engine, member_port, lag_lacp_iface_name)
                    else:
                        linux_lag_lacp_clis.add_bond_interface(engine, lag_lacp_iface_name)
                        if lag_lacp_info['type'] == 'lacp':
                            linux_lag_lacp_clis.set_bond_mode(engine, lag_lacp_iface_name, bond_mode='4')
                        for member_port in lag_lacp_info['members']:
                            linux_interface_clis.disable_interface(engine, member_port)
                            linux_lag_lacp_clis.add_port_to_bond(engine, member_port, lag_lacp_iface_name)
                            linux_interface_clis.enable_interface(engine, member_port)
                        linux_interface_clis.enable_interface(engine, lag_lacp_iface_name)

    @staticmethod
    def cleanup(topology_obj, lag_lacp_config_dict):
        """
        Method which are doing LAG/LACP cleanup
        :param topology_obj: topology object fixture
        :param lag_lacp_config_dict: configuration dictionary with all LAG/LACP related info
        Example: {'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [dutha1]}]}
        """
        with allure.step('Doing LAG/LACP cleanup'):
            for host_alias, configuration in lag_lacp_config_dict.items():
                engine = topology_obj.players[host_alias]['engine']

                for lag_lacp_info in configuration:
                    lag_lacp_iface_name = lag_lacp_info['name']
                    if host_alias == 'dut':
                        for member_port in lag_lacp_info['members']:
                            sonic_lag_lacp_clis.del_port_from_lacp(engine, member_port, lag_lacp_iface_name)
                        if lag_lacp_info['type'] == 'lag':
                            pass
                        elif lag_lacp_info['type'] == 'lacp':
                            sonic_lag_lacp_clis.del_lacp_interface(engine, lag_lacp_iface_name)
                    else:
                        linux_interface_clis.del_interface(engine, lag_lacp_iface_name)
                        for member_port in lag_lacp_info['members']:
                            linux_interface_clis.enable_interface(engine, member_port)
