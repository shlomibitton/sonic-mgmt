import allure
import pytest
import re
from ngts.tests.nightly.dynamic_port_breakout.conftest import get_mutual_breakout_modes, \
    is_splittable, set_dpb_conf, verify_port_speed


@pytest.mark.skip(reason="skip until all config_db.json file will be updated with breakout_cfg section")
@pytest.mark.ngts_skip({'github_ticket_list': ['https://github.com/Azure/sonic-buildimage/issues/6631',
                                               'https://github.com/Azure/sonic-buildimage/issues/6720']})
@allure.title('Dynamic Port Breakout on all ports')
def test_dpb_on_all_ports(topology_obj, dut_engine, cli_object, ports_breakout_modes, cleanup_list):
    """
    This test case will set every possible breakout mode on all the ports,
    then verify that unsplittable ports were not split and splittable ports were.
    configuration was updated as expected, and check link-state.
    :return: raise assertion error if expected output is not matched
    """
    try:
        ports_list = get_splittable_ports_list(topology_obj, ports_breakout_modes)
        breakout_modes = get_mutual_breakout_modes(ports_breakout_modes, ports_list)
        max_breakout_mode = get_max_breakout_mode(breakout_modes)
        with allure.step(
                'Configure breakout mode: {} on all splittable ports: {}'.format(max_breakout_mode, ports_list)):
            validate_split_all_splittable_ports(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                                ports_list, max_breakout_mode, cleanup_list)

    except Exception as e:
        raise e


def get_splittable_ports_list(topology_obj, ports_breakout_modes):
    """
    :return: a list of ports on dut which support split breakout mode,and aren't already split
    """
    splittable_ports = []
    for port_alias, port_name in topology_obj.ports.items():
        if port_alias.startswith("dut") and "splt" not in port_alias and \
                is_splittable(ports_breakout_modes, port_name):
            splittable_ports.append(port_name)
    return splittable_ports


def get_max_breakout_mode(breakout_modes):
    """
    :param breakout_modes: list of breakout modes  ['4x50G[40G,25G,10G,1G]', '2x100G[50G,40G,25G,10G,1G]']
    :return: the max breakout mode supported on dut from list of breakout modes
    """
    breakout_mode_pattern = r"\dx\d+G\[[\d*G,]*\]|\dx\d+G"
    breakout_modes_filtered = list(filter(lambda breakout_mode:
                                          re.search(breakout_mode_pattern,
                                                    breakout_mode), breakout_modes))
    breakout_mode_pattern_capture_breakout_number = r"(\d)x\d+G\[[\d*G,]*\]|(\d)x\d+G"
    max_breakout_mode = max(breakout_modes_filtered, key=lambda breakout_mode:
                            int(re.search(breakout_mode_pattern_capture_breakout_number,
                                breakout_mode).group(1)))
    return max_breakout_mode


def validate_split_all_splittable_ports(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                        ports_list, breakout_mode, cleanup_list):
    """
    executing breakout on all the ports and validating the ports state after the breakout.
    :param ports_list: a list of ports, i.e. ['Ethernet8', 'Ethernet4', 'Ethernet36', 'Ethernet40']
    :param breakout_mode: i.e. '4x50G[40G,25G,10G,1G]'
    :return:
    """
    breakout_ports_conf = set_dpb_conf(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                       conf={breakout_mode: ports_list}, cleanup_list=cleanup_list)
    verify_port_speed(dut_engine, cli_object, breakout_ports_conf)
