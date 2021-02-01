import allure
import logging
import pytest
from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.linux.linux_ip_clis import LinuxIpCli


"""

 Vlan Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+VLAN+Documentation

"""

logger = logging.getLogger()

show_vlan_config_pattern = r"Vlan{vid}\s+{vid}\s+{member}\s+{mode}"


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test VLAN access mode')
def test_vlan_access_mode(topology_obj):
    """
    This test will check vlan access mode.
    :param topology_obj: topology object fixture
    :return: raise assertion error if expected output is not matched
    """
    host_name = 'ha'
    dut_hb_1 = topology_obj.ports['dut-hb-1']
    hb_dut_1 = topology_obj.ports['hb-dut-1']
    dut_engine = topology_obj.players['dut']['engine']

    logger.info("Vlan access mode: verify PortChannel0001 in mode access")
    vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
    vlan_expected_info = [(show_vlan_config_pattern.format(vid='700', member='PortChannel0001', mode='untagged'), True),
                          (show_vlan_config_pattern.format(vid='700', member=dut_hb_1, mode='tagged'), True)]
    verify_show_cmd(vlan_info, vlan_expected_info)

    with allure.step('Vlan access mode: verify untagged traffic can reach from '
                     'bond0 to 70.0.0.1 ({}.700)'.format(hb_dut_1)):
        validation = {'sender': host_name, 'args': {'interface': 'bond0', 'count': 3, 'dst': '70.0.0.1'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 untagged packets from bond0 to 70.0.0.1 ({}.700)'.format(hb_dut_1))
        ping.run_validation()

    with allure.step('Vlan access mode: verify tagged traffic is dropped'):
        validation = {'sender': host_name, 'args': {'interface': 'bond0.700', 'count': 3,
                                                    'expected_count': 0,
                                                    'dst': '70.0.0.1'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 tagged packets from bond0.700 to to 70.0.0.1 ({}.700)'.format(hb_dut_1))
        ping.run_validation()


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test VLAN trunk mode')
def test_vlan_trunk_mode(topology_obj):
    """
    This test will check vlan trunk mode.
    :param topology_obj: topology object fixture
    :return: raise assertion error if expected output is not matched
    """
    host_a = 'ha'
    host_b = 'hb'
    dut_hb_1 = topology_obj.ports['dut-hb-1']
    dut_ha_2 = topology_obj.ports['dut-ha-2']
    hb_dut_1 = topology_obj.ports['hb-dut-1']
    ha_dut_2 = topology_obj.ports['ha-dut-2']
    dut_engine = topology_obj.players['dut']['engine']

    logger.info("Vlan trunk mode: verify {} and {} are in trunk mode".format(dut_hb_1, dut_ha_2))
    vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
    vlan_expected_info = [(show_vlan_config_pattern.format(vid='700', member=dut_ha_2, mode='tagged'), True),
                          (show_vlan_config_pattern.format(vid='700', member=dut_hb_1, mode='tagged'), True),
                          (show_vlan_config_pattern.format(vid='800', member=dut_hb_1, mode='tagged'), True)]
    verify_show_cmd(vlan_info, vlan_expected_info)

    with allure.step('Vlan trunk mode: verify tagged traffic can reach from '
                     '{}.700 to 70.0.0.4 ({}.700)'.format(hb_dut_1, ha_dut_2)):
        validation = {'sender': host_b, 'args': {'interface': '{}.700'.format(hb_dut_1),
                                                 'count': 3, 'dst': '70.0.0.4'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 tagged packets from {}.700 to 70.0.0.4 ({}.700)'.format(hb_dut_1, ha_dut_2))
        ping.run_validation()

    with allure.step('Vlan trunk mode: verify tagged traffic can reach from '
                     '{}.700 to 70.0.0.2 (bond0)'.format(hb_dut_1)):
        validation = {'sender': host_b, 'args': {'interface': '{}.700'.format(hb_dut_1),
                                                 'count': 3, 'dst': '70.0.0.2'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 tagged packets from {}.700 to 70.0.0.2 (bond0)'.format(hb_dut_1))
        ping.run_validation()

    with allure.step('Vlan trunk mode: verify tagged traffic is dropped '
                     'when vlan 800 is not configured on dut-ha-2'
                     'from 80.0.0.4 ({}.800) to {}.800'.format(ha_dut_2, hb_dut_1)):
        validation = {'sender': host_a, 'args': {'interface': '{}.800'.format(ha_dut_2),
                                                 'expected_count': 0,
                                                 'count': 3, 'dst': '80.0.0.1'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 tagged packets from 80.0.0.4 ({}.800) to {}.800'.format(ha_dut_2, hb_dut_1))
        ping.run_validation()

    with allure.step('Vlan trunk mode: verify untagged traffic is dropped'):
        validation = {'sender': host_b, 'args': {'interface': hb_dut_1, 'count': 3,
                                                 'expected_count': 0,
                                                 'dst': '70.0.0.4'}}
        ping = PingChecker(topology_obj.players, validation)
        logger.info('Sending 3 untagged packets from {} to {}.700'.format(hb_dut_1, ha_dut_2))
        ping.run_validation()


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test VLAN configuration on split port')
@pytest.mark.ngts_skip({'platform_prefix_list': ['simx']})
def test_vlan_on_split_port(topology_obj):
    """
    configure different vlans on split port in trunk/access mode.
    check port are in up state after configuration and vlans were configured correctly
    :param topology_obj: topology object fixture
    :return: raise assertion error if expected output is not matched
    """
    port_alias_template = "dut-lb-splt2-p{}-{}"
    vlan_list = [700, 800]
    port_indices = [1, 2]
    split_port_indices = [1, 2]
    mode = ['access', 'trunk']
    vlan_mode_dict = {'access': 'untagged', 'trunk': 'tagged'}
    vlan_expected_info = []
    ports_conf = {}

    dut_engine = topology_obj.players['dut']['engine']
    cli_object = topology_obj.players['dut']['cli']
    try:

        for port_num, vlan_mode in zip(port_indices, mode):
            for split_port_index, vlan_num in zip(split_port_indices, vlan_list):
                port_alias = port_alias_template.format(port_num, split_port_index)
                port_interface = topology_obj.ports[port_alias]
                ports_conf[port_interface] = vlan_num
                cli_object.vlan.add_port_to_vlan(dut_engine,
                                                 port_interface,
                                                 vlan_num, mode=vlan_mode)
                vlan_expected_info.append((show_vlan_config_pattern.format(vid=vlan_num,
                                                                           member=port_interface,
                                                                           mode=vlan_mode_dict[vlan_mode]), True))
        vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
        verify_show_cmd(vlan_info, vlan_expected_info)
        cli_object.interface.check_ports_status(dut_engine, ports_conf.keys(), expected_status='up')

    except Exception as e:
        raise e

    finally:
        # cleanup
        for port, vlan_num in ports_conf.items():
            cli_object.vlan.del_port_from_vlan(dut_engine, port, vlan_num)


@pytest.mark.skip(reason="skipped due bug 2253609")
@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test VLAN 4094/5 configuration')
def test_vlan_4094_5(topology_obj):
    """
    This test will check configuration of vlan 4095(which should not be configured)
    and vlan 4094 (last vlan) which should be correctly configured.
    :param topology_obj: topology object fixture
    :return: raise assertion error if expected output is not matched
    """
    host_a = 'ha'
    dut_hb_1 = topology_obj.ports['dut-hb-1']
    hb_dut_1 = topology_obj.ports['hb-dut-1']

    dut_engine = topology_obj.players['dut']['engine']
    cli_object = topology_obj.players['dut']['cli']

    try:

        logger.info("Configure Vlan 4095 on the dut {}".format(dut_engine.ip))
        output = cli_object.vlan.add_vlan(dut_engine, 4095)
        logger.info("Verify Configure Vlan 4095 on the dut {} failed".format(dut_engine.ip))
        expected_err_msg = [(r"Error:\s+Invalid\s+VLAN\s+ID\s+4095\s+\(1-4094\)", True)]
        verify_show_cmd(output, expected_err_msg)
        logger.info("Clean Vlan configuration from PortChannel0001".format(dut_hb_1))
        cli_object.vlan.del_port_from_vlan(dut_engine, 'PortChannel0001', 700)
        logger.info("Configure Vlan 4095 on ports PortChannel0001, {}".format(dut_hb_1))
        expected_err_msg = [(r"Error:\s+Vlan4095\s+doesn't\s+exist", True)]
        output = cli_object.vlan.add_port_to_vlan(dut_engine, 'PortChannel0001', 4095, mode='access')
        logger.info("Verify Configure Vlan 4095 on the ports failed")
        verify_show_cmd(output, expected_err_msg)
        output = cli_object.vlan.add_port_to_vlan(dut_engine, dut_hb_1, 4095, mode='trunk')
        verify_show_cmd(output, expected_err_msg)

        logger.info("Verify Configuration of Vlan 4095 on ports PortChannel0001, {} doesn't exist".format(dut_hb_1))
        vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
        vlan_expected_info = [(show_vlan_config_pattern.format(vid='4095', member='PortChannel0001', mode='untagged'), False),
                              (show_vlan_config_pattern.format(vid='4095', member=dut_hb_1, mode='tagged'), False)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan access mode: verify untagged traffic is dropped for vlan 4095 from '
                         'bond0 to 70.0.0.6 ({}.4095)'.format(hb_dut_1)):
            validation = {'sender': host_a, 'args': {'interface': 'bond0', 'count': 3, 'expected_count': 0, 'dst': '70.0.0.6'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 untagged packets from bond0 to 70.0.0.6 ({}.4095)'.format(hb_dut_1))
            ping.run_validation()

        logger.info("Configure Vlan 4094 on the dut {}".format(dut_engine.ip))
        cli_object.vlan.add_vlan(dut_engine, 4094)
        logger.info("Configure Vlan 4094 on ports PortChannel0001, {}".format(dut_hb_1))
        cli_object.vlan.add_port_to_vlan(dut_engine, 'PortChannel0001', 4094, mode='access')
        cli_object.vlan.add_port_to_vlan(dut_engine, dut_hb_1, 4094, mode='trunk')

        logger.info("Verify Configuration of Vlan 4094 on ports PortChannel0001, {} exist".format(dut_hb_1))
        vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
        vlan_expected_info = [(show_vlan_config_pattern.format(vid='4094', member='PortChannel0001', mode='untagged'), True),
                              (show_vlan_config_pattern.format(vid='4094', member=dut_hb_1, mode='tagged'), True)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan access mode: verify untagged traffic can reach from '
                         'bond0 to 70.0.0.7 ({}.4094)'.format(hb_dut_1)):
            validation = {'sender': host_a, 'args': {'interface': 'bond0', 'count': 3, 'dst': '70.0.0.7'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 untagged packets from bond0 to 70.0.0.7 ({}.4094)'.format(hb_dut_1))
            ping.run_validation()

        with allure.step('Vlan access mode: verify tagged traffic is dropped'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0.4094', 'count': 3,
                                                     'expected_count': 0,
                                                     'dst': '70.0.0.7'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0.4094 to to 70.0.0.7 ({}.4094)'.format(hb_dut_1))
            ping.run_validation()

    except Exception as e:
        raise e

    finally:
        # cleanup
        cli_object.vlan.del_port_from_vlan(dut_engine, 'PortChannel0001', 4094)
        cli_object.vlan.del_port_from_vlan(dut_engine, dut_hb_1, 4094)
        cli_object.vlan.add_port_to_vlan(dut_engine, 'PortChannel0001', 700, mode='access')


@pytest.mark.skip(reason="skipped due bug 2253609")
@pytest.mark.build
@allure.title('BUILD VLAN test case')
def test_vlan_access_with_trunk_mode(topology_obj):
    """
    this test verify changing port vlan mode between access and trunk does not yield unexpected protocol behaviour.
    :param topology_obj: topology object fixture
    :return: raise assertion error if expected output is not matched
    """
    # hosts
    host_a = 'ha'

    # tested ports:
    dut_hb_1 = topology_obj.ports['dut-hb-1']
    dut_ha_2 = topology_obj.ports['dut-ha-2']

    # engines
    dut_engine = topology_obj.players['dut']['engine']
    ha_engine = topology_obj.players[host_a]['engine']

    try:

        logger.info("Clean port dut-ha-1 from access mode")
        SonicVlanCli.del_port_from_vlan(dut_engine, 'PortChannel0001', '700')

        logger.info("Switch port dut-ha-1 vlan mode to trunk with 700 and 800.")
        SonicVlanCli.add_port_to_vlan(dut_engine, 'PortChannel0001', '700', 'trunk')
        SonicVlanCli.add_port_to_vlan(dut_engine, 'PortChannel0001', '800', 'trunk')

        logger.info("Vlan trunk mode: verify ports vlan mode")
        vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
        vlan_expected_info = [(show_vlan_config_pattern.format(vid='700', member='PortChannel0001', mode='tagged'), True),
                              (show_vlan_config_pattern.format(vid='700', member=dut_ha_2, mode='tagged'), True),
                              (show_vlan_config_pattern.format(vid='700', member=dut_hb_1, mode='tagged'), True),
                              (show_vlan_config_pattern.format(vid='800', member='PortChannel0001', mode='tagged'), True),
                              (show_vlan_config_pattern.format(vid='800', member=dut_hb_1, mode='tagged'), True)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan trunk mode: verify tagged traffic with vlan 700 from ha-dut-1.700 can reach hb-dut-1.700'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0.700', 'count': 3, 'dst': '70.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0.700 (ha-dut-1) to to 70.0.0.1 (hb-dut-1.700)')
            ping.run_validation()

        with allure.step('Vlan trunk mode: verify tagged traffic with vlan 800 from ha-dut-1.700 can reach hb-dut-1.800'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0.800', 'count': 3, 'dst': '80.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0.800 (ha-dut-1) to to 80.0.0.1 (hb-dut-1.800)')
            ping.run_validation()

        with allure.step('Vlan trunk mode: verify untagged traffic is dropped'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0', 'count': 3,
                                                     'expected_count': 0, 'dst': '70.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0 (ha-dut-1) to to 70.0.0.1 (hb-dut-1.700)')
            ping.run_validation()

        with allure.step('Vlan trunk mode: verify tagged traffic is dropped '
                         'when vlan 800 is not configured on dut-ha-2'
                         'ha-dut-1.800 to 80.0.0.4 (ha-dut-2.800)'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0.800',
                                                     'expected_count': 0,
                                                     'count': 3, 'dst': '80.0.0.4'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0.800 (ha-dut-1) to 80.0.0.4 (ha-dut-2.800)')
            ping.run_validation()

        logger.info("remove port dut-ha-1 vlan trunk mode configuration.")
        SonicVlanCli.del_port_from_vlan(dut_engine, 'PortChannel0001', '700')
        SonicVlanCli.del_port_from_vlan(dut_engine, 'PortChannel0001', '800')

        logger.info("Switch port dut-ha-1 vlan mode to access with vlan 800.")
        SonicVlanCli.add_port_to_vlan(dut_engine, 'PortChannel0001', '800', 'access')

        logger.info("Switch bond0 ip to be on subnet of vlan 800")
        LinuxIpCli.del_ip_from_interface(ha_engine, 'bond0', '70.0.0.2')
        LinuxIpCli.add_ip_to_interface(ha_engine, 'bond0', '80.0.0.2')

        logger.info("Vlan access mode: verify dut-ha-1 (PortChannel0001) in mode access with vlan 800")
        vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
        vlan_expected_info = [(show_vlan_config_pattern.format(vid='800', member='PortChannel0001', mode='untagged'), True),
                              (show_vlan_config_pattern.format(vid='800', member=dut_hb_1, mode='tagged'), True)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan access mode: verify untagged traffic can reach from '
                         'bond0 (ha-dut-1) to 80.0.0.1 (hb-dut-1.800)'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0', 'count': 3, 'dst': '80.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 untagged packets from bond0 (ha-dut-1) to 80.0.0.1 (hb-dut-1.800)')
            ping.run_validation()

        with allure.step('Vlan access mode: verify tagged traffic is dropped'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0.800', 'count': 3,
                                                     'expected_count': 0, 'dst': '80.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0.800 (ha-dut-1) to to 80.0.0.1 (hb-dut-1.800)')
            ping.run_validation()

        logger.info("Switch port dut-ha-1 vlan mode to access with vlan 700.")
        SonicVlanCli.del_port_from_vlan(dut_engine, 'PortChannel0001', '800')
        SonicVlanCli.add_port_to_vlan(dut_engine, 'PortChannel0001', '700', 'access')

        logger.info("Switch bond0 ip to be on subnet of vlan 700")
        LinuxIpCli.del_ip_from_interface(ha_engine, 'bond0', '80.0.0.2')
        LinuxIpCli.add_ip_to_interface(ha_engine, 'bond0', '70.0.0.2')

        logger.info("Vlan access mode: verify dut-ha-1 (PortChannel0001) in mode access with vlan 700")
        vlan_info = SonicVlanCli.show_vlan_config(dut_engine)
        vlan_expected_info = [(show_vlan_config_pattern.format(vid='700', member='PortChannel0001', mode='untagged'), True),
                              (show_vlan_config_pattern.format(vid='700', member=dut_hb_1, mode='tagged'), True)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan access mode: verify untagged traffic can reach from '
                         'bond0 (ha-dut-1) to 70.0.0.1 (hb-dut-1.700)'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0', 'count': 3, 'dst': '70.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 untagged packets from bond0 (ha-dut-1) to 70.0.0.1 (hb-dut-1.700)')
            ping.run_validation()

        with allure.step('Vlan access mode: verify tagged traffic is dropped'):
            validation = {'sender': host_a, 'args': {'interface': 'bond0.700', 'count': 3,
                                                     'expected_count': 0, 'dst': '70.0.0.1'}}
            ping = PingChecker(topology_obj.players, validation)
            logger.info('Sending 3 tagged packets from bond0.700 (ha-dut-1) to to 70.0.0.1 (hb-dut-1.700)')
        ping.run_validation()

    except Exception as e:
        raise e

    finally:
        # cleanup
        SonicVlanCli.del_port_from_vlan(dut_engine, 'PortChannel0001', '700')
        SonicVlanCli.del_port_from_vlan(dut_engine, 'PortChannel0001', '800')
        SonicVlanCli.add_port_to_vlan(dut_engine, 'PortChannel0001', '700', 'access')
        logger.info("Switch bond0 ip to be on subnet of vlan 700")
        LinuxIpCli.del_ip_from_interface(ha_engine, 'bond0', '80.0.0.2')
        LinuxIpCli.add_ip_to_interface(ha_engine, 'bond0', '70.0.0.2')