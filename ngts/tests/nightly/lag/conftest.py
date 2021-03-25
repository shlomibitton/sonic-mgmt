import allure
import logging
import pytest
import random
from retry.api import retry_call

from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate

logger = logging.getLogger()

TRAFFIC_TYPES = ['TCP', 'UDP']


@pytest.fixture()
def traffic_type():
    return random.choice(TRAFFIC_TYPES)


@pytest.fixture(scope='package', autouse=True)
def lag_lacp_base_configuration(topology_obj, interfaces, engines):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    :param interfaces: interfaces fixture
    :param engines: engines fixture
    """
    dut_cli = topology_obj.players['dut']['cli']

    ports_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_ha_2]
    with allure.step('Check that links are in UP state'.format(ports_list)):
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, ports_list], tries=10, delay=10, logger=logger)

    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(engines.dut, [interfaces.dut_ha_1,
                                                                                          interfaces.dut_hb_1,
                                                                                          interfaces.dut_hb_2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': interfaces.dut_hb_1,
                 'speed': '1G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_1, '1G')},
                {'iface': interfaces.dut_hb_2,
                 'speed': '1G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '1G')}]
    }

    # LAG/LACP config which will be used in test
    lag_lacp_config_dict = {
        'hb': [{'type': 'lacp', 'name': 'bond0', 'members': [interfaces.hb_dut_1]},
               {'type': 'lacp', 'name': 'bond0', 'members': [interfaces.hb_dut_2]}]
    }

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 50, 'vlan_members': [{interfaces.dut_ha_1: 'trunk'}]}],
        'ha': [{'vlan_id': 50, 'vlan_members': [{interfaces.ha_dut_1: None}]}],
        'hb': [{'vlan_id': 50, 'vlan_members': [{'bond0': None}]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan50', 'ips': [('50.0.0.1', '24')]}],
        'ha': [{'iface': '{}.50'.format(interfaces.ha_dut_1), 'ips': [('50.0.0.2', '24')]}],
        'hb': [{'iface': 'bond0.50', 'ips': [('50.0.0.3', '24')]}]
    }

    logger.info('Starting Lag LACP Test Common configuration')
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('Lag LACP Test Common configuration completed')

    yield

    logger.info('Starting Lag LACP Test Common configuration cleanup')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)

    dut_cli.general.save_configuration(engines.dut)

    logger.info('Lag LACP Test Common cleanup completed')


def cleanup(cleanup_list):
    """
    execute all the functions in the cleanup list
    :return: None
    """
    cleanup_list.reverse()
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
