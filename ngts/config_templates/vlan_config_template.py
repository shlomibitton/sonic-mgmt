import pytest
import allure
import logging

from ngts.cli_wrappers import sonic_vlan_clis
from ngts.cli_wrappers import linux_vlan_clis
from ngts.cli_wrappers import linux_interface_clis

logger = logging.getLogger()


def get_vlan_iface(topology_obj, device, iface, vlan_id):
    """
    Method which return VLAN interface name for dut or host
    :param topology_obj: topology object fixture
    :param device: device alias name
    :param iface: interface alias name
    :param vlan_id: vlan ID
    :return: network interface with VLAN, example: in case of host: enp67s0.5 or Vlan5 in case of DUT
    """
    if device == 'dut':
        return 'Vlan{}'.format(vlan_id)
    else:
        return '{}.{}'.format(topology_obj.ports[iface], vlan_id)


@pytest.fixture()
def vlan_configuration(topology_obj, configuration_dict):
    """
    Pytest fixture which are doing VLAN configuration
    :param topology_obj: topology object fixture
    :param configuration_dict: configuration dictionary from test case args
    """
    with allure.step('Doing VLAN configuration'):
        for host_alias, configuration in configuration_dict['vlan'].items():
            engine = topology_obj.players[host_alias]['engine']
            for vlan_info in configuration:
                if host_alias == 'dut':
                    sonic_vlan_clis.add_vlan(engine, vlan_info['vlan_id'])
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_port = topology_obj.ports[vlan_port]
                        sonic_vlan_clis.add_port_to_vlan(engine, vlan_port, vlan_info['vlan_id'])
                else:
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_port = topology_obj.ports[vlan_port]
                        linux_vlan_clis.add_vlan_interface(engine, vlan_port, vlan_info['vlan_id'])
                        vlan_iface = get_vlan_iface(topology_obj, host_alias, vlan_port, vlan_info['vlan_id'])
                        linux_interface_clis.enable_interface(engine, vlan_iface)

    yield

    with allure.step('Doing VLAN cleanup'):
        for host_alias, configuration in configuration_dict['vlan'].items():
            engine = topology_obj.players[host_alias]['engine']
            for vlan_info in configuration:
                if host_alias == 'dut':
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_port = topology_obj.ports[vlan_port]
                        sonic_vlan_clis.del_port_from_vlan(engine, vlan_port, vlan_info['vlan_id'])
                    sonic_vlan_clis.del_vlan(engine, vlan_info['vlan_id'])
                else:
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_port = topology_obj.ports[vlan_port]
                        vlan_iface = get_vlan_iface(topology_obj, host_alias, vlan_port, vlan_info['vlan_id'])
                        linux_interface_clis.del_interface(engine, vlan_iface)
