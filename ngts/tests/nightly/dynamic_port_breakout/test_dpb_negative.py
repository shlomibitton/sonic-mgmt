import allure
import pytest
import random
import re
from retry.api import retry_call
from ngts.tests.nightly.dynamic_port_breakout.conftest import all_breakout_options, logger, is_splittable, \
    compare_actual_and_expected_speeds, cleanup, get_mutual_breakout_modes, send_ping_and_verify_results, \
    set_dpb_conf, verify_port_speed_and_status, verify_no_breakout


@pytest.mark.ngts_skip({'github_ticket_list': [6631, 6610, 6720]})
@allure.title('Dynamic Port Breakout negative test: breakout on unbreakable port')
def test_breakout_unbreakable_ports(topology_obj, dut_engine, cli_object,
                                    ports_breakout_modes, tested_modes_lb_conf):
    """
    try break a unbreakable port and validate the breakout failed.
    :return:  raise assertion error if expected output is not matched
    """
    try:
        breakout_mode, lb = random.choice(list(tested_modes_lb_conf.items()))
        unsplittable_port = [random.choice(get_unsplittable_ports_list(topology_obj, ports_breakout_modes))]
        with allure.step('Verify breakout mode: {} on unsplittable port: {} Fails'
                                 .format(breakout_mode, unsplittable_port)):
            verify_negative_breakout_configuration(dut_engine, cli_object, unsplittable_port, breakout_mode)
    except Exception as e:
        raise e


@pytest.mark.ngts_skip({'github_ticket_list': [6631, 5947, 6610, 6720]})
@allure.title('Dynamic Port Breakout negative test: unsupported breakout mode')
def test_unsupported_breakout_mode(topology_obj, dut_engine, cli_object, tested_modes_lb_conf,
                                   ports_breakout_modes, cleanup_list):
    """
    This test case will set unsupported breakout mode on a port,
    then will verify that wrong configuration is not applied,
    and check link-state (split port are up and there’s no traffic loss)
    :return: raise assertion error if expected output is not matched
    """
    try:
        breakout_mode, lb = random.choice(list(tested_modes_lb_conf.items()))
        mutual_breakout_modes = get_mutual_breakout_modes(ports_breakout_modes, lb)
        unsupported_breakout_mode = random.choice(list(all_breakout_options.difference(set(mutual_breakout_modes))))

        with allure.step('Verify unsupported breakout mode {} on ports {} fails as expected'
                                 .format(unsupported_breakout_mode, lb)):
            verify_negative_breakout_configuration(dut_engine, cli_object, lb, unsupported_breakout_mode)
        send_ping_and_verify_results(topology_obj, dut_engine, cleanup_list, conf={unsupported_breakout_mode: lb})
    except Exception as e:
        raise e


@pytest.mark.ngts_skip({'github_ticket_list': [6631, 6610, 6720]})
@allure.title('Dynamic Port Breakout negative test: Wrong breakout removal from breakout port')
def test_ports_breakout_after_wrong_removal(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                            cleanup_list, tested_modes_lb_conf):
    """
    configure breakout on loopback than try to unbreak the loopback
    by configure unbreakout mode on the wrong ports.
    see if ports are still up after wrong removal tryout,
    then check that correct removal succeeded.
    :return: Raise assertion error if validation failed
    """

    breakout_mode, lb = random.choice(list(tested_modes_lb_conf.items()))
    with allure.step('Configure breakout mode: {} on loopback: {}'.format(breakout_mode, lb)):
        breakout_ports_conf = set_dpb_conf(topology_obj, dut_engine, cli_object, ports_breakout_modes,
                                           cleanup_list, conf={breakout_mode: lb})
    ports_list_after_breakout = list(breakout_ports_conf.keys())

    with allure.step('Verify ports {} are up after breakout'.format(ports_list_after_breakout)):
        verify_port_speed_and_status(cli_object, dut_engine, breakout_ports_conf)

    for port in lb:
        breakout_port_list = get_breakout_ports(ports_breakout_modes, breakout_mode, port)
        breakout_port_list.remove(port)
        breakout_port = random.choice(breakout_port_list)
        unbreakout_port_mode = ports_breakout_modes[port]['default_breakout_mode']
        err_msg = r"KeyError:\s+\'{}\'".format(breakout_port)
        with allure.step('Verify unbreak out with mode {} on breakout port {} failed as expected'
                                 .format(unbreakout_port_mode, breakout_port)):
            verify_breakout_on_port_failed(dut_engine, cli_object, breakout_port, unbreakout_port_mode, err_msg)

    with allure.step('Verify ports {} are up after wrong breakout removal'.format(ports_list_after_breakout)):
        retry_call(cli_object.interface.check_ports_status,
                   fargs=[dut_engine, ports_list_after_breakout],
                   tries=2, delay=2, logger=logger)

    with allure.step('Remove breakout from ports: {} with mode {}'.format(lb, unbreakout_port_mode)):
        cleanup(cleanup_list)

    with allure.step('Verify breakout ports were removed correctly'):
        verify_no_breakout(dut_engine, cli_object, ports_breakout_modes,  conf={breakout_mode: lb})


def get_breakout_ports(ports_breakout_modes, breakout_mode, port):
    """
    :param breakout_mode: i.e., '4x50G[40G,25G,10G,1G]'
    :param port: i.e, 'Ethernet8'
    :return: a list of ports after breakout, i.e ['Ethernet8','Ethernet9','Ethernet10','Ethernet11']
    """
    return list(ports_breakout_modes[port]['breakout_port_by_modes'][breakout_mode].keys())


def verify_negative_breakout_configuration(dut_engine, cli_object, ports_list, breakout_mode):
    with allure.step('Get speed configuration of ports {} before breakout'.format(ports_list)):
        pre_breakout_speed_conf = cli_object.interface.get_interfaces_speed(dut_engine, ports_list)
    err_msg = r"\[ERROR\]\s+Target\s+mode\s+.*is\s+not\s+available\s+for\s+the\s+port\s+{}"
    with allure.step('Verify breakout mode {} on ports {} fails as expected'
                             .format(breakout_mode, ports_list)):
        for port in ports_list:
            verify_breakout_on_port_failed(dut_engine, cli_object, port, breakout_mode, err_msg.format(port))
    with allure.step('Get speed configuration of ports {} after breakout'.format(ports_list)):
        post_breakout_speed_conf = cli_object.interface.get_interfaces_speed(dut_engine, ports_list)
    compare_actual_and_expected_speeds(pre_breakout_speed_conf, post_breakout_speed_conf)


def get_unsplittable_ports_list(topology_obj, ports_breakout_modes):
    """
    :return: a list of ports on dut which doesn't support any breakout mode
    """
    unsplittable_ports = []
    for port_alias, port_name in topology_obj.ports.items():
        if port_alias.startswith("dut") and "splt" not in port_alias and \
                not is_splittable(ports_breakout_modes, port_name):
            unsplittable_ports.append(port_name)
    return unsplittable_ports


def verify_breakout_on_port_failed(dut_engine, cli_object, port, breakout_mode, err_msg):
    """
    :param port: i.e, 'Ethernet8'
    :param breakout_mode: i.e., '4x50G[40G,25G,10G,1G]'
    :param err_msg: a regex expression
    :return: raise error if error message was not in output after breakout
    """
    with allure.step('Verify breakout mode {} on port {} failed as expected with error message: {}'
                             .format(breakout_mode, port, err_msg)):
        output = cli_object.interface.configure_dpb_on_port(dut_engine, port, breakout_mode,
                                                                 expect_error=True, force=False)
        if not re.search(err_msg, output, re.IGNORECASE):
            raise AssertionError("Expected breakout mode {} on port {} "
                                 "to failed with error msg {} but output {}".
                                 format(breakout_mode, port, err_msg, output))

