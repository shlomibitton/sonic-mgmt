import allure
import logging
import pytest

from infra.tools.validations.traffic_validations.ping.ping_runner import PingChecker

logger = logging.getLogger()

validation_types = ['fast-reboot', 'warm-reboot', 'reboot', 'config reload -y']

expected_traffic_loss_dict = {'fast-reboot': {'data': 30, 'control': 90},
                              'warm-reboot': {'data': 0, 'control': 90},
                              'reboot': {'data': 180, 'control': 180},
                              'config reload -y': {'data': 180, 'control': 180}
                              }


class TestRebootReload:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, interfaces, engines):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = self.topology_obj.players['dut']['cli']
        self.interfaces = interfaces
        self.ping_sender_iface = '{}.40'.format(self.interfaces.ha_dut_2)
        self.dut_vlan40_int_ip = '40.0.0.1'
        self.dut_port_channel_ip = '30.0.0.1'
        self.hb_vlan40_ip = '40.0.0.3'

    @pytest.fixture(autouse=True)
    def ignore_expected_loganalyzer_exceptions(self, loganalyzer):
        """
        expanding the ignore list of the loganalyzer for these tests because of reboot.
        :param loganalyzer: loganalyzer utility fixture
        :return: None
        """
        if loganalyzer:
            ignore_regex_list = loganalyzer.parse_regexp_file(src=str(os.path.join(os.path.dirname(os.path.abspath(__file__)),
                                                                                   "..", "..", "..",
                                                                                   "tools", "loganalyzer", "reboot_loganalyzer_ignore.txt")))
            loganalyzer.ignore_regex.extend(ignore_regex_list)

    @pytest.mark.ngts_skip({'platform_prefix_list': ['simx'], 'rm_ticket_list': [2566883]})
    @pytest.mark.parametrize('validation_type', validation_types)
    def test_push_gate_reboot(self, validation_type):
        """
        This tests checks reboot time, it doing reboot according to test parameter and after execution - it upload
        test results to MySQL DB
        :param validation_type: validation type - which will be executed
        """

        allowed_data_loss_time = expected_traffic_loss_dict[validation_type]['data']
        allowed_control_loss_time = expected_traffic_loss_dict[validation_type]['control']

        try:
            # Step below required, if no ARP for 30.0.0.2 warm/fast reboot will not work
            with allure.step('Resolve ARP on DUT for IP 30.0.0.2'):
                self.resolve_arp_static_route()

            with allure.step('Starting background validation for control plane traffic'):
                control_plane_checker = self.start_control_plane_validation(validation_type, allowed_control_loss_time)

            with allure.step('Starting background validation for data plane traffic'):
                data_plane_checker = self.start_data_plane_validation(validation_type, allowed_data_loss_time)

            self.do_reboot_or_reload_action(action=validation_type)

            with allure.step('Checking control plane traffic loss'):
                logger.info('Checking that control plane traffic loss not more '
                            'than: {}'.format(allowed_control_loss_time))
                control_plane_checker.complete_validation()

            with allure.step('Checking data plane traffic loss'):
                logger.info('Checking that data plane traffic loss not more than: {}'.format(allowed_data_loss_time))
                data_plane_checker.complete_validation()

        except Exception as err:
            raise AssertionError(err)

    def resolve_arp_static_route(self):
        validation = {'sender': 'ha', 'args': {'iface': 'bond0', 'count': 3, 'dst': self.dut_port_channel_ip}}
        ping = PingChecker(self.topology_obj.players, validation)
        logger.info('Sending 3 ping packets to {}'.format(self.dut_port_channel_ip))
        ping.run_validation()

    def start_control_plane_validation(self, validation_type, allowed_control_loss_time):
        validation_control_plane = {'sender': 'ha',
                                    'name': 'control_plane_{}'.format(validation_type),
                                    'background': 'start',
                                    'args': {'interface': self.ping_sender_iface,
                                             'count': 200, 'dst': self.dut_vlan40_int_ip,
                                             'allowed_traffic_interruptions': 1,
                                             'allowed_traffic_loss_time': allowed_control_loss_time},
                                    }
        control_plane_checker = PingChecker(self.topology_obj.players, validation_control_plane)
        logger.info('Starting background validation for control plane traffic')
        control_plane_checker.run_background_validation()
        return control_plane_checker

    def start_data_plane_validation(self, validation_type, allowed_data_loss_time):
        # Here we will send 1k pps - it allow to check traffic loss less than 1 second
        validation_data_plane = {'sender': 'ha',
                                 'name': 'data_plane_{}'.format(validation_type),
                                 'background': 'start',
                                 'args': {'interface': self.ping_sender_iface,
                                          'count': 200000, 'dst': self.hb_vlan40_ip,
                                          'interval': 0.001,
                                          'allowed_traffic_interruptions': 1,
                                          'allowed_traffic_loss_time': allowed_data_loss_time}}
        data_plane_checker = PingChecker(self.topology_obj.players, validation_data_plane)
        logger.info('Starting background validation for data plane traffic')
        data_plane_checker.run_background_validation()
        return data_plane_checker

    def do_reboot_or_reload_action(self, action):
        if 'reload' in action:
            with allure.step('Reloading the DUT config using cmd: "config reload -y"'):
                self.cli_object.general.reload_configuration(self.dut_engine)
            self.cli_object.general.verify_dockers_are_up(self.dut_engine)
            self.cli_object.general.check_link_state(self.dut_engine, ifaces=self.topology_obj.players_all_ports['dut'])
        else:
            with allure.step('Rebooting the DUT using reboot cmd: "sudo {}"'.format(action)):
                self.cli_object.general.reboot_flow(self.dut_engine, reboot_type=action, topology_obj=self.topology_obj,
                                                    wait_after_ping=0)
