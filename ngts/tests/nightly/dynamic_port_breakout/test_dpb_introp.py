import allure
import pytest
import random
import re
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.cli_util.cli_constants import SonicConstant
from ngts.tests.nightly.dynamic_port_breakout.conftest import logger, get_ports_list_from_loopback_tuple_list, \
    set_ip_dependency, verify_no_breakout, set_dpb_conf, verify_port_speed_and_status, \
    send_ping_and_verify_results


@pytest.mark.ngts_skip({'rm_ticket_list': [2456527], 'github_ticket_list': [6631, 6720, 6721, 5947]})
@allure.title('Dynamic Port Breakout with Dependencies')
def test_dpb_configuration_interop(topology_obj, dut_engine, cli_object, ports_breakout_modes, tested_modes_lb_conf,
                                   cleanup_list, dependency_list=['vlan', 'portchannel'], reboot_type=None):
    """
    self.tested_modes_lb_conf = a dictionary of the tested configuration,
    i.e breakout mode and ports list which breakout mode will be applied on
    {'2x50G[40G,25G,10G,1G]': ('Ethernet212', 'Ethernet216'), '4x25G[10G,1G]': ('Ethernet228', 'Ethernet232')}

    This test case will set dependency configuration on a port,
    then will try to break out the port with/without force,
    then check link-state and dependencies on the split port
    :param dependency_list: list of features that will be configured before port breakout
    :return: raise assertion error if expected output is not matched
    """
    try:
        ports_list = get_ports_list_from_loopback_tuple_list(tested_modes_lb_conf.values())
        ports_dependencies = set_dependencies(topology_obj, dependency_list, ports_list, cleanup_list)
        verify_breakout_without_force(dut_engine, cli_object, ports_breakout_modes,
                                      tested_modes_lb_conf, ports_dependencies)
        breakout_ports_conf = verify_breakout_with_force(topology_obj, dut_engine, cli_object,  ports_breakout_modes,
                                                         cleanup_list, tested_modes_lb_conf,
                                                         dependency_list, ports_dependencies)
        reboot_type = random.choice(
            list(SonicConstant.REBOOT_TYPES.values())) if reboot_type is None else reboot_type
        reboot_and_check_functionality(topology_obj, dut_engine, cli_object, cleanup_list,
                                       tested_modes_lb_conf, reboot_type, breakout_ports_conf)

    except Exception as e:
        raise e


def set_dependencies(topology_obj, dependency_list, ports_list, cleanup_list):
    """
    configure the dependencies in list on all the ports
    :param dependency_list: a list of features i.e. ['vlan', 'portchannel']
    :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
    :return:  a dictionary with the ports configured dependencies information
    for example,
    {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
    'Ethernet216': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0002'},...}

    """
    conf = {"vlan": set_vlan_dependency,
            "portchannel": set_port_channel_dependency,
            "ip": set_ip_dependency
            }
    ports_dependencies = {port: {} for port in ports_list}
    for dependency in dependency_list:
        conf[dependency](topology_obj, ports_list, ports_dependencies, cleanup_list)
    return ports_dependencies


def set_vlan_dependency(topology_obj, ports_list, ports_dependencies, cleanup_list):
    """
    configure vlan dependency on all the ports in ports_list and update the configuration
    in the dictionary ports_dependencies.
    :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
    :param ports_dependencies: a dictionary with the ports configured dependencies information
    for example,
    {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
    :return: None
    """
    vlan_num = random.choice(range(2, 4094))
    vlan_mode = random.choice(['access', 'trunk'])
    vlan_members = []
    for port in ports_list:
        vlan_members.append({port: vlan_mode})
        ports_dependencies[port].update({'vlan': 'Vlan{}'.format(vlan_num)})
    vlan_config_dict = {'dut': [{'vlan_id': vlan_num, 'vlan_members': vlan_members}]}
    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    cleanup_list.append((VlanConfigTemplate.cleanup, (topology_obj, vlan_config_dict,)))


def set_port_channel_dependency(topology_obj, ports_list, ports_dependencies, cleanup_list):
    """
    configure port-channel dependency on all the ports in ports_list and update the configuration
    in the dictionary ports_dependencies.
    :param ports_list: a list of the ports ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40',..]
    :param ports_dependencies: a dictionary with the ports configured dependencies information
    for example,
    {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
    :return: None
    """
    lag_lacp_config_dict = {'dut': []}
    for index, port in enumerate(ports_list):
        port_channel_name = 'PortChannel000{}'.format(index + 1)
        lag_lacp_config_dict['dut'].append({'type': 'lacp',
                                            'name': port_channel_name,
                                            'members': [port]})
        ports_dependencies[port].update({"portchannel": port_channel_name})
    LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
    cleanup_list.append((LagLacpConfigTemplate.cleanup, (topology_obj, lag_lacp_config_dict,)))


def verify_breakout_without_force(dut_engine, cli_object, ports_breakout_modes,
                                  tested_modes_lb_conf, ports_dependencies):
    """
    :param ports_dependencies: a dictionary with the ports configured dependencies information
    :return: None, raise assertion error in case of failure
    """
    for breakout_mode, lb in tested_modes_lb_conf.items():
        for port in lb:
            port_dependencies = ports_dependencies[port]
            verify_breakout_failed_due_dependency(dut_engine, cli_object, breakout_mode, port, port_dependencies)
    verify_no_breakout(dut_engine, cli_object, ports_breakout_modes, conf=tested_modes_lb_conf)


def verify_breakout_failed_due_dependency(dut_engine, cli_object, breakout_mode, port, port_dependencies):
    """
    Configure breakout_mode on port without force and verify that the breakout failed due the dependencies.
    :param breakout_mode: i.e. "4x25G[10G]"
    :param port: i.e. 'Ethernet212'
    :param port_dependencies: a dictionary with the port configured dependencies, i.e.
    {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'}
    :return: None, raise assertion error in case of failure
    """
    with allure.step('Configure breakout without force on port: {}'.format(port)):
        output = cli_object.interface.configure_dpb_on_port(dut_engine, port, breakout_mode,
                                                                 expect_error=True, force=False)
    verify_dependencies_in_output(port_dependencies, output)


def verify_dependencies_in_output(port_dependencies, breakout_output):
    """
    verify that the breakout failed due the dependencies.
    :param port_dependencies: a dictionary with the port configured dependencies, i.e.
    {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'}
    :param breakout_output: the output from the breakout configuration command
    :return: None, raise assertion error in case of failure
    """
    err_msg = r"Dependecies\s+Exist\.\s+No\s+further\s+action\s+will\s+be\s+taken"
    with allure.step('Configure breakout without force fail with error: {}'.format(err_msg)):
        if not re.search(err_msg, breakout_output, re.IGNORECASE):
            raise AssertionError("Error message: {} was not found in breakout output".format(err_msg))
        for dependency, value in port_dependencies.items():
            if not re.search(value, breakout_output, re.IGNORECASE):
                raise AssertionError(
                    "Dependency: {} with value {} was not mentioned when breakout port {} with mode {}")


def verify_breakout_with_force(topology_obj, dut_engine, cli_object, ports_breakout_modes, cleanup_list,
                               tested_modes_lb_conf, dependency_list, ports_dependencies):
    """
    configure breakout mode with force and verify breakout is
    successful and dependencies were removed from ports.
    :param dependency_list:  a list of features i.e. ['vlan', 'portchannel']
    :param ports_dependencies:  a dictionary with the ports configured dependencies information
    for example,
    {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
    'Ethernet216': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0002'},...}
    :return: a dictionary with the port configuration after breakout
    {'Ethernet216': '25G',
    'Ethernet217': '25G',...}
    """
    with allure.step('Configure breakout with force on ports: {}'.format(ports_dependencies.keys())):
        breakout_ports_conf = set_dpb_conf(topology_obj, dut_engine, cli_object,
                                           ports_breakout_modes, cleanup_list, tested_modes_lb_conf, force=True)
    verify_port_speed_and_status(cli_object, dut_engine, breakout_ports_conf)
    verify_no_dependencies_on_ports(dut_engine, cli_object, dependency_list, ports_dependencies)
    return breakout_ports_conf


def verify_no_dependencies_on_ports(dut_engine, cli_object, dependency_list, ports_dependencies):
    """
    verify all dependencies were removed from ports after breakout
    :param dependency_list:  a list of features i.e. ['vlan', 'portchannel']
    :param ports_dependencies:  a dictionary with the ports configured dependencies information
    for example,
    {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001'},
    'Ethernet216': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0002'},...}
    :return: raise assertion error in case dependency was not removed
    """
    conf = {"vlan": verify_no_vlan_on_ports,
            "portchannel": verify_no_port_channel_on_ports,
            "ip": verify_no_ip_on_ports
            }
    for dependency in dependency_list:
        conf[dependency](dut_engine, cli_object, ports_dependencies)


def verify_no_vlan_on_ports(dut_engine, cli_object, ports_dependencies):
    """
    :param ports_dependencies: a dictionary with the ports configured dependencies information
     i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
    :return: raise assertion error in case dependency still exist on port
    """
    with allure.step('verify no vlan configuration on ports: {}'.format(ports_dependencies.keys())):
        vlan_expected_info = []
        show_vlan_config_pattern = r"Vlan{vid}\s+{vid}\s+{member}"
        for port, port_dependency in ports_dependencies.items():
            vlan_id = port_dependency["vlan"]
            vlan_expected_info.append((show_vlan_config_pattern.format(vid=vlan_id, member=port), False))
        vlan_info = cli_object.vlan.show_vlan_config(dut_engine)
        verify_show_cmd(vlan_info, vlan_expected_info)


def verify_no_port_channel_on_ports(dut_engine, cli_object, ports_dependencies):
    """
    :param ports_dependencies: a dictionary with the ports configured dependencies information
     i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
    :return: raise assertion error in case dependency still exist on port
    """
    with allure.step('verify no port channel configuration on ports: {}'.format(ports_dependencies.keys())):
        port_channel_expected_info = []
        show_port_channel_config_pattern = r"{PORTCHANNEL}.*{PORT}"
        for port, port_dependency in ports_dependencies.items():
            port_channel_name = port_dependency["portchannel"]
            port_channel_expected_info.append((show_port_channel_config_pattern.
                                               format(PORTCHANNEL=port_channel_name, PORT=port), False))
        port_channel_info = cli_object.lag.show_interfaces_port_channel(dut_engine)
        verify_show_cmd(port_channel_info, port_channel_expected_info)


def verify_no_ip_on_ports(dut_engine, cli_object, ports_dependencies):
    """
    :param ports_dependencies: a dictionary with the ports configured dependencies information
     i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
    :return: raise assertion error in case dependency still exist on port
    """
    with allure.step('verify no ip configuration on ports: {}'.format(ports_dependencies.keys())):
        ip_expected_info = []
        show_ip_config_pattern = r"{port}/s+{ip}"
        for port, port_dependency in ports_dependencies.items():
            ip = port_dependency["ip"]
            ip_expected_info.append((show_ip_config_pattern.format(port=port, ip=ip), False))
        ip_info = cli_object.ip.show_ip_interfaces(dut_engine)
        verify_show_cmd(ip_info, ip_expected_info)


def reboot_and_check_functionality(topology_obj, dut_engine, cli_object, cleanup_list,
                                   tested_modes_lb_conf, reboot_type, breakout_ports_conf):
    """
    :param reboot_type: i.e reboot/warm-reboot/fast-reboot
    :param breakout_ports_conf: a dictionary with the port configuration after breakout
    {'Ethernet216': '25G',
    'Ethernet217': '25G',...}
    :return: raise assertion error in case validation failed after reboot
    """
    save_configuration_and_reboot(dut_engine, cleanup_list, reboot_type)
    verify_port_speed_and_status(cli_object, dut_engine, breakout_ports_conf)
    send_ping_and_verify_results(topology_obj, dut_engine, cleanup_list, tested_modes_lb_conf)


def save_configuration_and_reboot(dut_engine, cleanup_list, reboot_type):
    """
    save configuration and reboot
    :param reboot_type: i.e reboot/warm-reboot/fast-reboot
    :return: none
    """
    with allure.step('Save configuration and reboot with type: {}'.format(reboot_type)):
        dut_engine.run_cmd('sudo config save -y')
        cleanup_list.append((dut_engine.run_cmd, ('sudo config save -y',)))
        logger.info("Reload switch with reboot type: {}".format(reboot_type))
        dut_engine.reload(['sudo {}'.format(reboot_type)])


@pytest.mark.ngts_skip({'github_ticket_list': [6631, 6630, 6610, 6720, 6721, 5947]})
@allure.title('Dynamic Port remove breakout from breakout ports with dependencies')
def test_remove_dpb_configuration_interop(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                          cleanup_list, tested_modes_lb_conf, dependency_list=['vlan', 'portchannel']):
    """
    This test case will set dependency configuration on a split port,
    then will try to unsplit the port with/without force,
    then check link-state and dependencies on the port.
    :param dependency_list: list of features that will be configured before port breakout removal
    :return: raise assertion error if expected output is not matched
    """
    try:
        with allure.step('Configure breakout mode on ports: {}'.format(tested_modes_lb_conf)):
            breakout_ports_conf = set_dpb_conf(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                               cleanup_list, tested_modes_lb_conf)
        with allure.step('set dependencies on breakout ports: {}'.format(list(breakout_ports_conf.keys()))):
            ports_dependencies = set_dependencies(topology_obj, dependency_list,
                                                  list(breakout_ports_conf.keys()), cleanup_list)
        verify_remove_breakout_without_force(dut_engine, cli_object, ports_breakout_modes,
                                             tested_modes_lb_conf, ports_dependencies)
        verify_remove_breakout_with_force(topology_obj, dut_engine, cli_object,
                                          tested_modes_lb_conf, ports_breakout_modes,
                                          cleanup_list, dependency_list, ports_dependencies)

    except Exception as e:
        raise e


def verify_remove_breakout_without_force(dut_engine, cli_object, ports_breakout_modes,
                                         tested_modes_lb_conf, ports_dependencies):
    """
    verify remove breakout without force failed when port has dependencies configuration on it
    :param ports_dependencies: a dictionary with the ports configured dependencies information
     i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
    :return: raise assertion error in case validation failed
    """
    for breakout_mode, lb in tested_modes_lb_conf.items():
        for port in lb:
            port_dependencies = ports_dependencies[port]
            verify_remove_breakout_failed_due_dependency(dut_engine, cli_object, ports_breakout_modes,
                                                         breakout_mode, port, port_dependencies)


def verify_remove_breakout_failed_due_dependency(dut_engine, cli_object, ports_breakout_modes,
                                                 breakout_mode, port, port_dependencies):
    """
    configure un breakout mode and verify that it failed due to configured dependencies on port
    :param breakout_mode: port current breakout mode i.e, '4x25G[10G,1G]'
    :param port: i.e, 'Ethernet212'
    :param port_dependencies:  a dictionary with the ports configured dependencies information
     i.e {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}
    :return: raise assertion error in case validation failed
    """
    default_breakout_mode = ports_breakout_modes[port]['default_breakout_mode']

    with allure.step('Verify remove breakout without force failed '
                     'due dependencies configuration on port : {}'.format(port)):
        output = cli_object.interface.configure_dpb_on_port(dut_engine, port, default_breakout_mode,
                                                            expect_error=True, force=False)
    verify_dependencies_in_output(port_dependencies, output)
    verify_remove_breakout_failed(dut_engine, cli_object, ports_breakout_modes, breakout_mode, port)


def verify_remove_breakout_failed(dut_engine, cli_object, ports_breakout_modes, breakout_mode, port):
    """
    check that port is still in breakout mode and all it's breakout ports in state up
    :param breakout_mode: port current breakout mode i.e, '4x25G[10G,1G]'
    :param port:  i.e, 'Ethernet212'
    :return: raise assertion error in case validation failed
    """
    breakout_ports = ports_breakout_modes[port]['breakout_port_by_modes'][breakout_mode]
    with allure.step('Verify remove breakout without force failed and all breakout ports : {} are up'
                             .format(breakout_ports)):
        cli_object.interface.check_ports_status(dut_engine, breakout_ports, expected_status='up')


def verify_remove_breakout_with_force(topology_obj, dut_engine, cli_object,
                                      tested_modes_lb_conf, ports_breakout_modes,
                                      cleanup_list, dependency_list, ports_dependencies):
    """
    remove breakout configuration with force and validate all dependencies were removed from port
    :param ports_dependencies: a dictionary with the ports configured dependencies information
     i.e {'Ethernet212': {'vlan': 'Vlan3730', 'portchannel': 'PortChannel0001', 'ip': 10.10.10.1}, ...}
    :return: raise assertion error in case validation failed
    """
    remove_breakout_ports_conf = build_remove_dpb_conf(tested_modes_lb_conf, ports_breakout_modes)
    with allure.step('Configure remove breakout with force'):
        breakout_ports_conf = set_dpb_conf(topology_obj, dut_engine, cli_object, ports_breakout_modes, cleanup_list,
                                           remove_breakout_ports_conf, force=True)
    with allure.step('Verify remove breakout succeeded and breakout ports no longer exist'):
        verify_no_breakout(dut_engine, cli_object, ports_breakout_modes, conf=tested_modes_lb_conf)
    verify_port_speed_and_status(cli_object, dut_engine, breakout_ports_conf)
    verify_no_dependencies_on_ports(dut_engine, cli_object, dependency_list,  ports_dependencies)
    send_ping_and_verify_results(topology_obj, dut_engine, cleanup_list, tested_modes_lb_conf)
    return breakout_ports_conf


def build_remove_dpb_conf(tested_modes_lb_conf, ports_breakout_modes):
    """
    :return: a dictionary with the breakout mode to remove all the breakout configuration
    i.e,
    {'1x100G[50G,40G,25G,10G]': ('Ethernet212', 'Ethernet216'),
    '1x100G[50G,40G,25G,10G]': ('Ethernet228', 'Ethernet232')}
    """
    remove_breakout_ports_conf = {}
    for breakout_mode, lb in tested_modes_lb_conf.items():
        remove_breakout_ports_conf[ports_breakout_modes[lb[0]]['default_breakout_mode']] = lb
    return remove_breakout_ports_conf
