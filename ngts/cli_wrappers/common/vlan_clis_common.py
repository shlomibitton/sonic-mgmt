from ngts.cli_wrappers.interfaces.interface_vlan_clis import VlanCliInterface


class VlanCliCommon(VlanCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
