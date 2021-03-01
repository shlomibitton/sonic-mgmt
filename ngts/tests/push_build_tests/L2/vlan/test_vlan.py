import allure
import logging
import pytest

from infra.tools.validations.traffic_validations.scapy.scapy_runner import ScapyChecker
from ngts.cli_util.verify_cli_show_cmd import verify_show_cmd
from ngts.cli_wrappers.sonic.sonic_vlan_clis import SonicVlanCli


"""

 Vlan Test Cases

 Documentation: https://wikinox.mellanox.com/display/SW/SONiC+NGTS+VLAN+Documentation

"""

logger = logging.getLogger()


class TestVLAN:

    @pytest.fixture(autouse=True)
    def setup(self, topology_obj, ha_dut_1_mac, ha_dut_2_mac, hb_dut_1_mac, hb_dut_2_mac):
        self.topology_obj = topology_obj
        self.dut_engine = topology_obj.players['dut']['engine']
        self.cli_object = self.topology_obj.players['dut']['cli']

        self.dut_hb_1 = topology_obj.ports['dut-hb-1']
        self.dut_ha_2 = topology_obj.ports['dut-ha-2']
        self.hb_dut_1 = topology_obj.ports['hb-dut-1']
        self.ha_dut_2 = topology_obj.ports['ha-dut-2']

        self.ha_dut_1_mac = ha_dut_1_mac
        self.ha_dut_2_mac = ha_dut_2_mac
        self.hb_dut_1_mac = hb_dut_1_mac
        self.hb_dut_2_mac = hb_dut_2_mac

        self.vlan_30 = 30
        self.vlan_800 = 800
        self.vlan_4094 = 4094
        self.vlan_4095 = 4095
        self.po_iface = 'PortChannel0001'

        self.show_vlan_config_pattern = r"Vlan{vid}\s+{vid}\s+{member}\s+{mode}"

    @staticmethod
    def get_test_basic_packet(dst_mac, vlan=None):
        pkt = 'Ether(dst="{}")/'.format(dst_mac)
        if vlan:
            pkt += 'Dot1Q(vlan={})/'.format(vlan)
        pkt += 'IP(src="1.2.3.4", dst="5.6.7.8")/UDP(sport=68, dport=67)/Raw()'
        return pkt

    @staticmethod
    def get_tcpdump_filter(vlan=None):
        pkt_filter = 'src 1.2.3.4 and dst 5.6.7.8'
        if vlan:
            pkt_filter = 'vlan {} and '.format(vlan) + pkt_filter
        return pkt_filter

    @pytest.mark.build
    @pytest.mark.push_gate
    @allure.title('Test VLAN access mode')
    def test_vlan_access_mode(self):
        """
        This test will check vlan access mode.
        :return: raise assertion error if expected output is not matched
        """
        logger.info("Vlan access mode: verify PortChannel0001 in mode access")
        vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
        vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.po_iface,
                                                                    mode='untagged'), True),
                              (self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.dut_hb_1,
                                                                    mode='tagged'), True)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan access mode: verify untagged traffic can reach from '
                         'bond0 to {} with VLAN tag {})'.format(self.hb_dut_1, self.vlan_30)):
            validation = {'sender': 'ha', 'send_args': {'interface': 'bond0',
                                                        'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                      'filter': self.get_test_basic_packet(self.vlan_30),
                                                                      'count': 3}}
                              ]
                          }
            logger.info('Sending 3 untagged packets from bond0 to {} VLAN {}'.format(self.hb_dut_1, self.vlan_30))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

        with allure.step('Vlan access mode: verify tagged traffic with the same VLAN as port access configured - pass'):
            validation = {'sender': 'ha', 'send_args': {'interface': 'bond0',
                                                        'packets': self.get_test_basic_packet(self.hb_dut_1_mac,
                                                                                              self.vlan_30),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                      'filter': self.get_tcpdump_filter(self.vlan_30),
                                                                      'count': 3}}
                              ]
                          }
            logger.info('Sending 3 tagged packets from bond0 with VLAN tag {} to {} VLAN {}'.format(self.vlan_30,
                                                                                                    self.hb_dut_1,
                                                                                                    self.vlan_30))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

        with allure.step('Vlan access mode: verify tagged traffic with wlan != to access vlan - is dropped'):
            validation = {'sender': 'ha', 'send_args': {'interface': 'bond0',
                                                        'packets': self.get_test_basic_packet(self.hb_dut_1_mac,
                                                                                              self.vlan_800),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                      'filter': self.get_tcpdump_filter(),  # for check on all ifaces
                                                                      'count': 0}}
                              ]
                          }
            logger.info('Sending 3 tagged packets from bond0 with VLAN tag {} to {} VLAN {}'.format(self.vlan_800,
                                                                                                    self.hb_dut_1,
                                                                                                    self.vlan_800))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

    @pytest.mark.build
    @pytest.mark.push_gate
    @allure.title('Test VLAN trunk mode')
    def test_vlan_trunk_mode(self):
        """
        This test will check vlan trunk mode.
        :return: raise assertion error if expected output is not matched
        """
        logger.info("Vlan trunk mode: verify {} and {} are in trunk mode".format(self.dut_hb_1, self.dut_ha_2))
        vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
        vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.dut_ha_2,
                                                                    mode='tagged'), True),
                              (self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.dut_hb_1,
                                                                    mode='tagged'), True),
                              (self.show_vlan_config_pattern.format(vid=self.vlan_800, member=self.dut_hb_1,
                                                                    mode='tagged'), True)]
        verify_show_cmd(vlan_info, vlan_expected_info)

        with allure.step('Vlan trunk mode: verify tagged traffic with VLAN {} can reach from '
                         '{} to {} with VLAN {}'.format(self.vlan_30, self.hb_dut_1, self.ha_dut_2, self.vlan_30)):
            validation = {'sender': 'hb', 'send_args': {'interface': self.hb_dut_1,
                                                        'packets': self.get_test_basic_packet(self.ha_dut_2_mac,
                                                                                              self.vlan_30),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'ha', 'receive_args': {'interface': self.ha_dut_2,
                                                                      'filter': self.get_tcpdump_filter(self.vlan_30),
                                                                      'count': 3}}
                              ]
                          }
            logger.info('Sending 3 tagged packets in VLAN {} from {} to {} VLAN {}'.format(self.vlan_30, self.hb_dut_1,
                                                                                           self.ha_dut_2, self.vlan_30))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

        with allure.step('Vlan trunk mode: verify tagged traffic with VLAN {} can reach from '
                         '{} to bond0 on HA without VLAN tag'.format(self.vlan_30, self.hb_dut_1)):

            validation = {'sender': 'hb', 'send_args': {'interface': self.hb_dut_1,
                                                        'packets': self.get_test_basic_packet(self.ha_dut_1_mac,
                                                                                              self.vlan_30),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'ha', 'receive_args': {'interface': 'bond0',
                                                                      'filter': self.get_tcpdump_filter(),
                                                                      'count': 3}}
                              ]
                          }
            logger.info('Sending 3 tagged packets with VLAN {} from {} to bond0 on HA'.format(self.vlan_30,
                                                                                              self.hb_dut_1))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

        with allure.step('Vlan trunk mode: verify tagged traffic is dropped '
                         'when vlan {} is not configured on dut-ha-2'
                         'send traffic with VAN {} from {} to {} VLAN {}'.format(self.vlan_800, self.vlan_800,
                                                                                 self.ha_dut_2, self.hb_dut_1,
                                                                                 self.vlan_800)):
            validation = {'sender': 'ha', 'send_args': {'interface': self.ha_dut_2,
                                                        'packets': self.get_test_basic_packet(self.hb_dut_1_mac,
                                                                                              self.vlan_800),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                      'filter': self.get_tcpdump_filter(),  # to check on all ifaces
                                                                      'count': 0}}
                              ]
                          }
            logger.info('Sending 3 tagged packets with VLAN {} from {} to {} VLAN {}'.format(self.vlan_800,
                                                                                             self.ha_dut_2,
                                                                                             self.hb_dut_1,
                                                                                             self.vlan_800))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

        with allure.step('Vlan trunk mode: verify untagged traffic is dropped'):
            validation = {'sender': 'hb', 'send_args': {'interface': self.hb_dut_1,
                                                        'packets': self.get_test_basic_packet(self.ha_dut_2_mac),
                                                        'count': 3},
                          'receivers':
                              [
                                  {'receiver': 'ha', 'receive_args': {'interface': self.ha_dut_2,
                                                                      'filter': self.get_tcpdump_filter(),  # to check all on ifaces
                                                                      'count': 0}}
                              ]
                          }
            logger.info('Sending 3 untagged packets from {} to {} VLAN {}'.format(self.hb_dut_1, self.ha_dut_2,
                                                                                  self.vlan_30))
            ScapyChecker(self.topology_obj.players, validation).run_validation()

    @pytest.mark.build
    @pytest.mark.push_gate
    @allure.title('Test VLAN configuration on split port')
    @pytest.mark.ngts_skip({'platform_prefix_list': ['simx']})
    def test_vlan_on_split_port(self):
        """
        configure different vlans on split port in trunk/access mode.
        check port are in up state after configuration and vlans were configured correctly
        :return: raise assertion error if expected output is not matched
        """
        split_port_1 = self.topology_obj.ports['dut-lb-splt2-p1-1']
        split_port_2 = self.topology_obj.ports['dut-lb-splt2-p2-1']
        vlan_mode_dict = {'access': 'untagged', 'trunk': 'tagged'}
        vlan_expected_info = []
        try:
            # remove iface from vlan to prevent stp
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, self.dut_hb_1, self.vlan_30)

            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, split_port_1, self.vlan_30, mode='access')
            vlan_expected_info.append((self.show_vlan_config_pattern.format(vid=self.vlan_30,
                                                                            member=split_port_1,
                                                                            mode=vlan_mode_dict['access']), True))
            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, split_port_2, self.vlan_800, mode='trunk')
            vlan_expected_info.append((self.show_vlan_config_pattern.format(vid=self.vlan_800,
                                                                            member=split_port_2,
                                                                            mode=vlan_mode_dict['trunk']), True))
            vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
            verify_show_cmd(vlan_info, vlan_expected_info)
            self.cli_object.interface.check_ports_status(self.dut_engine, [split_port_1, split_port_2],
                                                         expected_status='up')

            # functional check
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, split_port_2, self.vlan_800)
            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, split_port_2, self.vlan_800, mode='access')

            with allure.step('Vlan access mode: verify untagged traffic can reach from '
                             'bond0 to {} with VLAN tag {} via split ports)'.format(self.hb_dut_1, self.vlan_800)):
                """
                Traffic flow:
                host_a untagged >>> PortChannel0001(access vlan 30) >>>> Vlan30 >>>> split-port(access vlan 30) exit >>>
                input split-port(access vlan 800) >>> Vlan800 >>> host_b tagged with VLAN 800
                """
                validation = {'sender': 'ha', 'send_args': {'interface': 'bond0',
                                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_800),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 untagged packets from bond0 to {} VLAN {} via split ports'.format(self.hb_dut_1,
                                                                                                         self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

        except Exception as e:
            raise e

        finally:
            # cleanup
            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, self.dut_hb_1, self.vlan_30, mode='trunk')
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, split_port_1, self.vlan_30)
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, split_port_2, self.vlan_800)

    @pytest.mark.build
    @pytest.mark.push_gate
    @allure.title('Test VLAN 4094/5 configuration')
    def test_vlan_4094_5(self):
        """
        This test will check configuration of vlan 4095(which should not be configured)
        and vlan 4094 (last vlan) which should be correctly configured.
        :return: raise assertion error if expected output is not matched
        """
        try:

            logger.info("Configure Vlan {} on the dut {}".format(self.vlan_4095, self.dut_engine.ip))
            output = self.cli_object.vlan.add_vlan(self.dut_engine, self.vlan_4095)
            logger.info("Verify Configure Vlan {} on the dut {} failed".format(self.vlan_4095, self.dut_engine.ip))
            expected_err_msg = [(r"Error:\s+Invalid\s+VLAN\s+ID\s+{}\s+\(1-{}\)".format(self.vlan_4095,
                                                                                        self.vlan_4094), True)]
            verify_show_cmd(output, expected_err_msg)
            logger.info("Clean Vlan configuration from {}".format(self.dut_hb_1, self.po_iface))
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_30)
            logger.info("Configure Vlan {} on ports {}, {}".format(self.vlan_4095, self.po_iface, self.dut_hb_1))
            output = self.cli_object.vlan.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_4095, mode='access')
            logger.info("Verify Configure Vlan {} on the ports failed".format(self.vlan_4095))
            verify_show_cmd(output, expected_err_msg)
            output = self.cli_object.vlan.add_port_to_vlan(self.dut_engine, self.dut_hb_1, self.vlan_4095, mode='trunk')
            verify_show_cmd(output, expected_err_msg)

            logger.info("Verify Configuration of Vlan {} on ports po_iface, {} doesn't exist".format(self.vlan_4095,
                                                                                                     self.po_iface,
                                                                                                     self.dut_hb_1))
            vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
            vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_4095, member=self.po_iface,
                                                                        mode='untagged'), False),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_4095, member=self.dut_hb_1,
                                                                        mode='tagged'), False)]
            verify_show_cmd(vlan_info, vlan_expected_info)

            with allure.step('Vlan access mode: verify untagged traffic is dropped for vlan {} from '
                             'bond0 to {} VLAN {})'.format(self.vlan_4095, self.hb_dut_1, self.vlan_4095)):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(),
                                                                          'count': 0}}
                                  ]
                              }
                logger.info('Sending 3 untagged packets from bond0 to {} VLAN {}'.format(self.hb_dut_1, self.vlan_4095))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            logger.info("Configure Vlan {} on the dut {}".format(self.vlan_4094, self.dut_engine.ip))
            self.cli_object.vlan.add_vlan(self.dut_engine, self.vlan_4094)
            logger.info("Configure Vlan {} on ports {}, {}".format(self.vlan_4094, self.po_iface, self.dut_hb_1))
            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_4094, mode='access')
            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, self.dut_hb_1, self.vlan_4094, mode='trunk')

            logger.info("Verify Configuration of Vlan {} on ports {}, {} exist".format(self.vlan_4094, self.po_iface,
                                                                                       self.dut_hb_1))
            vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
            vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_4094, member=self.po_iface,
                                                                        mode='untagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_4094, member=self.dut_hb_1,
                                                                        mode='tagged'), True)]
            verify_show_cmd(vlan_info, vlan_expected_info)

            with allure.step('Vlan access mode: verify untagged traffic can reach from '
                             'bond0 to {} VLAN {}'.format(self.hb_dut_1, self.vlan_4094)):

                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_4094),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 untagged packets from bond0 to {} VLAN {}'.format(self.hb_dut_1, self.vlan_4094))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan access mode: verify tagged traffic with the same VLAN as port access configured - pass'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_4094),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_4094),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 to {} VLAN {}'.format(self.vlan_4094,
                                                                                               self.hb_dut_1,
                                                                                               self.vlan_4094))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan access mode: verify tagged traffic with wlan != to access vlan - is dropped'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_800),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(),  # check all ifaces
                                                                          'count': 0}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 to {} VLAN {}'.format(self.vlan_800,
                                                                                               self.hb_dut_1,
                                                                                               self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

        except Exception as e:
            raise e

        finally:
            # cleanup
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_4094)
            self.cli_object.vlan.del_port_from_vlan(self.dut_engine, self.dut_hb_1, self.vlan_4094)
            self.cli_object.vlan.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_30, mode='access')

    @pytest.mark.build
    @allure.title('BUILD VLAN test case')
    def test_vlan_access_with_trunk_mode(self):
        """
        this test verify changing port vlan mode between access and trunk does not yield unexpected protocol behaviour.
        :return: raise assertion error if expected output is not matched
        """
        try:

            logger.info("Clean port dut-ha-1 from access mode")
            SonicVlanCli.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_30)

            logger.info("Switch port dut-ha-1 vlan mode to trunk with {} and {}.".format(self.vlan_30, self.vlan_800))
            SonicVlanCli.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_30, 'trunk')
            SonicVlanCli.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_800, 'trunk')

            logger.info("Vlan trunk mode: verify ports vlan mode")
            vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
            vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.po_iface,
                                                                        mode='tagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.dut_ha_2,
                                                                        mode='tagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.dut_hb_1,
                                                                        mode='tagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_800, member=self.po_iface,
                                                                        mode='tagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_800, member=self.dut_hb_1,
                                                                        mode='tagged'), True)]
            verify_show_cmd(vlan_info, vlan_expected_info)

            with allure.step('Vlan trunk mode: verify tagged traffic with vlan {} from bond0 '
                             'can reach hb-dut-1 VLAN {}'.format(self.vlan_30, self.vlan_30)):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_30),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_30),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 to hb-dut-1 VLAN {}'.format(self.vlan_30,
                                                                                                     self.vlan_30))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan trunk mode: verify tagged traffic with vlan {} from bond0 can reach '
                             'hb-dut-1 VLAN {}'.format(self.vlan_800, self.vlan_800)):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_800),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_800),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 to hb-dut-1 VLAN {}'.format(self.vlan_800,
                                                                                                     self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan trunk mode: verify untagged traffic is dropped'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(),  # check all ifaces
                                                                          'count': 0}}
                                  ]
                              }
                logger.info('Sending 3 untagged packets from bond0 (ha-dut-1) to hb-dut-1')
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan trunk mode: verify tagged traffic is dropped '
                             'when vlan {} is not configured on dut-ha-2'
                             'bond0 VLAN {} to ha-dut-2 vlan {}'.format(self.vlan_800, self.vlan_800, self.vlan_800)):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.ha_dut_2_mac, self.vlan_800),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'ha', 'receive_args': {'interface': self.ha_dut_2,
                                                                          'filter': self.get_tcpdump_filter(),  # check all ifaces
                                                                          'count': 0}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 (ha-dut-1) to ha-dut-2 VLAN {}'.format(
                    self.vlan_800, self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            logger.info("remove port dut-ha-1 vlan trunk mode configuration.")
            SonicVlanCli.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_30)
            SonicVlanCli.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_800)

            logger.info("Switch port dut-ha-1 vlan mode to access with vlan {}.".format(self.vlan_800))
            SonicVlanCli.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_800, 'access')

            logger.info("Vlan access mode: verify dut-ha-1 ({}) in mode access with vlan {}".format(self.po_iface,
                                                                                                    self.vlan_800))
            vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
            vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_800, member=self.po_iface,
                                                                        mode='untagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_800, member=self.dut_hb_1,
                                                                        mode='tagged'), True)]
            verify_show_cmd(vlan_info, vlan_expected_info)

            with allure.step('Vlan access mode: verify untagged traffic can reach from '
                             'bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(self.vlan_800)):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_800),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 untagged packets from bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan access mode: verify tagged traffic with the same VLAN as port access configured - pass'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_800),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_800),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(
                    self.vlan_800, self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan access mode: verify tagged traffic with wlan != to access vlan - is dropped'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_30),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(),  # check on all ifaces
                                                                          'count': 0}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(
                    self.vlan_30, self.vlan_30))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            logger.info("Switch port dut-ha-1 vlan mode to access with vlan {}.".format(self.vlan_30))
            SonicVlanCli.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_800)
            SonicVlanCli.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_30, 'access')

            logger.info("Vlan access mode: verify dut-ha-1 ({}) in mode access with vlan {}".format(self.po_iface,
                                                                                                    self.vlan_30))
            vlan_info = SonicVlanCli.show_vlan_config(self.dut_engine)
            vlan_expected_info = [(self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.po_iface,
                                                                        mode='untagged'), True),
                                  (self.show_vlan_config_pattern.format(vid=self.vlan_30, member=self.dut_hb_1,
                                                                        mode='tagged'), True)]
            verify_show_cmd(vlan_info, vlan_expected_info)

            with allure.step('Vlan access mode: verify untagged traffic can reach from '
                             'bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(self.vlan_30)):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_30),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 untagged packets from bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(self.vlan_30))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan access mode: verify tagged traffic with the same VLAN as port access configured - pass'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_30),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(self.vlan_30),
                                                                          'count': 3}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(
                    self.vlan_30, self.vlan_30))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

            with allure.step('Vlan access mode: verify tagged traffic with wlan != to access vlan - is dropped'):
                validation = {'sender': 'ha',
                              'send_args': {'interface': 'bond0',
                                            'packets': self.get_test_basic_packet(self.hb_dut_1_mac, self.vlan_800),
                                            'count': 3},
                              'receivers':
                                  [
                                      {'receiver': 'hb', 'receive_args': {'interface': self.hb_dut_1,
                                                                          'filter': self.get_tcpdump_filter(),  # check on all ifaces
                                                                          'count': 0}}
                                  ]
                              }
                logger.info('Sending 3 tagged packets VLAN {} from bond0 (ha-dut-1) to hb-dut-1 VLAN {}'.format(
                    self.vlan_800, self.vlan_800))
                ScapyChecker(self.topology_obj.players, validation).run_validation()

        except Exception as e:
            raise e

        finally:
            # cleanup
            SonicVlanCli.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_30)
            # del 800 required to have correct cleanup if test failed at beginning
            SonicVlanCli.del_port_from_vlan(self.dut_engine, self.po_iface, self.vlan_800)
            SonicVlanCli.add_port_to_vlan(self.dut_engine, self.po_iface, self.vlan_30, 'access')
            logger.info("Switch bond0 ip to be access in vlan {}".format(self.vlan_30))
