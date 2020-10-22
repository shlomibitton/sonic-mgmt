from ngts.cli_wrappers.interfaces.interface_lldp_clis import LldpCliInterface


class LldpCliCommon(LldpCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
