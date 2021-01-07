import pytest
import logging
import allure

from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate

logger = logging.getLogger()


@pytest.fixture(scope='package', autouse=True)
def my_test_configuration(topology_obj, is_simx):
    """
    Pytest fixture which are doing configuration fot test case based on my test config
    :param topology_obj: topology object fixture
    """
    # Ports which will be used in test
    dutha2 = topology_obj.ports['dut-ha-2']
    duthb1 = topology_obj.ports['dut-hb-1']

    # Hosts A ports
    hadut2 = topology_obj.ports['ha-dut-2']
    # Hosts B ports
    hbdut1 = topology_obj.ports['hb-dut-1']

    dut_engine = topology_obj.players['dut']['engine']

    with allure.step('Check that links in UP state'.format()):
        ports_list = [dutha2, duthb1]
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[dut_engine, ports_list], tries=10, delay=10, logger=logger)

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 100, 'vlan_members': [{dutha2: 'access'}]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan100', 'ips': [('10.0.0.1', '24')]},
                {'iface': '{}'.format(duthb1), 'ips': [('20.0.0.1', '24')]}],
        'ha': [{'iface': '{}'.format(hadut2), 'ips': [('10.0.0.2', '24')]}],
        'hb': [{'iface': '{}'.format(hbdut1), 'ips': [('20.0.0.2', '24')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'ha': [{'dst': '20.0.0.0', 'dst_mask': 24, 'via': ['10.0.0.1']}],
        'hb': [{'dst': '10.0.0.0', 'dst_mask': 24, 'via': ['20.0.0.1']}]
    }

    logger.info('Starting My Test Common configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('My_Test Common configuration completed')

    yield

    logger.info('Starting My Test Common configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)

    if not is_simx:
        topology_obj.players['dut']['engine'].run_cmd('sudo config reload -y')

    logger.info('My Test Common cleanup completed')
