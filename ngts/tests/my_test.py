import allure
import logging

from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker

logger = logging.getLogger()


@allure.title('My first test case')
def test_my_test(topology_obj):
    """
    Run My first test case, according to LAB-7
    """
    try:
        ha_ip = '10.0.0.2'
        hb_ip = '20.0.0.2'
        ha_name = 'ha'
        hb_name = 'hb'
        ha_iface = topology_obj.ports['ha-dut-2']
        hb_iface = topology_obj.ports['hb-dut-1']

        with allure.step('Sending 3 ping packets to {} from iface {}'.format(hb_ip, ha_iface)):
            validation = {'sender': ha_name, 'args': {'iface': ha_iface, 'count': 3, 'dst': hb_ip}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 ping packets to {} from iface {}'.format(hb_ip, ha_iface))
            ping.run_validation()

        icmp_pkt = 'Ether()/IP(src="{}",dst="{}")/ICMP()'

        with allure.step('Send scapy ICMP pkt to {} from {}'.format(ha_ip, hb_ip)):
            logger.info('Send scapy ICMP pkt to %s from %s', ha_ip, hb_ip)
            pkt = icmp_pkt.format(ha_ip, hb_ip)
            scapy_filter = 'icmp && dst {}'.format(hb_ip)
            validation = {'sender': ha_name,
                          'send_args': {'interface': ha_iface, 'packets': pkt, 'count': 3},
                          'receivers':
                              [
                                {'receiver': hb_name, 'receive_args': {'interface': hb_iface,
                                                                       'filter': scapy_filter, 'count': 3}}
                              ]
                          }
            ScapyChecker(topology_obj.players, validation).run_validation()

        with allure.step('Send scapy ICMP pkt to {} from {}'.format(hb_ip, ha_ip)):
            logger.info('Send scapy ICMP pkt to %s from %s', hb_ip, ha_ip)
            pkt = icmp_pkt.format(hb_ip, ha_ip)
            scapy_filter = 'icmp && dst {}'.format(ha_ip)
            validation = {'sender': hb_name,
                          'send_args': {'interface': hb_iface, 'packets': pkt, 'count': 3},
                          'receivers':
                              [
                                    {'receiver': ha_name, 'receive_args': {'interface': ha_iface,
                                                                           'filter': scapy_filter, 'count': 3}}
                              ]
                          }
            ScapyChecker(topology_obj.players, validation).run_validation()

    except Exception as err:
        raise AssertionError(err)
