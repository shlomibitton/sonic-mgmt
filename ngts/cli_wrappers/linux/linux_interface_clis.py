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
