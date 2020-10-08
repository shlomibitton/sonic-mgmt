import allure


def add_lacp_interface(engine, lacp_interface_name):
    """
    Method which adding LACP interface in SONiC
    :param engine: ssh engine object
    :param lacp_interface_name: LACP interface name which should be added
    :return: command output
    """
    with allure.step('{}: adding LACP interface: {}'.format(engine.ip, lacp_interface_name)):
        return engine.run_cmd("sudo config portchannel add {}".format(lacp_interface_name))


def del_lacp_interface(engine, lacp_interface_name):
    """
    Method which deleting LACP interface in SONiC
    :param engine: ssh engine object
    :param lacp_interface_name: LACP interface name which should be deleted
    :return: command output
    """
    with allure.step('{}: deleting LACP interface: {}'.format(engine.ip, lacp_interface_name)):
        return engine.run_cmd("sudo config portchannel del {}".format(lacp_interface_name))


def add_port_to_lacp(engine, interface, lacp_interface_name):
    """
    Method which adding interface to LACP interface in SONiC
    :param engine: ssh engine object
    :param interface: interface name which should be added to LACP
    :param lacp_interface_name: LACP interface name to which we will add interface
    :return: command output
    """
    with allure.step('{}: adding port {} to LACP interface: {}'.format(engine.ip, interface, lacp_interface_name)):
        return engine.run_cmd("sudo config portchannel member add {} {}".format(lacp_interface_name, interface))


def del_port_from_lacp(engine, interface, lacp_interface_name):
    """
    Method which deleting interface from LACP interface in SONiC
    :param engine: ssh engine object
    :param interface: interface name which should be deleted from LACP
    :param lacp_interface_name: LACP interface name from which we will remove interface
    :return: command output
    """
    with allure.step('{}: deleting port {} from LACP interface: {}'.format(engine.ip, interface, lacp_interface_name)):
        return engine.run_cmd("sudo config portchannel member del {} {}".format(lacp_interface_name, interface))
