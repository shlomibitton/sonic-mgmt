import re
import logging

from ngts.cli_wrappers.common.lldp_clis_common import LldpCliCommon

logger = logging.getLogger()


class SonicLldpCli(LldpCliCommon):

    @staticmethod
    def enable_lldp(engine):
        """
        This method enable the LLDP on the sonic switch
        :param engine: ssh enging object
        :return: command output
        """
        return engine.run_cmd('sudo config feature state lldp enabled')

    @staticmethod
    def disable_lldp(engine):
        """
        This method disables the LLDP on the sonic switch
        :param engine: ssh enging object
        :return: command output
        """
        return engine.run_cmd('sudo config feature state lldp disabled')

    @staticmethod
    def show_lldp_table(engine):
        """
        This method return output of "show lldp table" command
        :param engine: ssh enging object
        :return: command output
        """
        return engine.run_cmd('show lldp table')


    @staticmethod
    def parse_lldp_table_info(engine):
        """
        Method for get output for command "show lldp table"
        :param engine: ssh engine object
        :return: dictionary with parsed LLDP output
        for example:
        { 'Ethernet232':  ('r-tigris-06','etp58','BR,'Ethernet228'), ..
          'Ethernet252':  ('r-sonic-11-006', '0c:42:a1:46:55:8a', 'R', Interface   8 as enp5s0f0')
          }
        """
        lldp_table_output = SonicLldpCli.show_lldp_table(engine)
        regex_pattern = "(Ethernet\d+)\s*(\w*-[\w*-]*\w*\d+-*\d*)\s*([\d*\w*:]*\d*\w*)\s*(\w*)\s*(.*)"
        output_list = re.findall(regex_pattern, lldp_table_output)
        res_dict = {}
        for lldp_info_tuple in output_list:
            local_port, remote_device, remote_port_id, port_capabilities, port_descr = lldp_info_tuple
            res_dict[local_port] = (remote_device, remote_port_id, port_capabilities, port_descr)
        return res_dict

    @staticmethod
    def show_lldp_info_for_specific_interface(engine, interface_name):
        """
        This method return lldp information for a specified by the user interface
        :param engine: ssh enging object
        :param interface_name: SONiC interface name
        :return: command output
        """
        return engine.run_cmd('show lldp neighbors {}'.format(interface_name))

    @staticmethod
    def parse_lldp_info_for_specific_interface(engine, interface_name):
        """
        Method for get output for command "show lldp neighbors IFACE_NAME" in parsed format
        :param engine: ssh engine object
        :param interface_name: SONiC interface name
        :return: dictionary with parsed LLDP output
        """
        data = engine.run_cmd('show lldp neighbors {}'.format(interface_name))

        result = {'Interface': None, 'Chassis': {}, 'Port': {}, 'VLAN': None, 'Unknown TLVs': {}}

        try:
            result['Interface'] = re.search(r'Interface:\s+(Ethernet\d+|eth\d+),', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Chassis']['ChassisID'] = re.search(r'ChassisID:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Chassis']['SysName'] = re.search(r'SysName:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Chassis']['SysDescr'] = re.search(r'SysDescr:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Chassis']['MgmtIP'] = re.findall(r'MgmtIP:\s+(.*)\n', data)
        except Exception as err:
            logger.debug(err)
        try:
            result['Chassis']['Capability'] = re.findall(r'Capability:\s+(.*)\n', data)
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['PortID'] = re.search(r'PortID:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['PortDescr'] = re.search(r'PortDescr:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['TTL'] = re.search(r'TTL:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['PMD autoneg'] = re.search(r'PMD autoneg:\s+(.*)\n', data).groups()[0]  # TODO: make dict
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['Adv'] = re.findall(r'Adv:\s+(.*)\n', data)
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['MAU oper type'] = re.search(r'MAU oper type:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['MDI Power'] = re.search(r'MDI Power:\s+(.*)\n', data).groups()[0]  # TODO: make dict
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['Device type'] = re.search(r'Device type:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['Power pairs'] = re.search(r'Power pairs:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['Port']['Class'] = re.search(r'Class:\s+(.*)\n', data).groups()[0]
        except Exception as err:
            logger.debug(err)
        try:
            result['VLAN'] = re.search(r'VLAN:\s+(.*)\n', data).groups()[0]  # TODO: make dict
        except Exception as err:
            logger.debug(err)
        try:
            result['Unknown TLVs']['TLV'] = re.search(r'TLV:\s+(.*)\n', data).groups()[0]  # TODO: make dict
        except Exception as err:
            logger.debug(err)

        return result
