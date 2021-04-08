import allure
import logging
import pytest

from ngts.cli_wrappers.linux.linux_dhcp_clis import LinuxDhcpCli
from ngts.cli_wrappers.linux.linux_ip_clis import LinuxIpCli
from ngts.cli_wrappers.sonic.sonic_dhcp_relay_clis import SonicDhcpRelayCli
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from ngts.cli_util.stub_engine import StubEngine
from ngts.cli_util.cli_parsers import show_vlan_brief_parser
from ngts.helpers.network import get_bpf_filter_for_ipv6_address


"""

 DHCPv6 Relay Test Cases

 Documentation: https://wikinox.mellanox.com/pages/viewpage.action?spaceKey=SW&title=SONiC+NGTS+DHCPv6+Relay+Documentation

"""

logger = logging.getLogger()

RUN_DHCP6_CLIENT = LinuxDhcpCli.run_dhcp6_client
DHCP6_CLIENT_STOP_CMD = LinuxDhcpCli.stop_dhcp6_client


def get_ipv6_dhcp_relay_bpf_filter(s_port=547, d_port=547, upd_size=None, msg_type=None, msg_type_offset=48,
                                   hop_count=None, hop_count_offset=49, relay_iface_addr=None, relay_iface_offset=50,
                                   client_link_local=None, client_link_local_offset=66, relay_msg_option=None,
                                   relay_msg_option_offset=None, second_hop_count=None, second_hop_count_offset=None):
    """
    This method create tcpdump filter for DHCPv6 relay test cases - according to provided arguments
    :param s_port: packet src port
    :param d_port: packet dst port
    :param upd_size: packet size according to UDP header - DEC value
    :param msg_type: DHCP message type(relay-fwd, relay-reply) - HEX value
    :param msg_type_offset: IPv6 packet offset for message type
    :param hop_count: in case of relay-fwd packet - hop-count value - HEX value
    :param hop_count_offset: IPv6 packet offset for hop count
    :param relay_iface_addr: IPv6 address of relay iface(Vlan690 iface on DUT)
    :param relay_iface_offset: IPv6 packet offset for relay iface IPv6 address
    :param client_link_local: IPv6 link-local address of DHCP6 client
    :param client_link_local_offset: IPv6 packet offset for client link-local address
    :param relay_msg_option: relay message option - HEX value
    :param relay_msg_option_offset: IPv6 packet offset for relay message option
    :param second_hop_count: in case of relay-fwd which have encapsulated relay-fwd packet - hop-count value - HEX value
    :param second_hop_count_offset: IPv6 packet offset for second hop-count
    :return: string with tcdpump filter, example: 'udp src port 547 and dst port 547 and ip6[44:2] == 102'
    """

    tcpdump_filter = 'udp src port {s_port} and dst port {d_port}'.format(s_port=s_port, d_port=d_port)
    one_byte_size = 1
    two_bytes_size = 2

    if upd_size:
        ipv6_udp_pkt_size_offset = 44
        tcpdump_filter += ' and ip6[{}:{}] == {}'.format(ipv6_udp_pkt_size_offset, two_bytes_size, upd_size)

    if msg_type:
        tcpdump_filter += ' and ip6[{}:{}] == 0x{}'.format(msg_type_offset, one_byte_size, msg_type)

    if hop_count:
        tcpdump_filter += ' and ip6[{}:{}] == 0x{}'.format(hop_count_offset, one_byte_size, hop_count)

    if relay_iface_addr:
        tcpdump_filter += get_bpf_filter_for_ipv6_address(ipv6_address=relay_iface_addr,
                                                          offset=relay_iface_offset,
                                                          is_filter_part_of_another_filter=True)

    if client_link_local:
        tcpdump_filter += get_bpf_filter_for_ipv6_address(ipv6_address=client_link_local,
                                                          offset=client_link_local_offset,
                                                          is_filter_part_of_another_filter=True)

    if relay_msg_option and relay_msg_option_offset:
        tcpdump_filter += ' and ip6[{}:{}] == 0x{}'.format(relay_msg_option_offset, two_bytes_size, relay_msg_option)

    if second_hop_count and second_hop_count_offset:
        tcpdump_filter += ' and ip6[{}:{}] == 0x{}'.format(second_hop_count_offset, one_byte_size, second_hop_count)

    return tcpdump_filter


@pytest.fixture(scope='class')
def dhcp_client_link_local_addr(engines, interfaces):
    """
    Fixture which get dhcp client link-local IPv6 address
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    :return: link-local IPv6 address for interface ha-dut-2.690
    """
    dhclient_iface = '{}.690'.format(interfaces.ha_dut_2)
    link_local_address = LinuxIpCli().get_interface_link_local_ipv6_addresses(engines.ha, dhclient_iface)
    return link_local_address


def verify_dhcp6_client_output(engine, dhclient_cmd, dhclient_iface, expected_ip=None):
    """
    This method checks dhclient output. If expected_ip provided - it checks that IP obtained, if not - it checks
    that DHCP request failed and IP not obtained
    :param engine: dhcp client engine
    :param dhclient_cmd: dhcp client command for run dhclient
    :param dhclient_iface: interface on whicc we run dhclient
    :param expected_ip: expected ip address, if not provided - expected DHCP request fail
    """
    dhclient_output = engine.run_cmd(dhclient_cmd)

    if expected_ip:
        assert LinuxDhcpCli.reply_dhclient_message.format(dhclient_iface) in dhclient_output, 'Client does not have ' \
               'line "Reply message on " in dhcp client output'
        assert expected_ip in dhclient_output, 'dhclient output does not contain the expected IPv6 address'
        assert LinuxDhcpCli.successfull_dhclient_message in dhclient_output, 'dhclient output does not contain the ' \
                                                                             '"Bound to lease" line'
    else:
        assert LinuxDhcpCli.advertise_dhclient_message.format(dhclient_iface) not in dhclient_output, 'Unexpected' \
                'line "Advertise message on " in dhcp client output'
        assert LinuxDhcpCli.reply_dhclient_message.format(dhclient_iface) not in dhclient_output, 'Unexpected line ' \
               '"Reply message on " in dhcp client output'
        assert LinuxDhcpCli.successfull_dhclient_message not in dhclient_output, 'Unexpected line "Bound to lease" in' \
                                                                                 ' dhcp client output'


class TestDHCP6Relay:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, engines, players, interfaces, ha_dut_2_mac, hb_dut_2_mac, dut_mac,
              dhcp_client_link_local_addr):
        self.topology = topology_obj
        self.players = players
        self.engines = engines
        self.interfaces = interfaces
        self.ha_dut_2_mac = ha_dut_2_mac
        self.hb_dut_2_mac = hb_dut_2_mac
        self.dut_mac = dut_mac

        self.dhcp_server_vlan = '69'
        self.dut_dhcp_server_vlan_iface_ip = '6900::1'
        self.dhclient_main_vlan = '690'
        self.dhclient_second_vlan = '691'
        self.dhclient_main_iface = '{}.{}'.format(self.interfaces.ha_dut_2, self.dhclient_main_vlan)
        self.dhclient_second_iface = '{}.{}'.format(self.interfaces.ha_dut_2, self.dhclient_second_vlan)
        self.dut_dhcp_server_vlan_iface = 'Vlan' + self.dhcp_server_vlan
        self.dut_dhclient_main_vlan_iface = 'Vlan' + self.dhclient_main_vlan
        self.dut_dhclient_second_vlan_face = 'Vlan' + self.dhclient_second_vlan
        self.dhcp_server_iface = 'bond0.69'
        self.dhcp_server_ip = '6900::2'
        self.dut_dhclient_main_vlan_ip = '6900:1::1'
        self.dut_dhclient_second_vlan_ip = '6910::1'
        self.expected_main_vlan_ip = '6900:1::254'
        self.expected_second_vlan_ip = '6910::254'
        self.run_dhclient_main_iface = LinuxDhcpCli.run_dhcp6_client.format(self.dhclient_main_iface)
        self.run_dhclient_second_iface = LinuxDhcpCli.run_dhcp6_client.format(self.dhclient_second_iface)
        self.stop_dhclient_main_iface = LinuxDhcpCli.stop_dhcp6_client.format(self.dhclient_main_iface)
        self.stop_dhclient_second_iface = LinuxDhcpCli.stop_dhcp6_client.format(self.dhclient_second_iface)
        self.dhclient_main_iface_linklocal_ipv6 = dhcp_client_link_local_addr

        self.relay_fwd_msg_hex_value = '0c'
        self.dhcp_advertise_msg_hex_value = '02'
        self.relay_msg_hex_value = '0009'

        """
        Filter which checks that message type is Relay-FWD(type 12 - 0x0c), hop-count is 0(0x00)
        Check that inside in Relay-FWD message we have relay interface IPv6(50-62) and client link-local IPv6(66-80)
        """
        self.tcpdump_relay_forward_message_filter = get_ipv6_dhcp_relay_bpf_filter(msg_type=self.relay_fwd_msg_hex_value,
                                                                                   hop_count='00',  # hex value
                                                                                   relay_iface_addr=self.dut_dhclient_main_vlan_ip,
                                                                                   client_link_local=self.dhclient_main_iface_linklocal_ipv6)

        self.base_packet = LinuxDhcpCli.ipv6_base_pkt

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.push_gate
    @pytest.mark.build
    def test_basic_dhcp6_relay(self):
        """
        Test checks DHCPv6 Relay basic functionality. We perform DHCP6 request on 2 different VLAN ifaces
        and checks that IPv6 address obtained successfully
        :return: raise exception in case of failure
        """

        with allure.step('Verify that DHCP relay settings appear as expected in "show vlan brief"'):
            vlans_output = self.engines.dut.run_cmd('sudo show vlan brief')
            vlans_parsed_data = show_vlan_brief_parser(vlans_output)
            assert self.dhcp_server_ip in vlans_parsed_data[self.dhclient_main_vlan]['dhcp_servers'], \
                'Unable to find DHCP relay settings in VLAN output for VLAN {}'.format(self.dhclient_main_vlan)
            assert self.dhcp_server_ip in vlans_parsed_data[self.dhclient_second_vlan]['dhcp_servers'], \
                'Unable to find DHCP relay settings in VLAN output for VLAN {}'.format(self.dhclient_second_vlan)

        try:
            with allure.step('Validate that IPv6 address provided by the DHCP server, iface: {}'.format(
                    self.dhclient_main_iface)):
                logger.info('Getting IPv6 address from main DHCP client VLAN iface: {}'.format(
                    self.dhclient_main_iface))
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=self.expected_main_vlan_ip)

            with allure.step('Validate that IPv6 address provided by the DHCP server, iface: {}'.format(
                    self.dhclient_second_iface)):
                logger.info('Getting IPv6 address from second DHCP client VLAN iface: {}'.format(
                    self.dhclient_main_iface))
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_second_iface),
                                           dhclient_iface=self.dhclient_second_iface,
                                           expected_ip=self.expected_second_vlan_ip)
        except BaseException as err:
            raise AssertionError(err)
        finally:
            LinuxDhcpCli.kill_all_dhcp_clients(self.engines.ha)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcp6_relay_remove_dhcp_server(self):
        """
        Test verifies that after DHCPv6 relay settings removal, client can not get IPv6 address from DHCPv6
        server(dhcp request not forwarded)
        :return: raise exception in case of failure
        """
        cleanup_engine = StubEngine()
        try:
            with allure.step('Remove DHCP relay setting from DUT for VLAN {} IPv4'.format(self.dhclient_main_vlan)):
                SonicDhcpRelayCli.del_dhcp_relay(self.engines.dut, self.dhclient_main_vlan, '69.0.0.2')
                SonicDhcpRelayCli.add_dhcp_relay(cleanup_engine, self.dhclient_main_vlan, '69.0.0.2')

            with allure.step('Validate that IPv6 address provided by the DHCP server, iface: {}'.format(
                    self.dhclient_main_iface)):
                logger.info('Trying to get IPv6 address - when IPv4 relay settings removed')
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=self.expected_main_vlan_ip)

            with allure.step('Remove DHCP relay setting from DUT for VLAN {} IPv6'.format(self.dhclient_main_vlan)):
                SonicDhcpRelayCli.del_dhcp_relay(self.engines.dut, self.dhclient_main_vlan, '6900::2')
                SonicDhcpRelayCli.add_dhcp_relay(cleanup_engine, self.dhclient_main_vlan, '6900::2')

            with allure.step('Trying to GET IPv6 address from DHCP server when DHCP relay settings removed, '
                             'iface: {}'.format(self.dhclient_main_iface)):
                logger.info('Trying to get IPv6 address - when IPv6 relay settings removed')
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=None)

            with allure.step('Remove DHCP relay setting from DUT for VLAN {} IPv6'.format(self.dhclient_second_vlan)):
                SonicDhcpRelayCli.del_dhcp_relay(self.engines.dut, self.dhclient_second_vlan, '6900::2')
                SonicDhcpRelayCli.add_dhcp_relay(cleanup_engine, self.dhclient_second_vlan, '6900::2')

            with allure.step('Trying to GET IPv6 address from DHCP server when DHCP relay settings removed, '
                             'iface: {}'.format(self.dhclient_second_iface)):
                logger.info('Trying to get IPv6 address - when IPv6 relay settings removed - second dhcp client vlan')
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_second_iface),
                                           dhclient_iface=self.dhclient_second_iface,
                                           expected_ip=None)

        except BaseException as err:
            raise AssertionError(err)
        finally:
            LinuxDhcpCli.kill_all_dhcp_clients(self.engines.ha)
            self.engines.dut.run_cmd_set(cleanup_engine.commands_list)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcp6_relay_client_message(self):
        """
        Test checks that DHCP6 message from DHCP6 client forwarded to DHCP6 server from relay as Relay-FWD message
        :return: raise exception in case of failure
        """
        solicit_pkt = self.base_packet.format(dst_mac=LinuxDhcpCli.dhcpv6_reserved_dst_mac,
                                              src_ip=self.dhclient_main_iface_linklocal_ipv6,
                                              dst_ip=LinuxDhcpCli.dhcpv6_reserved_dst_ip,
                                              s_port=LinuxDhcpCli.ipv6_src_port,
                                              d_port=LinuxDhcpCli.ipv6_dst_port) + 'DHCP6_Solicit(trid=12345)/' \
                                                                                   'DHCP6OptElapsedTime()/' \
                                                                                   'DHCP6OptOptReq()'

        try:
            with allure.step('Validating that DHCPv6 message from DHCPv6 client forwarded to DHCPv6 server '
                             'as Relay-Forward message with expected payload'):
                validation = {'sender': 'ha', 'send_args': {'interface': self.dhclient_main_iface,
                                                            'packets': solicit_pkt,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.dhcp_server_iface,
                                                                          'filter': self.tcpdump_relay_forward_message_filter,
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending DHCP solicit message from client')
                ScapyChecker(self.players, validation).run_validation()

        except BaseException as err:
            raise AssertionError(err)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcp6_relay_relay_reply_message(self):
        """
        Test checks that Relay-Replay message from server to DHCP6 relay received by relay and correctly forwarded to
        DHCPv6 client via correct iface
        :return: raise exception in case of failure
        """
        # Filter: UDP size 25 bytes(8 bytes UDP header + 17 bytes in DHCP payload), DHCP message type Advertise
        tcpdump_filter = get_ipv6_dhcp_relay_bpf_filter(d_port=546,
                                                        upd_size=25,  # value in dec
                                                        msg_type=self.dhcp_advertise_msg_hex_value
                                                        )

        # DHCP response with few options - should forward only Relay content(without IAAdress)
        server_response_pkt = self.base_packet.format(dst_mac=self.dut_mac,
                                                      src_ip=self.dhcp_server_ip,
                                                      dst_ip=self.dut_dhcp_server_vlan_iface_ip,
                                                      s_port=LinuxDhcpCli.ipv6_server_src_port,
                                                      d_port=LinuxDhcpCli.ipv6_dst_port) + \
                              'DHCP6_RelayReply(linkaddr="{link_addr}", peeraddr="{peer_addr}")/' \
                              'DHCP6OptIAAddress()/' \
                              'DHCP6OptRelayMsg(message=[' \
                              'DHCP6_Advertise(trid=12345)/' \
                              'DHCP6OptDNSDomains(dnsdomains=["abc.com"])])'.format(link_addr=self.dut_dhclient_main_vlan_ip,
                                                                                    peer_addr=self.dhclient_main_iface_linklocal_ipv6)

        try:
            with allure.step('Validating that DHCPv6 relay-reply message from server with additional options '
                             'forwarded correctly to client(only Relay option content)'):
                validation = {'sender': 'hb', 'send_args': {'interface': self.dhcp_server_iface,
                                                            'packets': server_response_pkt,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'ha', 'receive_args': {'interface': self.dhclient_main_iface,
                                                                          'filter': tcpdump_filter, 'count': 3}}
                                  ]
                              }
                logger.info('Sending DHCP relay-reply from server to relay')
                ScapyChecker(self.players, validation).run_validation()

        except BaseException as err:
            raise AssertionError(err)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcp6_relay_relay_agent_message(self):
        """
        Test checks that DHCPv6 Relay can forward Relay-FWD messages from another relay servers. Check that
        message forwarded to DHCP6 server with correct hop-count and payload inside.
        :return: raise exception in case of failure
        """

        # Filter checks DHCP6 message type Relay-forward(0x0c)
        tcpdump_filter = get_ipv6_dhcp_relay_bpf_filter(msg_type=self.relay_fwd_msg_hex_value)
        relay_fwd_pkt_hop_count_32 = self.base_packet.format(dst_mac=self.dut_mac,
                                                             src_ip=self.expected_main_vlan_ip,
                                                             dst_ip=self.dut_dhclient_main_vlan_ip,
                                                             s_port=LinuxDhcpCli.ipv6_server_src_port,
                                                             d_port=LinuxDhcpCli.ipv6_dst_port) + \
                  'DHCP6_RelayForward(msgtype=12, hopcount=32, linkaddr="5700::1", peeraddr="fe80::e42:a1ff:fe17:e6fd")/' \
                  'DHCP6OptRelayMsg(message=[' \
                  'DHCP6_Solicit(trid=12345)/' \
                  'DHCP6OptElapsedTime()/' \
                  'DHCP6OptOptReq()])'

        try:
            with allure.step('Validating that DHCPv6 relay-forward message with hop-count=32 not encapsulated to '
                             'relay-forward message and not forwarded by relay to DHCP6 server'):

                validation = {'sender': 'ha', 'send_args': {'interface': self.dhclient_main_iface,
                                                            'packets': relay_fwd_pkt_hop_count_32,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.dhcp_server_iface,
                                                                          'filter': tcpdump_filter, 'count': 0}}
                                  ]
                              }
                logger.info('Sending DHCP relay-forward packet from dhcp client side to relay with hop-count 32')
                ScapyChecker(self.players, validation).run_validation()

        except BaseException as err:
            raise AssertionError(err)

        tcpdump_filter = get_ipv6_dhcp_relay_bpf_filter(upd_size=102, msg_type=self.relay_fwd_msg_hex_value,
                                                        hop_count='06', relay_msg_option=self.relay_msg_hex_value,
                                                        relay_msg_option_offset=82,
                                                        relay_iface_addr='5700::1', relay_iface_offset=88,
                                                        client_link_local='fe80::e42:a1ff:fe17:e6fd',
                                                        client_link_local_offset=104,
                                                        second_hop_count='05', second_hop_count_offset=87
                                                        )

        relay_fwd_pkt_hop_count_5 = self.base_packet.format(dst_mac=self.dut_mac,
                                                            src_ip=self.expected_main_vlan_ip,
                                                            dst_ip=self.dut_dhclient_main_vlan_ip,
                                                            s_port=LinuxDhcpCli.ipv6_server_src_port,
                                                            d_port=LinuxDhcpCli.ipv6_dst_port) + \
              'DHCP6_RelayForward(msgtype=12, hopcount=5, linkaddr="5700::1", peeraddr="fe80::e42:a1ff:fe17:e6fd")/' \
              'DHCP6OptRelayMsg(message=[' \
              'DHCP6_Solicit(trid=12345)/' \
              'DHCP6OptElapsedTime()/' \
              'DHCP6OptOptReq()])'

        try:
            with allure.step('Validating that DHCPv6 relay-forward message with hop-count=5 encapsulated to '
                             'relay-forward message and forwarded by relay to DHCP6 server'):

                validation = {'sender': 'ha', 'send_args': {'interface': self.dhclient_main_iface,
                                                            'packets': relay_fwd_pkt_hop_count_5,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.dhcp_server_iface,
                                                                          'filter': tcpdump_filter, 'count': 3}}
                                  ]
                              }
                logger.info('Sending DHCP relay-forward packet from dhcp client side to relay with hop-count 5')
                ScapyChecker(self.players, validation).run_validation()

        except BaseException as err:
            raise AssertionError(err)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcpv6_relay_client_request_with_empty_payload(self):
        """
        Test checks tha message from DHCP6 client with empty payload correctly forwarded by DHCP6 relay to server
        :return: raise exception in case of failure
        """
        dhcp_request_pkt = self.base_packet.format(dst_mac=LinuxDhcpCli.dhcpv6_reserved_dst_mac,
                                                   src_ip=self.dhclient_main_iface_linklocal_ipv6,
                                                   dst_ip=LinuxDhcpCli.dhcpv6_reserved_dst_ip,
                                                   s_port=LinuxDhcpCli.ipv6_src_port,
                                                   d_port=LinuxDhcpCli.ipv6_dst_port) + 'DHCP6_Request()'

        try:
            with allure.step('Validating that DHCPv6 request message with empty payload encapsulated in relay-forward'
                             'packet and forwarded to DHCP6 server'):

                validation = {'sender': 'ha', 'send_args': {'interface': self.dhclient_main_iface,
                                                            'packets': dhcp_request_pkt,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.dhcp_server_iface,
                                                                          'filter': self.tcpdump_relay_forward_message_filter,
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending DHCP request message from client with empty payload')
                ScapyChecker(self.players, validation).run_validation()

        except BaseException as err:
            raise AssertionError(err)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcpv6_relay_client_request_with_malformed_payload(self):
        """
        Test checks that message with malformed payload correctly forwarded by DHCP6 relay to DHCP6 server
        :return: raise exception in case of failure
        """
        dhcp_request_pkt_raw_payload = self.base_packet.format(dst_mac=LinuxDhcpCli.dhcpv6_reserved_dst_mac,
                                                               src_ip=self.dhclient_main_iface_linklocal_ipv6,
                                                               dst_ip=LinuxDhcpCli.dhcpv6_reserved_dst_ip,
                                                               s_port=LinuxDhcpCli.ipv6_src_port,
                                                               d_port=LinuxDhcpCli.ipv6_dst_port) + \
                                                               'DHCP6_Request()/' \
                                                               'Raw("test string here")'

        try:
            with allure.step('Validating that DHCPv6 request message with malformed payload encapsulated '
                             'in relay-forward packet and forwarded to DHCP6 server'):

                validation = {'sender': 'ha', 'send_args': {'interface': self.dhclient_main_iface,
                                                            'packets': dhcp_request_pkt_raw_payload,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.dhcp_server_iface,
                                                                          'filter': self.tcpdump_relay_forward_message_filter,
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending DHCP request message from client with malformed payload')
                ScapyChecker(self.players, validation).run_validation()
        except BaseException as err:
            raise AssertionError(err)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    @pytest.mark.build
    def test_dhcp6_relay_client_renew_request_from_global_ip(self):
        """
        Test checks that DHCP message from client with src addr from global range and dst addr of DHCPv6 server are
        correctly arrived to DHCP server and not forwarded by DHCP relay.
        :return: raise exception in case of failure
        """
        # Filter checks that regular packet exit and relay forward message does not exist(... and not ...)
        tcpdump_filter = "'(src {} and dst {}) and not (udp src port 547 and dst port 547 " \
                         "and ip6[48:1] == 0x0c " \
                         "and ip6[49:1] == 0x00)'".format(self.expected_main_vlan_ip, self.dhcp_server_ip)

        dhcp_renew_pkt_from_global_ip = self.base_packet.format(dst_mac=self.dut_mac,
                                                                src_ip=self.expected_main_vlan_ip,
                                                                dst_ip=self.dhcp_server_ip,
                                                                s_port=LinuxDhcpCli.ipv6_src_port,
                                                                d_port=LinuxDhcpCli.ipv6_dst_port) + 'DHCP6_Renew()'

        try:
            with allure.step('Validating that unicast DHCPv6 request message from client not affected by DHCP6 relay'):

                validation = {'sender': 'ha', 'send_args': {'interface': self.dhclient_main_iface,
                                                            'packets': dhcp_renew_pkt_from_global_ip,
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.dhcp_server_iface,
                                                                          'filter': tcpdump_filter, 'count': 3}},
                                  ]
                              }
                logger.info('Sending DHCP renew message from dhcp client from global IPv6 to dhcp server IPv6')
                ScapyChecker(self.players, validation).run_validation()

        except BaseException as err:
            raise AssertionError(err)

    @pytest.mark.skip('Feature was not implemented yet in SONiC')
    @pytest.mark.dhcp6_relay
    def test_dhcp6_relay_multiple_dhcp_servers(self, configure_additional_dhcp_server):
        """
        This test will check DHCP6 Relay functionality in case when multiple DHCP6 servers configured
        :return: raise assertion error in case when test failed
        """
        try:
            with allure.step('Getting IPv6 address from DHCP6 server when 2 DHCP6 servers configured and active'):
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=self.expected_main_vlan_ip)

            with allure.step('Release DHCP6 address from client'):
                self.engines.ha.run_cmd(DHCP6_CLIENT_STOP_CMD.format(self.run_dhclient_main_iface))

            with allure.step('Disable first DHCP6 server'):
                self.engines.hb.run_cmd(LinuxDhcpCli.dhcp_server_stop_cmd)

            with allure.step('Getting IPv6 from DHCP6 server when 2 DHCP6 servers configured and only second active'):
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=self.expected_main_vlan_ip)

            with allure.step('Release DHCP6 address from client'):
                self.engines.ha.run_cmd(DHCP6_CLIENT_STOP_CMD.format(self.run_dhclient_main_iface))

            with allure.step('Disable second DHCP6 server'):
                self.engines.ha.run_cmd(LinuxDhcpCli.dhcp_server_stop_cmd)

            with allure.step('Trying to GET ipv6 address from DHCP6 server when all DHCP6 servers disabled'):
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=None)

            with allure.step('Enable first DHCP6 server'):
                self.engines.hb.run_cmd(LinuxDhcpCli.dhcp_server_start_cmd)

            with allure.step('Getting IPv6 address from DHCP6 server when 2 DHCP6 servers configured '
                             'and first only active'):
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=self.expected_main_vlan_ip)

            with allure.step('Release DHCP6 address from client'):
                self.engines.ha.run_cmd(DHCP6_CLIENT_STOP_CMD.format(self.run_dhclient_main_iface))

            with allure.step('Enable second DHCP6 server'):
                self.engines.ha.run_cmd(LinuxDhcpCli.dhcp_server_start_cmd)

            with allure.step('Getting IPv6 address from DHCP6 server when 2 DHCP6 servers configured and 2 active'):
                verify_dhcp6_client_output(engine=self.engines.ha,
                                           dhclient_cmd='timeout 10 {}'.format(self.run_dhclient_main_iface),
                                           dhclient_iface=self.dhclient_main_iface,
                                           expected_ip=self.expected_main_vlan_ip)

            with allure.step('Release DHCP6 address from client'):
                self.engines.ha.run_cmd(DHCP6_CLIENT_STOP_CMD.format(self.run_dhclient_main_iface))

        except BaseException as err:
            raise AssertionError(err)
        finally:
            LinuxDhcpCli.kill_all_dhcp_clients(self.engines.ha)
