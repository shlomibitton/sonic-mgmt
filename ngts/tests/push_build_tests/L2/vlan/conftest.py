import pytest
import logging

from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def vlan_configuration(topology_obj):
    """
    :param topology_obj: topology object fixture
    """
    # Ports which will be used in test
    duthb1 = topology_obj.ports['dut-hb-1']
    dutha2 = topology_obj.ports['dut-ha-2']
    hadut2 = topology_obj.ports['ha-dut-2']

    hbdut1 = topology_obj.ports['hb-dut-1']

    # VLAN config which will be used in test
    vlan_config_dict = {'dut': [{'vlan_id': 700, 'vlan_members': [{'PortChannel0001': 'access'},
                                                                  {duthb1: 'trunk'},
                                                                  {dutha2: 'trunk'}]},
                                {'vlan_id': 800, 'vlan_members': [{duthb1: 'trunk'}]}],
                         'ha': [{'vlan_id': 700, 'vlan_members': [{'bond0': None}, {hadut2: None}]},
                                {'vlan_id': 800, 'vlan_members': [{'bond0': None}, {hadut2: None}]}],
                         'hb': [{'vlan_id': 700, 'vlan_members': [{hbdut1: None}]},
                                {'vlan_id': 800, 'vlan_members': [{hbdut1: None}]}]}

    # IP config which will be used in test
    ip_config_dict = {
        'ha': [{'iface': 'bond0', 'ips': [('70.0.0.2', '24')]},
               {'iface': 'bond0.700', 'ips': [('70.0.0.3', '24')]},
               {'iface': 'bond0.800', 'ips': [('80.0.0.3', '24')]},
               {'iface': '{}.700'.format(hadut2), 'ips': [('70.0.0.4', '24')]},
               {'iface': '{}.800'.format(hadut2), 'ips': [('80.0.0.4', '24')]}],
        'hb': [{'iface': "{}.700".format(hbdut1), 'ips': [('70.0.0.1', '24')]},
               {'iface': "{}.800".format(hbdut1), 'ips': [('80.0.0.1', '24')]}]
    }

    logger.info('Starting vlan configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    logger.info('vlan test cases configuration completed')

    yield

    logger.info('Starting vlan test cases configuration cleanup')
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
    logger.info('vlan cleanup completed')

