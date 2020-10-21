from ngts.cli_wrappers.interfaces.interface_ip_clis import IpCliInterface


class IpCliCommon(IpCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
