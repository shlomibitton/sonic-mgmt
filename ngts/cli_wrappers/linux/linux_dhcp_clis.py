class LinuxDhcpCli:

    run_dhcp_client = 'dhclient {} -v'
    run_dhcp6_client = 'dhclient -6 {} -v'
    run_dhcp_client_with_config = 'dhclient {} -cf {} -v'
    run_dhcp6_client_with_config = 'dhclient -6 {} -cf {} -v'
    stop_dhcp_client = 'dhclient {} -r'
    stop_dhcp6_client = 'dhclient -6 {} -r'
    dhcp_client_no_offers = 'No DHCPOFFERS received.'
    dhcpd_leases_path = '/var/lib/dhcp/dhcpd.leases'
    dhcp_server_start_cmd = '/etc/init.d/isc-dhcp-server start'
    dhcp_server_restart_cmd = '/etc/init.d/isc-dhcp-server restart'
    dhcp_server_stop_cmd = '/etc/init.d/isc-dhcp-server stop'
    dhcp_server_status_cmd = '/etc/init.d/isc-dhcp-server status'

    advertise_dhclient_message = 'Advertise message on {} from'
    reply_dhclient_message = 'Reply message on {} from'
    successfull_dhclient_message = 'Bound to lease'

    dhcpv6_reserved_dst_mac = "33:33:00:01:00:02"
    dhcpv6_reserved_dst_ip = "ff02::1:2"
    ipv6_src_port = 546
    ipv6_server_src_port = 547
    ipv6_dst_port = 547

    ipv6_base_pkt = 'Ether(dst="{dst_mac}")/IPv6(src="{src_ip}", dst="{dst_ip}")/UDP(sport={s_port}, dport={d_port})/'


    @staticmethod
    def kill_all_dhcp_clients(engine):
        return engine.run_cmd('killall dhclient')
