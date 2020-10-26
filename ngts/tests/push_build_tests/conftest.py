import pytest
import logging

from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.vrf_config_template import VrfConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate

logger = logging.getLogger()


@pytest.fixture(scope='package', autouse=True)
def push_gate_configuration(topology_obj):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    """
    # Ports which will be used in test
    dutha1 = topology_obj.ports['dut-ha-1']
    dutha2 = topology_obj.ports['dut-ha-2']
    duthb2 = topology_obj.ports['dut-hb-2']
    dutlb1_1 = topology_obj.ports['dut-lb1-1']
    dutlb2_1 = topology_obj.ports['dut-lb2-1']
    dutlb3_1 = topology_obj.ports['dut-lb3-1']
    dutlb4_1 = topology_obj.ports['dut-lb4-1']
    dutlb_splt2_p1_1 = topology_obj.ports['dut-lb-splt2-p1-1']
    dutlb_splt2_p1_2 = topology_obj.ports['dut-lb-splt2-p1-2']
    # Custom VRF ports
    duthb1 = topology_obj.ports['dut-hb-1']
    dutlb1_2 = topology_obj.ports['dut-lb1-2']
    dutlb2_2 = topology_obj.ports['dut-lb2-2']
    dutlb3_2 = topology_obj.ports['dut-lb3-2']
    dutlb4_2 = topology_obj.ports['dut-lb4-2']
    dutlb_splt2_p2_1 = topology_obj.ports['dut-lb-splt2-p2-1']
    dutlb_splt2_p2_2 = topology_obj.ports['dut-lb-splt2-p2-2']
    # Hosts A ports
    hadut1 = topology_obj.ports['ha-dut-1']
    hadut2 = topology_obj.ports['ha-dut-2']
    # Hosts B ports
    hbdut1 = topology_obj.ports['hb-dut-1']
    hbdut2 = topology_obj.ports['hb-dut-2']

    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(topology_obj.players['dut']['engine'],
                                                                            [dutha1, duthb2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': dutha1, 'speed': '10000', 'original_speed': dut_original_interfaces_speeds[dutha1]},
                {'iface': duthb2, 'speed': '10000', 'original_speed': dut_original_interfaces_speeds[duthb2]}]
    }

    # LAG/LACP config which will be used in test
    lag_lacp_config_dict = {
        'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [dutha1]},
                {'type': 'lacp', 'name': 'PortChannel0002', 'members': [duthb2]}],
        'ha': [{'type': 'lacp', 'name': 'bond0', 'members': [hadut1]}],
        'hb': [{'type': 'lacp', 'name': 'bond0', 'members': [hbdut2]}]
    }

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 31, 'vlan_members': [{dutlb1_1: 'access'}]},
                {'vlan_id': 32, 'vlan_members': [{dutlb2_1: 'access'}]},
                {'vlan_id': 33, 'vlan_members': [{dutlb3_1: 'access'}]},
                {'vlan_id': 34, 'vlan_members': [{dutlb4_1: 'access'}]},
                {'vlan_id': 35, 'vlan_members': [{dutlb_splt2_p1_1: 'access'}]},
                {'vlan_id': 36, 'vlan_members': [{dutlb_splt2_p1_2: 'access'}]},
                {'vlan_id': 69, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 500, 'vlan_members': [{dutha2: 'trunk'}]},
                {'vlan_id': 501, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 600, 'vlan_members': [{dutha2: 'trunk'}]},
                {'vlan_id': 601, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 690, 'vlan_members': [{dutha2: 'trunk'}]},
                {'vlan_id': 691, 'vlan_members': [{dutha2: 'trunk'}]}],
        'ha': [{'vlan_id': 500, 'vlan_members': [{hadut2: None}]},
               {'vlan_id': 600, 'vlan_members': [{hadut2: None}]},
               {'vlan_id': 690, 'vlan_members': [{hadut2: None}]},
               {'vlan_id': 691, 'vlan_members': [{hadut2: None}]}],
        'hb': [{'vlan_id': 501, 'vlan_members': [{'bond0': None}]},
               {'vlan_id': 601, 'vlan_members': [{'bond0': None}]},
               {'vlan_id': 69, 'vlan_members': [{'bond0': None}]}]
    }

    # VRF config which will be used in test
    vrf_config_dict = {
        'dut': [{'vrf': 'Vrf_custom', 'vrf_interfaces': [dutlb1_2, dutlb2_2, dutlb3_2, dutlb4_2, dutlb_splt2_p2_1, dutlb_splt2_p2_2,
                                                         duthb1]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan31', 'ips': [('31.1.1.1', '24')]},
                {'iface': 'Vlan32', 'ips': [('32.1.1.1', '24')]},
                {'iface': 'Vlan33', 'ips': [('33.1.1.1', '24')]},
                {'iface': 'Vlan34', 'ips': [('34.1.1.1', '24')]},
                {'iface': 'Vlan35', 'ips': [('35.1.1.1', '24')]},
                {'iface': 'Vlan36', 'ips': [('36.1.1.1', '24')]},

                {'iface': dutlb1_2, 'ips': [('31.1.1.2', '24')]},
                {'iface': dutlb2_2, 'ips': [('32.1.1.2', '24')]},
                {'iface': dutlb3_2, 'ips': [('33.1.1.2', '24')]},
                {'iface': dutlb4_2, 'ips': [('34.1.1.2', '24')]},
                {'iface': dutlb_splt2_p2_1, 'ips': [('35.1.1.2', '24')]},
                {'iface': dutlb_splt2_p2_2, 'ips': [('36.1.1.2', '24')]},

                {'iface': 'Vlan69', 'ips': [('69.0.0.1', '24')]},
                {'iface': 'Vlan500', 'ips': [('50.0.0.1', '24')]},
                {'iface': 'Vlan501', 'ips': [('50.1.0.1', '24')]},
                {'iface': 'Vlan600', 'ips': [('60.0.0.1', '24')]},
                {'iface': 'Vlan601', 'ips': [('60.1.0.1', '24')]},
                {'iface': 'Vlan690', 'ips': [('69.0.1.1', '24')]},
                {'iface': 'Vlan691', 'ips': [('69.1.1.1', '24')]},
                {'iface': 'PortChannel0001', 'ips': [('30.0.0.1', '24')]},
                {'iface': duthb1, 'ips': [('31.0.0.1', '24')]}],
        'ha': [{'iface': 'bond0', 'ips': [('30.0.0.2', '24')]},
               {'iface': '{}.500'.format(hadut2), 'ips': [('50.0.0.2', '24')]},
               {'iface': '{}.600'.format(hadut2), 'ips': [('60.0.0.2', '24')]}],
        'hb': [{'iface': hbdut1, 'ips': [('31.0.0.2', '24')]},
               {'iface': 'bond0.501', 'ips': [('50.1.0.2', '24')]},
               {'iface': 'bond0.601', 'ips': [('60.1.0.2', '24')]},
               {'iface': 'bond0.69', 'ips': [('69.0.0.2', '24')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'dut': [{'dst': '31.0.0.0', 'dst_mask': 24, 'via': ['33.1.1.2', '34.1.1.2', '35.1.1.2', '36.1.1.2']},
                {'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['33.1.1.1', '34.1.1.1', '35.1.1.1', '36.1.1.1'],
                 'vrf': 'Vrf_custom'}],
        'ha': [{'dst': '31.0.0.0', 'dst_mask': 24, 'via': ['30.0.0.1']}],
        'hb': [{'dst': '30.0.0.0', 'dst_mask': 24, 'via': ['31.0.0.1']}]
    }

    logger.info('Starting PushGate configuration')
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    VrfConfigTemplate.configuration(topology_obj, vrf_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('PushGate configuration completed')

    yield

    logger.info('Starting PushGate configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VrfConfigTemplate.cleanup(topology_obj, vrf_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)

    # Workaround for bug: https://github.com/Azure/sonic-buildimage/issues/5347
    topology_obj.players['dut']['engine'].run_cmd('sudo config reload -y')

    logger.info('PushGate cleanup completed')
