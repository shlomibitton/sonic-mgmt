import logging
from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_lag_lacp_clis import SonicLagLacpCli
from ngts.cli_wrappers.sonic.sonic_lldp_clis import SonicLldpCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli

logger = logging.getLogger()


class SonicCli:
    def __init__(self):
        self.ip = SonicIpCli()
        self.lldp = SonicLldpCli()
        self.mac = SonicMacCli()
        self.vlan = SonicVlanCli()
        self.lag = SonicLagLacpCli()


