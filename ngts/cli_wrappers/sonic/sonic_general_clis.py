from ngts.cli_wrappers.common.general_clis_common import GeneralCliCommon


class SonicGeneralCli(GeneralCliCommon):
    """
    This class is for general cli commands for sonic only
    """

    @staticmethod
    def show_feature_status(engine):
        """
        This method show feature status on the sonic switch
        :param engine: ssh enging object
        :return: command output
        """
        return engine.run_cmd('show feature status')