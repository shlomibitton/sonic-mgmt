import logging
import allure

from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_lag_lacp_clis import SonicLagLacpCli
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.cli_wrappers.sonic.sonic_lldp_clis import SonicLldpCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.cli_wrappers.sonic.sonic_vrf_clis import SonicVrfCli
from ngts.cli_wrappers.sonic.sonic_chassis_clis import SonicChassisCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_dhcp_relay_clis import SonicDhcpRelayCli
from ngts.cli_wrappers.sonic.sonic_ifconfig_clis import SonicIfconfigCli
from ngts.cli_wrappers.sonic.sonic_crm_clis import SonicCrmCli
from ngts.cli_wrappers.sonic.sonic_acl_clis import SonicAclCli

logger = logging.getLogger()


class SonicCli:
    def __init__(self):
        self.ip = SonicIpCli()
        self.lldp = SonicLldpCli()
        self.mac = SonicMacCli()
        self.vlan = SonicVlanCli()
        self.lag = SonicLagLacpCli()
        self.interface = SonicInterfaceCli()
        self.route = SonicRouteCli()
        self.vrf = SonicVrfCli()
        self.chassis = SonicChassisCli()
        self.general = SonicGeneralCli()
        self.dhcp_relay = SonicDhcpRelayCli()
        self.ifconfig = SonicIfconfigCli()
        self.crm = SonicCrmCli()
        self.acl = SonicAclCli()
