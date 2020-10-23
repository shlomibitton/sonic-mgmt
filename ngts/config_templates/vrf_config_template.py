import allure


class VrfConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup VRF related settings.
    """
    @staticmethod
    def configuration(topology_obj, vrf_config_dict):
        """
        Method which are doing VRF configuration
        :param topology_obj: topology object fixture
        :param vrf_config_dict: configuration dictionary with all VRF related info
        Example: {'dut': [{'vrf': 'Vrf_custom', 'vrf_interfaces': [dutlb1_2, dutlb2_2, dutlb3_2, dutlb4_2, dutlb5_2,
        dutlb6_2, duthb1]}]}
        """
        with allure.step('Applying VRF configuration'):
            for player_alias, configuration in vrf_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for vrf_info in configuration:
                    vrf = vrf_info['vrf']
                    cli_object.vrf.add_vrf(engine, vrf)
                    for interface in vrf_info['vrf_interfaces']:
                        cli_object.vrf.add_interface_to_vrf(engine, interface, vrf)

    @staticmethod
    def cleanup(topology_obj, vrf_config_dict):
        """
        Method which are doing VRF configuration cleanup
        :param topology_obj: topology object fixture
        :param vrf_config_dict: configuration dictionary with all VRF related info
        Example: {'dut': [{'vrf': 'Vrf_custom', 'vrf_interfaces': [dutlb1_2, dutlb2_2, dutlb3_2, dutlb4_2, dutlb5_2,
        dutlb6_2, duthb1]}]}
        """
        with allure.step('Performing VRF configuration cleanup'):
            for player_alias, configuration in vrf_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for vrf_info in configuration:
                    vrf = vrf_info['vrf']
                    for interface in vrf_info['vrf_interfaces']:
                        cli_object.vrf.del_interface_from_vrf(engine, interface, vrf)
                    cli_object.vrf.del_vrf(engine, vrf)
