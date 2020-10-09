import pytest
import logging

from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate

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
    duthb1 = topology_obj.ports['dut-hb-1']
    duthb2 = topology_obj.ports['dut-hb-2']

    hadut1 = topology_obj.ports['ha-dut-1']
    hadut2 = topology_obj.ports['ha-dut-2']

    hbdut1 = topology_obj.ports['hb-dut-1']
    hbdut2 = topology_obj.ports['hb-dut-2']

    # LAG/LACP config which will be used in test
    lag_lacp_config_dict = {
        'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [dutha1]},
                {'type': 'lacp', 'name': 'PortChannel0002', 'members': [duthb2]}],
        'ha': [{'type': 'lacp', 'name': 'bond0', 'members': [hadut1]}],
        'hb': [{'type': 'lacp', 'name': 'bond0', 'members': [hbdut2]}]
    }

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 31, 'vlan_members': []},
                {'vlan_id': 32, 'vlan_members': []},
                {'vlan_id': 33, 'vlan_members': []},
                {'vlan_id': 34, 'vlan_members': []},
                {'vlan_id': 35, 'vlan_members': []},
                {'vlan_id': 36, 'vlan_members': []},
                {'vlan_id': 500, 'vlan_members': [{dutha2: 'trunk'}]},
                {'vlan_id': 501, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 600, 'vlan_members': [{dutha2: 'trunk'}]},
                {'vlan_id': 601, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 69, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
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
        'dut': [{'iface': 'Vlan31', 'ips': [('31.1.1.1', '24')]},
                {'iface': 'Vlan32', 'ips': [('32.1.1.1', '24')]},
                {'iface': 'Vlan33', 'ips': [('33.1.1.1', '24')]},
                {'iface': 'Vlan34', 'ips': [('34.1.1.1', '24')]},
                {'iface': 'Vlan35', 'ips': [('35.1.1.1', '24')]},
                {'iface': 'Vlan36', 'ips': [('36.1.1.1', '24')]},
                {'iface': 'Vlan500', 'ips': [('50.0.0.1', '24')]},
                {'iface': 'Vlan501', 'ips': [('50.1.0.1', '24')]},
                {'iface': 'Vlan600', 'ips': [('60.0.0.1', '24')]},
                {'iface': 'Vlan601', 'ips': [('60.1.0.1', '24')]},
                {'iface': 'Vlan69', 'ips': [('69.0.0.1', '24')]},
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

    logger.info('Starting PushGate configuration')
    LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('PushGate configuration completed')

    yield

    logger.info('Starting PushGate configuration cleanup')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)

    # Workaround for bug: https://github.com/Azure/sonic-buildimage/issues/5347
    topology_obj.players['dut']['engine'].run_cmd('sudo config reload -y')

    logger.info('PushGate cleanup completed')
