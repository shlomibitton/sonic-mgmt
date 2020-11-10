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
    def get_interface_speed(engine, interface):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface speed, example: 200G
        """
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
        result = {}
        interfaces_data = SonicInterfaceCli.show_interfaces_status(engine)
        for interface in interfaces_list:
            for line in interfaces_data.splitlines():
                if re.match('\s*{}\s+'.format(interface), line):
                    result[interface] = line.split()[3]
        return result

    @staticmethod
    def show_interfaces_alias(engine):
        """
        This method return output of "show interfaces alias" command
        :param engine: ssh enging object
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
