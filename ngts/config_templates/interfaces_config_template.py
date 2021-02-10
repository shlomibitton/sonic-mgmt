import allure

from ngts.cli_util.stub_engine import StubEngine
from ngts.config_templates.parallel_config_runner import parallel_config_runner


class InterfaceConfigTemplate:
    """
    This class contain 2 methods: configuration and deletion of interfaces related setting.
    """
    @staticmethod
    def configuration(topology_obj, interfaces_config_dict):
        """
        This method applies interfaces configuration
        :param topology_obj: topology object fixture
        :param interfaces_config_dict: configuration dictionary with all interfaces related info
        Example: {'dut': [{'iface': eth0, 'speed': 1000, 'mtu': 1500, 'original_speed': 10000, 'original_mtu': 1500},
        {'iface': 'static_route', 'create': True, 'type': 'dummy'}]}
        """
        with allure.step('Applying interfaces configuration'):
            conf = {}
            for player_alias, configuration in interfaces_config_dict.items():
                stub_engine = StubEngine()
                cli_object = topology_obj.players[player_alias]['cli']
                for interface_info in configuration:
                    iface = interface_info['iface']
                    speed = interface_info.get('speed')
                    mtu = interface_info.get('mtu')
                    dynamic_port_breakout = interface_info.get('dpb')
                    if interface_info.get('create'):
                        if_type = interface_info['type']
                        cli_object.interface.add_interface(stub_engine, iface, if_type)
                        cli_object.interface.enable_interface(stub_engine, iface)
                    if speed:
                        cli_object.interface.set_interface_speed(stub_engine, iface, speed)
                    if mtu:
                        cli_object.interface.set_interface_mtu(stub_engine, iface, mtu)
                    if dynamic_port_breakout:
                        breakout_mode = dynamic_port_breakout['breakout_mode']
                        cli_object.interface.configure_dpb_on_port(stub_engine, iface, breakout_mode,
                                                                   expect_error=False, force=False)
                conf[player_alias] = stub_engine.commands_list

            parallel_config_runner(topology_obj, conf)

    @staticmethod
    def cleanup(topology_obj, interfaces_config_dict):
        """
        This method performs interfaces configuration clean-up
        :param topology_obj: topology object fixture
        :param interfaces_config_dict: configuration dictionary with all interfaces related info
        Example: {'dut': [{'iface': eth0, 'speed': 1000, 'mtu': 1500, 'original_speed': 10000, 'original_mtu': 1500},
        {'iface': 'static_route', 'create': True, 'type': 'dummy'}]}
        """
        with allure.step('Performing interfaces configuration cleanup'):
            conf = {}
            for player_alias, configuration in interfaces_config_dict.items():
                stub_engine = StubEngine()
                cli_object = topology_obj.players[player_alias]['cli']
                for interface_info in configuration:
                    iface = interface_info['iface']
                    original_speed = interface_info.get('original_speed')
                    original_mtu = interface_info.get('original_mtu')
                    dynamic_port_breakout = interface_info.get('dpb')
                    if original_speed:
                        cli_object.interface.set_interface_speed(stub_engine, iface, original_speed)
                    if original_mtu:
                        cli_object.interface.set_interface_mtu(stub_engine, iface, original_mtu)
                    if interface_info.get('create'):
                        cli_object.interface.del_interface(stub_engine, iface)
                    if dynamic_port_breakout:
                        original_breakout_mode = dynamic_port_breakout['original_breakout_mode']
                        cli_object.interface.configure_dpb_on_port(stub_engine, iface, original_breakout_mode,
                                                                   expect_error=False, force=True)
                conf[player_alias] = stub_engine.commands_list

            parallel_config_runner(topology_obj, conf)
