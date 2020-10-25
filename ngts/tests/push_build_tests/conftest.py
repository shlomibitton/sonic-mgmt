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

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan69', 'ips': [('69.0.0.1', '24')]}],
        'ha': [{'iface': '{}.500'.format(hadut2), 'ips': [('50.0.0.2', '24')]},
               {'iface': '{}.600'.format(hadut2), 'ips': [('60.0.0.2', '24')]}],
        'hb': [{'iface': 'bond0.501', 'ips': [('50.1.0.2', '24')]},
               {'iface': 'bond0.601', 'ips': [('60.1.0.2', '24')]},
               {'iface': 'bond0.69', 'ips': [('69.0.0.2', '24')]}]
    }

    logger.info('Starting PushGate Common configuration')
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('PushGate Common configuration completed')

    yield

    logger.info('Starting PushGate Common configuration cleanup')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)

    # Workaround for bug: https://github.com/Azure/sonic-buildimage/issues/5347
    topology_obj.players['dut']['engine'].run_cmd('sudo config reload -y')

    logger.info('PushGate Common cleanup completed')
