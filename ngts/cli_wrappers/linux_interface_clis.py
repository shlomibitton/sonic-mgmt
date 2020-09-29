import allure


def del_interface(engine, interface):
    """
    Method which remove linux interface
    :param engine: ssh engine object
    :param interface: interface name which should be removed, example: bond0.5
    :return: command output
    """
    with allure.step('{}: deleting interface {}'.format(engine.ip, interface)):
        return engine.run_cmd("ip link del {}".format(interface))


def enable_interface(engine, interface):
    """
    Method which enable linux interface
    :param engine: ssh engine object
    :param interface: interface name which should be enabled, example: bond0.5
    :return: command output
    """
    with allure.step('{}: setting interface {} to be in UP state'.format(engine.ip, interface)):
        return engine.run_cmd("ip link set {} up".format(interface))


def disable_interface(engine, interface):
    """
    Method which disable linux interface
    :param engine: ssh engine object
    :param interface: interface name which should be disabled, example: bond0.5
    :return: command output
    """
    with allure.step('{}: setting interface {} to be in DOWN state'.format(engine.ip, interface)):
        return engine.run_cmd("ip link set {} down".format(interface))
