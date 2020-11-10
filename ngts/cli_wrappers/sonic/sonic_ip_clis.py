from ngts.cli_wrappers.common.ip_clis_common import IpCliCommon


class SonicIpCli(IpCliCommon):

    @staticmethod
    def add_del_ip_from_interface(engine, action, interface, ip, mask):
        """
        This method adds/remove ip address to/from network interface
        :param engine: ssh engine object
        :param action: action which should be executed: add or remove
        :param interface: interface name to which IP should be assigned/removed
        :param ip: ip address which should be assigned/removed
        :param mask: mask which should be assigned/remove to/from IP
        :return: method which do required action
        """
        if action not in ['add', 'remove']:
            raise NotImplementedError('Incorrect action {} provided, supported only add/del'.format(action))

        engine.run_cmd('sudo config interface ip {} {} {}/{}'.format(action, interface, ip, mask))

    @staticmethod
    def add_ip_to_interface(engine, interface, ip, mask=24):
        """
        This method adds IP to SONiC interface
        :param engine: ssh engine object
        :param interface: interface name to which IP should be assigned
        :param ip: ip address which should be assigned
        :param mask: mask which should be assigned to IP
        :return: command output
        """
        SonicIpCli.add_del_ip_from_interface(engine, 'add', interface, ip, mask)

    @staticmethod
    def del_ip_from_interface(engine, interface, ip, mask=24):
        """
        This method removes IP from SONiC interface
        :param engine: ssh engine object
        :param interface: interface name from which IP should be removed
        :param ip: ip address which should be removed
        :param mask: network mask
        :return: command output
        """
        SonicIpCli.add_del_ip_from_interface(engine, 'remove', interface, ip, mask)
