import pytest
import allure
import logging

from ngts.cli_wrappers import sonic_ip_clis
from ngts.cli_wrappers import linux_ip_clis

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
def ip_configuration(topology_obj, configuration_dict):
    """
    Pytest fixture which are doing IP configuration
    :param topology_obj: topology object fixture
    :param configuration_dict: configuration dictionary from test case args
    """
    with allure.step('Doing IP configuration'):
        for host_alias, configuration in configuration_dict['ip'].items():
            engine = topology_obj.players[host_alias]['engine']
            for port_info in configuration:
                if port_info.get('iface_type') == 'vlan':
                    iface = get_vlan_iface(topology_obj, host_alias, port_info['iface'], port_info['vlan_id'])
                else:
                    iface = topology_obj.ports[port_info['iface']]

                for ip_mask in port_info['ips']:
                    ip = ip_mask[0]
                    mask = ip_mask[1]
                    if host_alias == 'dut':
                        sonic_ip_clis.add_ip_to_interface(engine, iface, ip, mask)
                    else:
                        linux_ip_clis.add_ip_to_interface(engine, iface, ip, mask)

    yield

    with allure.step('Doing IP cleanup'):
        for host_alias, configuration in configuration_dict['ip'].items():
            engine = topology_obj.players[host_alias]['engine']
            for port_info in configuration:
                if port_info.get('iface_type') == 'vlan':
                    iface = get_vlan_iface(topology_obj, host_alias, port_info['iface'], port_info['vlan_id'])
                else:
                    iface = topology_obj.ports[port_info['iface']]

                for ip_mask in port_info['ips']:
                    ip = ip_mask[0]
                    mask = ip_mask[1]
                    if host_alias == 'dut':
                        sonic_ip_clis.del_ip_from_interface(engine, iface, ip, mask)
                    else:
                        linux_ip_clis.del_ip_from_interface(engine, iface, ip, mask)
