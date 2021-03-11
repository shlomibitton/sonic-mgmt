#!/usr/bin/env python
import allure
import logging
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()


@allure.title('Deploy sonic image')
def test_deploy_sonic_image(topology_obj, setup_name, platform, hwsku, base_version, wjh_deb_url):
    """
    This script will deploy sonic image on the dut.
    :param topology_obj: topology object fixture
    :param setup_name: setup_name fixture
    :param platform: platform fixture
    :param hwsku: hwsku fixture
    :param base_version: path to sonic version to be installed
    :return: raise assertion error in case of script failure
    """
    dut_engine = topology_obj.players['dut']['engine']
    try:
        SonicGeneralCli.deploy_image(dut_engine, base_version, apply_base_config=True, setup_name=setup_name,
                                     platform=platform, hwsku=hwsku, wjh_deb_url=wjh_deb_url, deploy_type='onie')
    except Exception as err:
        raise AssertionError(err)
