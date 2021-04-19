import allure
import logging
import re
import ipaddress
import time
import pytest
from retry.api import retry_call

from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from ngts.cli_wrappers.linux.linux_interface_clis import LinuxInterfaceCli
from ngts.cli_wrappers.linux.linux_mac_clis import LinuxMacCli
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.conftest import cleanup_last_config_in_stack


logger = logging.getLogger()
PORTCHANNEL_NAME = 'PortChannel1111'
BASE_PKT = 'Ether(dst="{}")/IP(src="50.0.0.2",dst="50.0.0.3")/{}()/Raw()'
CHIP_LAGS_LIM = {
    'SPC':  64,
    'SPC2': 128,
    'SPC3': 128
}
CHIP_LAG_MEMBERS_LIM = {
    'SPC':  32,
    'SPC2': 64,
    'SPC3': 64
}


@pytest.mark.ngts_skip({'platform_prefix_list': ['simx'], 'rm_ticket_list': [2618296]})
@allure.title('LAG_LACP core functionality and reboot')
def test_core_functionality_with_reboot(topology_obj, traffic_type, interfaces, engines, cleanup_list):
    """
    This test case will check the base functionality of LAG/LACP feature.
    Config base configuration as in the picture below.
    Validate port channel and links state.
    Disable port 1 on the host. Validate port channel was affected.
    Disable port 2 and enable port 1 on the host. Validate port channel was affected.
    Enable port 2 on the host. Validate port channel was affected.
    Reboot switch and validate.
    :param topology_obj: topology object
    :param traffic_type: the type of the traffic
    :param interfaces: interfaces fixture
    :param engines: engines fixture
    :param cleanup_list: list with functions to cleanup
    :return: raise assertion error on unexpected behavior

                                                dut
                                       ------------------------------
                     ha                |    Vlan50 50.0.0.1/24      |                                  hb
              ------------------       |                            |duthb1 in lag               ------------------
              |                |       |dutha1 vlan50 trunk         |----------------------------|                |
              |     hadut1.50  |-------|                            |              hbdut1 in bond|  bond0.50      |
              |     50.0.0.2/24|       |                            |              hbdut2 in bond|  50.0.0.3/24   |
              |                |       |            PortChannel1111 |----------------------------|                |
              ------------------       |              vlan 50 trunk |duthb2 in lag               ------------------
                                       |                            |
                                       ------------------------------
    """
    dut_cli = topology_obj.players['dut']['cli']

    cleanup_list.append((LinuxInterfaceCli.enable_interface, (engines.hb, interfaces.dut_hb_1,)))
    cleanup_list.append((LinuxInterfaceCli.enable_interface, (engines.hb, interfaces.dut_hb_2,)))
    cleanup_list.append((LinuxInterfaceCli.enable_interface, (engines.hb, 'bond0',)))

    # LAG/LACP config which will be used in this test
    lag_lacp_config_dict = {
        'dut': [{'type': 'lacp', 'name': PORTCHANNEL_NAME, 'members': [interfaces.dut_hb_1, interfaces.dut_hb_2]}]
    }
    add_lag_conf(topology_obj, lag_lacp_config_dict, cleanup_list)

    # VLAN config which will be used in this test
    vlan_config_dict = {
        'dut': [{'vlan_id': 50, 'vlan_members': [{PORTCHANNEL_NAME: 'trunk'}]}]
    }
    add_vlan_conf(topology_obj, vlan_config_dict, cleanup_list)

    try:
        with allure.step('Validate the PortChannel status'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'S')],
                                                  tries=1)

        with allure.step('Validate the base functionality of LAG - traffic'):
            # PING below need to prevent issue when packet not forwarded to host from switch
            validation_ping = {'sender': 'ha', 'args': {'count': 3, 'dst': '50.0.0.1'}}
            PingChecker(topology_obj.players, validation_ping).run_validation()
            traffic_validation(topology_obj, traffic_type)

        with allure.step('STEP1: Disable interface 1 on host, traffic should pass via interface 2'):
            LinuxInterfaceCli.disable_interface(engines.hb, interfaces.hb_dut_1)
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'D'), (interfaces.dut_hb_2, 'S')])
            traffic_validation(topology_obj, traffic_type)

        with allure.step('STEP2: Enable interface 1 and disable interface 2 on host,'
                         ' traffic should pass via interface 1'):
            LinuxInterfaceCli.enable_interface(engines.hb, interfaces.hb_dut_1)
            LinuxInterfaceCli.disable_interface(engines.hb, interfaces.hb_dut_2)
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'D')])
            traffic_validation(topology_obj, traffic_type)

        with allure.step('STEP3: Enable both interfaces on host'):
            LinuxInterfaceCli.enable_interface(engines.hb, interfaces.hb_dut_2)
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'S')])
            traffic_validation(topology_obj, traffic_type)

        with allure.step('STEP4: Reboot dut'):
            dut_cli.general.save_configuration(engines.dut)
            dut_cli.general.reboot_flow(engines.dut, topology_obj=topology_obj)

        with allure.step('STEP5: Validate port channel status and send traffic'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'S')])
            traffic_validation(topology_obj, traffic_type)

        with allure.step('STEP6: Validate fallback parameter (default - false)'):
            LinuxInterfaceCli.disable_interface(engines.hb, 'bond0')
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Dw',
                                                  [(interfaces.dut_hb_1, 'D'), (interfaces.dut_hb_2, 'D')])
            LinuxInterfaceCli.enable_interface(engines.hb, 'bond0')

        with allure.step('STEP7: Validate configuration of LAG with fallback parameter "true"'):
            cleanup_last_config_in_stack(cleanup_list)  # pop vlan cleanup from stack
            cleanup_last_config_in_stack(cleanup_list)  # remove LAG
            lag_lacp_config_dict = {
                'dut': [{'type': 'lacp', 'name': PORTCHANNEL_NAME, 'members': [interfaces.dut_hb_1, interfaces.dut_hb_2],
                         'params': '--fallback enable'}]
            }
            add_lag_conf(topology_obj, lag_lacp_config_dict, cleanup_list)
            add_vlan_conf(topology_obj, vlan_config_dict, cleanup_list)
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'S')])
            traffic_validation(topology_obj, traffic_type)

        with allure.step('STEP8: Validate functionality of LAG with fallback parameter "true"'):
            LinuxInterfaceCli.disable_interface(engines.hb, 'bond0')
            logger.info('Wait 120 seconds for LACP timeout')
            time.sleep(120)
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'S')])

    except BaseException as err:
        raise AssertionError(err)


@allure.title('Test port cannot be added to LAG')
def test_port_cannot_be_added_to_lag(topology_obj, traffic_type, interfaces, engines, cleanup_list):
    """
    This test case will check the interop of the port channel.
    Check 'ip', 'speed', 'other_lag', 'vlan' dependencies.
    Config dependency on a port. Trying to add the port to port channel.
    Validate expected error message.
    :param topology_obj: topology object
    :param traffic_type: the type of the traffic
    :param interfaces: interfaces fixture
    :param engines: engines fixture
    :param cleanup_list: list with functions to cleanup
    :return: raise assertion error on unexpected behavior
    """
    try:
        dut_cli = topology_obj.players['dut']['cli']

        # LAG/LACP config which will be used in this test
        lag_lacp_config_dict = {
            'dut': [{'type': 'lacp', 'name': PORTCHANNEL_NAME, 'members': [interfaces.dut_hb_1]}]
        }
        add_lag_conf(topology_obj, lag_lacp_config_dict, cleanup_list)

        # Add VLAN config
        vlan_config_dict = {
            'dut': [{'vlan_id': 50, 'vlan_members': [{PORTCHANNEL_NAME: 'trunk'}]}]
        }
        add_vlan_conf(topology_obj, vlan_config_dict, cleanup_list)

        dependency_list = ['ip', 'speed', 'other_lag', 'vlan']

        for dependency in dependency_list:
            check_dependency(topology_obj, dependency, cleanup_list)

        with allure.step('Validate the PortChannel status'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S')],
                                                  tries=1)

        with allure.step('Validate the traffic via the LAG'):
            # PING below need to prevent issue when packet not forwarded to host from switch
            validation_ping = {'sender': 'ha', 'args': {'count': 3, 'dst': '50.0.0.1'}}
            PingChecker(topology_obj.players, validation_ping).run_validation()
            traffic_validation(topology_obj, traffic_type)

    except BaseException as err:
        raise AssertionError(err)


@allure.title('LAG min-links Test')
def test_lag_min_links(topology_obj, traffic_type, interfaces, engines, cleanup_list):
    """
    This test case will check the functionality of 'min-links' parameter.
    Checks that port channel in down state, until he have num of members < min-links parameter.( 0 value is exclusion)
    :param topology_obj: topology object
    :param traffic_type: the type of the traffic
    :param interfaces: interfaces fixture
    :param engines: engines fixture
    :param cleanup_list: list with functions to cleanup
    :return: raise assertion error on unexpected behavior
    """
    try:
        dut_cli = topology_obj.players['dut']['cli']

        with allure.step('STEP1: Create PortChannel with min-links 0 and no members'):
            lag_config_dict = {
                'dut': [{'type': 'lacp', 'name': PORTCHANNEL_NAME, 'members': [], 'params': '--min-links 0'}]
            }
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Validate the PortChannel status is Down'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Dw',
                                                  [],
                                                  tries=2)
        cleanup_last_config_in_stack(cleanup_list)

        with allure.step('STEP2: Create PortChannel with min-links 1 and 1 member'):
            lag_config_dict = {
                'dut': [{'type': 'lacp',
                         'name': PORTCHANNEL_NAME,
                         'members': [interfaces.dut_hb_1],
                         'params': '--min-links 1'}]
            }
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Validate the PortChannel status is Up, port status is Selected'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S')],
                                                  tries=2)
        cleanup_last_config_in_stack(cleanup_list)

        with allure.step('STEP3: Create PortChannel with min-links 2 and 1 member'):
            lag_config_dict = {
                'dut': [{'type': 'lacp',
                         'name': PORTCHANNEL_NAME,
                         'members': [interfaces.dut_hb_1],
                         'params': '--min-links 2'}]
            }
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Validate the PortChannel status is Down, port status is Selected'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Dw',
                                                  [(interfaces.dut_hb_1, 'S')],
                                                  tries=2)

        with allure.step('STEP4: Add second member to PortChannel with min-links 2'):
            lag_config_dict = {
                'dut': [{'type': 'lacp', 'name': PORTCHANNEL_NAME, 'members': [interfaces.dut_hb_2]}]
            }
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Validate the PortChannel status is Up, both members status is Selected'):
            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  [(interfaces.dut_hb_1, 'S'), (interfaces.dut_hb_2, 'S')],
                                                  tries=2)

        vlan_config_dict = {
            'dut': [{'vlan_id': 50, 'vlan_members': [{PORTCHANNEL_NAME: 'trunk'}]}]
        }
        add_vlan_conf(topology_obj, vlan_config_dict, cleanup_list)

        with allure.step('Validate the traffic via a LAG'):
            validation_ping = {'sender': 'ha', 'args': {'count': 3, 'dst': '50.0.0.1'}}
            PingChecker(topology_obj.players, validation_ping).run_validation()
            traffic_validation(topology_obj, traffic_type)
    except BaseException as err:
        raise AssertionError(err)


@allure.title('LAG members scale Test')
def test_lag_members_scale(topology_obj, interfaces, engines, cleanup_list):
    """
    This test case will check the configuration of 1 port channel with max number of members.
    :param topology_obj: topology object
    :param interfaces: interfaces fixture
    :param engines: engines fixture
    :param cleanup_list: list with functions to cleanup
    :return: raise assertion error on unexpected behavior
    """
    try:
        dut_cli = topology_obj.players['dut']['cli']

        del_port_from_vlan(engines.dut, interfaces.dut_ha_1, '50', cleanup_list)

        chip_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['chip_type']
        max_lag_members = CHIP_LAG_MEMBERS_LIM[chip_type]
        all_interfaces = list(dut_cli.interface.parse_interfaces_status(engines.dut))
        member_interfaces = all_interfaces[:min(max_lag_members, len(all_interfaces))]

        with allure.step('Set same speed to all interfaces'):
            dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(engines.dut, all_interfaces)
            interfaces_config_list = []
            for interface in all_interfaces:
                interfaces_config_list.append({'iface': interface,
                                               'speed': '10G',
                                               'original_speed': dut_original_interfaces_speeds.get(interface, '10G')})
            interfaces_config_dict = {
                'dut': interfaces_config_list
            }
            add_interface_conf(topology_obj, interfaces_config_dict, cleanup_list)

        with allure.step('Create PortChannel with all ports as members'):
            lag_config_dict = {
                'dut': [{'type': 'lacp', 'name': PORTCHANNEL_NAME, 'members': member_interfaces}]
            }
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Check that all interfaces in Up state'.format()):
            ports_list = member_interfaces + [PORTCHANNEL_NAME]
            retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, ports_list], tries=10, delay=10,
                       logger=logger)

        with allure.step('Validate members status in PortChannel'):
            expected_ports_status_list = []
            for interface in member_interfaces:
                if interface in [interfaces.dut_hb_1, interfaces.dut_hb_2]:
                    expected_ports_status_list.append((interface, 'S'))
                else:
                    expected_ports_status_list.append((interface, 'D'))

            verify_port_channel_status_with_retry(dut_cli,
                                                  engines.dut,
                                                  PORTCHANNEL_NAME,
                                                  'Up',
                                                  expected_ports_status_list,
                                                  tries=3)
        with allure.step('Validate dockers status'):
            SonicGeneralCli.verify_dockers_are_up(engines.dut)
    except BaseException as err:
        raise AssertionError(err)


@pytest.mark.ngts_skip({'platform_prefix_list': ['simx'], 'rm_ticket_list': [2618296]})
@allure.title('LAGs scale Test')
def test_lags_scale(topology_obj, engines, cleanup_list):
    """
    This test case will check the configuration of maximum number of port channels without members.
    :param topology_obj: topology object
    :param engines: engines fixture
    :param cleanup_list: list with functions to cleanup
    :return: raise assertion error on unexpected behavior
    """
    try:
        dut_cli = topology_obj.players['dut']['cli']

        chip_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['chip_type']
        number_of_lags = CHIP_LAGS_LIM[chip_type]

        lag_config_dict, lag_expected_info = get_lags_scale_configuration(number_of_lags)

        with allure.step('Create max number of PortChannels'):
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Validation port channels were created'):
            retry_call(
                verify_port_channels_status,
                fargs=[dut_cli, engines.dut, lag_expected_info],
                tries=10,
                delay=5,
                logger=logger,
            )

        with allure.step('Validation for bug 2435254 - reboot, validate dockers and lags'):
            dut_cli.general.save_configuration(engines.dut)
            dut_cli.general.reboot_flow(engines.dut, reboot_type='reboot', topology_obj=topology_obj)
            retry_call(
                verify_port_channels_status,
                fargs=[dut_cli, engines.dut, lag_expected_info],
                tries=10,
                delay=5,
                logger=logger,
            )

    except BaseException as err:
        raise AssertionError(err)


@pytest.mark.ngts_skip({'rm_ticket_list': [2602350]})
@allure.title('LAG port channels with member scale Test')
def test_lags_with_member_scale(topology_obj, interfaces, engines, cleanup_list):
    """
    This test case will check the configuration of maximum number of port channels with one member and IP address.
    :param topology_obj: topology object
    :param interfaces: interfaces fixture
    :param engines: engines fixture
    :param cleanup_list: list with functions to cleanup
    :return: raise assertion error on unexpected behavior
    """
    try:
        dut_cli = topology_obj.players['dut']['cli']

        del_port_from_vlan(engines.dut, interfaces.dut_ha_1, '50', cleanup_list)

        chip_type = topology_obj.players['dut']['attributes'].noga_query_data['attributes']['Specific']['chip_type']
        max_lag_members = CHIP_LAGS_LIM[chip_type]

        all_interfaces = list(dut_cli.interface.parse_interfaces_status(engines.dut))

        lag_config_dict, ip_config_dict, lag_expected_info, ip_expected_info\
            = get_lags_with_member_scale_configuration(interfaces, max_lag_members, all_interfaces)

        with allure.step('Create max numbers of PortChannels, each one with member'):
            add_lag_conf(topology_obj, lag_config_dict, cleanup_list)

        with allure.step('Validate PortChannels and members status'):
            verify_port_channels_status(dut_cli, engines.dut, lag_expected_info)

        with allure.step('Validate for bug 2435816 - add and verify IPs on all PortChannels'):
            add_ip_conf(topology_obj, ip_config_dict, cleanup_list)
            verify_port_channels_ip(dut_cli, engines.dut, ip_expected_info)
    except BaseException as err:
        raise AssertionError(err)


def get_lags_scale_configuration(number_of_lags):
    """
    Create configuration info for large number of lags and expected result
    :param number_of_lags: number of lags
    :return: lag_config_dict - lag configuration dictionary
             lag_expected_info - lag expected status information
    """
    base_lag_name = 'PortChannel'
    base_lag_index = '1'
    lag_config_list = []
    lag_expected_info = []
    logger.info('Generate PortChannels configuration lists')
    for index in range(number_of_lags):
        lag_name = '{}{}'.format(base_lag_name, str(int(base_lag_index) + index))
        lag_config_list.append({'type': 'lacp', 'name': lag_name, 'members': []})
        lag_expected_info.append((r'{PORTCHANNEL}.*{PORTCHANNEL_STATUS}.*N/A'
                                  .format(PORTCHANNEL=lag_name,
                                          PORTCHANNEL_STATUS='Dw'), True))
    lag_config_dict = {
        'dut': lag_config_list
    }
    logger.debug('lag_config_dict: {} \nlag_expected_info: {}'.format(lag_config_dict, lag_expected_info))
    return lag_config_dict, lag_expected_info


def get_lags_with_member_scale_configuration(interfaces, max_lag_members, all_interfaces):
    """
    Create configuration info for lag, ip, vlan and expected result
    :param interfaces: interfaces object
    :param max_lag_members: system SDK limit of number members in lag
    :param all_interfaces: all interfaces list
    :return: lag_config_dict - lag configuration dictionary
             ip_config_dict - ip configuration dictionary
             vlan_config_dict - vlan configuration dictionary
             lag_expected_info - lag expected status information
    """
    base_lag_name = 'PortChannel'
    base_lag_index = '2000'
    base_ip = ipaddress.IPv4Address('100.0.0.0')
    ip_config_list = []
    lag_config_list = []
    lag_expected_info = []
    ip_expected_info = []
    logger.info('Generate PortChannels configuration lists')
    for index in range(min(int(max_lag_members), len(all_interfaces))):
        lag_name = '{}{}'.format(base_lag_name, str(int(base_lag_index) + index))
        lag_config_list.append({'type': 'lacp', 'name': lag_name, 'members': [all_interfaces[index]]})
        if all_interfaces[index] in [interfaces.dut_hb_1, interfaces.dut_hb_2]:
            lag_status = 'Up'
            port_status = 'S'
        else:
            lag_status = 'Dw'
            port_status = 'D'
        # create lists with expected results
        lag_expected_info.append((r'{PORTCHANNEL}.*{PORTCHANNEL_STATUS}.*{PORT}\({PORTS_STATUS}\)'
                                  .format(PORTCHANNEL=lag_name,
                                          PORTCHANNEL_STATUS=lag_status,
                                          PORT=all_interfaces[index],
                                          PORTS_STATUS=port_status), True))
        lag_ip_address = base_ip + index
        ip_config_list.append({'iface': lag_name, 'ips': [(lag_ip_address, '24')]})
        ip_expected_info.append((r'{PORTCHANNEL}\s+{IP}'.format(PORTCHANNEL=lag_name, IP=lag_ip_address), True))

    lag_config_dict = {
        'dut': lag_config_list
    }
    ip_config_dict = {
        'dut': ip_config_list
    }
    logger.debug('lag_config_dict: {} \nip_config_dict: {} \n lag_expected_info: {}\n ip_expected_info: {}'
                 .format(lag_config_dict, ip_config_dict, lag_expected_info, ip_expected_info))
    return lag_config_dict, ip_config_dict, lag_expected_info, ip_expected_info


def check_dependency(topology_obj, dependency, cleanup_list):
    """
    Verify port channel dependencies
    :param topology_obj: topology object
    :param dependency: type of dependency
    :param cleanup_list: list with functions to cleanup
    :return: None, raise error in case of unexpected result
    """
    with allure.step('Validate the {} dependency'.format(dependency)):
        dut_engine = topology_obj.players['dut']['engine']
        dut_cli = topology_obj.players['dut']['cli']
        duthb2 = topology_obj.ports['dut-hb-2']
        eval('config_{}_dependency(topology_obj, cleanup_list)'.format(dependency))
        err_msg = eval('get_{}_dependency_err_msg(duthb2)'.format(dependency))
        verify_add_member_to_lag_failed_with_err(dut_engine, dut_cli, duthb2, err_msg)
        cleanup_last_config_in_stack(cleanup_list)


def config_ip_dependency(topology_obj, cleanup_list):
    """
    Add ip configurations to verify the ip dependency
    :param topology_obj: topology object
    :param cleanup_list: list with functions to cleanup
    """
    duthb2 = topology_obj.ports['dut-hb-2']
    ip_config_dict = {
        'dut': [{'iface': duthb2, 'ips': [('50.0.0.10', '24')]}]
    }
    add_ip_conf(topology_obj, ip_config_dict, cleanup_list)


def add_ip_conf(topology_obj, ip_config_dict, cleanup_list):
    """
    Add ip configurations
    :param topology_obj: topology object
    :param ip_config_dict: vlan configuration to add
    :param cleanup_list: list with functions to cleanup
    """
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    cleanup_list.append((IpConfigTemplate.cleanup, (topology_obj, ip_config_dict,)))


def get_ip_dependency_err_msg(interface):
    """
    Get expected error message of adding the port to port channel
    :param interface: interface name
    :return: expected error message
    """
    err_msg = '{} has ip address 50.0.0.10/24 configured'.format(interface)
    return err_msg


def config_speed_dependency(topology_obj, cleanup_list):
    """
    Add speed configurations to verify the speed dependency
    :param topology_obj: topology object
    :param cleanup_list: list with functions to cleanup
    """
    duthb2 = topology_obj.ports['dut-hb-2']
    interfaces_config_dict = {
        'dut': [{'iface': duthb2, 'speed': '10G', 'original_speed': '1G'}]
    }
    add_interface_conf(topology_obj, interfaces_config_dict, cleanup_list)


def add_interface_conf(topology_obj, interfaces_config_dict, cleanup_list):
    """
    Add interface configurations
    :param topology_obj: topology object
    :param interfaces_config_dict: vlan configuration to add
    :param cleanup_list: list with functions to cleanup
    """
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    cleanup_list.append((InterfaceConfigTemplate.cleanup, (topology_obj, interfaces_config_dict,)))


def get_speed_dependency_err_msg(interface):
    """
    Get expected error message of adding the port to port channel
    :param interface: interface name
    :return: expected error message
    """
    err_msg = 'Port speed of {} is different than the other members of the portchannel {}'. \
        format(interface, PORTCHANNEL_NAME)
    return err_msg


def config_other_lag_dependency(topology_obj, cleanup_list):
    """
    Add lag configurations to verify the lag dependency
    :param topology_obj: topology object
    :param cleanup_list: list with functions to cleanup
    """
    duthb2 = topology_obj.ports['dut-hb-2']
    lag_config_dict_second_lag = {
        'dut': [{'type': 'lacp', 'name': 'PortChannel2222', 'members': [duthb2]}]
    }
    add_lag_conf(topology_obj, lag_config_dict_second_lag, cleanup_list)


def add_lag_conf(topology_obj, lag_config_dict, cleanup_list):
    """
    Add lag configurations
    :param topology_obj: topology object
    :param lag_config_dict: vlan configuration to add
    :param cleanup_list: list with functions to cleanup
    """
    LagLacpConfigTemplate.configuration(topology_obj, lag_config_dict)
    cleanup_list.append((LagLacpConfigTemplate.cleanup, (topology_obj, lag_config_dict,)))


def get_other_lag_dependency_err_msg(interface):
    """
    Get expected error message of adding the port to port channel
    :param interface: interface name
    :return: expected error message
    """
    err_msg = '{} Interface is already member of {}'.format(interface, 'PortChannel2222')
    return err_msg


def config_vlan_dependency(topology_obj, cleanup_list):
    """
    Add vlan configurations to verify the vlan dependency
    :param topology_obj: topology object
    :param cleanup_list: list with functions to cleanup
    """
    duthb2 = topology_obj.ports['dut-hb-2']
    vlan_config_dict = {
        'dut': [{'vlan_id': 50, 'vlan_members': [{duthb2: 'trunk'}]}]
    }
    add_vlan_conf(topology_obj, vlan_config_dict, cleanup_list)


def get_vlan_dependency_err_msg(interface):
    """
    Get expected error message of adding the port to port channel
    :param interface: interface name
    :return: expected error message
    """
    err_msg = '{} Interface configured as VLAN_MEMBER under vlan : Vlan50'.format(interface)
    return err_msg


def add_vlan_conf(topology_obj, vlan_config_dict, cleanup_list):
    """
    Add vlan configurations
    :param topology_obj: topology object
    :param vlan_config_dict: vlan configuration to add
    :param cleanup_list: list with functions to cleanup
    """
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    cleanup_list.append((VlanConfigTemplate.cleanup, (topology_obj, vlan_config_dict,)))


def del_port_from_vlan(dut_engine, port, vlan, cleanup_list):
    """
    Delete port from vlan
    :param dut_engine: dut engine
    :param port: port name
    :param cleanup_list: list with functions to cleanup
    """
    SonicVlanCli.del_port_from_vlan(dut_engine, port, vlan)
    cleanup_list.append((SonicVlanCli.add_port_to_vlan, (dut_engine, port, vlan, 'trunk',)))


def verify_add_member_to_lag_failed_with_err(dut_engine, cli_object, member_port, err_msg):
    """
    Verify negative adding member to port channel
    :param dut_engine: dut engine
    :param cli_object: dut cli object
    :param member_port: name of member port to be added
    :param err_msg: expected error message
    :return: None, raise error in case of unexpected result
    """
    with allure.step('Verify lag dependency, adding member failed as expected with error message: {}'.format(err_msg)):
        output = cli_object.lag.add_port_to_port_channel(dut_engine, member_port, PORTCHANNEL_NAME)
        if not re.search(err_msg, output, re.IGNORECASE):
            output = cli_object.lag.delete_port_from_port_channel(dut_engine, member_port, PORTCHANNEL_NAME)
            raise AssertionError("Expected to failed on adding member to LAG "
                                 "with error msg '{}' but output {}".
                                 format(err_msg, output))


def get_pkt_to_send(traffic_type, engine, dst_iface):
    """
    Create scapy packet for validation
    :param traffic_type: the type of the traffic
    :param engine: device engine
    :param dst_iface: destination interface name
    :return: scapy packet
    """
    dst_mac = LinuxMacCli.get_mac_address_for_interface(engine, dst_iface)
    return BASE_PKT.format(dst_mac, traffic_type)


def verify_port_channel_status_with_retry(cli_object, dut_engine, lag_name, lag_status,
                                          expected_ports_status_list, tries=8, delay=15):
    """
    Verify the PortChannels from "show interfaces portchannel" output, accordingly to handed statuses with retry
    :param cli_object: dut cli object
    :param dut_engine: dut engine
    :param lag_name: port channel name
    :param lag_status: port channel status
    :param expected_ports_status_list: list of typles - (member port name, status)
    :param tries: number of attempts
    :param delay: delay time between attempts
    """
    retry_call(cli_object.lag.verify_port_channel_status,
               fargs=[dut_engine, lag_name, lag_status, expected_ports_status_list],
               tries=tries,
               delay=delay,
               logger=logger)


def verify_port_channels_status(cli_object, dut_engine, expected_lag_info):
    """
    Verify the PortChannels from "show interfaces portchannel" output
    :param cli_object: dut cli object
    :param dut_engine: dut engine
    :param expected_lag_info: expected port channels information
    :return: None, raise error in case of unexpected result
    """
    port_channel_info = cli_object.lag.show_interfaces_port_channel(dut_engine)
    verify_show_cmd(port_channel_info, expected_lag_info)


def verify_port_channels_ip(cli_object, dut_engine, expected_ip_info):
    """
    Verify the PortChannels ips from "show ip interfaces" output
    :param cli_object: dut cli object
    :param dut_engine: dut engine
    :param expected_ip_info: expected ip information
    :return: None, raise error in case of unexpected result
    """
    ip_info = cli_object.ip.show_ip_interfaces(dut_engine)
    verify_show_cmd(ip_info, expected_ip_info)


def traffic_validation(topology_obj, traffic_type):
    """
    Validate the handed traffic type on the setup
    :param topology_obj: topology object
    :param traffic_type: the type of the traffic (TCP/UDP)
    :return: None, raise error in case of unexpected result
    """
    tcpdump_filter = 'dst 50.0.0.3 and {}'.format(traffic_type.lower())
    hadut1 = topology_obj.ports['ha-dut-1']
    hb_engine = topology_obj.players['hb']['engine']
    pkt = get_pkt_to_send(traffic_type, hb_engine, 'bond0')
    validation = {'sender': 'ha', 'send_args': {'interface': hadut1 + '.50',
                                                'packets': pkt, 'count': 100},
                  'receivers':
                      [
                          {'receiver': 'hb',
                           'receive_args': {'interface': 'bond0.50',
                                            'filter': tcpdump_filter, 'count': 100}}
                      ]
                  }
    ScapyChecker(topology_obj.players, validation).run_validation()
