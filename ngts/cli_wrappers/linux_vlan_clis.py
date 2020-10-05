import allure


def add_vlan_interface(engine, interface, vlan):
    """
    Method which adding VLAN interface to Linux host
    :param engine: ssh engine object
    :param interface: linux interface name on top of it we will create vlan interface
    :param vlan: vlan ID
    :return: command output
    """
    vlan_interface = '{}.{}'.format(interface, vlan)
    with allure.step('{}: adding VLAN interface {}'.format(engine.ip, vlan_interface)):
        return engine.run_cmd("ip link add link {} name {} type vlan id {}".format(interface, vlan_interface, vlan))
