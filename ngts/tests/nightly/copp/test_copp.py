import allure
import logging
import pytest
import json
import time
import os
import random
import copy

from abc import abstractmethod
from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker

logger = logging.getLogger()

# config file constants
CONFIG_DB_COPP_CONFIG_NAME = 'copp_cfg.json'
UPDATED_FILE_PATH = '/tmp/' + CONFIG_DB_COPP_CONFIG_NAME
CONFIG_DB_COPP_CONFIG_REMOTE = '/etc/sonic/' + CONFIG_DB_COPP_CONFIG_NAME
COPP_TRAP = 'COPP_TRAP'
COPP_GROUP = 'COPP_GROUP'
DEFAULT_TRAP_GROUP = 'queue1_group2'
TRAP_GROUP = 'trap_group'
TRAP_IDS = 'trap_ids'

RATE_TRAFFIC_MULTIPLIER = 3
BURST_TRAFFIC_MULTIPLIER = 30
RATE_TRAFFIC_DURATION = 10
BURST_TRAFFIC_DURATION = 0.06

# list of tested protocols
PROTOCOLS_LIST = ["ARP", "IP2ME", "SNMP"]


@pytest.fixture(scope='module')
def protocol_for_reboot_flow():
    """
    Randomize protocol for reboot flow
    :param parser: pytest builtin
    :return: protocol
    """
    return random.choice(PROTOCOLS_LIST)


@allure.title('CoPP Policer test case')
@pytest.mark.parametrize("protocol", PROTOCOLS_LIST)
def test_copp_policer(topology_obj, protocol, protocol_for_reboot_flow):
    """
    Run CoPP Policer test case, which will check that the policer enforces the rate limit for protocols.
    :param topology_obj: topology object fixture
    :param protocol: tested protocol name
    :param protocol_for_reboot_flow: protocol name for reboot flow
    :return: None, raise error in case of unexpected result
    """
    try:
        # CIR (committed information rate) - bandwidth limit set by the policer
        # CBS (committed burst size) - largest burst of packets allowed by the policer
        tested_protocol_obj = eval(protocol + 'Test' + '(topology_obj)')
        tested_protocol_obj.copp_test_runner(protocol_for_reboot_flow)

    except Exception as err:
        raise AssertionError(err)

# -------------------------------------------------------------------------------


class CoppBase:
    """
    Base CoPP class
    """
    def __init__(self, topology_obj):
        self.topology = topology_obj
        self.sender = 'ha'
        self.host_iface = topology_obj.ports['ha-dut-1']
        self.dut_iface = topology_obj.ports['dut-ha-1']
        self.dut_engine = topology_obj.players['dut']['engine']
        self.host_engine = topology_obj.players['ha']['engine']
        self.dut_cli_object = topology_obj.players['dut']['cli']
        self.host_cli_object = topology_obj.players['ha']['cli']
        self.src_mac = self.host_cli_object.mac.get_mac_address_for_interface(self.host_engine,
                                                                              topology_obj.ports['ha-dut-1'])
        self.dst_mac = self.dut_cli_object.mac.get_mac_address_for_interface(self.dut_engine,
                                                                             topology_obj.ports['dut-ha-1'])
        self.validation = None
        self.pre_validation = None
        self.traffic_duration = None
        self.pre_rx_counts = self.dut_cli_object.ifconfig.get_interface_ifconfig_details(self.dut_engine,
                                                                                         self.dut_iface).rx_packets
        self.tested_protocol = self.get_tested_protocol_name()
        self.post_rx_counts = None
        self.default_cir = None
        self.default_cbs = None
        self.low_limit = 100
        self.user_limit = None
        self.trap_ids = None

    # -------------------------------------------------------------------------------

    def copp_test_runner(self, protocol_for_reboot_flow):
        """
        Test runner, defines general logic of the test case.
        Note - To validate specific traffic type, need to set low value for second traffic type in configuration file.
        :param protocol_for_reboot_flow: protocol name for reboot flow
        :return: None, raise error in case of unexpected result
        """
        # check default burst and rate value
        with allure.step('Check functionality of default burst limit'):
            self.run_validation_flow(self.default_cbs, self.low_limit, 'burst')
        with allure.step('Check functionality of default rate limit'):
            self.run_validation_flow(self.low_limit, self.default_cir)

        # check non default burst and rate limit value with reboot
        if protocol_for_reboot_flow.lower() == self.tested_protocol:
            self.run_validation_flow_with_reboot()
        else:
            logger.info('Ignore reboot validation on this protocol, '
                        'reboot validation will run on: {}'.format(protocol_for_reboot_flow))
            with allure.step('Check functionality of configured burst limit'):
                self.run_validation_flow(self.user_limit, self.low_limit, 'burst')
            with allure.step('Check functionality of configured rate limit'):
                self.run_validation_flow(self.low_limit, self.user_limit)

        # check restored default burst and rate value
        with allure.step('Check functionality of restored to default burst limit'):
            self.run_validation_flow(self.default_cbs, self.low_limit, 'burst')
        with allure.step('Check functionality of restored to default rate limit'):
            self.run_validation_flow(self.low_limit, self.default_cir)

    # -------------------------------------------------------------------------------

    def run_validation_flow_with_reboot(self):
        """
        Runs validation flow logic with reboot.
        To save time and do not reboot for each traffic type,
        will be randomized primary validation, which will be checked specific traffic type before and after reboot,
        and secondary validation,which will be checked specific traffic type only after reboot
        :return: None, raise error in case of unexpected result
        """
        traffic_type = random.choice(['rate', 'burst'])
        if traffic_type == 'rate':
            with allure.step('Check functionality of non default rate limit before reboot'):
                self.run_validation_flow(self.low_limit, self.user_limit, 'rate')
            primary_validation_flow = "self.run_validation_flow(self.low_limit, self.user_limit, 'rate', False)"
            secondary_validation_flow = "self.run_validation_flow(self.user_limit, self.low_limit, 'burst')"
        else:
            with allure.step('Check functionality of non default burst limit before reboot'):
                self.run_validation_flow(self.user_limit, self.low_limit, 'burst')
            primary_validation_flow = "self.run_validation_flow(self.user_limit, self.low_limit, 'burst', False)"
            secondary_validation_flow = "self.run_validation_flow(self.low_limit, self.user_limit, 'rate')"

        logger.info('Reboot Switch')
        self.dut_cli_object.general.save_configuration(self.dut_engine)
        self.dut_cli_object.general.reboot_flow(self.dut_engine, topology_obj=self.topology)
        self.pre_rx_counts = self.dut_cli_object.ifconfig. \
            get_interface_ifconfig_details(self.dut_engine, self.dut_iface).rx_packets

        with allure.step('Check functionality of non default {} limit value after reboot'.format(traffic_type[0])):
            eval(primary_validation_flow)
        with allure.step('Check functionality of non default {} limit value'.format(traffic_type[1])):
            eval(secondary_validation_flow)

    # -------------------------------------------------------------------------------

    def run_validation_flow(self, cbs_value, cir_value, traffic_type='rate', update_configs_request=True):
        """
        Runs validation flow logic
        :param cbs_value: burst limit value
        :param cir_value: rate limit value
        :param traffic_type: type of the traffic - rate/burst
        :param update_configs_request: the flag to update limit values in the config file
        :return: None, raise error in case of unexpected result
        """
        if update_configs_request:
            self.config_limit_value(cir_value, cbs_value)

        if traffic_type == 'rate':
            self.create_rate_validation(cir_value)
            pps = cir_value
        else:
            self.create_burst_validation(cbs_value)
            pps = cbs_value
        self.send_traffic()
        self.validate_results(pps)

    # -------------------------------------------------------------------------------

    def get_tested_protocol_name(self):
        """
        Getting the name of tested protocol, based on class name
        :return: protocol name (Example: arp or snmp etc.)
        """
        return type(self).__name__.replace('Test', '').lower()

    # -------------------------------------------------------------------------------

    def create_burst_validation(self, cbs_value):
        """
        Creating burst valudation, based on given CBS value
        :param cbs_value: CBS value
        """
        self.create_validation(pps=cbs_value*BURST_TRAFFIC_MULTIPLIER,
                               times=int(cbs_value*BURST_TRAFFIC_MULTIPLIER*BURST_TRAFFIC_DURATION))
        self.create_pre_validation()

    # -------------------------------------------------------------------------------

    def create_rate_validation(self, cir_value):
        """
        Creating rate valudation, based on given CIR value
        :param cir_value: CIR value
        """
        self.create_validation(pps=cir_value*RATE_TRAFFIC_MULTIPLIER,
                               times=cir_value*RATE_TRAFFIC_MULTIPLIER*RATE_TRAFFIC_DURATION)
        self.create_pre_validation()

    # -------------------------------------------------------------------------------

    @abstractmethod
    def create_validation(self, pps, times):
        """
        This method is abstractmethod and should be implemented in child classes
        """
        pass

    # -------------------------------------------------------------------------------

    def create_pre_validation(self):
        """
        Creating pre validation with 1 packet to send. Based on main validation
        """
        self.pre_validation = copy.deepcopy(self.validation)
        self.pre_validation['send_args']['loop'] = 1

    # -------------------------------------------------------------------------------

    def send_traffic(self):
        """
        Sending Scapy traffic.
        Pre validation - to be sure main all validation will be received
        Validation - main traffic sends
        """
        logger.info('validation: {}'.format(str(self.validation)))
        with allure.step('Send pre traffic of 1 packet'):
            ScapyChecker(self.topology.players, self.pre_validation).run_validation()
            time.sleep(1)
        with allure.step('Send traffic'):
            start_time = time.time()
            ScapyChecker(self.topology.players, self.validation).run_validation()
            self.traffic_duration = time.time() - start_time
            time.sleep(1)

    # -------------------------------------------------------------------------------

    def validate_results(self, expected_pps):
        """
        Verifying the result of received traffic
        :param expected_pps: expected packet rate
        :return: None, raise error in case of unexpected result
        """
        with allure.step('Validate results'):
            self.post_rx_counts = self.dut_cli_object.ifconfig.get_interface_ifconfig_details(self.dut_engine,
                                                                                              self.dut_iface).rx_packets
            rx_count = int(self.post_rx_counts) - int(self.pre_rx_counts)
            self.pre_rx_counts = self.post_rx_counts
            logger.info('The traffic duration is {:10.4f} '.format(self.traffic_duration))
            logger.info('The delta of RX counters is {} '.format(rx_count))
            self.traffic_duration = correct_traffic_duration_for_calculations(self.traffic_duration)
            rx_pps = int(rx_count / self.traffic_duration)
            # We use +- 15% threshold due to not possible to be more precise
            logger.info("Verify that received pps({}) is in allowed rate: {} +-15%".format(rx_pps, expected_pps))
            assert int(rx_pps) > int(expected_pps) * 0.85, \
                "The received pps {} is less then 85% of expected {}".format(rx_pps, expected_pps)
            assert int(rx_pps) < int(expected_pps) * 1.15, \
                "The received pps {} is bigger then 115% of expected {}".format(rx_pps, expected_pps)

    # -------------------------------------------------------------------------------

    def config_limit_value(self, cir_value, cbs_value):
        """
        Configuration of given CIR and CBS values into the config database
        :param cir_value: value of CIR
        :param cbs_value: value of CBS
        :return:
        """
        # copy file from switch to local system ( will be copied to current location ".")
        self.copy_remote_file(CONFIG_DB_COPP_CONFIG_REMOTE, CONFIG_DB_COPP_CONFIG_NAME, '/', 'get')

        # update the json file
        update_copp_json_file(self.get_tested_protocol_name(), cir_value, cbs_value, self.trap_ids)

        # copy file back to switch
        self.copy_remote_file(CONFIG_DB_COPP_CONFIG_NAME, CONFIG_DB_COPP_CONFIG_NAME, '/tmp')

        # remove local file
        os.remove(CONFIG_DB_COPP_CONFIG_NAME)

        # apply updated config file
        self.dut_cli_object.general.load_configuration(self.dut_engine, UPDATED_FILE_PATH)

    # -------------------------------------------------------------------------------

    def copy_remote_file(self, src, dst, file_system, direction='put'):
        """
        Copying the file TO / FROM tested switch
        :param src: path to the source file
        :param dst: destination file name
        :param file_system: location of destination file
        :param direction: the direction of the copy
        :return: None, raise error in case of unexpected result
        """
        self.dut_engine.copy_file(source_file=src,
                                  dest_file=dst,
                                  file_system=file_system,
                                  direction=direction,
                                  overwrite_file=True,
                                  verify_file=False)

# -------------------------------------------------------------------------------


class ARPTest(CoppBase):
    """
    ARP class/test extends the basic CoPP class with with specific validation for ARP protocol
    """
    def __init__(self, topology_obj):
        CoppBase.__init__(self, topology_obj)
        self.default_cir = 600
        self.default_cbs = 600
        self.user_limit = 500
        self.dst_mac = 'ff:ff:ff:ff:ff:ff'

    # -------------------------------------------------------------------------------

    def create_validation(self, pps, times):
        """
        Creating Scapy validation for ARP protocol. One legal packet from list.
        :param pps: packets rate value
        :param times: packets number
        """
        arp_dict = {'ARP Request':            'ARP(op=1, psrc="192.168.1.1", pdst="192.168.2.2")',
                    'ARP Reply':              'ARP(op=2, psrc="192.168.1.1", pdst="192.168.2.2")',
                    'Neighbor Solicitation':  'IPv6(src="2001:db8:5::5",dst="ff02::1")/ICMPv6ND_NS()',
                    'Neighbor Advertisement': 'IPv6(src="2001:db8:5::5",dst="ff02::1")/ICMPv6ND_NA()'}
        chosen_packet = random.choice(list(arp_dict.keys()))

        with allure.step('ARP - Create "{}" validation'.format(chosen_packet)):
            arp_pkt = 'Ether(src="{}", dst="{}")/' + arp_dict[chosen_packet]
            self.validation = {'sender': self.sender,
                               'send_args': {'interface': self.host_iface,
                                             'send_method': 'sendpfast',
                                             'packets': arp_pkt.format(self.src_mac, self.dst_mac),
                                             'pps': pps,
                                             'loop': times,
                                             'timeout': 20}
                               }

# -------------------------------------------------------------------------------


class SNMPTest(CoppBase):
    """
    SNMP class/test extends the basic CoPP class with with specific validation for SNMP protocol
    """
    def __init__(self, topology_obj):
        CoppBase.__init__(self, topology_obj)
        # TODO trapped as ip2me. Mellanox should add support for SNMP trap. update values accordingly
        self.default_cir = 6000
        self.default_cbs = 1000
        self.user_limit = 600
        self.trap_ids = 'snmp'
        logger.info("The tested protocol SNMP have too big default value for burst, "
                    "can't be tested on canonical systems. "
                    "Will be tested the value {} instead"
                    .format(self.default_cbs))

    # -------------------------------------------------------------------------------

    def create_validation(self, pps, times):
        """
        Creating Scapy validation for SNMP protocol. One legal packet from list.
        :param pps: packets rate value
        :param times: packets number
        """
        snmp_dict = {'SNMP get': 'SNMP(community="public",'
                                 'PDU=SNMPget(varbindlist=[SNMPvarbind(oid=ASN1_OID("1.3.6.1.2.1.1.1.0"))]))',
                     'SNMP set': 'SNMP(community="private",'
                                 'PDU=SNMPset(varbindlist='
                                 '[SNMPvarbind(oid=ASN1_OID("1.3.6.1.4.1.9.2.1.55.192.168.2.100"),'
                                 'value="192.168.2.150.config")]))'
                     }
        chosen_packet = random.choice(list(snmp_dict.keys()))

        with allure.step('SNMP - Create "{}" validation'.format(chosen_packet)):
            snmp_pkt = 'Ether(src="{}", dst="{}")/IP(dst="192.168.1.1")/UDP(sport=161)/' + snmp_dict[chosen_packet]
            self.validation = {'sender': self.sender,
                               'send_args': {'interface': self.host_iface,
                                             'send_method': 'sendpfast',
                                             'packets': snmp_pkt.format(self.src_mac, self.dst_mac),
                                             'pps': pps,
                                             'loop': times,
                                             'timeout': 20}
                               }

# -------------------------------------------------------------------------------


class IP2METest(CoppBase):
    """
    IP2ME class/test extends the basic CoPP class with with specific validation for IP2ME packets type
    """
    def __init__(self, topology_obj):
        CoppBase.__init__(self, topology_obj)
        self.default_cir = 6000
        self.default_cbs = 1000
        self.user_limit = 600
        logger.info("The tested protocol IP2ME have too big default value for burst, "
                    "can't be tested on canonical systems. "
                    "Will be tested the value {} instead"
                    .format(self.default_cbs))

    # -------------------------------------------------------------------------------

    def create_validation(self, pps, times):
        """
        Creating Scapy validation for IP2ME packets. Simple IP packet.
        :param pps: packets rate value
        :param times: packets number
        """
        with allure.step('IP2ME - Create validation (with simple IP packet and right destination ip)'):
            ip2me_pkt = 'Ether(src="{}", dst="{}")/IP(dst="192.168.1.1")'
            self.validation = {'sender': self.sender,
                               'send_args': {'interface': self.host_iface,
                                             'send_method': 'sendpfast',
                                             'packets': ip2me_pkt.format(self.src_mac, self.dst_mac),
                                             'pps': pps,
                                             'loop': times,
                                             'timeout': 20}
                               }

# -------------------------------------------------------------------------------


class SSHTest(CoppBase):
    """
    SSH class/test extends the basic CoPP class with with specific validation for SSH packet type
    """
    def __init__(self, topology_obj):
        CoppBase.__init__(self, topology_obj)
        self.default_cir = 600
        self.default_cbs = 600
        self.user_limit = 400
        self.trap_ids = 'ssh'

    # -------------------------------------------------------------------------------

    def create_validation(self, pps, times):
        """
        Creating Scapy validation for SSH packets. Simple TCP packet with specific destination port.
        :param pps: packets rate value
        :param times: packets number
        """
        with allure.step('SSH - Create validation (with simple TCP packed and destination port 22)'):
            ssh_pkt = 'Ether(dst="{}")/IP(dst="192.168.1.100")/TCP(dport=22)'
            self.validation = {'sender': self.sender,
                               'send_args': {'interface': self.host_iface,
                                             'send_method': 'sendpfast',
                                             'packets': ssh_pkt.format(self.dst_mac),
                                             'pps': pps,
                                             'loop': times,
                                             'timeout': 20}
                               }

# -------------------------------------------------------------------------------


def update_copp_json_file(protocol, cir_value, cbs_value, trap_ids):
    """
    This function updates the local copp.json configuration file with given CIR and CBS value for given protocol
    :param protocol: protocol name
    :param cir_value: value of CIR
    :param cbs_value: value of CBS
    :param trap_ids: traps_ids value of the protocol.
                    Used if  the protocol doesn't exist in default copp_cfg.json file.
    :return:
    """
    with open(CONFIG_DB_COPP_CONFIG_NAME) as copp_json_file:
        copp_json_file_dic = json.load(copp_json_file)
    trap_group = get_trap_group(protocol, copp_json_file_dic, trap_ids)
    update_limit_values(copp_json_file_dic, trap_group, cir_value, cbs_value)
    os.remove(CONFIG_DB_COPP_CONFIG_NAME)
    with open(CONFIG_DB_COPP_CONFIG_NAME, 'w') as copp_json_file:
        json.dump(copp_json_file_dic, copp_json_file, indent=4)

# -------------------------------------------------------------------------------


def get_trap_group(protocol, copp_dict, trap_ids=''):
    """
    Getting the trap group by give protocol name.
    If this protocol not into the config dictionary(copp_cfg.json) file,
        add new key-value tuple and the trap_group will be default.
    :param protocol: protocol name
    :param copp_dict: config dictionary
    :param trap_ids: trap_ids of the protocol
    :return: trap_group
    For example the part of config dictionary:
        "COPP_TRAP": {
            "bgp": {
                "trap_ids": "bgp,bgpv6",
                "trap_group": "queue4_group1"
            },
            "arp": {
                "trap_ids": "arp_req,arp_resp,neigh_discovery",
                "trap_group": "queue4_group2"
            }
        }
    """
    # TODO SNMP trapped as ip2me. Mellanox should add support for SNMP trap
    if protocol == 'snmp':
        protocol = 'ip2me'
    if protocol in copp_dict[COPP_TRAP]:
        logger.info('protocon in a dict')
        return copp_dict[COPP_TRAP][protocol][TRAP_GROUP]
    else:
        add_new_protocol_to_config(protocol, copp_dict, trap_ids)
    return DEFAULT_TRAP_GROUP

# -------------------------------------------------------------------------------


def add_new_protocol_to_config(protocol, copp_dict, trap_ids):
    """
    Add new protocon to config dictionary
    :param protocol: protocol name
    :param copp_dict: config dictionary
    :param trap_ids: traps ids
    """
    copp_dict[COPP_TRAP].update({protocol: {TRAP_IDS: trap_ids, TRAP_GROUP: DEFAULT_TRAP_GROUP}})

# -------------------------------------------------------------------------------


def update_limit_values(copp_dict, trap_group, cir_value, cbs_value):
    """
    Update the CIR and CBS values for given trap group.
    :param copp_dict: config dictionary
    :param trap_group: trap group
    :param cir_value: value of CIR
    :param cbs_value: value of CBS
    :return:
    """
    if 'cir'in copp_dict[COPP_GROUP][trap_group]:
        copp_dict[COPP_GROUP][trap_group]['cir'] = cir_value
    else:
        copp_dict[COPP_GROUP][trap_group].update({'cir': cir_value})

    if 'cbs'in copp_dict[COPP_GROUP][trap_group]:
        copp_dict[COPP_GROUP][trap_group]['cbs'] = cbs_value
    else:
        copp_dict[COPP_GROUP][trap_group].update({'cbs': cbs_value})

# -------------------------------------------------------------------------------


def correct_traffic_duration_for_calculations(current_traffic_duration):
    """
    This function correct the traffic duration time from some network/scapy delays.
    :param current_traffic_duration: current traffic duration time
    :return: traffic duration time after correction
    """
    if current_traffic_duration >= 10:
        return rate_traffic_duration_time_correction(current_traffic_duration)
    else:
        return burst_traffic_duration_time_correction()

# -------------------------------------------------------------------------------


def rate_traffic_duration_time_correction(current_traffic_duration):
    """
    The rate traffic time is 10 seconds. So the traffic duration time can't be bigger then 11 seconds
    :param current_traffic_duration: current traffic duration time
    :return: traffic duration time after correction
    """
    max_rate_traffic_duration = 11
    return min(current_traffic_duration, max_rate_traffic_duration)

# -------------------------------------------------------------------------------


def burst_traffic_duration_time_correction():
    """
    The burst traffic time is <0.1 second. So for calculation burst traffic will be returned value 1
    :return: traffic duration time after correction
    """
    return 1
