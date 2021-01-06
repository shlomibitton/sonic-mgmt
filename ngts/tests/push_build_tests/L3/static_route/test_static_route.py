import allure
import logging
import pytest

from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.tools.skip_test.skip import ngts_skip

"""

 Static Route Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+Static+Routes+Documentation

"""

logger = logging.getLogger()


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test Basic Static Route')
def test_basic_static_route(topology_obj, current_platform):
    """
    This test will check basic static route functionality.
    :param topology_obj: topology object fixture
    :return: raise assertion error in case when test failed
    """
    ngts_skip(current_platform, rm_ticket_list=[2399954])
    hadut2 = topology_obj.ports['ha-dut-2']
    dut_engine = topology_obj.players['dut']['engine']

    try:
        # TODO: Workaround for bug https://redmine.mellanox.com/issues/2350931
        validation_create_arp_1_ipv4 = {'sender': 'hb', 'args': {'interface': 'bond0.69', 'count': 3, 'dst': '69.0.0.1'}}
        PingChecker(topology_obj.players, validation_create_arp_1_ipv4).run_validation()
        validation_create_arp_1_ipv6 = {'sender': 'hb', 'args': {'interface': 'bond0.69', 'count': 3, 'dst': '6900::1'}}
        PingChecker(topology_obj.players, validation_create_arp_1_ipv6).run_validation()
        validation_create_arp_2_ipv4 = {'sender': 'ha', 'args': {'interface': 'bond0', 'count': 3, 'dst': '30.0.0.1'}}
        PingChecker(topology_obj.players, validation_create_arp_2_ipv4).run_validation()
        validation_create_arp_2_ipv6 = {'sender': 'ha', 'args': {'interface': 'bond0', 'count': 3, 'dst': '3000::1'}}
        PingChecker(topology_obj.players, validation_create_arp_2_ipv6).run_validation()
        # TODO: End workaround for bug https://redmine.mellanox.com/issues/2350931

        # Test started here
        with allure.step('Check that static routes IPv4 on switch using CLI'):
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route='20.0.0.10/32'),
                            expected_output_list=[(r'\*\s69.0.0.2,\svia\sVlan69', True)])
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route='20.0.0.1'),
                            expected_output_list=[(r'\*\s+directly\sconnected,\sPortChannel0001', True)])
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route='20.0.0.0'),
                            expected_output_list=[(r'\*\s30.0.0.2,\svia\sPortChannel0001', True)])

        with allure.step('Check that static routes IPv6 on switch using CLI'):
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route='2000::10/128', ipv6=True),
                            expected_output_list=[(r'\*\s6900::2,\svia\sVlan69', True)])
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route='2000::1', ipv6=True),
                            expected_output_list=[(r'\*\sdirectly\sconnected,\sVlan69', True)])
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route='2000::', ipv6=True),
                            expected_output_list=[(r'\*\s3000::2,\svia\sPortChannel0001', True)])

        dut_mac = SonicMacCli.get_mac_address_for_interface(dut_engine, topology_obj.ports['dut-ha-1'])
        sender_interface = '{}.40'.format(hadut2)
        receiver_interface_ha = 'bond0'
        receiver_interface_hb = 'bond0.69'
        pkt_ipv4 = 'Ether(dst="{}")/IP(dst="{}", src="1.2.3.4")/TCP()'
        pkt_ipv6 = 'Ether(dst="{}")/IPv6(dst="{}", src="1234::5678")/TCP()'

        # TODO: cmd below for debug - need to remove later
        dut_engine.run_cmd('show interfaces status')
        dut_engine.run_cmd('show dropcounters configuration')
        dut_engine.run_cmd('show arp')
        dut_engine.run_cmd('show ip interfaces')
        dut_engine.run_cmd('sudo tail -n 100 /var/log/syslog')

        with allure.step('Functional check IPv4 static route via Interface'):
            logger.info('Functional checking IPv4 static route via Interface')
            dst_ip = '20.0.0.1'
            pkt = pkt_ipv4.format(dut_mac, dst_ip)
            # Filter below will catch ARP packet with DST IP 20.0.0.1(Who has 20.0.0.1 ....)
            tcpdump_filter = 'arp[24:4]==0x14000001'
            validation_1 = {'sender': 'ha',
                            'send_args': {'interface': sender_interface, 'packets': pkt, 'count': 3},
                            'receivers':
                                [
                                    {'receiver': 'ha', 'receive_args': {'interface': receiver_interface_ha,
                                                                        'filter': tcpdump_filter,
                                                                        'count': 1}}
                                ]
                            }
            ScapyChecker(topology_obj.players, validation_1).run_validation()

        with allure.step('Functional check IPv4 /32 static route'):
            logger.info('Functional checking IPv4 /32 static route')
            dst_ip = '20.0.0.10'
            pkt = pkt_ipv4.format(dut_mac, dst_ip)
            tcpdump_filter = 'host 20.0.0.10'
            validation_1 = {'sender': 'ha',
                            'send_args': {'interface': sender_interface, 'packets': pkt, 'count': 3},
                            'receivers':
                                [
                                    {'receiver': 'ha', 'receive_args': {'interface': receiver_interface_ha,
                                                                        'filter': tcpdump_filter, 'count': 0}},
                                    {'receiver': 'hb', 'receive_args': {'interface': receiver_interface_hb,
                                                                        'filter': tcpdump_filter,
                                                                        'count': 1}}
                                ]
                            }
            ScapyChecker(topology_obj.players, validation_1).run_validation()

        with allure.step('Functional check IPv4 /24 static route'):
            logger.info('Functional checking IPv4 /24 static route')
            dst_ip = '20.0.0.100'
            pkt = pkt_ipv4.format(dut_mac, dst_ip)
            tcpdump_filter = 'host 20.0.0.100'
            validation_2 = {'sender': 'ha',
                            'send_args': {'interface': sender_interface, 'packets': pkt, 'count': 3},
                            'receivers':
                                [
                                    {'receiver': 'ha', 'receive_args': {'interface': receiver_interface_ha,
                                                                        'filter': tcpdump_filter, 'count': 1}}
                                ]
                            }
            ScapyChecker(topology_obj.players, validation_2).run_validation()

        with allure.step('Functional check IPv6 static route via Interface'):
            logger.info('Functional checking IPv6 static route via Interface')
            dst_ip = '2000::1'
            pkt = pkt_ipv6.format(dut_mac, dst_ip)
            # Filter below fill catch Neighbour Solicitation message TODO: need to make it more precise
            tcpdump_filter = 'icmp6 && ip6[40]==135'
            validation_4 = {'sender': 'ha',
                            'send_args': {'interface': sender_interface, 'packets': pkt, 'count': 3},
                            'receivers':
                                [
                                    {'receiver': 'hb', 'receive_args': {'interface': receiver_interface_hb,
                                                                        'filter': tcpdump_filter, 'count': 1}}
                                ]
                            }
            ScapyChecker(topology_obj.players, validation_4).run_validation()

        with allure.step('Functional check IPv6 /128 static route'):
            logger.info('Functional checking IPv6 /128 static route')
            dst_ip = '2000::10'
            pkt = pkt_ipv6.format(dut_mac, dst_ip)
            tcpdump_filter = 'host 2000::10'
            validation_3 = {'sender': 'ha',
                            'send_args': {'interface': sender_interface, 'packets': pkt, 'count': 3},
                            'receivers':
                                [
                                    {'receiver': 'ha', 'receive_args': {'interface': receiver_interface_ha,
                                                                        'filter': tcpdump_filter, 'count': 0}},
                                    {'receiver': 'hb', 'receive_args': {'interface': receiver_interface_hb,
                                                                        'filter': tcpdump_filter, 'count': 1}}
                                ]
                            }
            ScapyChecker(topology_obj.players, validation_3).run_validation()

        with allure.step('Functional check IPv6 /64 static route'):
            logger.info('Functional checking IPv6 /64 static route')
            dst_ip = '2000::100'
            pkt = pkt_ipv6.format(dut_mac, dst_ip)
            tcpdump_filter = 'host 2000::100'
            validation_4 = {'sender': 'ha',
                            'send_args': {'interface': sender_interface, 'packets': pkt, 'count': 3},
                            'receivers':
                                [
                                    {'receiver': 'ha', 'receive_args': {'interface': receiver_interface_ha,
                                                                        'filter': tcpdump_filter, 'count': 1}}
                                ]
                            }
            ScapyChecker(topology_obj.players, validation_4).run_validation()

    except Exception as err:
        raise AssertionError(err)
    # TODO: cmd below for debug - need to remove later
    finally:
        dut_engine.run_cmd('sudo tail -n 200 /var/log/syslog')
        dut_engine.run_cmd('show interfaces status')
        dut_engine.run_cmd('show dropcounters configuration')
        dut_engine.run_cmd('show arp')
        dut_engine.run_cmd('show ip interfaces')
