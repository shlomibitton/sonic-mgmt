from ngts.cli_wrappers.interfaces.interface_route_clis import RouteCliInterface


class RouteCliCommon(RouteCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
