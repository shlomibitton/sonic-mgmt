from ngts.cli_wrappers.interfaces.interface_ifconfig_clis import IfconfigCliInterface
from ifconfigparser import IfconfigParser


class IfconfigCliCommon(IfconfigCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    @staticmethod
    def get_ifconfig(engine, options):
        """
        Get ifconfig output
        :param engine: ssh engine object
        :param options: additional options of ifconfig command
        :return: ifconfig output
        """
        return engine.run_cmd('sudo ifconfig {}'.format(options))

    @staticmethod
    def get_interface_ifconfig_details(engine, iface):
        """
        Parse and show interface ifconfig details
        :param engine: ssh engine object
        :param iface: Interface name (Example: 'Ethernet120')
        :return: interface object with all parameters
            Interface(name='Ethernet120',
                      flags='4163',
                      state='UP,BROADCAST,RUNNING,MULTICAST',
                      mtu='9100',
                      ipv4_addr='192.168.1.1',
                      ipv4_mask='255.255.255.0',
                      ipv4_bcast='192.168.1.255',
                      ipv6_addr='fe80::1e34:daff:fe19:a400',
                      ipv6_mask='64',
                      ipv6_scope='0x20',
                      mac_addr='1c:34:da:19:a4:00',
                      type='Ethernet',
                      rx_packets='40138',
                      rx_bytes='1898202',
                      rx_errors='0',
                      rx_dropped='0',
                      rx_overruns='0',
                      rx_frame='0',
                      tx_packets='451',
                      tx_bytes='102257',
                      tx_errors='0',
                      tx_dropped='0',
                      tx_overruns='0',
                      tx_carrier='0',
                      tx_collisions='0',
                      metric=None)
            Usage example:
                interface.rx_packets
        """
        ifdata_obj = IfconfigParser(console_output=IfconfigCliCommon.get_ifconfig(engine, iface))
        return ifdata_obj.get_interface(iface)
