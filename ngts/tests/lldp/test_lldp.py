import allure
import logging
import pytest

from ngts.cli_wrappers.sonic_mac_clis import get_mac_address
from ngts.cli_wrappers.sonic_lldp_clis import parse_lldp_info_for_specific_interface


logger = logging.getLogger()

# Dict below will be send to test as parameters
test_args = {'host_ports': ['ha-dut-1', 'ha-dut-2', 'hb-dut-1', 'hb-dut-2'],
             'dut_ports': ['dut-ha-1', 'dut-ha-2', 'dut-hb-1', 'dut-hb-2']}


@pytest.mark.lldp
@pytest.mark.parametrize('arguments', [test_args])
@allure.title('Basic LLDP test case')
def test_lldp_basic(topology_obj, arguments):
    """
    Run basic LLDP test case. Test doing check for LLDP peer device MAC address
    """
    try:
        dut_engine = topology_obj.players['dut']['engine']

        for host_dut_port in zip(arguments['host_ports'], arguments['dut_ports']):
            host_port_alias = host_dut_port[0]
            host_name_alias = host_port_alias.split('-')[0]
            host_engine = topology_obj.players[host_name_alias]['engine']
            host_port_mac = get_mac_address(host_engine, topology_obj.ports[host_port_alias])
            dut_port = topology_obj.ports[host_dut_port[1]]
            with allure.step('Checking peer MAC address via LLDP in interface {}'.format(dut_port)):
                lldp_info = parse_lldp_info_for_specific_interface(dut_engine, dut_port)
                logger.info('Checking that peer mac address available in LLDP output')
                assert host_port_mac in lldp_info['Chassis']['ChassisID']

    except Exception as err:
        raise AssertionError(err)
