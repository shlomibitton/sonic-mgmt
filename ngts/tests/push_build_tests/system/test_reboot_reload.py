import allure
import logging
import pytest
import time
import os
import yaml

from ngts.tools.skip_test.skip import ngts_skip
from ngts.tools.mysql_api.mysql_api import DB

logger = logging.getLogger()

reboot_types = ['fast-reboot', 'warm-reboot', 'reboot']


class TestRebootReload:

    @pytest.fixture(autouse=True)
    def setup(self, testdir, topology_obj, engines, platform_params, sonic_version):
        self.topology_obj = topology_obj
        self.dut_engine = engines.dut
        self.cli_object = self.topology_obj.players['dut']['cli']

        self.platform_params = platform_params
        platform_index = 1
        self.platform = self.platform_params.hwsku.split('-')[platform_index]
        self.current_test_folder = testdir.request.fspath.dirname
        expected_reboot_reload_time_file_path = os.path.join(self.current_test_folder,
                                                             'expected_reboot_reload_time.yaml')
        with open(expected_reboot_reload_time_file_path) as raw_reboot_reload_time_data:
            expected_reboot_reload_time_dict = yaml.load(raw_reboot_reload_time_data, Loader=yaml.FullLoader)
        self.expected_reboot_reload_time_dict = expected_reboot_reload_time_dict[self.platform]
        self.setup_name = platform_params.setup_name
        self.sonic_ver = sonic_version

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
    @pytest.mark.parametrize('reboot_type', reboot_types)
    def test_push_gate_reboot(self, platform_params, request, reboot_type):
        """
        This tests checks reboot time, it doing reboot according to test parameter and after execution - it upload
        test results to MySQL DB
        :param platform_params: pytest fixture with platform params
        :param request: pytest buildin
        :param reboot_type: reboot type - which will be executed
        """
        if reboot_type == 'fast-reboot':
            ngts_skip(platform_params.platform,
                      github_ticket_list=['https://github.com/Azure/sonic-buildimage/issues/4793'])

        start_time = time.time()
        reboot_time = 0.0
        try:
            with allure.step('Rebooting the dut using reboot cmd: "sudo {}"'.format(reboot_type)):
                dut_cli = self.topology_obj.players['dut']['cli']
                dut_cli.general.reboot_flow(self.dut_engine, reboot_type=reboot_type, topology_obj=self.topology_obj,
                                            wait_after_ping=0)

            reboot_time = time.time() - start_time
            logger.info('Test reboot: {} run time is: {}'.format(reboot_type, reboot_time))
            expected_reboot_time = self.expected_reboot_reload_time_dict[reboot_type]
            assert reboot_time < expected_reboot_time, 'Reboot time: {} is bigger ' \
                                                       'than expected: {}'.format(reboot_time, expected_reboot_time)

        except Exception as err:
            raise AssertionError(err)
        finally:
            mysql_columns_values = {
                                    "test_name": request.node.originalname,
                                    "setup_name": self.setup_name,
                                    "time_stamp": time.time(),
                                    "os_version": self.sonic_ver,
                                    "platform": self.platform,
                                    "reboot_type": reboot_type,
                                    "reboot_time": reboot_time
            }
            logger.info('Uploading test results to MySQL DB')
            DB().insert(table='reboot_time', columns_values=mysql_columns_values)

    @pytest.mark.ngts_skip({'platform_prefix_list': ['simx'], 'rm_ticket_list': [2615940]})
    def test_push_gate_config_reload(self, request):
        """
        This tests checks config reload time, it doing reload and after execution - it upload test results to MySQL DB
        :param request: pytest buildin
        """
        start_time = time.time()
        reload_time = 0.0
        try:
            with allure.step('Reloading the DUT config by cmd: "config reload -y"'):
                self.cli_object.general.reload_configuration(self.dut_engine)

            self.cli_object.general.verify_dockers_are_up(self.dut_engine)
            self.cli_object.general.check_link_state(self.dut_engine)

            reload_time = time.time() - start_time
            logger.info('Config reload run time is: {}'.format(reload_time))
            expected_reload_time = self.expected_reboot_reload_time_dict['config_reload']
            assert reload_time < expected_reload_time, 'Reload time: {} is bigger ' \
                                                       'than expected: {}'.format(reload_time, expected_reload_time)

        except Exception as err:
            raise AssertionError(err)
        finally:
            mysql_columns_values = {
                                    "test_name": request.node.originalname,
                                    "setup_name": self.setup_name,
                                    "time_stamp": time.time(),
                                    "os_version": self.sonic_ver,
                                    "platform": self.platform,
                                    "reload_time": reload_time
            }
            logger.info('Uploading test results to MySQL DB')
            DB().insert(table='reload_time', columns_values=mysql_columns_values)
