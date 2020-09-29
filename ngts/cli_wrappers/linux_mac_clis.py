import allure


def get_mac_address(engine, interface):
    """
    Method for get mac address for Linux interface
    :param engine: ssh engine object
    :param interface: Linux interface name
    :return: mac address
    """
    with allure.step('{}: getting MAC address for device {}'.format(engine.ip, interface)):
        return engine.run_cmd("cat /sys/class/net/{}/address".format(interface))
