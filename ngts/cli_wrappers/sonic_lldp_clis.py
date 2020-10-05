import re
import logging
import allure

logger = logging.getLogger()


def show_lldp_info_for_specific_interface(engine, interface_name):
    """
    Method for get output for command "show lldp neighbors IFACE_NAME"
    :param engine: ssh engine object
    :param interface_name: SONiC interface name
    :return: command output
    """
    with allure.step('{}" show LLDP info for interface {}'.format(engine.ip, interface_name)):
        return engine.run_cmd('show lldp neighbors {}'.format(interface_name))


def parse_lldp_info_for_specific_interface(engine, interface_name):
    """
    Method for get output for command "show lldp neighbors IFACE_NAME" in parsed format
    :param engine: ssh engine object
    :param interface_name: SONiC interface name
    :return: dictionary with parsed LLDP output
    """
    with allure.step('{}" getting LLDP info for interface {}'.format(engine.ip, interface_name)):
        data = engine.run_cmd('show lldp neighbors {}'.format(interface_name))

        result = {'Interface': None, 'Chassis': {}, 'Port': {}, 'VLAN': None, 'Unknown TLVs': {}}

        try:
            result['Interface'] = re.search(r'Interface:\s+(Ethernet\d+|eth\d+),', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Chassis']['ChassisID'] = re.search(r'ChassisID:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Chassis']['SysName'] = re.search(r'SysName:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Chassis']['SysDescr'] = re.search(r'SysDescr:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Chassis']['MgmtIP'] = re.findall(r'MgmtIP:\s+(.*)\n', data)
        except Exception as err:
            logger.warning(err)
        try:
            result['Chassis']['Capability'] = re.findall(r'Capability:\s+(.*)\n', data)
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['PortID'] = re.search(r'PortID:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['PortDescr'] = re.search(r'PortDescr:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['TTL'] = re.search(r'TTL:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['PMD autoneg'] = re.search(r'PMD autoneg:\s+(.*)\n', data).groups()[0]  # make dict
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['Adv'] = re.findall(r'Adv:\s+(.*)\n', data)
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['MAU oper type'] = re.search(r'MAU oper type:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['MDI Power'] = re.search(r'MDI Power:\s+(.*)\n', data).groups()[0]  # make dict
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['Device type'] = re.search(r'Device type:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['Power pairs'] = re.search(r'Power pairs:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['Port']['Class'] = re.search(r'Class:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.warning(err)
        try:
            result['VLAN'] = re.search(r'VLAN:\s+(.*)\n', data).groups()[0]  # make dict
        except Exception as err:
            logger.warning(err)
        try:
            result['Unknown TLVs']['TLV'] = re.search(r'TLV:\s+(.*)\n', data).groups()[0]  # make dict
        except Exception as err:
            logger.warning(err)

        return result
