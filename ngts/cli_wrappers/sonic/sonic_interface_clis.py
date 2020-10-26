import allure
import re

from ngts.cli_wrappers.common.interface_clis_common import InterfaceCliCommon


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
        with allure.step('{}: setting interface {} to admin UP state'.format(engine.ip, interface)):
            return engine.run_cmd("sudo config interface startup {}".format(interface))

    @staticmethod
    def disable_interface(engine, interface):
        """
        This method disables network interface
        :param engine: ssh engine object
        :param interface: interface name which should be disabled, example: Ethernet0
        :return: command output
        """
        with allure.step('{}: setting interface {} to admin DOWN state'.format(engine.ip, interface)):
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

        with allure.step('{}: setting interface {} speed {}'.format(engine.ip, interface, speed)):
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
        with allure.step('{}: setting interface {} MTU {}'.format(engine.ip, interface, mtu)):
            return engine.run_cmd("sudo config interface mtu {} {}".format(interface, mtu))

    @staticmethod
    def show_interfaces_status(engine):
        """
        Method which getting interfaces status
        :param engine: ssh engine object
        :return: parsed command output
        """
        with allure.step('{}: doing "show interfaces status"'.format(engine.ip)):
            return engine.run_cmd("sudo show interfaces status")

    @staticmethod
    def get_interface_speed(engine, interface):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface speed, example: 200G
        """
        with allure.step('{}: getting speed for interface: {}'.format(engine.ip, interface)):
            interfaces_data = SonicInterfaceCli.show_interfaces_status(engine)
            for line in interfaces_data.splitlines():
                if re.match('\s*{}\s+'.format(interface), interfaces_data):
                    return line.split()[2]

    @staticmethod
    def get_interfaces_speed(engine, interfaces_list):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface speed dict, example: {'eth1': 200G, 'eth2': '100G'}
        """
        with allure.step('{}: getting speed for interfaces: {}'.format(engine.ip, interfaces_list)):
            result = {}
            interfaces_data = SonicInterfaceCli.show_interfaces_status(engine)
            for interface in interfaces_list:
                for line in interfaces_data.splitlines():
                    if re.match('\s*{}\s+'.format(interface), line):
                        result[interface] = line.split()[2]
            return result

    @staticmethod
    def get_interface_mtu(engine, interface):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface MTU, example: 9100
        """
        with allure.step('{}: getting MTU value for interface {}'.format(engine.ip, interface)):
            interfaces_data = SonicInterfaceCli.show_interfaces_status(engine)
            for line in interfaces_data.splitlines():
                if re.match('\s*{}\s+'.format(interface), interfaces_data):
                    return line.split()[3]

    @staticmethod
    def get_interfaces_mtu(engine, interfaces_list):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface MTU, example: interface mtu dict, example: {'eth1': 9100, 'eth2': '1500'}
        """
        with allure.step('{}: getting MTU value for interfaces: {}'.format(engine.ip, interfaces_list)):
            result = {}
            interfaces_data = SonicInterfaceCli.show_interfaces_status(engine)
            for interface in interfaces_list:
                for line in interfaces_data.splitlines():
                    if re.match('\s*{}\s+'.format(interface), line):
                        result[interface] = line.split()[3]
            return result
