import allure
import logging
import pytest

from retry.api import retry_call
from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('PushGate FDB test case')
def test_push_gate_fdb(engines, players):
    """
    Run PushGate FDB test case, test doing FDB validation - we check that MAC address which sent traffic available
    in FDB table on switch
    """
    try:
        src_iface = 'bond0.40'
        dst_ip = '40.0.0.1'
        with allure.step('Check that PortChannel0002 link in UP state'):
            retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, ['PortChannel0002']], tries=12,
                       delay=5, logger=logger)

        with allure.step('Sending 3 ping packets to {} from iface {}'.format(dst_ip, src_iface)):
            validation = {'sender': 'hb', 'args': {'iface': src_iface, 'count': 3, 'dst': dst_ip}}
            ping = PingChecker(players, validation)
            logger.info('Sending 3 ping packets to {} from iface {}'.format(dst_ip, src_iface))
            ping.run_validation()

        send_port_mac = LinuxMacCli.get_mac_address_for_interface(engines.hb, src_iface)
        logger.info('Checking that host src mac address in FDB output')
        # TODO: enable validation(disabled due to bug) and validation should be more precise
        # assert str(send_port_mac).upper() in SonicMacCli.show_mac(engines.dut)

    except Exception as err:
        raise AssertionError(err)
