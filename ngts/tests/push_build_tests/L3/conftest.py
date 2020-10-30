import pytest
import logging

from ngts.config_templates.vrf_config_template import VrfConfigTemplate
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
    dutlb1_1 = topology_obj.ports['dut-lb1-1']
    # Custom VRF ports
    duthb1 = topology_obj.ports['dut-hb-1']
    dutlb1_2 = topology_obj.ports['dut-lb1-2']
    # Hosts B ports
    hbdut1 = topology_obj.ports['hb-dut-1']

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 31, 'vlan_members': [{dutlb1_1: 'access'}]}]
    }

    # VRF config which will be used in test
    vrf_config_dict = {
        'dut': [{'vrf': 'Vrf_custom', 'vrf_interfaces': [dutlb1_2, duthb1]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan31', 'ips': [('31.1.1.1', '24'), ('3111::1', '64')]},
                {'iface': dutlb1_2, 'ips': [('31.1.1.2', '24'), ('3111::2', '64')]},
                {'iface': 'PortChannel0001', 'ips': [('30.0.0.1', '24'), ('3000::1', '64')]},
                {'iface': duthb1, 'ips': [('31.0.0.1', '24'), ('3100::1', '64')]}],
        'ha': [{'iface': 'bond0', 'ips': [('30.0.0.2', '24'), ('3000::2', '64')]}],
        'hb': [{'iface': hbdut1, 'ips': [('31.0.0.2', '24'), ('3100::2', '64')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'dut': [{'dst': '31.0.0.0', 'dst_mask': 24, 'via': ['31.1.1.2']},
                {'dst': '3100::', 'dst_mask': 64, 'via': ['3111::2']},
                {'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['31.1.1.1'],
                 'vrf': 'Vrf_custom'},
                {'dst': '3000::', 'dst_mask': 64, 'via': ['3111::1'],
                 'vrf': 'Vrf_custom'},
                # Below routes for static route test
                {'dst': '20.0.0.10', 'dst_mask': 32, 'via': ['69.0.0.2']},
                {'dst': '20.0.0.1', 'dst_mask': 32, 'via': ['PortChannel0001']},
                {'dst': '20.0.0.0', 'dst_mask': 24, 'via': ['30.0.0.2']},
                {'dst': '2000::10', 'dst_mask': 128, 'via': ['6900::2']},
                {'dst': '2000::1', 'dst_mask': 128, 'via': ['Vlan69']},
                {'dst': '2000::', 'dst_mask': 64, 'via': ['3000::2']}
                # Routes for static route test end
                ],
        'ha': [{'dst': '31.0.0.0', 'dst_mask': 24, 'via': ['30.0.0.1']},
               {'dst': '3100::', 'dst_mask': 64, 'via': ['3000::1']}],
        'hb': [{'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['31.0.0.1']},
               {'dst': '3000::', 'dst_mask': 64, 'via': ['3100::1']}]
    }

    logger.info('Starting PushGate L3 configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    VrfConfigTemplate.configuration(topology_obj, vrf_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('PushGate L3 configuration completed')

    yield

    logger.info('Starting PushGate L3 configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VrfConfigTemplate.cleanup(topology_obj, vrf_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)

    logger.info('PushGate L3 cleanup completed')
