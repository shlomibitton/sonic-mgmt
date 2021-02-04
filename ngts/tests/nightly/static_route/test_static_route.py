import allure
import logging
import pytest

from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd

from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker
from infra.tools.yaml_tools.yaml_loops import ip_range


"""

 Static Route Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+Static+Routes+Documentation

"""

logger = logging.getLogger()


@pytest.fixture()
def static_route_configuration(topology_obj):
    """
    This function will configure 100k IPv6 static routes and 100k IPv6 static routes
    :param topology_obj: topology object fixture
    :return: 2 lists with IPv4 and IPv6 addresses
    """
    dutha1 = topology_obj.ports['dut-ha-1']
    duthb1 = topology_obj.ports['dut-hb-1']
    hadut1 = topology_obj.ports['ha-dut-1']
    hbdut1 = topology_obj.ports['hb-dut-1']

    # Range for 100 000 IPv4 and IPv6 addresses
    ipv4_list = ip_range('100.0.0.1', '100.1.134.160', ip_type='ipv4', step=1)
    ipv6_list = ip_range('2000::1', '2000::1:86a0', ip_type='ipv6', step=1)

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'hb': [{'iface': 'dummy1', 'create': True, 'type': 'dummy'}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': dutha1, 'ips': [('150.0.0.1', '24'), ('1500::1', '64')]},
                {'iface': duthb1, 'ips': [('160.0.0.1', '24'), ('1600::1', '64')]}],
        'ha': [{'iface': hadut1, 'ips': [('150.0.0.2', '24'), ('1500::2', '64')]}],
        'hb': [{'iface': hbdut1, 'ips': [('160.0.0.2', '24'), ('1600::2', '64')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'dut': [],
        'ha': [],
        'hb': [{'dst': '150.0.0.2', 'dst_mask': 32, 'via': ['160.0.0.1']},
               {'dst': '1500::2', 'dst_mask': 128, 'via': ['1600::1']}]
    }

    dummy1_ip_config_list = []

    for ip_addr in ipv4_list:
        dummy1_ip_config_list.append((ip_addr, '32'))
        static_route_config_dict['dut'].append({'dst': ip_addr, 'dst_mask': 32, 'via': ['160.0.0.2']})
        static_route_config_dict['ha'].append({'dst': ip_addr, 'dst_mask': 32, 'via': ['150.0.0.1']})

    for ip_addr in ipv6_list:
        dummy1_ip_config_list.append((ip_addr, '128'))
        static_route_config_dict['dut'].append({'dst': ip_addr, 'dst_mask': 128, 'via': ['1600::2']})
        static_route_config_dict['ha'].append({'dst': ip_addr, 'dst_mask': 128, 'via': ['1500::1']})

    ip_config_dict['hb'].append({'iface': 'dummy1', 'ips': dummy1_ip_config_list})

    logger.info('Starting StaticRoute Scale configuration')
    InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    logger.info('StaticRoute Scale configuration completed')

    yield ipv4_list, ipv6_list

    logger.info('Starting StaticRoute Scale configuration cleanup')
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)

    logger.info('StaticRoute Scale cleanup completed')


@pytest.mark.skip(reason="Too long test, will be created separate cases file")
@allure.title('Test Scale Static Route')
def test_scale_static_route(topology_obj, disable_ssh_client_alive_interval, static_route_configuration):
    """
    This test will check scale for static route functionality(we will use 100 000 static routes)
    Test(fixture before) will configure on DUT 100 000 static routes for IPv4 with mask /32
    and 100 000 static routes for IPv6 with mask /128
    Test will create on HB interface dummy1 and will assign on it all IPs(v4 and v6) for which we have routes on DUT
    Test will add static routes on HA for IPs for which we have routes on DUT via DUT
    Test will add on HB route to HA IPs

    Validation:
    - Test will check total number of static routes
    - Test will send ICMP from HA to each IP address(IPv4 and IPv6) on HB via DUT(dut should route traffic)

    :param topology_obj: topology object fixture
    :param disable_ssh_client_alive_interval: pytest fixture which will disable SSH client disconnection after 15 min
    without activity
    :return: raise assertion error in case when test failed
    """
    hadut1 = topology_obj.ports['ha-dut-1']
    hbdut1 = topology_obj.ports['hb-dut-1']
    dut_engine = topology_obj.players['dut']['engine']

    try:
        # TODO: Workaround for bug https://redmine.mellanox.com/issues/2350931
        validation_create_arp_ipv4 = {'sender': 'hb', 'args': {'interface': hbdut1, 'count': 3, 'dst': '160.0.0.1'}}
        PingChecker(topology_obj.players, validation_create_arp_ipv4).run_validation()
        validation_create_arp_ipv6 = {'sender': 'hb', 'args': {'interface': hbdut1, 'count': 3, 'dst': '1600::1'}}
        PingChecker(topology_obj.players, validation_create_arp_ipv6).run_validation()
        # TODO: End workaround for bug https://redmine.mellanox.com/issues/2350931

        with allure.step('Check that static routes IPv4 on switch using CLI'):
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route_type='summary'),
                            expected_output_list=[(r'static\s+100000\s+100000', True)])

        with allure.step('Check that static routes IPv6 on switch using CLI'):
            verify_show_cmd(SonicRouteCli.show_ip_route(dut_engine, route_type='summary', ipv6=True),
                            expected_output_list=[(r'static\s+100000\s+100000', True)])

        ipv4_list, ipv6_list = static_route_configuration

        for ip in ipv4_list:
            with allure.step('Check static routes IPv4 on switch by sending PING to {}'.format(ip)):
                validation_ipv4 = {'sender': 'ha', 'args': {'interface': hadut1, 'count': 3, 'dst': ip}}
                logger.info('Sending 3 ping packets to {}'.format(ip))
                PingChecker(topology_obj.players, validation_ipv4).run_validation()

        for ip in ipv6_list:
            with allure.step('Check static routes IPv6 on switch by sending PING to {}'.format(ip)):
                validation_ipv6 = {'sender': 'ha', 'args': {'interface': hadut1, 'count': 3, 'dst': ip}}
                logger.info('Sending 3 ping packets to {}'.format(ip))
                PingChecker(topology_obj.players, validation_ipv6).run_validation()

    except Exception as err:
        raise AssertionError(err)
