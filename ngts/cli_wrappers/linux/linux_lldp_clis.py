import logging

from ngts.cli_wrappers.common.lldp_clis_common import LldpCliCommon

logger = logging.getLogger()


class LinuxLldpCli(LldpCliCommon):

    @staticmethod
    def show_lldp_info_for_specific_interface(engine, interface_name):
        """
        This method gets LLDP information for a specific interface
        :param engine: ssh enging object
        :param interface_name: interface name
        :return: command output
        """
        raise NotImplementedError
