import allure


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
        Example: {'dut': [{'iface': eth0, 'speed': 1000, 'mtu': 1500, 'original_speed': 10000, 'original_mtu': 1500}]}
        """
        with allure.step('Applying interfaces configuration'):
            for player_alias, configuration in interfaces_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for interface_info in configuration:
                    iface = interface_info['iface']
                    speed = interface_info.get('speed')
                    mtu = interface_info.get('mtu')
                    if speed:
                        cli_object.interface.set_interface_speed(engine, iface, speed)
                    if mtu:
                        cli_object.interface.set_interface_mtu(engine, iface, mtu)

    @staticmethod
    def cleanup(topology_obj, interfaces_config_dict):
        """
        This method performs interfaces configuration clean-up
        :param topology_obj: topology object fixture
        :param interfaces_config_dict: configuration dictionary with all interfaces related info
        Example: {'dut': [{'iface': eth0, 'speed': 1000, 'mtu': 1500, 'original_speed': 10000, 'original_mtu': 1500}]}
        """
        with allure.step('Performing interfaces configuration cleanup'):
            for player_alias, configuration in interfaces_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for interface_info in configuration:
                    iface = interface_info['iface']
                    original_speed = interface_info.get('original_speed')
                    original_mtu = interface_info.get('original_mtu')
                    if original_speed:
                        cli_object.interface.set_interface_speed(engine, iface, original_speed)
                    if original_mtu:
                        cli_object.interface.set_interface_mtu(engine, iface, original_mtu)
