import allure

from ngts.cli_wrappers.common.ip_clis_common import IpCliCommon


class SonicIpCli(IpCliCommon):

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
        with allure.step('{}: adding IP address {}/{} to interface {}'.format(engine.ip, ip, mask, interface)):
            return engine.run_cmd("sudo config interface ip add {} {}/{}".format(interface, ip, mask))

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
        with allure.step('{}: deleting IP address {}/{} from interface {}'.format(engine.ip, ip, mask, interface)):
            return engine.run_cmd("sudo config interface ip remove {} {}/{}".format(interface, ip, mask))


