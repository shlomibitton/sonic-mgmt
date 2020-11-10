from ngts.cli_wrappers.common.route_clis_common import RouteCliCommon


class LinuxRouteCli(RouteCliCommon):

    @staticmethod
    def add_del_route(engine, action, dst, via, dst_mask, vrf):
        """
        This method create/remove static IP route
        :param engine: ssh engine object
        :param action: action which should be executed - add or del
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to add/remove route in custom vrf
        :return: command output
        """
        if vrf:
            raise NotImplementedError('VRF not supported for Linux host')
        if action not in ['add', 'del']:
            raise NotImplementedError('Incorrect action {} provided, supported only add/del'.format(action))

        return engine.run_cmd("sudo ip route {} {}/{} via {}".format(action, dst, dst_mask, via))

    @staticmethod
    def add_route(engine, dst, via, dst_mask, vrf=None):
        """
        This method create static IP route
        :param engine: ssh engine object
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to add route in custom vrf
        :return: command output
        """
        LinuxRouteCli.add_del_route(engine, 'add', dst, via, dst_mask, vrf)

    @staticmethod
    def del_route(engine, dst, via, dst_mask, vrf=None):
        """
        This method deletes static IP route
        :param engine: ssh engine object
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to del route in custom vrf
        :return: command output
        """
        LinuxRouteCli.add_del_route(engine, 'del', dst, via, dst_mask, vrf)
