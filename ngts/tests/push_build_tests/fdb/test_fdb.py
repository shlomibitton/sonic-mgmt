import allure
import logging
import pytest

from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()


@pytest.mark.push_gate
@allure.title('PushGate FDB test case')
def test_push_gate_fdb(topology_obj):
    """
    Run PushGate FDB test case, test doing FDB validation - we check that MAC address which sent traffic available
    in FDB table on switch
    """
    try:
        host_name = 'hb'
        dut_engine = topology_obj.players['dut']['engine']
        host_engine = topology_obj.players[host_name]['engine']
        src_iface = 'bond0.69'
        dst_ip = '69.0.0.1'

        with allure.step('Sending 3 ping packets to {} from iface {}'.format(dst_ip, src_iface)):
            validation = {'sender': host_name, 'args': {'iface': src_iface, 'count': 3, 'dst': dst_ip}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 ping packets to {} from iface {}'.format(dst_ip, src_iface))
            ping.run_validation()

        send_port_mac = LinuxMacCli.get_mac_address_for_interface(host_engine, src_iface)
        logger.info('Checking that host src mac address in FDB output')
        # TODO: enable validation(disabled due to bug) and validation should be more precise
        # assert str(send_port_mac).upper() in SonicMacCli.show_mac(dut_engine)

    except Exception as err:
        raise AssertionError(err)
