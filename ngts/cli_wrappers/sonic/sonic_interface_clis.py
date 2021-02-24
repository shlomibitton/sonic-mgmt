import re
import logging

from ngts.cli_wrappers.common.interface_clis_common import InterfaceCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser

logger = logging.getLogger()


class SonicInterfaceCli(InterfaceCliCommon):

    @staticmethod
    def add_interface(engine, interface, iface_type):
        raise NotImplementedError

    @staticmethod
    def del_interface(engine, interface):
        raise NotImplementedError

    @staticmethod
    def enable_interface(engine, interface):
        """
        This method enables a network interface
        :param engine: ssh engine object
        :param interface: interface name which should be enabled, example: Ethernet0
        :return: command output
        """
        return engine.run_cmd("sudo config interface startup {}".format(interface))

    @staticmethod
    def disable_interface(engine, interface):
        """
        This method disables network interface
        :param engine: ssh engine object
        :param interface: interface name which should be disabled, example: Ethernet0
        :return: command output
        """
        return engine.run_cmd("sudo config interface shutdown {}".format(interface))

    @staticmethod
    def set_interface_speed(engine, interface, speed):
        """
        Method which setting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :param speed: speed value
        :return: command output
        """
        # TODO: Move 2 lines below to separate method in ngts/utilities
        if 'G' in speed:
            speed = int(speed.split('G')[0]) * 1000

        return engine.run_cmd("sudo config interface speed {} {}".format(interface, speed))

    @staticmethod
    def set_interface_mtu(engine, interface, mtu):
        """
        Method which setting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :param mtu: mtu value
        :return: command output
        """
        return engine.run_cmd("sudo config interface mtu {} {}".format(interface, mtu))

    @staticmethod
    def show_interfaces_status(engine):
        """
        Method which getting interfaces status
        :param engine: ssh engine object
        :return: parsed command output
        """
        return engine.run_cmd("sudo show interfaces status")

    @staticmethod
    def parse_interfaces_status(engine):
        """
        Method which getting parsed interfaces status
        :param engine: ssh engine object
        :return: dictionary, example: {'Ethernet0': {'Lanes': '0,1,2,3,4,5,6,7', 'Speed': '100G', 'MTU': '9100',
        'FEC': 'N/A', 'Alias': 'etp1', 'Vlan': 'routed', 'Oper': 'up', 'Admin': 'up', 'Type': 'QSFP28 or later',
        'Asym PFC': 'N/A'}, 'Ethernet8': {'Lanes'.......
        """
        ifaces_status = SonicInterfaceCli.show_interfaces_status(engine)
        return generic_sonic_output_parser(ifaces_status, headers_ofset=0, len_ofset=1, data_ofset_from_start=2,
                                           data_ofset_from_end=None, column_ofset=2, output_key='Interface')

    @staticmethod
    def get_interface_speed(engine, interface):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface speed, example: 200G
        """
        return SonicInterfaceCli.parse_interfaces_status(engine)[interface]['Speed']

    @staticmethod
    def get_interfaces_speed(engine, interfaces_list):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface speed dict, example: {'eth1': 200G, 'eth2': '100G'}
        """
        result = {}
        interfaces_data = SonicInterfaceCli.parse_interfaces_status(engine)
        for interface in interfaces_list:
            result[interface] = interfaces_data[interface]['Speed']
        return result

    @staticmethod
    def get_interface_mtu(engine, interface):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface MTU, example: 9100
        """
        return SonicInterfaceCli.parse_interfaces_status(engine)[interface]['MTU']

    @staticmethod
    def get_interfaces_mtu(engine, interfaces_list):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface MTU, example: interface mtu dict, example: {'eth1': 9100, 'eth2': '1500'}
        """
        result = {}
        interfaces_data = SonicInterfaceCli.parse_interfaces_status(engine)
        for interface in interfaces_list:
            result[interface] = interfaces_data[interface]['MTU']
        return result

    @staticmethod
    def show_interfaces_alias(engine):
        """
        This method return output of "show interfaces alias" command
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('show interfaces alias')

    @staticmethod
    def parse_ports_aliases_on_sonic(engine):
        """
        Method which parse "show interfaces alias" command
        :param engine: ssh engine object
        :return: a dictionary with port aliases, example: {'Ethernet0': 'etp1'}
        """
        result = {}
        interfaces_data = SonicInterfaceCli.show_interfaces_alias(engine)
        regex_pattern = "(Ethernet\d+)\s*(etp\d+\w*)"
        list_output = re.findall(regex_pattern, interfaces_data, re.IGNORECASE)
        for port, port_sonic_alias in list_output:
            result[port] = port_sonic_alias
        return result

    @staticmethod
    def check_ports_status(engine, ports_list, expected_status='up'):
        """
        This method verifies that each iinterface is in expected oper state
        :param engine: ssh engine object
        :param ports_list: list with port names which should be in UP state
        :param expected_status_up: 'up' if expected UP, or 'down' if expected DOWN
        :return Assertion exception in case of failure
        """
        logger.info('Checking that ifaces: {} in expected state: {}'.format(ports_list, expected_status))
        ports_status = SonicInterfaceCli.parse_interfaces_status(engine)

        for port in ports_list:
            assert ports_status[port]['Oper'] == expected_status

    def configure_dpb_on_ports(self, engine, conf, expect_error=False, force=False):
        for breakout_mode, ports_list in conf.items():
            for port in ports_list:
                self.configure_dpb_on_port(engine, port, breakout_mode, expect_error, force)

    @staticmethod
    def configure_dpb_on_port(engine, port, breakout_mode, expect_error=False, force=False):
        """
        :param engine: ssh engine object
        :param port: i.e, Ethernet0
        :param breakout_mode: i.e, 4x50G[40G,25G,10G,1G]
        :param expect_error: True if breakout configuration is expected to fail, else False
        :param force: True if breakout configuration should be applied with force, else False
        :return: command output
        """
        logger.info('Configuring breakout mode: {} on port: {}, force mode: {}'.format(breakout_mode, port, force))
        force = "" if force is False else "-f"
        try:
            cmd = 'sudo config interface breakout {PORT} {MODE} -y {FORCE}'.format(PORT=port,
                                                                                   MODE=breakout_mode,
                                                                                   FORCE=force)
            output = engine.send_config_set([cmd, 'y'])
            logger.info(output)
            return output
        except Exception as e:
            if expect_error:
                logger.info(output)
                return output
            else:
                raise AssertionError("Command: {} failed with error {} when was expected to pass".format(cmd, e))

