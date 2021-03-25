from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon


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
