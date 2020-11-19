from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon


class SonicGeneralCli(GeneralCliCommon):
    """
    This class is for general cli commands for sonic only
    """

    @staticmethod
    def show_feature_status(engine):
        """
        This method show feature status on the sonic switch
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show feature status')

    @staticmethod
    def install_image(engine, image_path):
        output = engine.run_cmd('sudo sonic_installer install {} -y'.format(image_path))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to install image {}'.format(image_path))
        return output

    @staticmethod
    def get_image_binary_version(engine, image_path):
        output = engine.run_cmd('sudo sonic_installer binary_version {}'.format(image_path))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to get binary version for: {}'.format(image_path))
        return output

    @staticmethod
    def set_default_image(engine, image_binary):
        output = engine.run_cmd('sudo sonic_installer set_default {}'.format(image_binary))
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to set default image: {}'.format(image_binary))
        return output

    @staticmethod
    def get_sonic_image_list(engine):
        output = engine.run_cmd('sudo sonic_installer list')
        SonicGeneralCli.verify_cmd_rc(engine, 'Unable to get image list')
        return output

    @staticmethod
    def verify_cmd_rc(engine, error_message):
        rc = engine.run_cmd('echo $?')
        assert int(rc) == 0, error_message

