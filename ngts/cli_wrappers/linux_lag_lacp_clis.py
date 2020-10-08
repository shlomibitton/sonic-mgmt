import allure


def add_bond_interface(engine, interface):
    """
    Method which adding bond interface to linux
    :param engine: ssh engine object
    :param interface: interface name which should be added
    :return: command output
    """
    with allure.step('{}: adding bond interface: {}'.format(engine.ip, interface)):
        return engine.run_cmd("ip link add {} type bond".format(interface))


def add_port_to_bond(engine, interface, bond_name):
    """
    Method which adding slave to bond interface in linux
    :param engine: ssh engine object
    :param interface: interface name which should be added to bond
    :param bond_name: bond interface name
    :return: command output
    """
    with allure.step('{}: adding interface {} to bond {}'.format(engine.ip, interface, bond_name)):
        return engine.run_cmd("ip link set {} master {}".format(interface, bond_name))


def set_bond_mode(engine, bond_name, bond_mode):
    """
    Method which setting specific bond mode for linux bond interface
    :param engine: ssh engine object
    :param bond_name: bond interface name
    :param bond_mode: bond mode which will be set
    :return: command output
    """
    with allure.step('{}: setting bond mode {} for interface {}'.format(engine.ip, bond_mode, bond_name)):
        return engine.run_cmd("ip link set dev {} type bond mode {}".format(bond_name, bond_mode))
