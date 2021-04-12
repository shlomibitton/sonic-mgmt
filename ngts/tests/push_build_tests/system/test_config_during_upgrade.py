import logging
import pytest
import yaml
import json
import re
import os
import allure

from deepdiff import DeepDiff
from ngts.cli_wrappers.sonic.sonic_general_clis import SonicGeneralCli


logger = logging.getLogger()
PRE_UPGRADE_CONFIG = '/tmp/config_db_{}_base.json'
POST_UPGRADE_CONFIG = '/tmp/config_db_{}_target.json'


def test_validate_config_db_json_during_upgrade(upgrade_params, testdir, engines,
                                                allowed_diff_file='upgrade_allowed_diff.yaml'):
    """
    This tests checking diff in config_db.json between base and target version
    Test expects that we already have config_db.json for base and target version in /tmp folder
    We getting config for base and target version during push_gate_config fixture execution(in case of upgrade)
    """
    if not upgrade_params.is_upgrade_required:
        pytest.skip('Upgrade was not ran, no need to compare configs')
    test_folder_path = testdir.request.fspath.dirname
    allowed_diff_file_path = os.path.join(test_folder_path, allowed_diff_file)

    with allure.step('Getting base and target versions'):
        base_image, target_image = get_base_and_target_images(engines.dut)

    with allure.step('Comparing configurations before and after the upgrade'):
        upgrade_diff = compare_dut_configs(base_config=PRE_UPGRADE_CONFIG.format(engines.dut.ip),
                                           target_config=POST_UPGRADE_CONFIG.format(engines.dut.ip),
                                           base_ver=base_image,
                                           target_ver=target_image,
                                           allowed_diff_file=allowed_diff_file_path)

    with allure.step('Checking diff in config_db.json between base and target versions'):
        if upgrade_diff:
            allure.attach.file(PRE_UPGRADE_CONFIG.format(engines.dut.ip),
                               'base_config_db.json', allure.attachment_type.JSON)
            allure.attach.file(POST_UPGRADE_CONFIG.format(engines.dut.ip),
                               'target_config_db.json', allure.attachment_type.JSON)
            raise AssertionError('Found unexpected diff in config_db.json during upgrade: \n {}'.format(upgrade_diff))


def get_base_and_target_images(dut_engine):
    """
    This method getting base and target image from "sonic-installer list" output
    """
    installed_list_output = SonicGeneralCli.get_sonic_image_list(dut_engine)
    target_image = re.search(r'Current:\s(.*)', installed_list_output, re.IGNORECASE).group(1)
    try:
        available_images = re.search(r'Available:\s\n(.*)\n(.*)', installed_list_output, re.IGNORECASE)
        available_image_1 = available_images.group(1)
        available_image_2 = available_images.group(2)
        if target_image == available_image_1:
            base_image = available_image_2
        else:
            base_image = available_image_1
    except Exception as err:
        logger.error('Only 1 installed image available')
        raise err

    return base_image, target_image


def compare_dut_configs(base_config, target_config, base_ver, target_ver, allowed_diff_file):
    """
    This method compare base and target config_db.json files.
    Then it compare diff which was found with allowed_diff_file - it unallowed diff found - then return
    list with unexpected diff
    """

    unexpected_diff_list = []

    with open(base_config) as base:
        base_dict = json.load(base)
    with open(target_config) as target:
        target_dict = json.load(target)

    with open(allowed_diff_file) as diff_file:
        allowed_diff_keys = yaml.load(diff_file, Loader=yaml.FullLoader)

    base_branch = None
    target_branch = None

    for base in allowed_diff_keys.keys():
        if '{}.'.format(base) in base_ver:
            for target in allowed_diff_keys[base].keys():
                if '{}.'.format(target) in target_ver:
                    base_branch = base
                    target_branch = target
                    break
    if not (base_branch and target_branch):
        raise AssertionError('Can not find base and target branch in yaml file with upgrade diff')

    diff = DeepDiff(base_dict, target_dict)

    allowed_diff_for_our_branch = allowed_diff_keys[base_branch][target_branch]
    for key, value in diff.items():
        logger.info('Found next difference in config_db.json after upgrade: {} \n {}'.format(key, diff[key]))
        for diff_item in value:
            if diff_item not in allowed_diff_for_our_branch.get(key, []):
                logger.error('Found unexpected diff in config_db.json after upgrade: {} \n {}'.format(key, diff_item))
                unexpected_diff_list.append({key: diff_item})

    for key, value in allowed_diff_for_our_branch.items():
        for diff_item in value:
            if diff_item not in diff.get(key, []):
                logger.error('Expected diff not found in config_db.json after upgrade: {} \n {}'.format(key, diff_item))
                unexpected_diff_list.append({key: diff_item})

    return unexpected_diff_list
