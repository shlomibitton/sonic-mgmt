import allure

from ngts.cli_util.stub_engine import StubEngine
from ngts.config_templates.parallel_config_runner import parallel_config_runner


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
        with allure.step('Applying IP configuration'):
            conf = {}
            for player_alias, configuration in ip_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                for port_info in configuration:
                    iface = port_info['iface']
                    for ip_mask in port_info['ips']:
                        ip = ip_mask[0]
                        mask = ip_mask[1]
                        cli_object.ip.add_ip_to_interface(stub_engine, iface, ip, mask)
                conf[player_alias] = stub_engine.commands_list
            # here we will do parallel configuration
            parallel_config_runner(topology_obj, conf)

    @staticmethod
    def cleanup(topology_obj, ip_config_dict):
        """
        Method which are doing IP configuration cleanup
        :param topology_obj: topology object fixture
        :param ip_config_dict: configuration dictionary with all IP related info
        Example: {'dut': [{'iface': 'Vlan31', 'ips': [('31.1.1.1', '24')]}]}
        """
        with allure.step('Performing IP configuration cleanup'):
            conf = {}
            for player_alias, configuration in ip_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                for port_info in configuration:
                    iface = port_info['iface']
                    for ip_mask in port_info['ips']:
                        ip = ip_mask[0]
                        mask = ip_mask[1]
                        cli_object.ip.del_ip_from_interface(stub_engine, iface, ip, mask)
                conf[player_alias] = stub_engine.commands_list

            parallel_config_runner(topology_obj, conf)
