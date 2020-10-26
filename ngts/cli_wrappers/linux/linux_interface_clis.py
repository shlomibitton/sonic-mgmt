import allure

from ngts.cli_wrappers.common.interface_clis_common import InterfaceCliCommon


class LinuxInterfaceCli(InterfaceCliCommon):

    @staticmethod
    def add_interface(engine, interface, iface_type):
        """
        This method creates a network interface with specific type
        :param engine: ssh engine object
        :param interface: interface name which should be added
        :param iface_type: linux interface type
        :return: command output
        """
        with allure.step('{}: creating interface: {}, type {}'.format(engine.ip, interface, iface_type)):
            return engine.run_cmd("sudo ip link add {} type {}".format(interface, iface_type))

    @staticmethod
    def del_interface(engine, interface):
        """
        This method delete a network interface
        :param engine: ssh engine object
        :param interface: interface name which should be removed, example: bond0.5
        :return: command output
        """
        with allure.step('{}: deleting interface {}'.format(engine.ip, interface)):
            return engine.run_cmd("sudo ip link del {}".format(interface))

    @staticmethod
    def add_bond_interface(engine, interface):
        """
        Method which adding bond interface to linux
        :param engine: ssh engine object
        :param interface: interface name which should be added
        :return: command output
        """
        with allure.step('{}: adding bond interface: {}'.format(engine.ip, interface)):
            return engine.run_cmd("sudo ip link add {} type bond".format(interface))

    @staticmethod
    def enable_interface(engine, interface):
        """
        This method enables a network interface
        :param engine: ssh engine object
        :param interface: interface name which should be enabled, example: bond0.5
        :return: command output
        """
        with allure.step('{}: setting interface {} to admin UP state'.format(engine.ip, interface)):
            return engine.run_cmd("sudo ip link set {} up".format(interface))

    @staticmethod
    def disable_interface(engine, interface):
        """
        This method disables network interface
        :param engine: ssh engine object
        :param interface: interface name which should be disabled, example: bond0.5
        :return: command output
        """
        with allure.step('{}: setting interface {} to admin DOWN state'.format(engine.ip, interface)):
            return engine.run_cmd("sudo ip link set {} down".format(interface))

    @staticmethod
    def add_port_to_bond(engine, interface, bond_name):
        """
        Method which adding slave to bond interface in linux
        :param engine: ssh engine object
        :param interface: interface name which should be added to bond
        :param bond_name: bond interface name
        :return: command output
        """
        with allure.step('{}: adding interface {} to bond {}'.format(engine.ip, interface, bond_name)):
            return engine.run_cmd("sudo ip link set {} master {}".format(interface, bond_name))

    @staticmethod
    def set_interface_speed(engine, interface, speed):
        """
        Method which setting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :param speed: speed value
        :return: command output
        """
        raise NotImplementedError

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
            return engine.run_cmd("ip link set mtu {} dev {}".format(mtu, interface))

    @staticmethod
    def show_interfaces_status(engine):
        """
        Method which getting interfaces status
        :param engine: ssh engine object
        :return: parsed command output
        """
        with allure.step('{}: doing "ifconfig"'.format(engine.ip)):
            return engine.run_cmd("ifconfig")

    @staticmethod
    def get_interface_speed(engine, interface):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface speed, example: 200G
        """
        raise NotImplementedError

    @staticmethod
    def get_interfaces_speed(engine, interfaces_list):
        """
        Method which getting interface speed
        :param engine: ssh engine object
        :param interfaces_list: interfaces name list, example: ['eth1', 'eth2']
        :return: interface speed dict, example: {'eth1': 200G, 'eth2': '100G'}
        """
        raise NotImplementedError

    @staticmethod
    def get_interface_mtu(engine, interface):
        """
        Method which getting interface MTU
        :param engine: ssh engine object
        :param interface: interface name
        :return: interface MTU, example: 9100
        """
        with allure.step('{}: getting MTU value for interface {}'.format(engine.ip, interface)):
            return engine.run_cmd('cat /sys/class/net/{}/mtu'.format(interface))

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
            for interface in interfaces_list:
                result[interface] = engine.run_cmd('cat /sys/class/net/{}/mtu'.format(interface))
            return result
