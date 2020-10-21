import logging
from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli
from ngts.cli_wrappers.linux.linux_lag_lacp_clis import LinuxLagLacpCli
from ngts.cli_wrappers.linux.linux_ip_clis import LinuxIpCli
from ngts.cli_wrappers.linux.linux_lldp_clis import LinuxLldpCli
from ngts.cli_wrappers.linux.linux_vlan_clis import LinuxVlanCli


logger = logging.getLogger()


class LinuxCli:
    def __init__(self):
        self.ip = LinuxIpCli()
        self.lldp = LinuxLldpCli()
        self.lag = LinuxLagLacpCli()
        self.interface = LinuxInterfaceCli()
        self.vlan = LinuxVlanCli()
