import allure
import logging
import pytest
import os
import random
from retry.api import retry_call

from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_mac_clis import SonicMacCli
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from infra.tools.yaml_tools.yaml_loops import ip_range
from scapy.all import Ether, IP, IPv6, UDP, wrpcap


"""

 Static Route Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+Static+Routes+Documentation

"""

logger = logging.getLogger()

ROUTE_APP_CONFIG_SET = 'route_scale_conf.json'
ROUTE_APP_CONFIG_SET_LOCAL_PATH = os.path.join('/tmp', ROUTE_APP_CONFIG_SET)
ROUTE_APP_CONFIG_SET_DUT_PATH = os.path.join('/etc/sonic', ROUTE_APP_CONFIG_SET)
ROUTE_APP_CONFIG_DEL = 'route_scale_conf_del.json'
ROUTE_APP_CONFIG_DEL_LOCAL_PATH = os.path.join('/tmp', ROUTE_APP_CONFIG_DEL)
ROUTE_APP_CONFIG_DEL_DUT_PATH = os.path.join('/etc/sonic', ROUTE_APP_CONFIG_DEL)


def generate_test_config(interfaces, ipv4_list, ipv6_list):
    """
    Generate route scale test configuration
    :param interfaces: fixture interfaces
    :param ipv4_list: list with IPv4 subnets(route destinations)
    :param ipv6_list: list with IPv6 subnets(route destinations)
    :return: ip_config_dict
    """
    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'ips': [('150.0.0.1', '24'), ('1500::1', '64')]},
                {'iface': interfaces.dut_hb_1, 'ips': [('160.0.0.1', '24'), ('1600::1', '64')]}],
        'ha': [{'iface': interfaces.ha_dut_1, 'ips': [('150.0.0.2', '24'), ('1500::2', '64')]}],
        'hb': [{'iface': interfaces.hb_dut_1, 'ips': [('160.0.0.2', '24'), ('1600::2', '64')]}]
    }

    # Prepare lists with IPs(routes), route masks, route next hops, route interfaces and generate app configs
    ip_list, mask_list, n_hop_list, ifaces_list = prepare_data_for_route_app_config_generation(ipv4_list, ipv6_list,
                                                                                               interfaces.dut_hb_1)

    SonicRouteCli.generate_route_app_data(ip_list, mask_list, n_hop_list, ifaces_list, ROUTE_APP_CONFIG_SET_LOCAL_PATH,
                                          op='SET')
    SonicRouteCli.generate_route_app_data(ip_list, mask_list, n_hop_list, ifaces_list, ROUTE_APP_CONFIG_DEL_LOCAL_PATH,
                                          op='DEL')

    return ip_config_dict


def prepare_data_for_route_app_config_generation(ipv4_list, ipv6_list, interface):
    """

    :param ipv4_list: list with IPv4 subnets addresses
    :param ipv6_list: list with IPv6 subnets addresses
    :param interface: interface which will be used in route app config as destination
    :return: few lists: ip_list - list with IPs, list with masks for each IP route, n_hoplist - list with next-hops
    for each IP route, ifaces_list - list with ifaces for each IP route
    """
    ip_list = ipv4_list + ipv6_list
    mask_ipv4_list = ['32'] * len(ipv4_list)
    mask_ipv6_list = ['128'] * len(ipv6_list)
    mask_list = mask_ipv4_list + mask_ipv6_list
    n_hop_ipv4_list = ['160.0.0.2'] * len(ipv4_list)
    n_hop_ipv6_list = ['1600::2'] * len(ipv6_list)
    n_hop_list = n_hop_ipv4_list + n_hop_ipv6_list
    ifaces_list = [interface] * len(ip_list)

    return ip_list, mask_list, n_hop_list, ifaces_list


def apply_config(topology_obj, engine, ip_config_dict):
    """
    Apply static route scale config on DUT
    :param topology_obj: topology_obj
    :param engine: due engine object
    :param ip_config_dict: ip config dictionary
    """
    copy_route_app_configs_to_dut(engine, ROUTE_APP_CONFIG_SET_LOCAL_PATH, ROUTE_APP_CONFIG_SET_DUT_PATH,
                                  ROUTE_APP_CONFIG_SET, ROUTE_APP_CONFIG_DEL_LOCAL_PATH,
                                  ROUTE_APP_CONFIG_DEL_DUT_PATH, ROUTE_APP_CONFIG_DEL)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    add_routes_command = 'swssconfig {}'.format(ROUTE_APP_CONFIG_SET_DUT_PATH)
    SonicGeneralCli.execute_command_in_docker(engine, docker='swss', command=add_routes_command)


def copy_route_app_configs_to_dut(engine, ROUTE_APP_CONFIG_SET_LOCAL_PATH, ROUTE_APP_CONFIG_SET_DUT_PATH,
                                  ROUTE_APP_CONFIG_SET, ROUTE_APP_CONFIG_DEL_LOCAL_PATH,
                                  ROUTE_APP_CONFIG_DEL_DUT_PATH, ROUTE_APP_CONFIG_DEL):
    """
    Copy route application config to from host DUT
    """

    engine.copy_file(source_file=ROUTE_APP_CONFIG_SET_LOCAL_PATH, dest_file=ROUTE_APP_CONFIG_SET,
                     file_system='/tmp', overwrite_file=True, verify_file=False)
    engine.run_cmd('sudo mv {} {}'.format(ROUTE_APP_CONFIG_SET_LOCAL_PATH, ROUTE_APP_CONFIG_SET_DUT_PATH))
    engine.copy_file(source_file=ROUTE_APP_CONFIG_DEL_LOCAL_PATH, dest_file=ROUTE_APP_CONFIG_DEL,
                     file_system='/tmp', overwrite_file=True, verify_file=False)
    engine.run_cmd('sudo mv {} {}'.format(ROUTE_APP_CONFIG_DEL_LOCAL_PATH, ROUTE_APP_CONFIG_DEL_DUT_PATH))


def cleanup_config(topology_obj, engine, ip_config_dict):
    """
    Remove all route configurations from DUT and hosts
    :param topology_obj: topology_obj fixture
    :param engine: dut engine
    :param ip_config_dict: ip_config_dict
    """
    del_routes_command = 'swssconfig {}'.format(ROUTE_APP_CONFIG_DEL_DUT_PATH)
    SonicGeneralCli.execute_command_in_docker(engine, docker='swss', command=del_routes_command)
    engine.run_cmd('sudo rm -f {}'.format(ROUTE_APP_CONFIG_SET_DUT_PATH))
    engine.run_cmd('sudo rm -f {}'.format(ROUTE_APP_CONFIG_DEL_DUT_PATH))
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)


@pytest.fixture()
def static_route_configuration(topology_obj, engines, interfaces, platform_params):
    """
    This function will configure 32766 IPv6 static routes and 32766 IPv6 static routes
    :return: 2 lists with IPv4 and IPv6 addresses
    """
    # Range for 32766 IPv4 and IPv6 addresses
    # TODO: need to use max number of routes from specification document
    ipv4_list = ip_range('100.0.0.1', '100.0.127.254', ip_type='ipv4', step=1)
    ipv6_list = ip_range('2000::1', '2000::7ffd', ip_type='ipv6', step=1)

    # if SPC1 - use less value which supported by platform
    if 'MSN2' in platform_params.hwsku:
        # Range for 8191 IPv4 and IPv6 addresses
        ipv4_list = ip_range('100.0.0.1', '100.0.31.255', ip_type='ipv4', step=1)
        ipv6_list = ip_range('2000::1', '2000::1fff', ip_type='ipv6', step=1)

    ip_config_dict = generate_test_config(interfaces, ipv4_list, ipv6_list)

    logger.info('Starting StaticRoute Scale configuration, using {} IPv4 and {} IPv6 routes'.format(len(ipv4_list),
                                                                                                    len(ipv6_list)))
    apply_config(topology_obj, engines.dut, ip_config_dict)
    logger.info('StaticRoute Scale configuration completed')

    yield ipv4_list, ipv6_list

    logger.info('Starting StaticRoute Scale configuration cleanup')
    cleanup_config(topology_obj, engines.dut, ip_config_dict)
    logger.info('StaticRoute Scale cleanup completed')


@pytest.mark.ngts_skip({'rm_ticket_list': [2613057]})
@allure.title('Test Scale Static Route')
def test_scale_static_route(engines, players, interfaces, static_route_configuration):
    """
    This test will check scale for static route functionality(we will use 32766 static routes)
    Test(fixture before) will configure on DUT 32766 static routes for IPv4 with mask /32
    and 32766 static routes for IPv6 with mask /128 using app db json config
    Test will use scapy for validate routes

    Validation:
    - Test will randomly choose 1k IPs and will send UDP packet from HA to HB(no direct connection).
     DUT know route to HB and will forward packet according to route table.
     Test will do validation for IPv4 and IPv6 routes

    :return: raise assertion error in case when test failed
    """
    dut_mac = SonicMacCli.get_mac_address_for_interface(engines.dut, interfaces.dut_ha_1)

    ipv4_list, ipv6_list = static_route_configuration
    # Instead of use big list with IPs use one smaller with 1k IPs(in other case - scapy will fail, too many packets)
    validation_list_ipv4_1k = [ipv4_list[0], ipv4_list[-1]] + random.sample(ipv4_list, 998) 
    validation_list_ipv6_1k = [ipv6_list[0], ipv6_list[-1]] + random.sample(ipv6_list, 998)
    tcpdump_filter = 'udp src port 1234 and dst port 5678'
    pcap_ipv4_file_path = '/tmp/1k_ipv4_packets.pcap'
    pcap_ipv6_file_path = '/tmp/1k_ipv6_packets.pcap'

    try:
        # TODO: Workaround for bug https://redmine.mellanox.com/issues/2350931
        validation_create_arp_ipv4 = {'sender': 'hb', 'args': {'interface': interfaces.hb_dut_1, 'count': 3,
                                                               'dst': '160.0.0.1'}}
        PingChecker(players, validation_create_arp_ipv4).run_validation()
        validation_create_arp_ipv6 = {'sender': 'hb', 'args': {'interface': interfaces.hb_dut_1, 'count': 3,
                                                               'dst': '1600::1'}}
        PingChecker(players, validation_create_arp_ipv6).run_validation()
        # TODO: End workaround for bug https://redmine.mellanox.com/issues/2350931

        with allure.step('Check static routes IPv4 on switch by sending traffic'):

            ipv4_pkts = Ether(dst=dut_mac)/IP(src='1.2.3.4', dst=validation_list_ipv4_1k)/UDP(sport=1234, dport=5678)
            wrpcap(pcap_ipv4_file_path, ipv4_pkts)

            do_traffic_validation(sender_host='ha', sender_iface=interfaces.ha_dut_1, pcap_file=pcap_ipv4_file_path,
                                  receiver_host='hb', receiver_iface=interfaces.hb_dut_1, tcpdump_filter=tcpdump_filter,
                                  expected_packets=len(validation_list_ipv4_1k), players=players)

        with allure.step('Check static routes IPv6 on switch by sending traffic'):
            ipv6_pkts = Ether(dst=dut_mac)/IPv6(src='1500::2', dst=validation_list_ipv6_1k)/UDP(sport=1234, dport=5678)
            wrpcap(pcap_ipv6_file_path, ipv6_pkts)

            do_traffic_validation(sender_host='ha', sender_iface=interfaces.ha_dut_1, pcap_file=pcap_ipv6_file_path,
                                  receiver_host='hb', receiver_iface=interfaces.hb_dut_1, tcpdump_filter=tcpdump_filter,
                                  expected_packets=len(validation_list_ipv6_1k), players=players)

    except Exception as err:
        raise AssertionError(err)
    finally:
        try:
            os.remove(pcap_ipv4_file_path)
            os.remove(pcap_ipv6_file_path)
        except Exception as err:
            logger.error('Failed to remove files: {}'.format(err))


def do_traffic_validation(sender_host, sender_iface, pcap_file, receiver_host, receiver_iface, tcpdump_filter,
                          expected_packets, players):
    """
    This method will run traffic validation, it created to avoid code duplication above
    """
    validation = {'sender': sender_host, 'send_args': {'interface': sender_iface, 'pcap': pcap_file,
                                                       'count': 1},
                  'receivers':
                      [
                          {'receiver': receiver_host, 'receive_args': {'interface': receiver_iface,
                                                                       'filter': tcpdump_filter,
                                                                       'count': expected_packets,
                                                                       'timeout': 20}},
                      ]
                  }
    logger.info('Sending traffic')
    scapy_checker = ScapyChecker(players, validation)
    retry_call(scapy_checker.run_validation, fargs=[], tries=3, delay=10, logger=logger)
