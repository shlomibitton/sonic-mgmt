import allure
import logging
import random

from retry import retry
from retry.api import retry_call
from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_wrappers.sonic.sonic_interface_clis import SonicInterfaceCli

DOCKERS_LIST = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp', 'dhcp_relay']

logger = logging.getLogger()


class SonicGeneralCli(GeneralCliCommon):
    """
    This class is for general cli commands for sonic only
    """

    @staticmethod
    def show_feature_status(engine):
        """
        This method show feature status on the sonic switch
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show feature status')

    @staticmethod
    def get_installer_delimiter(engine):
        dash_installer = 'sonic-installer'
        delimiter = '_'
        output = engine.run_cmd('which {}'.format(dash_installer))
        if dash_installer in output:
            delimiter = '-'
        return delimiter

    @staticmethod
    def install_image(engine, image_path, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer install {} -y'.format(delimiter, image_path))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to install image {}'.format(image_path))
        return output

    @staticmethod
    def get_image_binary_version(engine, image_path, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer binary{}version {}'.format(delimiter, delimiter, image_path))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to get binary version for: {}'.format(image_path))
        return output

    @staticmethod
    def set_default_image(engine, image_binary, delimiter='-'):
        output = engine.run_cmd('sudo sonic{}installer set{}default {}'.format(delimiter, delimiter, image_binary))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to set default image: {}'.format(image_binary))
        return output

    @staticmethod
    def get_sonic_image_list(engine, delimiter='_'):
        output = engine.run_cmd('sudo sonic{}installer list'.format(delimiter))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to get image list')
        return output

    @staticmethod
    def load_configuration(engine, config_file):
        engine.run_cmd('sudo config load -y {}'.format(config_file))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to load configuration file {}'.format(config_file))

    @staticmethod
    def save_configuration(engine):
        engine.run_cmd('sudo config save -y')
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to save configuration')

    @staticmethod
    def reboot_flow(engine, reboot_type=''):
        """
        Rebooting switch by given way(reboot, fast-reboot, warm-reboot)
        :param engine: ssh engine object
        :param reboot_type: reboot type
        :return: None, raise error in case of unexpected result
        """
        if not reboot_type:
            reboot_type = random.choice(['reboot', 'fast-reboot', 'warm-reboot'])
        with allure.step('Reboot switch by CLI - sudo {}'.format(reboot_type)):
            engine.reload(['sudo {}'.format(reboot_type)])
            SonicGeneralCli.verify_dockers_is_up(engine, DOCKERS_LIST)
            SonicGeneralCli.check_link_state(engine)

    @staticmethod
    @retry(AssertionError, tries=10, delay=10)
    def verify_dockers_is_up(engine, dockers_list=None):
        """
        Verifying the dockers are in up state
        :param engine: ssh engine object
        :param dockers_list: list of dockers to check
        :return: None, raise error in case of unexpected result
        """
        if dockers_list is None:
            dockers_list = DOCKERS_LIST
        for docker in dockers_list:
            engine.run_cmd('docker ps | grep {}'.format(docker))
            SonicGeneralCli.verify_cmd_rc(engine, '{} is not running'.format(docker))

    @staticmethod
    def check_link_state(engine, iface='Ethernet0'):
        """
        Verify that link in UP state. Default interface is  Ethernet0, this link exist in each Canonical setup
        :param engine: ssh engine object
        :param iface: interface to check
        :return: None, raise error in case of unexpected result
        """
        with allure.step('Check that link in UP state'):
            retry_call(SonicInterfaceCli.check_ports_status,
                       fargs=[engine, [iface]],
                       tries=5,
                       delay=10,
                       logger=logger)
