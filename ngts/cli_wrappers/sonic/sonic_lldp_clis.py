import re
import logging
import allure
from ngts.cli_wrappers.common.lldp_clis_common import LldpCliCommon
from ngts.cli_util.cli_constants import SonicDockersConstant

logger = logging.getLogger()


class SonicLldpCli(LldpCliCommon):

    @staticmethod
    def enable_lldp(engine):
        """
        This method enable the LLDP on the sonic switch
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo config feature state lldp enabled')

    @staticmethod
    def disable_lldp(engine):
        """
        This method disables the LLDP on the sonic switch
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('sudo config feature state lldp disabled')

    @staticmethod
    def show_lldp_table(engine):
        """
        This method return output of "show lldp table" command
        :param engine: ssh engine object
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
        :param engine: ssh engine object
        :param interface_name: SONiC interface name
        :return: command output
        """
        return engine.run_cmd('show lldp neighbors {}'.format(interface_name))

    @staticmethod
    def change_lldp_tx_interval(engine, interval=30):
        """
        This method change transmit delay to the specified value in seconds. The transmit delay is the
        delay between two transmissions of LLDP PDU. The default value is 30 seconds.
        :param engine: ssh engine object
        :param interval: value of interval in seconds
        :return: command output
        """
        configure_lldp_interval_cmd = 'docker exec {}  /bin/bash -c \"lldpcli configure lldp tx-interval {}\"'.format(SonicDockersConstant.LLDP, interval)
        with allure.step("change lldp transmit delay to {} seconds on player {}".format(interval, engine.ip)):
            engine.run_cmd(configure_lldp_interval_cmd)

    @staticmethod
    def verify_lldp_tx_interval(engine, expected_transmit_interval=30):
        """
        This method verify the transmit delay is the specified interval value in seconds.
        :param engine: ssh engine object
        :param expected_transmit_interval: value of the expected interval in seconds
        :return: command output
        """
        show_lldp_interval_cmd = "docker exec {}  /bin/bash -c \"lldpcli show running-configuration\""\
            .format(SonicDockersConstant.LLDP)
        with allure.step('Check lldp transmit delay is {} seconds on player {}'
                                 .format(expected_transmit_interval, engine.ip)):
            output = engine.run_cmd(show_lldp_interval_cmd)
            actual_transmit_delay = re.search("Transmit delay: (\d+)", output, re.IGNORECASE).group(1)
            assert int(actual_transmit_delay) == int(expected_transmit_interval), \
                "The expected transmit delay for lldp is {}, the actual transmit is {}."\
                    .format(expected_transmit_interval, actual_transmit_delay)

    @staticmethod
    def pause_lldp(engine):
        """
        pause lldp demon.
        :param engine: ssh engine object
        :return: command output
        """
        pause_lldp_demon = "docker exec {}  /bin/bash -c \"lldpcli pause\""\
            .format(SonicDockersConstant.LLDP)
        with allure.step('Pause lldp demon on {}'.format(engine.ip)):
            engine.run_cmd(pause_lldp_demon)

    @staticmethod
    def resume_lldp(engine):
        """
        resume lldp demon.
        :param engine: ssh engine object
        :return: command output
        """
        resume_lldp_demon = "docker exec {}  /bin/bash -c \"lldpcli resume\"".format(SonicDockersConstant.LLDP)
        with allure.step('Resume lldp demon on player {}'.format(engine.ip)):
            engine.run_cmd(resume_lldp_demon)

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
