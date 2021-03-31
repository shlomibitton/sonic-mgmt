from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser


class SonicAppExtensionCli:
    """
    This class hosts SONiC APP Extension cli methods
    """
    def __init__(self):
        pass

    @staticmethod
    def add_repository(engine, app_name, repository_name):
        engine.run_cmd('sudo sonic-package-manager repository add {} {}'.format(app_name, repository_name),
                       validate=True)

    @staticmethod
    def remove_repository(engine, app_name):
        engine.run_cmd('sudo sonic-package-manager repository remove {}'.format(app_name), validate=True)

    @staticmethod
    def install_app(engine, app_name, version=""):
        if version:
            engine.run_cmd('sudo sonic-package-manager install {}=={} -y'.format(app_name, version), validate=True)
        else:
            engine.run_cmd('sudo sonic-package-manager install {} -y'.format(app_name), validate=True)

    @staticmethod
    def uninstall_app(engine, app_name):
        engine.run_cmd('sudo sonic-package-manager uninstall {} -y'.format(app_name), validate=True)

    @staticmethod
    def show_app_list(engine):
        return engine.run_cmd('sudo sonic-package-manager list')

    @staticmethod
    def parse_app_package_list_dict(engine):
        """
        Parse app package data into dict by "sonic-package-manager list" output
        :param dut_engine: ssh engine object
        :Return app package dict, or raise exception
        """
        app_package_repo_list = SonicAppExtensionCli.show_app_list(engine)
        app_package_repo_dict = generic_sonic_output_parser(app_package_repo_list,
                                                            headers_ofset=0,
                                                            len_ofset=1,
                                                            data_ofset_from_start=2,
                                                            data_ofset_from_end=None,
                                                            column_ofset=2,
                                                            output_key='Name')
        return app_package_repo_dict
