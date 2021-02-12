import pytest
import allure
import logging

from retry.api import retry_call
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.dhcp_relay_config_template import DhcpRelayConfigTemplate
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()
num_of_dhcp_servers = 10


@pytest.fixture()
def configure_dhcp_scale(topology_obj):
    dutha1 = topology_obj.ports['dut-ha-1']
    duthb1 = topology_obj.ports['dut-hb-1']
    hbdut1 = topology_obj.ports['hb-dut-1']
    dhcp_client_vlan = 100
    dhcp_servers_first_vlan = 101

    vlan_config_dict = {
        'dut': [{'vlan_id': dhcp_client_vlan, 'vlan_members': [{dutha1: 'access'}]}],
        'hb': []
    }

    ip_config_dict = {
        'dut': [{'iface': 'Vlan100', 'ips': [('10.0.0.1', '24')]}],
        'hb': []
    }

    dhcp_relay_config_dict = {
        'dut': [{'vlan_id': dhcp_client_vlan, 'dhcp_servers': []}]
    }
    # Generate 10 DHCP relays
    for item in range(dhcp_servers_first_vlan, dhcp_servers_first_vlan + num_of_dhcp_servers):
        vlan_config_dict['dut'].append({'vlan_id': item, 'vlan_members': [{duthb1: 'trunk'}]})
        vlan_config_dict['hb'].append({'vlan_id': item, 'vlan_members': [{hbdut1: None}]})
        ip_config_dict['dut'].append({'iface': 'Vlan{}'.format(item), 'ips': [('10.{}.0.1'.format(item), '24')]})
        ip_config_dict['hb'].append({'iface': '{}.{}'.format(hbdut1, item), 'ips': [('10.{}.0.2'.format(item), '24')]})
        dhcp_relay_config_dict['dut'][0]['dhcp_servers'].append('10.{}.0.2'.format(item))

    logger.info('Starting DHCP relay scale configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    DhcpRelayConfigTemplate.configuration(topology_obj, dhcp_relay_config_dict)
    logger.info('DHCP relay scale configuration completed')

    # Validation below required for update ARP for peers(DHCP servers)
    for item in range(dhcp_servers_first_vlan, dhcp_servers_first_vlan + num_of_dhcp_servers):
        validation_create_arp_ipv4 = {'sender': 'hb', 'args': {'interface': '{}.{}'.format(hbdut1, item),
                                                               'count': 3, 'dst': '10.{}.0.1'.format(item)}}
        ping_checker = PingChecker(topology_obj.players, validation_create_arp_ipv4)
        retry_call(ping_checker.run_validation, fargs=[], tries=3, delay=10, logger=logger)

    yield

    logger.info('Starting DHCP relay scale configuration cleanup')
    DhcpRelayConfigTemplate.cleanup(topology_obj, dhcp_relay_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    logger.info('DHCP relay scale configuration completed')


@allure.title('Test DHCP Relay scale')
def test_dhcp_relay_few_dhcp_servers(topology_obj, configure_dhcp_scale):
    """
    This test will check DHCP Relay functionality in case when few DHCP servers configured
    We send DHCP request from client and expected to see it on all DHCP servers which configured in relay settings
    :param topology_obj: topology object fixture
    :return: raise assertion error in case when test failed
    """
    src_mac = '64:42:a1:17:e6:35'
    chaddr = bytes.fromhex(src_mac.replace(':', ''))
    pkt = 'Ether(src="{}",dst="ff:ff:ff:ff:ff:ff")/IP(src="0.0.0.0",dst="255.255.255.255")/' \
          'UDP(sport=68,dport=67)/BOOTP(chaddr="{}",xid=RandInt())/DHCP()'.format(src_mac, chaddr)

    hadut1 = topology_obj.ports['ha-dut-1']
    hbdut1 = topology_obj.ports['hb-dut-1']

    try:
        with allure.step('Validate that DHCP packet(request) forwarded to all DHCP servers'):
            validation = {'sender': 'ha', 'send_args': {'interface': hadut1, 'packets': pkt, 'count': 1},
                          'receivers':
                              [
                                 {'receiver': 'hb',
                                  'receive_args': {'interface': hbdut1, 'filter': 'port 67', 'count': num_of_dhcp_servers}}
                              ]
                          }
            ScapyChecker(topology_obj.players, validation).run_validation()
    except BaseException as err:
        raise AssertionError(err)

