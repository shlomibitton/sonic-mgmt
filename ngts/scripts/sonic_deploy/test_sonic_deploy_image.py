#!/usr/bin/env python
import allure
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()


@allure.title('Deploy sonic image')
def test_deploy_sonic_image(topology_obj, setup_name, platform_params, base_version, wjh_deb_url, deploy_type):
    """
    This script will deploy sonic image on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :param platform: platform fixture
    :param hwsku: hwsku fixture
    :param base_version: path to sonic version to be installed
    :return: raise assertion error in case of script failure
    """
    try:
        SonicGeneralCli.deploy_image(topology_obj, base_version, apply_base_config=True, setup_name=setup_name,
                                     platform=platform_params['platform'], hwsku=platform_params['hwsku'],
                                     wjh_deb_url=wjh_deb_url, deploy_type=deploy_type)
    except Exception as err:
        raise AssertionError(err)
