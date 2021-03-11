import pytest
import logging

from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def vlan_configuration(topology_obj):
    """
    :param topology_obj: topology object fixture
    """
    # Ports which will be used in test
    duthb1 = topology_obj.ports['dut-hb-1']
    dutha2 = topology_obj.ports['dut-ha-2']

    # VLAN config which will be used in test
    vlan_config_dict = {'dut': [{'vlan_id': 30, 'vlan_members': [{'PortChannel0001': 'access'},
                                                                 {duthb1: 'trunk'},
                                                                 {dutha2: 'trunk'}
                                                                 ]},
                                {'vlan_id': 800, 'vlan_members': [{duthb1: 'trunk'}]}
                                ]
                        }

    dut_engine = topology_obj.players['dut']['engine']
    SonicIpCli.del_ip_from_interface(dut_engine, 'PortChannel0001', '30.0.0.1')
    SonicIpCli.del_ip_from_interface(dut_engine, 'PortChannel0001', '3000::1', '64')

    logger.info('Starting vlan configuration')
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    logger.info('vlan test cases configuration completed')

    yield

    logger.info('Starting vlan test cases configuration cleanup')
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)

    SonicIpCli.add_ip_to_interface(dut_engine, 'PortChannel0001', '30.0.0.1')
    SonicIpCli.add_ip_to_interface(dut_engine, 'PortChannel0001', '3000::1', '64')

    logger.info('vlan cleanup completed')
