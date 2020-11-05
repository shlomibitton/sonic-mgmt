import logging
import allure

from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_lag_lacp_clis import SonicLagLacpCli
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.cli_wrappers.sonic.sonic_lldp_clis import SonicLldpCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.sonic.sonic_static_route_clis import SonicStaticRouteCli
from ngts.cli_wrappers.sonic.sonic_vrf_clis import SonicVrfCli
from ngts.cli_wrappers.sonic.sonic_chassis_clis import SonicChassisCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
logger = logging.getLogger()


class SonicCli:
    def __init__(self):
        self.ip = SonicIpCli()
        self.lldp = SonicLldpCli()
        self.mac = SonicMacCli()
        self.vlan = SonicVlanCli()
        self.lag = SonicLagLacpCli()
        self.interface = SonicInterfaceCli()
        self.static_route = SonicStaticRouteCli()
        self.vrf = SonicVrfCli()
        self.chassis = SonicChassisCli()
        self.general = SonicGeneralCli()
