import pytest
import logging
import allure

from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
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

    # Hosts A ports
    hadut1 = topology_obj.ports['ha-dut-1']
    hadut2 = topology_obj.ports['ha-dut-2']
    # Hosts B ports
    hbdut2 = topology_obj.ports['hb-dut-2']

    dut_engine = topology_obj.players['dut']['engine']

    with allure.step('Check that links in UP state'.format()):
        ports_list = [dutha1, dutha2, duthb1, duthb2]
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[dut_engine, ports_list], tries=10, delay=10, logger=logger)

    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(dut_engine, [dutha1, duthb2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': dutha1, 'speed': '10G', 'original_speed': dut_original_interfaces_speeds.get(dutha1, '10G')},
                {'iface': duthb2, 'speed': '10G', 'original_speed': dut_original_interfaces_speeds.get(duthb2, '10G')}]
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
        'dut': [{'vlan_id': 40, 'vlan_members': [{'PortChannel0002': 'trunk'}, {dutha2: 'trunk'}]}],
        'ha': [{'vlan_id': 40, 'vlan_members': [{hadut2: None}]}],
        'hb': [{'vlan_id': 40, 'vlan_members': [{'bond0': None}]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan40', 'ips': [('40.0.0.1', '24'), ('4000::1', '64')]}],
        'ha': [{'iface': '{}.40'.format(hadut2), 'ips': [('40.0.0.2', '24'), ('4000::2', '64')]}],
        'hb': [{'iface': 'bond0.40', 'ips': [('40.0.0.3', '24'), ('4000::3', '64')]}]
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
