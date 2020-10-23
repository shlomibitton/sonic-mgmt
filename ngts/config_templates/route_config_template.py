import allure


class RouteConfigTemplate:
    """
    This class contain 2 methods for configure and cleanup Route related settings.
    """
    @staticmethod
    def configuration(topology_obj, route_config_dict):
        """
        Method which are doing route configuration
        :param topology_obj: topology object fixture
        :param route_config_dict: configuration dictionary with all route related info
        Example: {'dut': [{'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['33.1.1.1', '34.1.1.1', '35.1.1.1', '36.1.1.1'],
                 'vrf': 'Vrf_custom'}]}
        """
        with allure.step('Applying route configuration'):
            for player_alias, configuration in route_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for route_info in configuration:
                    dst = route_info['dst']
                    dst_mask = route_info['dst_mask']
                    vrf = route_info.get('vrf')
                    for gateway in route_info['via']:
                        cli_object.route.add_route(engine, dst, gateway, dst_mask, vrf)

    @staticmethod
    def cleanup(topology_obj, route_config_dict):
        """
        Method which are doing route configuration cleanup
        :param topology_obj: topology object fixture
        :param route_config_dict: configuration dictionary with all route related info
        Example: {'dut': [{'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['33.1.1.1', '34.1.1.1', '35.1.1.1', '36.1.1.1'],
                 'vrf': 'Vrf_custom'}]}
        """
        with allure.step('Performing route configuration cleanup'):
            for player_alias, configuration in route_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for route_info in configuration:
                    dst = route_info['dst']
                    dst_mask = route_info['dst_mask']
                    vrf = route_info.get('vrf')
                    for gateway in route_info['via']:
                        cli_object.route.del_route(engine, dst, gateway, dst_mask, vrf)
