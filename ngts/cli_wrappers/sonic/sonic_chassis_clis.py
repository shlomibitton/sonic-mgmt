import re
from ngts.cli_wrappers.common.chassis_clis_common import ChassisCliCommon


class SonicChassisCli(ChassisCliCommon):
    """
    This class is for chassis cli commands for sonic only
    """
    def __init__(self):
        pass

    @staticmethod
    def get_platform(engine):
        """
        This method excute command "show platform summery" and return the dut platform type
        :param engine: ssh engine object
        :return: the dut platform type
        """
        output = SonicChassisCli.show_platform_summery(engine)
        pattern = "Platform:\s*(.*)"
        try:
            platform = re.search(pattern, output, re.IGNORECASE).group(1)
            return platform
        except e:
            raise AssertionError("Could not match platform type for switch {}".format(engine.ip))

    @staticmethod
    def show_platform_summery(engine):
        """
        This method excute command "show platform summery" on dut
        :param engine: ssh engine object
        :return: the cmd output
        """
        return engine.run_cmd("show platform summary")
