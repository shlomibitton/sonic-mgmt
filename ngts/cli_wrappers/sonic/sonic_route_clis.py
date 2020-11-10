from ngts.cli_wrappers.common.route_clis_common import RouteCliCommon


class SonicRouteCli(RouteCliCommon):

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
        if action not in ['add', 'del']:
            raise NotImplementedError('Incorrect action {} provided, supported only add/del'.format(action))

        cmd = 'sudo config route {} prefix '.format(action)
        if vrf:
            cmd += 'vrf {} '.format(vrf)
        cmd += '{}/{} nexthop {}'.format(dst, dst_mask, via)

        return engine.run_cmd(cmd)

    @staticmethod
    def add_route(engine, dst, via, dst_mask, vrf=None):
        """
        This method create static IP route
        :param engine: ssh engine object
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to add route in custom vrf
        :return: add_del_route method
        """
        SonicRouteCli.add_del_route(engine, 'add', dst, via, dst_mask, vrf)

    @staticmethod
    def del_route(engine, dst, via, dst_mask, vrf=None):
        """
        This method deletes static IP route
        :param engine: ssh engine object
        :param dst: IP address for host or subnet
        :param via: Gateway IP address or interface name
        :param dst_mask: mask for dst IP
        :param vrf: vrf name - in case when need to del route in custom vrf
        :return: add_del_route method
        """
        SonicRouteCli.add_del_route(engine, 'del', dst, via, dst_mask, vrf)

    @staticmethod
    def show_ip_route(engine, route_type=None, ipv6=False, route=None, vrf=None):
        """
        This method gets IP routes from device
        :param engine: ssh engine object
        :param route_type: route type(example: static, bgp)
        :param ipv6: True if need to get IPv6 routes
        :param route: IP address - for which we need to find route(example: 1.1.1.1 or 1.1.1.0/24)
        :param vrf: vrf name for which we need to see routes(example: all)
        :return: command output
        """
        if route_type and route:
            raise Exception('It is not allowed to use together route_type and route arguments')

        cmd = 'show {} route '.format('ipv6' if ipv6 else 'ip')
        if vrf:
            cmd += 'vrf {} '.format(vrf)
        if route_type:
            cmd += route_type
        if route:
            cmd += route

        return engine.run_cmd(cmd)
