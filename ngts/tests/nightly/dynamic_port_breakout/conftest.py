import allure
import logging
import pytest
import random
import json
import re
import pingparsing
from retry.api import retry_call
from textwrap import dedent
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.cli_util.cli_constants import SonicConstant



"""

 Dynamic Port Breakout Test Plan

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+Port+Breakout+Documentation

"""

logger = logging.getLogger()

platform_json_path = "/usr/share/sonic/device/{PLATFORM}/platform.json"

all_breakout_options = {"1x100G[40G]", "2x50G", "4x25G[10G]", "1x400G", "2x200G", "4x100G", "8x50G",
                        "1x200G[100G,50G,40G,25G,10G,1G]",
                        "2x100G[50G,40G,25G,10G,1G]", "4x50G[40G,25G,10G,1G]", "1x25G[10G]",
                        "1x100G[50G,40G,25G,10G]", "2x50G[40G,25G,10G]", "4x25G[10G]", "1x25G[10G,1G]",
                        "1x100G[50G,40G,25G,10G,1G]", "2x50G[40G,25G,10G,1G]", "4x25G[10G,1G]",
                        "1x400G[200G,100G,50G,40G,25G,10G,1G]",
                        "2x200G[100G,50G,40G,25G,10G,1G]", "4x100G[50G,40G,25G,10G,1G]"}


@pytest.fixture(autouse=True, scope='session')
def dut_engine(topology_obj):
    return topology_obj.players['dut']['engine']


@pytest.fixture(autouse=True, scope='session')
def cli_object(topology_obj):
    return topology_obj.players['dut']['cli']


@pytest.fixture(autouse=True, scope='session')
def ports_breakout_modes(dut_engine, cli_object):
    return get_dut_breakout_modes(dut_engine, cli_object)


@pytest.fixture(autouse=True, scope='session')
def tested_modes_lb_conf(topology_obj, ports_breakout_modes):
    return get_random_lb_breakout_conf(topology_obj, ports_breakout_modes)


def get_dut_breakout_modes(dut_engine, cli_object):
    """
    parsing platform breakout options and config_db.json breakout configuration.
    :return: a dictionary with available breakout options on all dut ports
    i.e,
       { 'Ethernet0' :{'index': ['1', '1', '1', '1'],
                       'lanes': ['0', '1', '2', '3'],
                       'alias_at_lanes': ['etp1a', ' etp1b', ' etp1c', ' etp1d'],
                       'breakout_modes': ['1x200G[100G,50G,40G,25G,10G,1G]',
                                          '2x100G[50G,40G,25G,10G,1G]',
                                          '4x50G[40G,25G,10G,1G]'],
                       'breakout_port_by_modes': {'1x200G[100G,50G,40G,25G,10G,1G]': {'Ethernet0': '200G'},
                                                  '2x100G[50G,40G,25G,10G,1G]': {'Ethernet0': '100G[',
                                                                                 'Ethernet2': '100G'},
                                                  '4x50G[40G,25G,10G,1G]': {'Ethernet0': '50G',
                                                                            'Ethernet1': '50G',
                                                                            'Ethernet2': '50G',
                                                                            'Ethernet3': '50G'}},
                       'default_breakout_mode': '1x200G[100G,50G,40G,25G,10G,1G]'}, .....}

    """
    platform = cli_object.chassis.get_platform(dut_engine)
    platform_path = platform_json_path.format(PLATFORM=platform)
    platform_detailed_info_output = dut_engine.run_cmd("cat {}".format(platform_path), print_output=False)
    config_db_output = dut_engine.run_cmd("cat /etc/sonic/config_db.json ", print_output=False)
    platform_json = json.loads(platform_detailed_info_output)
    config_db_json = json.loads(config_db_output)
    return parse_platform_json(platform_json, config_db_json)


def parse_platform_json(platform_json_obj, config_db_json):
    """
    parsing platform breakout options and config_db.json breakout configuration.
    :param platform_json_obj: a json object of platform.json file
    :param config_db_json: a json object of config_db.json file
    :return: a dictionary with available breakout options on all dut ports
    i.e,
       { 'Ethernet0' :{'index': ['1', '1', '1', '1'],
                       'lanes': ['0', '1', '2', '3'],
                       'alias_at_lanes': ['etp1a', ' etp1b', ' etp1c', ' etp1d'],
                       'breakout_modes': ['1x200G[100G,50G,40G,25G,10G,1G]',
                                          '2x100G[50G,40G,25G,10G,1G]',
                                          '4x50G[40G,25G,10G,1G]'],
                       'breakout_port_by_modes': {'1x200G[100G,50G,40G,25G,10G,1G]': {'Ethernet0': '200G'},
                                                  '2x100G[50G,40G,25G,10G,1G]': {'Ethernet0': '100G',
                                                                                 'Ethernet2': '100G'},
                                                  '4x50G[40G,25G,10G,1G]': {'Ethernet0': '50G',
                                                                            'Ethernet1': '50G',
                                                                            'Ethernet2': '50G',
                                                                            'Ethernet3': '50G'}},
                       'default_breakout_mode': '1x200G[100G,50G,40G,25G,10G,1G]'}, .....}
    """
    ports_breakout_info = {}
    breakout_options = r"\dx\d+G\(\d\)\+\dx\d+G\(\d\)|\dx\d+G\[[\d*G,]*\]|\dx\d+G"
    for port_name, port_dict in platform_json_obj["interfaces"].items():
        parsed_port_dict = dict()
        parsed_port_dict[SonicConstant.INDEX] = port_dict[SonicConstant.INDEX].split(",")
        parsed_port_dict[SonicConstant.LANES] = port_dict[SonicConstant.LANES].split(",")
        parsed_port_dict[SonicConstant.ALIAS_AT_LANE] = port_dict[SonicConstant.ALIAS_AT_LANE].split(",")
        breakout_modes = re.findall(breakout_options, port_dict[SonicConstant.BREAKOUT_MODES])
        parsed_port_dict[SonicConstant.BREAKOUT_MODES] = breakout_modes
        parsed_port_dict['breakout_port_by_modes'] = get_breakout_port_by_modes(breakout_modes,
                                                                                     parsed_port_dict
                                                                                     [SonicConstant.LANES])
        parsed_port_dict['default_breakout_mode'] = \
            config_db_json[SonicConstant.BREAKOUT_CFG][port_name][SonicConstant.BRKOUT_MODE]
        ports_breakout_info[port_name] = parsed_port_dict
    return ports_breakout_info


def get_breakout_port_by_modes(breakout_modes, lanes):
    """
    :param breakout_modes: a list of breakout modes supported by a port, i.e,
    ['1x200G[100G,50G,40G,25G,10G,1G]', '2x100G[50G,40G,25G,10G,1G]', '4x50G[40G,25G,10G,1G]']
    :param lanes: a list with port lanes, i.e, for port Ethernet0 the list will be [0, 1, 2, 3]
    :return: a dictionary with ports and speed configuration result for each breakout modes,
    i.e,
    {'1x200G[100G,50G,40G,25G,10G,1G]': {'Ethernet0': '200G'},
    '2x100G[50G,40G,25G,10G,1G]': {'Ethernet0': '100G',
                                   'Ethernet2': '100G'},
    '4x50G[40G,25G,10G,1G]': {'Ethernet0': '50G', 'Ethernet1': '50G',
                              'Ethernet2': '50G', 'Ethernet3': '50G'}}
    """
    breakout_port_by_modes = {}
    for breakout_mode in breakout_modes:
        breakout_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
        if re.search(breakout_pattern, breakout_mode):
            breakout_num, speed_conf = breakout_mode.split("x")
            speed_value = r"(\d+G)\[[\d*G,]*\]|(\d+G)"
            speed = re.match(speed_value, speed_conf).group(1)
            num_lanes_after_breakout = len(lanes) // int(breakout_num)
            lanes_after_breakout = [lanes[idx:idx + num_lanes_after_breakout]
                                    for idx in range(0, len(lanes), num_lanes_after_breakout)]
            breakout_port = {'Ethernet{}'.format(lanes[0]): speed for lanes in lanes_after_breakout}
            breakout_port_by_modes[breakout_mode] = breakout_port
    return breakout_port_by_modes


def get_random_lb_breakout_conf(topology_obj, ports_breakout_modes):
    """
    :return: A dictionary with different loopback for each supported breakout modes.
    this will be used later in the test t configure different breakout modes on loopbacks and test them.
    i.e,
    {'2x100G[50G,40G,25G,10G,1G]': ('Ethernet48', 'Ethernet44'),
    '4x50G[40G,25G,10G,1G]': ('Ethernet116', 'Ethernet120')}
    """
    conf = {}
    breakout_modes_supported_lb, unbreakout_modes_supported_lb = \
        divide_breakout_modes_to_breakout_and_unbreakout_modes(topology_obj, ports_breakout_modes)
    for breakout_mode, supported_lb_list in breakout_modes_supported_lb.items():
        unused_loopbacks = list(set(supported_lb_list).difference(set(conf.values())))
        if unused_loopbacks:
            lb = random.choice(unused_loopbacks)
            conf[breakout_mode] = lb
        else:
            continue
    if len(conf.keys()) < len(breakout_modes_supported_lb.keys()):
        logger.warning("Test configuration doesn't cover all breakout modes, missing breakout modes: {}"
                       .format(list(set(breakout_modes_supported_lb.keys()).difference(set(conf.keys())))))
    if not conf:
        raise AssertionError("Failed to build valid tested configuration for this test")
    return conf


def divide_breakout_modes_to_breakout_and_unbreakout_modes(topology_obj, ports_breakout_modes):
    """

    :return: a dictionary with a list of loopbacks that support each breakout modes
    and a dictionary with a list of loopbacks that support each unbreakout modes,
    i.e,
    breakout_modes_supported_lb =

    {'4x50G[40G,25G,10G,1G]': [('Ethernet8', 'Ethernet4'), ('Ethernet36', 'Ethernet40'),...],
    '2x100G[50G,40G,25G,10G,1G]': [('Ethernet8', 'Ethernet4'), ('Ethernet36', 'Ethernet40'),...] }
    -------------------------------------------------------------------------------
    unbreakout_modes_supported_lb =
    {'1x200G[100G,50G,40G,25G,10G,1G]': [('Ethernet8', 'Ethernet4'), ('Ethernet36', 'Ethernet40'),..]}
    """
    breakout_modes = parsed_dut_loopbacks_by_breakout_modes(topology_obj, ports_breakout_modes)
    breakout_modes_supported_lb = {}
    unbreakout_modes_supported_lb = {}
    for breakout_mode, supported_lb_list in breakout_modes.items():
        if is_breakout_mode(breakout_mode):
            breakout_modes_supported_lb[breakout_mode] = supported_lb_list
        else:
            unbreakout_modes_supported_lb[breakout_mode] = supported_lb_list
    return breakout_modes_supported_lb, unbreakout_modes_supported_lb


def is_breakout_mode(breakout_mode):
    """
    :param breakout_mode: a breakout mode, such as:  "1x50G(2)+2x25G(2)", "2x100G[50G,40G,25G,10G,1G]" etc.
    :return: True if is breakout mode, False other wise
    For example:
    breakout_mode: "2x100G[50G,40G,25G,10G,1G]" -> return True
    breakout_mode: "1x50G(2)+2x25G(2)" -> return True
    breakout_mode: "1x100G[40G]" -> return False
    """
    breakout_pattern = r"\dx\d+G\(\d\)\+\dx\d+G\(\d\)"
    return re.search(breakout_pattern, breakout_mode) or not breakout_mode.startswith('1')


def parsed_dut_loopbacks_by_breakout_modes(topology_obj, ports_breakout_modes):
    """
    :return: A dictionary with a list of loopbacks that support each breakout modes.
    i.e,
    breakout_modes_supported_lb =
    {'4x50G[40G,25G,10G,1G]': [('Ethernet8', 'Ethernet4'), ('Ethernet36', 'Ethernet40'),...],
    '2x100G[50G,40G,25G,10G,1G]': [('Ethernet8', 'Ethernet4'), ('Ethernet36', 'Ethernet40'),...] },
    '1x200G[100G,50G,40G,25G,10G,1G]': [('Ethernet8', 'Ethernet4'), ('Ethernet36', 'Ethernet40'),..]}

    """
    breakout_modes_supported_lb = {}
    dut_loopback = get_dut_loopbacks(topology_obj)
    for lb in dut_loopback:
        mutual_breakoutmodes = get_mutual_breakout_modes(ports_breakout_modes, lb)
        for breakout_mode in mutual_breakoutmodes:
            if breakout_modes_supported_lb.get(breakout_mode):
                breakout_modes_supported_lb[breakout_mode].append(lb)
            else:
                breakout_modes_supported_lb[breakout_mode] = [lb]
    return breakout_modes_supported_lb


def get_mutual_breakout_modes(ports_breakout_modes, ports_list):
    """
    :param ports_list: a list of ports, i.e. ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40']
    :return: a list of breakout modes supported by all the ports on the list
    """
    breakout_mode_sets = []
    for port in ports_list:
        breakout_mode_sets.append(set(ports_breakout_modes[port]['breakout_modes']))
    return set.intersection(*breakout_mode_sets)


def get_dut_loopbacks(topology_obj):
    """
    :return: a list of ports tuple which are connected as loopbacks on dut
    i.e,
    [('Ethernet4', 'Ethernet8'), ('Ethernet40', 'Ethernet36'), ...]
    """
    dut_loopbacks = {}
    pattern = r"dut-lb\d+-\d"
    for alias, connected_alias in topology_obj.ports_interconnects.items():
        if dut_loopbacks.get(connected_alias):
            continue
        if re.search(pattern, alias):
            dut_loopbacks[alias] = connected_alias
    dut_loopback_aliases_list = dut_loopbacks.items()
    return list(map(lambda lb_tuple: (topology_obj.ports[lb_tuple[0]], topology_obj.ports[lb_tuple[1]]),
                    dut_loopback_aliases_list))


def cleanup(cleanup_list):
    """
    execute all the functions in the cleanup list
    :return: None
    """
    for func, args in cleanup_list:
        func(*args)


@pytest.fixture(autouse=True)
def cleanup_list():
    """
    Fixture to execute cleanup after a test is run
    :return: None
    """
    cleanup_list = []
    yield cleanup_list
    logger.info("------------------test teardown------------------")
    cleanup(cleanup_list)


def set_dpb_conf(topology_obj, dut_engine, cli_object, ports_breakout_modes, cleanup_list, conf, force=False):
    interfaces_config_dict = {'dut': []}
    breakout_ports_conf = {}
    for breakout_mode, ports_list in conf.items():
        for port in ports_list:
            interfaces_config_dict['dut'].append({'iface': port,
                                                  'dpb': {'breakout_mode': breakout_mode,
                                                          'original_breakout_mode':
                                                              ports_breakout_modes[port][
                                                                  'default_breakout_mode']}})
            breakout_ports_conf.update(ports_breakout_modes[port]['breakout_port_by_modes'][breakout_mode])
    cleanup_list.append((InterfaceConfigTemplate.cleanup, (topology_obj, interfaces_config_dict,)))
    cli_object.interface.configure_dpb_on_ports(dut_engine, conf, force=force)
    return breakout_ports_conf


def is_splittable(ports_breakout_modes, port_name):
    """
    :param port_name: i.e 'Ethernet4'
    :return: True if port is supporting at least 1 breakout mode, else False
    """
    has_breakout_mode = False
    port_breakout_modes = ports_breakout_modes[port_name]['breakout_modes']
    for port_breakout_mode in port_breakout_modes:
        if is_breakout_mode(port_breakout_mode):
            has_breakout_mode = True
            break
    return has_breakout_mode


def verify_port_speed_and_status(cli_object, dut_engine, breakout_ports_conf):
    """
    verify the ports state is up and speed configuration is as expected
    :param breakout_ports_conf: a dictionary with the port configuration after breakout
    {'Ethernet216': '25G',
    'Ethernet217': '25G',...}
    :return: raise assertion error in case validation of port status or speed fail
    """
    interfaces_list = list(breakout_ports_conf.keys())
    with allure.step('Verify interfaces {} are in up state'.format(interfaces_list)):
        retry_call(cli_object.interface.check_ports_status,
                   fargs=[dut_engine, interfaces_list],
                   tries=2, delay=2, logger=logger)
    verify_port_speed(dut_engine, cli_object, breakout_ports_conf)


def verify_port_speed(dut_engine, cli_object, breakout_ports_conf):
    """
    :param breakout_ports_conf: a dictionary with the port configuration after breakout
    {'Ethernet216': '25G',
    'Ethernet217': '25G',...}
    :return: raise assertion error in case configured speed is not as expected
    """
    interfaces_list = list(breakout_ports_conf.keys())
    actual_speed_conf = cli_object.interface.get_interfaces_speed(dut_engine, interfaces_list)
    compare_actual_and_expected_speeds(breakout_ports_conf, actual_speed_conf)


def compare_actual_and_expected_speeds(expected_speeds_dict, actual_speeds_dict):
    """
    :param expected_speeds_dict: a dictionary of ports expected speeds,
    i.e, {'Ethernet216': '25G',
    'Ethernet217': '25G',...}
    :param actual_speeds_dict: a dictionary of ports actual speeds
    :return: raise assertion error in case expected and actual speed don't match
    """
    with allure.step('Compare expected and actual speeds'):
        logger.debug("expected_speeds_dict: {}".format(expected_speeds_dict))
        logger.debug("actual_speeds_dict: {}".format(actual_speeds_dict))
        for interface, expected_speed in expected_speeds_dict.items():
            actual_speed = actual_speeds_dict[interface]
            assert actual_speed == expected_speed, "Interface {} actual speed ({}) " \
                                                   "after breakout doesn't match expected speed ({}),". \
                format(interface, actual_speed, expected_speed)


def verify_no_breakout(dut_engine, cli_object, ports_breakout_modes, conf):
    """
    :param conf: a dictionary of the tested configuration,
    i.e breakout mode and ports list which breakout mode will be applied on
    {'2x50G[40G,25G,10G,1G]': ('Ethernet212', 'Ethernet216'), '4x25G[10G,1G]': ('Ethernet228', 'Ethernet232')}
    :return: raise assertion error in case the breakout mode is still applied on the ports
    """
    all_breakout_ports = []
    ports_list = []
    for breakout_mode, ports in conf.items():
        for port in ports:
            ports_list.append(port)
            breakout_ports = list(
                ports_breakout_modes[port]['breakout_port_by_modes'][breakout_mode].keys())
            breakout_ports.remove(port)
            all_breakout_ports += breakout_ports

    with allure.step('Verify ports {} are up'.format(ports_list)):
        retry_call(cli_object.interface.check_ports_status,
                   fargs=[dut_engine, ports_list],
                   tries=2, delay=2, logger=logger)

    with allure.step('Verify there is no breakout ports: {}'.format(all_breakout_ports)):
        cmd_output = cli_object.interface.show_interfaces_status(dut_engine)
        verify_show_cmd(cmd_output, [(port, False) for port in all_breakout_ports])


def send_ping_and_verify_results(topology_obj, dut_engine, cleanup_list, conf):
    """
    :param conf: a dictionary of the tested configuration,
    i.e breakout mode and ports list which breakout mode will be applied on
    {'2x50G[40G,25G,10G,1G]': ('Ethernet212', 'Ethernet216'), '4x25G[10G,1G]': ('Ethernet228', 'Ethernet232')}
    :return: raise assertion error in case ping failed
    """
    ports_list = get_ports_list_from_loopback_tuple_list(conf.values())
    ports_ip_conf = {port: {} for port in ports_list}
    set_ip_dependency(topology_obj, ports_list, ports_ip_conf, cleanup_list)
    for breakout_mode, lb in conf.items():
        with allure.step('Send ping validation between ports: {}'.format(lb)):
            src_port = lb[0]
            dst_port = lb[1]
            src_ip = ports_ip_conf[lb[0]]['ip']
            dst_ip = ports_ip_conf[lb[1]]['ip']
            ping_cmd = "ping -I {} {} -c 3".format(src_port, dst_ip)
            logger.info('Sending 3 tagged packets from interface {} with ip {} to interface {} with ip {}'
                        .format(src_port, src_ip, dst_port, dst_ip))
            output = dut_engine.run_cmd(ping_cmd)
            parser = pingparsing.PingParsing()
            stats = parser.parse(dedent(output))
            json_ping_output = json.dumps(stats.as_dict(), indent=4)
            logger.info("[extracted ping statistics]:\n {}".format(json_ping_output))
            assert json_ping_output["packet_loss_count"] == 0, \
                "Ping validation failed because ping actual loss count: {}, expected loss count: 0"\
                    .format(json_ping_output["packet_loss_count"])


def get_ports_list_from_loopback_tuple_list(lb_list):
    """
    :param lb_list: a list of tuples of ports connected by loopback, i.e. [('Ethernet8', 'Ethernet4'),
    ('Ethernet36', 'Ethernet40'),..]
    :return: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
    """
    ports_list = []
    for lb_port_1, lb_port_2 in lb_list:
        ports_list.append(lb_port_1)
        ports_list.append(lb_port_2)
    return ports_list


def set_ip_dependency(topology_obj, ports_list, ports_dependencies, cleanup_list):
    """
    configure ip dependency on all the ports in ports_list and update the configuration
    in the dictionary ports_dependencies.
    :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
    :param ports_dependencies: a dictionary with the ports configured dependencies information
    for example,
    {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1},
    :return: None
    """
    ip_config_dict = {'dut': []}
    idx = 1
    for port in ports_list:
        ip = '10.0.0.{}'.format(idx)
        ip_config_dict['dut'].append({'iface': port, 'ips': [(ip, '24')]})
        ports_dependencies[port].update({'ip': ip})
        idx += 1
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    cleanup_list.append((IpConfigTemplate.cleanup, (topology_obj, ip_config_dict,)))
