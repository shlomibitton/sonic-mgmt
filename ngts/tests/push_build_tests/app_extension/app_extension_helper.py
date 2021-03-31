import re
import logging
from ngts.cli_wrappers.sonic.sonic_app_extension_clis import SonicAppExtensionCli
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.cli_util.cli_parsers import generic_sonic_output_parser

logger = logging.getLogger()


def verify_app_repository_list_format(output_cmd):
    """
    Verify format from "sonic-package-manager list" output
    :param output_cmd: output from cmd
    :return: None if output is like follow format, raise error in case of unexpected result:
        Name            Repository                                Description                   Version    Status
        --------------  ----------------------------------------  ----------------------------  ---------  ---------
        database        docker-database                           SONiC database package        1.0.0      Built-In
        dhcp-relay      docker-dhcp-relay                         N/A                           1.0.0      Installed

    """
    excepted_out_list = [[r"Name\s+Repository\s+Description\s+Version\s+Status", True],
                         [r"--+\s{2,}--+\s{2,}--+\s{2,}--+\s{2,}--+", True]]
    verify_show_cmd(output_cmd, excepted_out_list)


def verify_add_app_to_repo(dut_engine, app_name, repo_name, desc="N/A", version="N/A", status="Not Installed"):
    """
    Verify if app is added into repo From "sonic-package-manager list" output
    :param dut_engine: ssh engine object
    :param app_name: app package name
    :param repo_name: app package repository
    :param desc: app package description
    :param version: app package version
    :parm status: indicate if the app package is installed or not
    :Return None, or raise exception  if app info not match all

    """
    app_package_repo_dict = SonicAppExtensionCli.parse_app_package_list_dict(dut_engine)
    if app_name in app_package_repo_dict:
        app_info = app_package_repo_dict[app_name]
        assert all([repo_name == app_info["Repository"],
                    desc == app_info["Description"],
                    version == app_info["Version"],
                    status == app_info["Status"]]),\
            "{} install fail..., app info is {}".format(app_name, app_info)
    else:
        assert False, "{} is not in the package list:{}".format(app_package_repo_dict)




