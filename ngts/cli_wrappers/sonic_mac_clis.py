import allure


def get_mac_address(engine, interface):
    """
    Method for get mac address for SONiC interface
    :param engine: ssh engine object
    :param interface: SONiC interface name
    :return: mac address
    """
    with allure.step('{}: getting MAC address for device {}'.format(engine.ip, interface)):
        return engine.run_cmd("cat /sys/class/net/{}/address".format(interface))


def show_mac(engine):
    """
    Method which doing command "show mac" on SONiC device
    :param engine: ssh engine object
    :return: command output
    """
    with allure.step('{}: getting output for command: show mac'.format(engine.ip)):
        return engine.run_cmd('show mac')
