import pytest
import logging
import allure

from retry.api import retry_call
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli
from ngts.config_templates.interfaces_config_template import InterfaceConfigTemplate
from ngts.config_templates.lag_lacp_config_template import LagLacpConfigTemplate
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.config_templates.dhcp_relay_config_template import DhcpRelayConfigTemplate
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli
from ngts.cli_wrappers.sonic.sonic_ip_clis import SonicIpCli
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli
from ngts.cli_wrappers.sonic.sonic_route_clis import SonicRouteCli
from ngts.constants.constants import SonicConst

PRE_UPGRADE_CONFIG = '/tmp/config_db_{}_base.json'
POST_UPGRADE_CONFIG = '/tmp/config_db_{}_target.json'
logger = logging.getLogger()


@pytest.fixture(scope='session')
def run_config_only(request):
    """
    Method for get run_config_only from pytest arguments
    """
    return request.config.getoption('--run_config_only')


@pytest.fixture(scope='session')
def run_test_only(request):
    """
    Method for get run_test_only from pytest arguments
    """
    return request.config.getoption('--run_test_only')


@pytest.fixture(scope='session')
def run_cleanup_only(request):
    """
    Method for get run_cleanup_only from pytest arguments
    """
    return request.config.getoption('--run_cleanup_only')


@pytest.fixture(scope='package', autouse=True)
def push_gate_configuration(topology_obj, engines, interfaces, platform_params, upgrade_params,
                            run_config_only, run_test_only, run_cleanup_only):
    """
    Pytest fixture which are doing configuration fot test case based on push gate config
    :param topology_obj: topology object fixture
    :param engines: engines fixture
    :param interfaces: interfaces fixture
    :param platform_params: platform_params fixture
    :param upgrade_params: upgrade_params fixture
    :param run_config_only: test run mode run_config_only
    :param run_test_only: test run mode run_test_only
    :param run_cleanup_only: test run mode run_cleanup_only
    """
    full_flow_run = all(arg is False for arg in [run_config_only, run_test_only, run_cleanup_only])
    skip_tests = False

    cli_object = topology_obj.players['dut']['cli']

    if upgrade_params.is_upgrade_required:
        with allure.step('Installing base version from ONIE'):
            logger.info('Deploying via ONIE or call manufacture script with arg onie')
            reboot_after_install = True if '201911' in upgrade_params.base_version else None
            SonicGeneralCli.deploy_image(topology_obj, upgrade_params.base_version, apply_base_config=True,
                                         setup_name=platform_params.setup_name, platform=platform_params.platform,
                                         hwsku=platform_params.hwsku, deploy_type='onie',
                                         reboot_after_install=reboot_after_install)

    with allure.step('Check that links in UP state'.format()):
        ports_list = [interfaces.dut_ha_1, interfaces.dut_ha_2, interfaces.dut_hb_1, interfaces.dut_hb_2]
        retry_call(SonicInterfaceCli.check_ports_status, fargs=[engines.dut, ports_list], tries=10, delay=10,
                   logger=logger)

    # variable below required for correct interfaces speed cleanup
    dut_original_interfaces_speeds = SonicInterfaceCli.get_interfaces_speed(engines.dut, [interfaces.dut_ha_1,
                                                                                          interfaces.dut_hb_2])

    # Interfaces config which will be used in test
    interfaces_config_dict = {
        'dut': [{'iface': interfaces.dut_ha_1, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_ha_1, '10G')},
                {'iface': interfaces.dut_hb_2, 'speed': '10G',
                 'original_speed': dut_original_interfaces_speeds.get(interfaces.dut_hb_2, '10G')}]
    }

    # LAG/LACP config which will be used in test
    lag_lacp_config_dict = {
        'dut': [{'type': 'lacp', 'name': 'PortChannel0001', 'members': [interfaces.dut_ha_1]},
                {'type': 'lacp', 'name': 'PortChannel0002', 'members': [interfaces.dut_hb_2]}],
        'ha': [{'type': 'lacp', 'name': 'bond0', 'members': [interfaces.ha_dut_1]}],
        'hb': [{'type': 'lacp', 'name': 'bond0', 'members': [interfaces.hb_dut_2]}]
    }

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 40, 'vlan_members': [{'PortChannel0002': 'trunk'}, {interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 69, 'vlan_members': [{'PortChannel0002': 'trunk'}]},
                {'vlan_id': 690, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]},
                {'vlan_id': 691, 'vlan_members': [{interfaces.dut_ha_2: 'trunk'}]}
                ],
        'ha': [{'vlan_id': 40, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 690, 'vlan_members': [{interfaces.ha_dut_2: None}]},
               {'vlan_id': 691, 'vlan_members': [{interfaces.ha_dut_2: None}]}
               ],
        'hb': [{'vlan_id': 40, 'vlan_members': [{'bond0': None}]},
               {'vlan_id': 69, 'vlan_members': [{'bond0': None}]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan40', 'ips': [('40.0.0.1', '24'), ('4000::1', '64')]},
                {'iface': 'PortChannel0001', 'ips': [('30.0.0.1', '24'), ('3000::1', '64')]},
                {'iface': 'Vlan69', 'ips': [('69.0.0.1', '24'), ('6900::1', '64')]},
                {'iface': 'Vlan690', 'ips': [('69.0.1.1', '24'), ('6900:1::1', '64')]},
                {'iface': 'Vlan691', 'ips': [('69.1.0.1', '24'), ('6910::1', '64')]}
                ],
        'ha': [{'iface': '{}.40'.format(interfaces.ha_dut_2), 'ips': [('40.0.0.2', '24'), ('4000::2', '64')]},
               {'iface': 'bond0', 'ips': [('30.0.0.2', '24'), ('3000::2', '64')]}],
        'hb': [{'iface': 'bond0.40', 'ips': [('40.0.0.3', '24'), ('4000::3', '64')]},
               {'iface': 'bond0.69', 'ips': [('69.0.0.2', '24'), ('6900::2', '64')]},
               ]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'dut': [{'dst': '20.0.0.10', 'dst_mask': 32, 'via': ['69.0.0.2']},
                # TODO: static route below commented(we add it directly in static_route test case)
                #  due to the bug: https://github.com/Azure/sonic-buildimage/issues/7028
                # {'dst': '20.0.0.1', 'dst_mask': 32, 'via': ['PortChannel0001']},
                {'dst': '20.0.0.0', 'dst_mask': 24, 'via': ['30.0.0.2']},
                {'dst': '2000::10', 'dst_mask': 128, 'via': ['6900::2']},
                {'dst': '2000::1', 'dst_mask': 128, 'via': ['Vlan69']},
                {'dst': '2000::', 'dst_mask': 64, 'via': ['3000::2']}
                ],
        'hb': [{'dst': '69.0.1.0', 'dst_mask': 24, 'via': ['69.0.0.1']},
               {'dst': '69.1.0.0', 'dst_mask': 24, 'via': ['69.0.0.1']}]
    }

    # DHCP Relay config which will be used in test
    dhcp_relay_config_dict = {
        'dut': [{'vlan_id': 690, 'dhcp_servers': ['69.0.0.2', '6900::2']},
                # Second DHCP relay for check bug: https://github.com/Azure/sonic-buildimage/issues/6053
                {'vlan_id': 691, 'dhcp_servers': ['69.0.0.2', '6900::2']}
                ]
    }

    if run_config_only or full_flow_run:
        logger.info('Starting PushGate Common configuration')
        InterfaceConfigTemplate.configuration(topology_obj, interfaces_config_dict)
        LagLacpConfigTemplate.configuration(topology_obj, lag_lacp_config_dict)
        VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
        IpConfigTemplate.configuration(topology_obj, ip_config_dict)
        RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
        DhcpRelayConfigTemplate.configuration(topology_obj, dhcp_relay_config_dict)
        logger.info('PushGate Common configuration completed')

        with allure.step('Doing debug logs print'):
            log_debug_info_before_upgrade(engines.dut)

        with allure.step('Doing conf save'):
            logger.info('Doing config save')
            cli_object.general.save_configuration(engines.dut)

    if upgrade_params.is_upgrade_required:
        with allure.step('Doing upgrade to target version'):
            with allure.step('Copying config_db.json from base version'):
                engines.dut.copy_file(source_file='config_db.json',
                                      dest_file=PRE_UPGRADE_CONFIG.format(engines.dut.ip),
                                      file_system=SonicConst.SONIC_CONFIG_FOLDER, overwrite_file=True, verify_file=False,
                                      direction='get')
            with allure.step('Performing sonic to sonic upgrade'):
                logger.info('Performing sonic to sonic upgrade')
                SonicGeneralCli.deploy_image(topology_obj, upgrade_params.target_version, apply_base_config=False,
                                             wjh_deb_url=upgrade_params.wjh_deb_url, deploy_type='sonic')
            with allure.step('Copying config_db.json from target version'):
                engines.dut.copy_file(source_file='config_db.json',
                                      dest_file=POST_UPGRADE_CONFIG.format(engines.dut.ip),
                                      file_system=SonicConst.SONIC_CONFIG_FOLDER, overwrite_file=True, verify_file=False,
                                      direction='get')

    if run_test_only or full_flow_run:
        yield
    else:
        skip_tests = True

    if run_cleanup_only or full_flow_run:
        logger.info('Starting PushGate Common configuration cleanup')
        DhcpRelayConfigTemplate.cleanup(topology_obj, dhcp_relay_config_dict)
        RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
        IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
        VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)
        LagLacpConfigTemplate.cleanup(topology_obj, lag_lacp_config_dict)
        InterfaceConfigTemplate.cleanup(topology_obj, interfaces_config_dict)
        logger.info('Doing config save after cleanup')
        cli_object.general.save_configuration(engines.dut)
        logger.info('PushGate Common cleanup completed')

    if skip_tests:
        pytest.skip('Skipping test according to flags: run_config_only/run_test_only/run_cleanup_only')


def log_debug_info_before_upgrade(dut_engine):
    logger.info('Started debug prints')
    SonicInterfaceCli.show_interfaces_status(dut_engine)
    SonicIpCli.show_ip_interfaces(dut_engine)
    SonicVlanCli.show_vlan_config(dut_engine)
    SonicRouteCli.show_ip_route(dut_engine)
    SonicRouteCli.show_ip_route(dut_engine, ipv6=True)
    logger.info('Finished debug prints')
