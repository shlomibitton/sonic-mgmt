import allure

from ngts.cli_wrappers import sonic_ip_clis
from ngts.cli_wrappers import linux_ip_clis


class IpConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup IP related settings.
    """
    @staticmethod
    def configuration(topology_obj, ip_config_dict):
        """
        Method which are doing IP configuration
        :param topology_obj: topology object fixture
        :param ip_config_dict: configuration dictionary with all IP related info
        Example: {'dut': [{'iface': 'Vlan31', 'ips': [('31.1.1.1', '24')]}]}
        """
        with allure.step('Doing IP configuration'):
            for host_alias, configuration in ip_config_dict.items():
                engine = topology_obj.players[host_alias]['engine']

                for port_info in configuration:
                    iface = port_info['iface']
                    for ip_mask in port_info['ips']:
                        ip = ip_mask[0]
                        mask = ip_mask[1]
                        if host_alias == 'dut':
                            sonic_ip_clis.add_ip_to_interface(engine, iface, ip, mask)
                        else:
                            linux_ip_clis.add_ip_to_interface(engine, iface, ip, mask)

    @staticmethod
    def cleanup(topology_obj, ip_config_dict):
        """
        Method which are doing IP configuration cleanup
        :param topology_obj: topology object fixture
        :param ip_config_dict: configuration dictionary with all IP related info
        Example: {'dut': [{'iface': 'Vlan31', 'ips': [('31.1.1.1', '24')]}]}
        """
        with allure.step('Doing IP cleanup'):
            for host_alias, configuration in ip_config_dict.items():
                engine = topology_obj.players[host_alias]['engine']
                for port_info in configuration:
                    iface = port_info['iface']
                    for ip_mask in port_info['ips']:
                        ip = ip_mask[0]
                        mask = ip_mask[1]
                        if host_alias == 'dut':
                            sonic_ip_clis.del_ip_from_interface(engine, iface, ip, mask)
                        else:
                            linux_ip_clis.del_ip_from_interface(engine, iface, ip, mask)
