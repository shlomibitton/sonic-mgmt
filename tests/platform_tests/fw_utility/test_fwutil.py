import logging
import pytest

from fwutil_helper import FW_TYPE_INSTALL, FW_TYPE_UPDATE
from fwutil_helper import FW_INSTALL_INVALID_NAME_LOG, FW_INSTALL_INVALID_PATH_LOG, FW_INSTALL_INVALID_URL_LOG
from fwutil_helper import FW_UPDATE_INVALID_PLATFORM_SCHEMA_LOG, FW_UPDATE_INVALID_CHASSIS_SCHEMA_LOG, FW_UPDATE_INVALID_COMPONENT_SCHEMA_LOG
from fwutil_helper import get_fw_status, install_firmware, generate_invalid_components_file, execute_invalid_command
from fwutil_helper import update_from_current_image, update_from_next_image

logger = logging.getLogger(__name__)


def test_show_positive(duthost, platform_components):
    """
    Verify firmware status is valid
    Note: use vendor specific platform config file
    """
    fw_status = get_fw_status(duthost)

    logger.info("Verify platform schema")
    for comp in platform_components:
        if comp not in fw_status:
            pytest.fail("Missing component {}".format(comp))


@pytest.mark.disable_loganalyzer
@pytest.mark.parametrize("component_firmware", [ FW_TYPE_INSTALL ], indirect=True)
def test_install_positive(request, skip_if_no_update, component_object, component_firmware, pdu_controller):
    """
    Verify firmware install from local path
    """
    comp_name = component_object.get_name()

    if not component_firmware['is_latest_installed']:
        fw_path = component_firmware['latest_firmware']
        fw_version = component_firmware['latest_version']

        # install latest firmware
        logger.info("Install latest {} firmware: version={}, path={}".format(comp_name, fw_version, fw_path))
        install_firmware(request, fw_path, fw_version)
    else:
        fw_path = component_firmware['previous_firmware']
        fw_version = component_firmware['previous_version']

        # install previous firmware
        logger.info("Install previous {} firmware: version={}, path={}".format(comp_name, fw_version, fw_path))
        install_firmware(request, fw_path, fw_version)

        fw_path = component_firmware['latest_firmware']
        fw_version = component_firmware['latest_version']

        # install latest firmware
        logger.info("Install latest {} firmware: version={}, path={}".format(comp_name, fw_version, fw_path))
        install_firmware(request, fw_path, fw_version)


@pytest.mark.disable_loganalyzer
@pytest.mark.parametrize("component_firmware", [ FW_TYPE_INSTALL ], indirect=True)
def test_install_negative(request, duthost, component_object, component_firmware):
    """
    Verify that firmware utility is able to handle
    invalid install flow as expected
    """
    comp_name = component_object.get_name()
    fw_path = component_firmware['latest_firmware']

    # invalid component name
    logger.info("Verify invalid component name case")
    cmd = "fwutil install chassis component {} fw -y {}".format('INVALID_COMPONENT', fw_path)
    execute_invalid_command(duthost, cmd, FW_INSTALL_INVALID_NAME_LOG)

    # invalid path
    logger.info("Verify invalid path case")
    cmd = "fwutil install chassis component {} fw -y {}".format(comp_name, '/this/is/invalid/path')
    execute_invalid_command(duthost, cmd, FW_INSTALL_INVALID_PATH_LOG)

    # invalid url
    logger.info("Verify invalid url case")
    cmd = "fwutil install chassis component {} fw -y {}".format(comp_name, 'http://this/is/invalid/url')
    execute_invalid_command(duthost, cmd, FW_INSTALL_INVALID_URL_LOG)


@pytest.mark.disable_loganalyzer
@pytest.mark.parametrize("component_firmware", [ FW_TYPE_UPDATE ], indirect=True)
def test_update_positive(request, skip_if_no_update, component_firmware, setup_images):
    """
    Verify firmware update from current/next image
    """
    update_from_current_image(request)
    update_from_next_image(request)


@pytest.mark.disable_loganalyzer
def test_update_negative(request, duthost, component_object, backup_platform_file):
    """
    Verify that firmware utility is able to handle
    invalid 'platform_components.json' file as expected
    """
    comp_name = component_object.get_name()
    cmd = "fwutil update chassis component {} fw -y".format(comp_name)

    # invalid platform schema
    logger.info("Verify invalid platform schema case")
    generate_invalid_components_file(
        request,
        chassis_key='INVALID_CHASSIS',
        component_key='component',
        is_valid_comp_structure=True
    )
    execute_invalid_command(duthost, cmd, FW_UPDATE_INVALID_PLATFORM_SCHEMA_LOG)

    # invalid chassis schema
    logger.info("Verify invalid chassis schema case")
    generate_invalid_components_file(
        request,
        chassis_key='chassis',
        component_key='INVALID_COMPONENT',
        is_valid_comp_structure=True
    )
    execute_invalid_command(duthost, cmd, FW_UPDATE_INVALID_CHASSIS_SCHEMA_LOG)

    # invalid components schema
    logger.info("Verify invalid components schema case")
    generate_invalid_components_file(
        request,
        chassis_key='chassis',
        component_key='component',
        is_valid_comp_structure=False
    )
    execute_invalid_command(duthost, cmd, FW_UPDATE_INVALID_COMPONENT_SCHEMA_LOG)
