import pytest
import os

from ngts.cli_wrappers.sonic.sonic_dhcp_relay_clis import SonicDhcpRelayCli
from ngts.cli_wrappers.linux.linux_route_clis import LinuxRouteCli


@pytest.fixture(scope='package', autouse=True)
def dhcp_server_configuration(topology_obj, engines):
    """
    Pytest fixture which are doing configuration fot dhcp server
    :param topology_obj: topology object fixture
    """
    dhcpd_conf_name = 'dhcpd.conf'
    dhcpd_conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dhcpd_conf_name)

    engines.hb.copy_file(source_file=dhcpd_conf_path, dest_file=dhcpd_conf_name, file_system='/etc/dhcp/',
                        overwrite_file=True, verify_file=False)

    # Create dhclient.conf with timeout of 10 sec
    ha_engine = topology_obj.players['ha']['engine']
    ha_engine.run_cmd('echo "timeout 10;" > dhclient.conf')

    dhcp_ifaces = 'bond0.69'
    engines.hb.run_cmd('sed -e "s/INTERFACESv4=\\"\\"/INTERFACESv4=\\"{}\\"/g" -i /etc/default/isc-dhcp-server'.format(dhcp_ifaces))
    engines.hb.run_cmd('/etc/init.d/isc-dhcp-server restart')

    yield

    engines.hb.run_cmd('rm -f dhclient.conf')
    engines.hb.run_cmd('sed -e "s/INTERFACESv4=\\"{}\\"/INTERFACESv4=\\"\\"/g" -i /etc/default/isc-dhcp-server'.format(dhcp_ifaces))


@pytest.fixture(scope='class')
def configure_additional_dhcp_server(topology_obj, engines):
    dhcpd_conf_name = 'dhcpd.conf'
    dhcpd_template_conf_name = 'dhcpd_additional.conf'
    dhcpd_conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dhcpd_template_conf_name)

    engines.ha.copy_file(source_file=dhcpd_conf_path, dest_file=dhcpd_conf_name, file_system='/etc/dhcp/',
                        overwrite_file=True, verify_file=False)

    engines.ha.run_cmd('sed -e "s/INTERFACESv4=\\"\\"/INTERFACESv4=\\"bond0\\"/g" -i /etc/default/isc-dhcp-server')
    engines.ha.run_cmd('/etc/init.d/isc-dhcp-server restart')
    SonicDhcpRelayCli.add_dhcp_relay(engines.dut, 690, '30.0.0.2')
    SonicDhcpRelayCli.add_dhcp_relay(engines.dut, 691, '30.0.0.2')
    LinuxRouteCli.add_route(engines.ha, '69.0.1.0', '30.0.0.1', '24')
    LinuxRouteCli.add_route(engines.ha, '69.1.0.0', '30.0.0.1', '24')

    yield

    engines.ha.run_cmd('sed -e "s/INTERFACESv4=\\"bond0\\"/INTERFACESv4=\\"\\"/g" -i /etc/default/isc-dhcp-server')
    SonicDhcpRelayCli.del_dhcp_relay(engines.dut, 690, '30.0.0.2')
    SonicDhcpRelayCli.del_dhcp_relay(engines.dut, 691, '30.0.0.2')
    LinuxRouteCli.del_route(engines.ha, '69.0.1.0', '30.0.0.1', '24')
    LinuxRouteCli.del_route(engines.ha, '69.1.0.0', '30.0.0.1', '24')
