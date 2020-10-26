from ngts.cli_wrappers.interfaces.interface_static_route_clis import StaticRouteCliInterface


class StaticRouteCliCommon(StaticRouteCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
