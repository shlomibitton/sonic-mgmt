import allure

from ngts.cli_util.stub_engine import StubEngine
from ngts.config_templates.parallel_config_runner import parallel_config_runner


class DhcpRelayConfigTemplate:
    """
    This class contains 2 methods for configuring and cleaning-up DHCP Relay related settings.
    """
    @staticmethod
    def configuration(topology_obj, dhcp_relay_config_dict):
        """
        Method which are performing DHCP Relay configuration
        :param topology_obj: topology object fixture
        :param dhcp_relay_config_dict: configuration dictionary with all DHCP Relay related info
        Example: {'dut': [{'vlan_id': 690, 'dhcp_servers': ['69.0.0.2', '6900::2']}]}
        """
        with allure.step('Applying DHCP Relay configuration'):
            conf = {}
            for player_alias, configuration in dhcp_relay_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                for dhcp_relay_info in configuration:
                    vlan = dhcp_relay_info['vlan_id']
                    for dhcp_server in dhcp_relay_info['dhcp_servers']:
                        cli_object.dhcp_relay.add_dhcp_relay(stub_engine, vlan, dhcp_server)
                conf[player_alias] = stub_engine.commands_list
            # here we perform parallel configuration
            parallel_config_runner(topology_obj, conf)

    @staticmethod
    def cleanup(topology_obj, dhcp_relay_config_dict):
        """
        Method which are doing DHCP Relay configuration cleanup
        :param topology_obj: topology object fixture
        :param dhcp_relay_config_dict: configuration dictionary with all DHCP Relay related info
        Example: {'dut': [{'vlan_id': 690, 'dhcp_servers': ['69.0.0.2', '6900::2']}]}
        """
        with allure.step('Performing DHCP Relay configuration cleanup'):
            conf = {}
            for player_alias, configuration in dhcp_relay_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                for dhcp_relay_info in configuration:
                    vlan = dhcp_relay_info['vlan_id']
                    for dhcp_server in dhcp_relay_info['dhcp_servers']:
                        cli_object.dhcp_relay.del_dhcp_relay(stub_engine, vlan, dhcp_server)
                conf[player_alias] = stub_engine.commands_list
            # here we perform parallel cleaning-up
            parallel_config_runner(topology_obj, conf)
