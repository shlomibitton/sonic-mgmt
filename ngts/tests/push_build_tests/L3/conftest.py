import pytest
import logging

from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate

logger = logging.getLogger()


@pytest.fixture(scope='package', autouse=True)
def l3_configuration(topology_obj):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    """
    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 69, 'vlan_members': [{'PortChannel0002': 'trunk'}]}],
        'hb': [{'vlan_id': 69, 'vlan_members': [{'bond0': None}]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'PortChannel0001', 'ips': [('30.0.0.1', '24'), ('3000::1', '64')]},
                {'iface': 'Vlan69', 'ips': [('69.0.0.1', '24'), ('6900::1', '64')]}],
        'ha': [{'iface': 'bond0', 'ips': [('30.0.0.2', '24'), ('3000::2', '64')]}],
        'hb': [{'iface': 'bond0.69', 'ips': [('69.0.0.2', '24'), ('6900::2', '64')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'dut': [{'dst': '20.0.0.10', 'dst_mask': 32, 'via': ['69.0.0.2']},
                {'dst': '20.0.0.1', 'dst_mask': 32, 'via': ['PortChannel0001']},
                {'dst': '20.0.0.0', 'dst_mask': 24, 'via': ['30.0.0.2']},
                {'dst': '2000::10', 'dst_mask': 128, 'via': ['6900::2']},
                {'dst': '2000::1', 'dst_mask': 128, 'via': ['Vlan69']},
                {'dst': '2000::', 'dst_mask': 64, 'via': ['3000::2']}
                ]
    }

    logger.info('Starting PushGate L3 configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('PushGate L3 configuration completed')

    yield

    logger.info('Starting PushGate L3 configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)

    logger.info('PushGate L3 cleanup completed')
