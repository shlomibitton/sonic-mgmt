import allure
import logging
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.tests.push_build_tests.app_extension.app_extension_helper import (
    verify_app_repository_list_format, verify_add_app_to_repo)

logger = logging.getLogger()


@allure.title('Test repo management')
def test_repo_management(engines):
    """
    This test case will check the functionality of package repository management
    Firstly, check sonic-package-manager list, output like as follows:
    Name            Repository                                Description                   Version    Status
    --------------  ----------------------------------------  ----------------------------  ---------  ---------
    database        docker-database                           SONiC database package        1.0.0      Built-In
    dhcp-relay      docker-dhcp-relay                         N/A                           1.0.0      Installed
    fpm-frr         docker-fpm-frr                            SONiC fpm-frr package         1.0.0      Built-In
    lldp            docker-lldp                               SONiC lldp package            1.0.0      Built-In
    Secondly, Add a test repository to the package database with sonic-package-manager repository add <NAME>
    <REPOSITORY>
    and then check the package list that there is a new app added like as follows:
    Name            Repository                                Description                   Version    Status
    --------------  ----------------------------------------  ----------------------------  ---------  ---------
    p4-sampling     harbor.mellanox.com/sonic-p4/p4-sampling  N/A                           N/A        Not Installed
    Thirdly, Remove a test repository from the package database with sonic-package-manager repository remove <NAME>
     <REPOSITORY>,
    and then hen check the package list that the specified app is removed.
    :param topology_obj: topology object
    :param engines: ssh engine object
    """
    dut_engine = engines.dut
    app_name = "p4-sampling"
    app_repository_name = "harbor.mellanox.com/sonic-p4/p4-sampling"

    try:

        with allure.step('Show app package list'):
            app_package_repo_list = SonicAppExtensionCli.show_app_list(dut_engine)
            verify_app_repository_list_format(app_package_repo_list)

        with allure.step('Add a test repository to the package database'):
            SonicAppExtensionCli.add_repository(dut_engine, app_name, app_repository_name)
            verify_add_app_to_repo(dut_engine, app_name, app_repository_name)

        with allure.step('Remove a test repository from the package database'):
            SonicAppExtensionCli.remove_repository(dut_engine, app_name)
            assert app_name not in SonicAppExtensionCli.parse_app_package_list_dict(dut_engine), "{} is not removed ".format(app_name)
    except Exception as err:
        raise AssertionError(err)

    finally:
        # clear app package from repository
        if app_name in SonicAppExtensionCli.parse_app_package_list_dict(dut_engine):
            SonicAppExtensionCli.remove_repository(dut_engine, app_name)