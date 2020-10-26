import allure

from ngts.cli_wrappers.common.static_route_clis_common import StaticRouteCliCommon


class LinuxStaticRouteCli(StaticRouteCliCommon):
    @staticmethod
    def add_route(engine, dst, via, dst_mask='32', vrf=None):
        """
        This method create static IP route
        :param engine: ssh engine object
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to add route in custom vrf
        :return: command output
        """
        with allure.step('{}: creating a static IP route to {}/{} via {}'.format(engine.ip, dst, dst_mask, via)):
            if vrf:
                raise NotImplementedError
            else:
                return engine.run_cmd("sudo ip route add {}/{} via {}".format(dst, dst_mask, via))

    @staticmethod
    def del_route(engine, dst, via, dst_mask='32', vrf=None):
        """
        This method deletes static IP route
        :param engine: ssh engine object
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to del route in custom vrf
        :return: command output
        """
        with allure.step('{}: deleting a static IP route to {}/{} via {}'.format(engine.ip, dst, dst_mask, via)):
            if vrf:
                raise NotImplementedError
            else:
                return engine.run_cmd("sudo ip route del {}/{} via {}".format(dst, dst_mask, via))
