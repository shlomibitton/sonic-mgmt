from ngts.cli_wrappers.interfaces.interface_vrf_clis import VrfCliInterface


class VrfCliCommon(VrfCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
