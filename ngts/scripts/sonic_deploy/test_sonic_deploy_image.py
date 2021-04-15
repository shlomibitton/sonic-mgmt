#!/usr/bin/env python
import allure
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()


@allure.title('Deploy sonic image')
def test_deploy_sonic_image(topology_obj, setup_name, platform_params, base_version, wjh_deb_url, deploy_type, apply_base_config):
    """
    This script will deploy sonic image on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :param platform_params: platform_params fixture
    :param base_version: path to sonic version to be installed
    :param wjh_deb_url: wjh_deb_url fixture
    :param deploy_type: deploy_type fixture
    :param apply_base_config: apply_base_config fixture
    :return: raise assertion error in case of script failure
    """
    try:
        SonicGeneralCli.deploy_image(topology_obj, base_version, apply_base_config=apply_base_config, setup_name=setup_name,
                                     platform=platform_params['platform'], hwsku=platform_params['hwsku'],
                                     wjh_deb_url=wjh_deb_url, deploy_type=deploy_type)
    except Exception as err:
        raise AssertionError(err)
