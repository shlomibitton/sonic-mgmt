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

show_vlan_config_pattern = "Vlan{vid}\s+{vid}\s+{member}\s+{mode}"


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

