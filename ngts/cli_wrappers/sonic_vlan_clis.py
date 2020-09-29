import allure


def add_vlan(engine, vlan):
    """
    Method which adding VLAN to SONiC dut
    :param engine: ssh engine object
    :param vlan: vlan ID
    :return: command output
    """
    with allure.step('{}: adding VLAN {}'.format(engine.ip, vlan)):
        return engine.run_cmd("sudo config vlan add {}".format(vlan))


def del_vlan(engine, vlan):
    """
    Method which removing VLAN to SONiC dut
    :param engine: ssh engine object
    :param vlan: vlan ID
    :return: command output
    """
    with allure.step('{}: deleting VLAN {}'.format(engine.ip, vlan)):
        return engine.run_cmd("sudo config vlan del {}".format(vlan))


def add_port_to_vlan(engine, port, vlan):
    """
    Method which adding physical port to VLAN on SONiC dut
    :param engine: ssh engine object
    :param port: network port which should be VLAN member
    :param vlan: vlan ID
    :return: command output
    """
    with allure.step('{}: adding port {} to be member of VLAN: {}'.format(engine.ip, port, vlan)):
        return engine.run_cmd("sudo config vlan member add {} {}".format(vlan, port))


def del_port_from_vlan(engine, port, vlan):
    """
    Method which deleting physical port from VLAN on SONiC dut
    :param engine: ssh engine object
    :param port: network port which should be deleted from VLAN members
    :param vlan: vlan ID
    :return: command output
    """
    with allure.step('{}: deleting port {} from VLAN: {}'.format(engine.ip, port, vlan)):
        return engine.run_cmd("sudo config vlan member del {} {}".format(vlan, port))
