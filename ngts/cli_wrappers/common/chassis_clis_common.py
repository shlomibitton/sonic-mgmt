import allure
from ngts.cli_wrappers.interfaces.interface_chassis_clis import ChassisCliInterface


class ChassisCliCommon(ChassisCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    @staticmethod
    def get_hostname(engine):
        """
        This method return the hostname of host/switch
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd("hostname")
