import logging
import re

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
        return engine.run_cmd("lldptool -i {} -t -n".format(interface_name))

    @staticmethod
    def disable_lldp_on_interface(engine, interface):
        """
        This method disable LLDP on host interface
        :param engine: ssh enging object
        :param interface: interface name
        :return: command output
        """
        return engine.run_cmd("lldptool set-lldp -i {} adminStatus=disabled".format(interface))

    @staticmethod
    def enable_lldp_on_interface(engine, interface):
        """
        This method enable LLDP on host interface
        :param engine: ssh enging object
        :param interface: interface name
        :return: command output
        """
        return engine.run_cmd("lldptool set-lldp -i {} adminStatus=rxtx".format(interface))

    @staticmethod
    def enable_lldp_on_host(engine):
        """
        This method enable LLDP on host
        :param engine: ssh enging object
        :return: command output
        """
        return engine.run_cmd("lldpad -d")

    @staticmethod
    def is_lldp_enabled_on_host(engine):
        """
        This method enable LLDP on host
        :param engine: ssh enging object
        :return: command output
        """
        regex_pattern = "lldpad -d"
        output = engine.run_cmd("ps -aux | grep lldpad")
        return bool(re.search(regex_pattern,output, re.IGNORECASE))