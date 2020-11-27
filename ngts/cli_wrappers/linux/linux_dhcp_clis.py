import re


class LinuxDhcpCli:

    run_dhcp_client = 'dhclient {} -v'
    run_dhcp_client_with_config = 'dhclient {} -cf {} -v'
    stop_dhcp_client = 'dhclient {} -r'
    dhcp_client_no_offers = 'No DHCPOFFERS received.'
    dhcpd_leases_path = '/var/lib/dhcp/dhcpd.leases'
    dhcp_server_start_cmd = '/etc/init.d/isc-dhcp-server start'
    dhcp_server_restart_cmd = '/etc/init.d/isc-dhcp-server restart'
    dhcp_server_stop_cmd = '/etc/init.d/isc-dhcp-server stop'
    dhcp_server_status_cmd = '/etc/init.d/isc-dhcp-server status'

    @staticmethod
    def kill_all_dhcp_clients(engine):
        return engine.run_cmd('killall dhclient')
