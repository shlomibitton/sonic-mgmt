from ngts.cli_wrappers.common.mac_clis_common import MacCliCommon


class SonicMacCli(MacCliCommon):

    @staticmethod
    def show_mac(engine):
        """
        This method runs 'show mac' command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show mac')
