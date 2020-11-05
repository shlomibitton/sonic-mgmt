import allure


class RouteConfigTemplate:
    """
    This class contain 2 methods for configuration and deletion of static route related settings.
    """
    @staticmethod
    def configuration(topology_obj, static_route_config_dict):
        """
        This method applies static route configuration
        :param topology_obj: topology object fixture
        :param static_route_config_dict: configuration dictionary with all route related info
        Example: {'dut': [{'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['33.1.1.1', '34.1.1.1', '35.1.1.1', '36.1.1.1'],
                 'vrf': 'Vrf_custom'}]}
        """
        with allure.step('Applying route configuration'):
            for player_alias, configuration in static_route_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for route_info in configuration:
                    dst = route_info['dst']
                    dst_mask = route_info['dst_mask']
                    vrf = route_info.get('vrf')
                    for nexthop in route_info['via']:
                        cli_object.route.add_route(engine, dst, nexthop, dst_mask, vrf)

    @staticmethod
    def cleanup(topology_obj, static_route_config_dict):
        """
        This method performs static route configuration clean-up
        :param topology_obj: topology object fixture
        :param static_route_config_dict: configuration dictionary with all route related info
        Example: {'dut': [{'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['33.1.1.1', '34.1.1.1', '35.1.1.1', '36.1.1.1'],
                 'vrf': 'Vrf_custom'}]}
        """
        with allure.step('Performing route configuration cleanup'):
            for player_alias, configuration in static_route_config_dict.items():
                cli_object = topology_obj.players[player_alias]['cli']
                engine = topology_obj.players[player_alias]['engine']
                for route_info in configuration:
                    dst = route_info['dst']
                    dst_mask = route_info['dst_mask']
                    vrf = route_info.get('vrf')
                    for nexthop in route_info['via']:
                        cli_object.route.del_route(engine, dst, nexthop, dst_mask, vrf)
