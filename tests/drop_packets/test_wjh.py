import pytest
import logging
import scapy
import re
import random
from drop_packets import *
from ptf.testutils import verify_no_packet_any, simple_ip_only_packet, simple_ipv4ip_packet
from tests.common.helpers.assertions import pytest_assert
from collections import OrderedDict
from tests.common.platform.device_utils import fanout_switch_port_lookup
from tests.common.utilities import wait
import json


logger = logging.getLogger(__name__)
pytest.CHANNEL_CONF = None

protocols = {
    '0x6'   : 'tcp',
    '0x11'  : 'udp',
    '0x2'   : 'igmp',
    '0x4'   : 'ipencap',
    '0x1'   : 'icmp'
}


def parse_wjh_table(table):
    entries = []
    headers = []
    header_lines_num = 2
    table_lines = table.splitlines()
    if not table_lines:
        return table_lines

    # check separators index
    for sep_index in range(len(table_lines)):
        if table_lines[sep_index][0] == '-':
            break

    separators = re.split(r'\s{2,}', table.splitlines()[sep_index])[0].split()  # separators between headers and content
    headers_line = table_lines[0]
    start = 0
    # separate headers by table separators
    for sep in separators:
        curr_len = len(sep)
        headers.append(headers_line[start:start+curr_len].strip())
        start += curr_len + 1
    # check if headers appears in next line as well (only for Drop Group header - raw)
    if table_lines[1].strip() == "Group":
        headers[11] = headers[11] + " Group"
        header_lines_num = 3
    output_lines = table.splitlines()[header_lines_num:]  # Skip the header lines in output

    for line in output_lines:
        # if the previous line was too long and has splitted to 2 lines
        if line[0] == " ":
            start_index = len(line) - len(line.lstrip()) + 1
            sep_len = 0
            for j in range(len(separators)):
                sep = separators[j]
                sep_len += len(sep)
                if start_index <= sep_len:
                    break
            # j is the index in the entry
            start_index -= 1
            if (entries[-1][headers[j]].endswith(']') or entries[-1][headers[j]].endswith(':')):
                space = ''
                first_space_index = line[start_index:].index(' ')
                entries[-1][headers[j]] = entries[-1][headers[j]] + space + line[start_index:start_index + first_space_index].strip()
            else:
                space = ' '
                entries[-1][headers[j]] = entries[-1][headers[j]] + space + line.strip()
            continue

        entry = {}
        data = []
        start = 0
        for sep in separators:
            curr_len = len(sep)
            data.append(line[start:start + curr_len].strip())
            start += curr_len + 1

        for i in range(len(data)):
            entry[headers[i]] = data[i]
        entries.append(entry)
    return entries


def check_for_daemon_error(stderr_lines):
    if not stderr_lines:
        return

    for err in stderr_lines:
        if 'failed to connect to daemon' in err:
            pytest.fail("{} error has appeared.\n\
            Please check if SDK version in WJH and Syncd containers is the same.".format(err))


def get_raw_table_output(duthost, command="show what-just-happened"):
    stdout = duthost.command(command)
    check_for_daemon_error(stdout['stderr_lines'])
    if stdout['rc'] != 0:
        raise Exception(stdout['stdout'] + stdout['stderr'])
    table_output = parse_wjh_table(stdout['stdout'])
    return table_output


def get_agg_table_output(duthost, command="show what-just-happened --aggregate"):
    stdout = duthost.command(command)
    check_for_daemon_error(stdout['stderr_lines'])
    if stdout['rc'] != 0:
        raise Exception(stdout['stdout'] + stdout['stderr'])
    splitted_table = stdout['stdout'].splitlines()[3:]
    table = "\n".join(splitted_table)
    table_output = parse_wjh_table(table)
    return table_output


def check_if_entry_exists(table, pkt):
    entries = []
    entry_found = False
    ip_key = 'IP'
    proto_key = 'proto'
    if ip_key not in pkt:
        ip_key = 'IPv6'
        proto_key = 'nh'
    for entry in table:
        src_ip_port = entry['Src IP:Port'].rsplit(':', 1)
        dst_ip_port = entry['Dst IP:Port'].rsplit(':', 1)
        if (pkt.dst.lower() == entry['dMAC'].lower() and
            pkt.src.lower() == entry['sMAC'].lower()):

                if src_ip_port[0] != 'N/A':
                    if ip_key in pkt:
                        if isinstance(pkt[ip_key].dst, scapy.base_classes.Net):
                            pkt[ip_key].dst = '0.0.0.0'
                        if (pkt[ip_key].src.lower() != src_ip_port[0].replace('[', '').replace(']', '').lower() or
                            pkt[ip_key].dst.lower() != dst_ip_port[0].replace('[', '').replace(']', '').lower()):
                                continue
                        if proto_key == 'proto':
                            if (protocols[hex(pkt[ip_key].proto)] == entry['IP Proto']):
                                entries.append(entry)
                                break
                        else:
                            if (protocols[hex(pkt[ip_key].nh)] == entry['IP Proto']):
                                entries.append(entry)
                                break

                    if ('TCP' in pkt and len(src_ip_port) > 1 and len(dst_ip_port) > 1):
                        if (str(pkt['TCP'].sport) != src_ip_port[1] or
                            str(pkt['TCP'].dport) != dst_ip_port[1]):
                                continue

                entries.append(entry)

    return entries


def verify_drop_on_wjh_raw_table(duthost, pkt, discard_group):
    table = get_raw_table_output(duthost)
    entries = check_if_entry_exists(table, pkt)
    for entry in entries:
        if discard_group == entry['Drop Group']:
            return True
    return False


def verify_drop_on_agg_wjh_table(duthost, pkt, num_packets):
    table = get_agg_table_output(duthost)
    entries = check_if_entry_exists(table, pkt)
    for entry in entries:
        if int(entry['Count']) == num_packets:
            return True
    return False


def do_raw_test(discard_group, pkt, ptfadapter, duthost, ports_info, sniff_ports, tx_dut_ports=None, comparable_pkt=None):
    # send packet
    send_packets(pkt, duthost, ptfadapter, ports_info["ptf_tx_port_id"])
    # verify packet is dropped
    exp_pkt = expected_packet_mask(pkt)
    testutils.verify_no_packet_any(ptfadapter, exp_pkt, ports=sniff_ports)
    # verify wjh table
    if comparable_pkt:
        pkt = comparable_pkt
    if not verify_drop_on_wjh_raw_table(duthost, pkt, discard_group):
        pytest.fail("Could not find drop on WJH table. packet: {}".format(pkt))


def do_agg_test(discard_group, pkt, ptfadapter, duthost, ports_info, sniff_ports, tx_dut_ports=None, comparable_pkt=None):
    num_packets = random.randint(2,100)
    send_packets(pkt, duthost, ptfadapter, ports_info["ptf_tx_port_id"], num_packets=num_packets)
    # verify packet is dropped
    exp_pkt = expected_packet_mask(pkt)
    testutils.verify_no_packet_any(ptfadapter, exp_pkt, ports=sniff_ports)
    # verify wjh table
    if comparable_pkt:
        pkt = comparable_pkt
    if not verify_drop_on_agg_wjh_table(duthost, pkt, num_packets):
        pytest.fail("Could not find drop on aggregation WJH table. packet: {}".format(pkt))


@pytest.fixture(scope='module')
def do_test():
    def do_wjh_test(discard_group, pkt, ptfadapter, duthost, ports_info, sniff_ports, tx_dut_ports=None, comparable_pkt=None):
        try:
            if (pytest.CHANNEL_CONF['forwarding']['type'].find('raw') != -1):
                do_raw_test(discard_group, pkt, ptfadapter, duthost, ports_info, sniff_ports, tx_dut_ports, comparable_pkt)
        finally:
            if (pytest.CHANNEL_CONF['forwarding']['type'].find('aggregate') != -1):
                # a temporary check. there is a problem with IP header absent in aggregate
                # TODO: remove this check when issue is fixed
                if 'IP' in pkt or 'IPv6' in pkt:
                    do_agg_test(discard_group, pkt, ptfadapter, duthost, ports_info, sniff_ports, tx_dut_ports, comparable_pkt)

    return do_wjh_test


def verify_l1_raw_drop_exists(table, port):
    entry_exists = False
    for entry in table:
        if (entry['Drop Group'] == 'L1' and
            entry['sPort'] == port and
            entry['Severity'] == 'Warn' and
            entry['Drop reason - Recommended action'] == 'Generic L1 event - Check layer 1 aggregated information'):
                entry_exists = True
                break

    return entry_exists


@pytest.fixture(scope='module', autouse=True)
def check_global_configuration(duthost):
    global_conf = {}
    wjh_global = duthost.shell('sonic-db-cli CONFIG_DB hgetall "WJH|global"', module_ignore_errors=False)['stdout_lines']
    pytest_assert(wjh_global is not None, "WJH|global does not exist in config_db")

    global_iter = iter(range(len(wjh_global)))
    for i in global_iter:
        global_conf[wjh_global[i]] = wjh_global[i+1]
        next(global_iter, None)

    if global_conf['mode'] != 'debug':
        pytest.skip("Debug mode is not enabled. Skipping test.")


@pytest.fixture(scope='module', autouse=True)
def get_channel_configuration(duthost):
    config_facts  = duthost.config_facts(host=duthost.hostname, source="running")['ansible_facts']
    pytest.CHANNEL_CONF = config_facts.get('WJH_CHANNEL', {})


@pytest.fixture(scope='module', autouse=True)
def check_feature_enabled(duthost):
    features = duthost.feature_facts()['ansible_facts']['feature_facts']
    if 'what-just-happened' not in features or features['what-just-happened'] != 'enabled':
        pytest.skip("what-just-happened feature is not available. Skipping the test.")


def test_tunnel_ip_in_ip(do_test, ptfadapter, duthost, setup, pkt_fields, ports_info):
    dst_ip = pkt_fields['ipv4_dst']

    # gather facts
    dscp_range = list(range(0, 33))
    ttl_range = list(range(2, 65))
    router_mac = ports_info['dst_mac']
    src_mac = ports_info['src_mac']
    dscp_in_idx = 0
    dscp_out_idx = len(dscp_range) / 2
    ttl_in_idx = 0
    ttl_out_idx = len(ttl_range) / 2

    dscp_in = dscp_range[dscp_in_idx]
    tos_in = dscp_in << 2
    dscp_out = dscp_range[dscp_out_idx]
    tos_out = dscp_out << 2

    ecn_in = 0
    ecn_out = 2
    ttl_in = ttl_range[ttl_in_idx]
    ttl_in |= ecn_in
    ttl_out = ttl_range[ttl_out_idx]
    ttl_out |= ecn_out

    inner_src_ip = '1.1.1.1'

    inner_packet = simple_ip_only_packet(
                ip_dst=dst_ip,
                ip_src=inner_src_ip,
                ip_ttl=ttl_in,
                ip_tos=tos_in
    )

    pkt = simple_ipv4ip_packet(
        eth_dst=router_mac,
        eth_src=src_mac,
        ip_src='0.0.0.0',
        ip_dst=dst_ip,
        ip_tos=tos_out,
        ip_ttl=ttl_out,
        inner_frame=inner_packet
    )

    do_test("L3", pkt, ptfadapter, duthost, ports_info, setup['neighbor_sniff_ports'])


def check_if_l1_enabled(type):
    if "layer-1" not in pytest.CHANNEL_CONF:
        pytest.skip("layer-1 channel is not confiugred on WJH.")
    if pytest.CHANNEL_CONF['layer-1']['type'].find(type) == -1:
        pytest.skip("layer-1 {} channel type is not confiugred on WJH.".format(type))


def get_active_port(duthost):
    intf_facts = duthost.interface_facts()['ansible_facts']['ansible_interface_facts']

    for port in intf_facts.keys():
        if intf_facts[port]['active'] and port.startswith('Ethernet'):
            return port

    pytest.skip("Could not find port in active state. Skipping the test.")


def get_inactive_phy_port(duthost):
    intf_facts = duthost.interface_facts()['ansible_facts']['ansible_interface_facts']

    for port in intf_facts.keys():
        if (not intf_facts[port]['active'] and port.startswith('Ethernet')):
            return port

    pytest.skip("Could not find port in Down state. Skipping the test.")


def test_l1_raw_drop(duthost):
    check_if_l1_enabled('raw')

    port = get_active_port(duthost)
    # shut down one of the ports
    duthost.command("config interface shutdown {}".format(port))

    try:
        table = get_raw_table_output(duthost, "show what-just-happened layer-1")
        if not verify_l1_raw_drop_exists(table, port):
            pytest.fail("Could not find L1 drop on WJH table.")
    finally:
        duthost.command("config interface startup {}".format(port))


def verify_l1_agg_drop_exists(table, port, state):
    entry_exists = False
    for entry in table:
        if (entry['State'] == state and
            entry['Port'] == port and
            entry['State Change'] > 0):
                entry_exists = True
                break
    if not entry_exists:
        pytest.fail("Could not find L1 drop on WJH aggregated table.")
    return entry


def test_l1_agg_port_up(duthost):
    check_if_l1_enabled('aggregate')

    port = get_inactive_phy_port(duthost)

    duthost.command("config interface startup {}".format(port))
    try:
        table = get_agg_table_output(duthost, command="show what-just-happened layer-1 --aggregate")
        entry = verify_l1_agg_drop_exists(table, port, 'Up')
        if entry['Down Reason - Recommended Action'] != 'N/A':
            pytest.fail("Could not find L1 drop on WJH aggregated table.")
    finally:
        duthost.command("config interface shutdown {}".format(port))


def test_l1_agg_port_down(duthost):
    check_if_l1_enabled('aggregate')
    port = get_active_port(duthost)

    duthost.command("config interface shutdown {}".format(port))
    try:
        table = get_agg_table_output(duthost, command="show what-just-happened layer-1 --aggregate")
        entry = verify_l1_agg_drop_exists(table, port, 'Down')
        if entry['Down Reason - Recommended Action'] != 'Port admin down - Validate port configuration':
            pytest.fail("Could not find L1 drop on WJH aggregated table.")
    finally:
        duthost.command("config interface startup {}".format(port))


def test_l1_agg_fanout_port_down(duthost, fanouthosts):
    check_if_l1_enabled('aggregate')
    port = get_active_port(duthost)

    fanout, fanout_port = fanout_switch_port_lookup(fanouthosts, duthost.hostname, port)
    fanout.shutdown(fanout_port)
    wait(15, 'Wait for fanout port to shutdown')
    try:
        table = get_agg_table_output(duthost, command="show what-just-happened layer-1 --aggregate")
        entry = verify_l1_agg_drop_exists(table, port, 'Down')
        # TODO: need to uncomment the down reason check after SDK bug #2373739 will be fixed.
        # if entry['Down Reason - Recommended Action'] != 'Auto-negotiation failure - Set port speed manually, disable auto-negotiation':
        #     pytest.fail("Could not find L1 drop on WJH aggregated table.")
    finally:
        fanout.no_shutdown(fanout_port)