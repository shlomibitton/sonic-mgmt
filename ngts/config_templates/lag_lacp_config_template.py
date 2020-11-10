import allure

from ngts.cli_util.stub_engine import StubEngine
from ngts.config_templates.parallel_config_runner import parallel_config_runner


class LagLacpConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup LAG/LACP related settings.
    """
    @staticmethod
    def configuration(topology_obj, lag_lacp_config_dict):
        with allure.step('Applying LAG/LACP configuration'):
            conf = {}
            for player_alias, lag_list in lag_lacp_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                for lag in lag_list:
                    cli_object.lag.create_lag_interface_and_assign_physical_ports(stub_engine, lag)
                conf[player_alias] = stub_engine.commands_list

            parallel_config_runner(topology_obj, conf)

    @staticmethod
    def cleanup(topology_obj, lag_lacp_config_dict):
        """
        Method which are doing LAG/LACP cleanup
        :param topology_obj: topology object fixture
        :param lag_lacp_config_dict: configuration dictionary with all LAG/LACP related info
        Example: {'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [dutha1]}]}
        """
        with allure.step('Performing LAG/LACP configuration cleanup'):
            conf = {}
            for player_alias, lag_list in lag_lacp_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                stub_engine = StubEngine()
                for lag in lag_list:
                    cli_object.lag.delete_lag_interface_and_unbind_physical_ports(stub_engine, lag)
                conf[player_alias] = stub_engine.commands_list

            parallel_config_runner(topology_obj, conf)
