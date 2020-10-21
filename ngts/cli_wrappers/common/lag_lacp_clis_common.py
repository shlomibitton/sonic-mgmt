from ngts.cli_wrappers.interfaces.interafce_lag_lacp_clis import LagLacpCliInterface


class LagLacpCliCommon(LagLacpCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass
