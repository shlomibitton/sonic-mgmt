#!/usr/bin/env python
import allure
import pytest
from pathlib import Path
from retry import retry
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest builtin
    """
    logger.info('Parsing image path')
    parser.addoption('--base_version', action='store', required=True, default=None,
                     help='Path to SONiC version')


@pytest.fixture()
def base_version(request):
    """
    Method for getting base version from pytest arguments
    :param request: pytest builtin
    :return: setup name
    """
    return request.config.getoption('--base_version')


@allure.title('Deploy sonic image')
def test_deploy_sonic_image(topology_obj, base_version):
    """
    This script will deploy sonic image on the dut.
    :param topology_obj: topology object fixture
    :param base_version: sonic version to be installed
    :return: raise assertion error in case of script failure
    """
    try:
        image_path = Path(base_version)
        assert image_path.exists(), "The provided image path does not exist: {}".format(image_path)
        image_name = image_path.name
        target_path = '/tmp'
        image_target_path = target_path + '/' + image_name
        dut_engine = topology_obj.players['dut']['engine']
        delimiter = SonicGeneralCli.get_installer_delimiter(dut_engine)

        with allure.step('Deploying image'):
            with allure.step('Copying image to dut'):
                dut_engine.copy_file(source_file=image_path, dest_file=image_name, file_system='/tmp',
                                     overwrite_file=True, verify_file=False)

            with allure.step('Installing the image'):
                SonicGeneralCli.install_image(dut_engine, image_target_path, delimiter)

            with allure.step('Setting image as default'):
                image_binary = SonicGeneralCli.get_image_binary_version(dut_engine, image_target_path, delimiter)
                SonicGeneralCli.set_default_image(dut_engine, image_binary, delimiter)

        with allure.step('Rebooting the dut'):
            dut_engine.reload(['sudo reboot'])

        with allure.step('Verifying installation'):
            with allure.step('Verifying dut booted with correct image'):
                # installer flavor might change after loading a different version
                delimiter = SonicGeneralCli.get_installer_delimiter(dut_engine)
                image_list = SonicGeneralCli.get_sonic_image_list(dut_engine, delimiter)
                assert 'Current: {}'.format(image_binary) in image_list

            with allure.step('Verifying all dockers are up'):
                docker_list = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp', 'dhcp_relay']
                for docker in docker_list:
                    verify_docker_is_up(dut_engine, docker)

    except Exception as err:
        raise AssertionError(err)


@retry(AssertionError, tries=10, delay=10)
def verify_docker_is_up(dut_engine, docker_name):
    dut_engine.run_cmd('docker ps | grep {}'.format(docker_name))
    SonicGeneralCli.verify_cmd_rc(dut_engine, '{} is not running'.format(docker_name))
