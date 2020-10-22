import allure


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
            for player_alias, configuration in vlan_config_dict.items():
                engine = topology_obj.players[player_alias]['engine']
                cli_object = topology_obj.players[player_alias]['cli']
                for vlan_info in configuration:
                    cli_object.vlan.configure_vlan_and_add_ports(engine, vlan_info)

    @staticmethod
    def cleanup(topology_obj, vlan_config_dict):
        """
        Method which are doing VLAN cleanup
        :param topology_obj: topology object fixture
        :param vlan_config_dict: configuration dictionary with all VLANs related info
        Example: {'dut': [{'vlan_id': 31, 'vlan_members': []},{'vlan_id': 500, 'vlan_members': [{dutha2: 'trunk'}]}]}
        """
        with allure.step('Doing VLAN cleanup'):
            for player_alias, configuration in vlan_config_dict.items():
                engine = topology_obj.players[player_alias]['engine']
                cli_object = topology_obj.players[player_alias]['cli']
                for vlan_info in configuration:
                    cli_object.vlan.delete_vlan_and_remove_ports(engine, vlan_info)
