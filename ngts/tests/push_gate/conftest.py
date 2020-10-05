import pytest
import allure
import logging

from ngts.cli_wrappers import sonic_vlan_clis
from ngts.cli_wrappers import linux_vlan_clis
from ngts.cli_wrappers import linux_interface_clis
from ngts.cli_wrappers import sonic_ip_clis
from ngts.cli_wrappers import linux_ip_clis

logger = logging.getLogger()


@pytest.fixture(scope='module', autouse=True)
def push_gate_configuration(topology_obj, vlan_configuration, ip_configuration):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    :param vlan_configuration: fixture which are doing VLAN configuration
    :param ip_configuration: fixture which are doing IP configuration
    """
    logger.info('PushGate configuration created')
    yield
    logger.info('Doing PushGate configuration cleanup')


@pytest.fixture(scope='module')
def vlan_configuration(topology_obj, request):
    """
    Pytest fixture which are doing VLAN configuration
    :param topology_obj: topology object fixture
    :param request: pytest buildin argument
    """
    vlan_config_dict = getattr(request.module, 'vlan', {})
    with allure.step('Doing VLAN configuration'):
        # TODO: implement logic for set port mode: trunk/access
        for host_alias, configuration in vlan_config_dict.items():
            engine = topology_obj.players[host_alias]['engine']
            for vlan_info in configuration:
                if host_alias == 'dut':
                    sonic_vlan_clis.add_vlan(engine, vlan_info['vlan_id'])
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_port = topology_obj.ports[vlan_port]
                        sonic_vlan_clis.add_port_to_vlan(engine, vlan_port, vlan_info['vlan_id'])
                else:
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_iface = get_vlan_iface(topology_obj, host_alias, vlan_port, vlan_info['vlan_id'])
                        vlan_port = topology_obj.ports[vlan_port]
                        linux_vlan_clis.add_vlan_interface(engine, vlan_port, vlan_info['vlan_id'])
                        linux_interface_clis.enable_interface(engine, vlan_iface)

    yield

    with allure.step('Doing VLAN cleanup'):
        for host_alias, configuration in vlan_config_dict.items():
            engine = topology_obj.players[host_alias]['engine']
            for vlan_info in configuration:
                if host_alias == 'dut':
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_port = topology_obj.ports[vlan_port]
                        sonic_vlan_clis.del_port_from_vlan(engine, vlan_port, vlan_info['vlan_id'])
                    sonic_vlan_clis.del_vlan(engine, vlan_info['vlan_id'])
                else:
                    for vlan_port in vlan_info['vlan_members']:
                        vlan_iface = get_vlan_iface(topology_obj, host_alias, vlan_port, vlan_info['vlan_id'])
                        linux_interface_clis.del_interface(engine, vlan_iface)


@pytest.fixture(scope='module')
def ip_configuration(topology_obj, request):
    """
    Pytest fixture which are doing IP configuration
    :param topology_obj: topology object fixture
    :param request: pytest buildin argument
    """
    ip_config_dict = getattr(request.module, 'ip', {})
    with allure.step('Doing IP configuration'):
        for host_alias, configuration in ip_config_dict.items():
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
        for host_alias, configuration in ip_config_dict.items():
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


# Helper methods
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
