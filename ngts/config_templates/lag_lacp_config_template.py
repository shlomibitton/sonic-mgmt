import allure


class LagLacpConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup LAG/LACP related settings.
    """
    @staticmethod
    def configuration(topology_obj, lag_lacp_config_dict):
        """
        This method is applies LAG configuration, according to the parameters specified in the configuration dict
        :param topology_obj: topology object
        :param lag_lacp_config_dict: configuration dictionary with all LAG/LACP related info
        Syntax: {'player_alias':[{'type': 'lag type', 'name':'port_name', 'members':[list of LAG members]}]}
        Example: {'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [eth1]}]}
        """
        with allure.step('Applying LAG/LACP configuration'):
            for player_alias, lag_list in lag_lacp_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for lag in lag_list:
                    cli_object.lag.create_lag_interface_and_assign_physical_ports(engine, lag)

    @staticmethod
    def cleanup(topology_obj, lag_lacp_config_dict):
        """
        Method which are doing LAG/LACP cleanup
        :param topology_obj: topology object fixture
        :param lag_lacp_config_dict: configuration dictionary with all LAG/LACP related info
        Example: {'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [dutha1]}]}
        """
        with allure.step('Performing LAG/LACP configuration cleanup'):
            for player_alias, lag_list in lag_lacp_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for lag in lag_list:
                    cli_object.lag.delete_lag_interface_and_unbind_physical_ports(engine, lag)
