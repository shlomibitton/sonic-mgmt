import logging

logger = logging.getLogger()


def generic_sonic_output_parser(output, headers_ofset=0, len_ofset=1, data_ofset_from_start=2, data_ofset_from_end=None,
                                column_ofset=2, output_key=None):
    """
    This method doing parse for command output and provide dictionary or list of dictionaries with parsed results.
    Method works only in case when cmd output has structure like below
    :param output: command output which should be parsed, example:
    Capability codes: (R) Router, (B) Bridge, (O) Other                                                 <<< This line we can skip by ofset args
    LocalPort    RemoteDevice             RemotePortID       Capability    RemotePortDescr              <<< Mandatory line
    -----------  -----------------------  -----------------  ------------  -------------------------    <<< Mandatory line
    Ethernet0    r-sonic-10-006           0c:42:a1:88:0a:1c  R             Interface   8 as enp5s0f0
    :param headers_ofset: Line number in which we have headers, in example above it is line 1(in real it is 2, but in python it is 1)
    :param len_ofset: Line number from which we can find len for all fields, in example above it is line 2
    :param data_ofset_from_start: Line number from which we will start parsing data and fill dictionary with results
    :param data_ofset_from_end: Line number till which we will do parse(parameter is optional)
    :param column_ofset: Number of spaces between columns in output(usually 2)
    :param output_key: parameter which specify which key should be used in output(from example above can be used: LocalPort,
    RemoteDevice, RemotePortID, Capability, RemotePortDescr). If NONE - than we we will return list
    :return: dictionary, example for output of "show lldp table" with args for method: headers_ofset=1,
                                                                                       len_ofset=2,
                                                                                       data_ofset_from_start=3,
                                                                                       data_ofset_from_end=-2,
                                                                                       output_key='LocalPort'
    {'Ethernet0': {'LocalPort': 'Ethernet0', 'RemoteDevice': 'r-sonic-10-006', ' RemotePortID': '0c:42:a1:88:0a:1c',
    ' Capability': 'R', 'RemotePortDescr': 'Interface   8 as enp5s0f0'}, 'Ethernet8': {'LocalPort': 'Ethernet8',
    'RemoteDevice': 'r-ocelot-02',...................}}
    Or LIST can be returned, example: [{'LocalPort': 'Ethernet0', 'RemoteDevice': 'r-sonic-10-006',
    ' RemotePortID': '0c:42:a1:88:0a:1c', ' Capability': 'R', 'RemotePortDescr': 'Interface   8 as enp5s0f0'},
    {'LocalPort': 'Ethernet8', 'RemoteDevice': 'r-ocelot-02',........}]
    """
    # Get all headers
    headers = output.splitlines()[headers_ofset]

    """Get lens for each column according to "---------" symbols len in output
    Interface    Oper    Admin    Alias    Description
    -----------  ------  -------  -------  -------------    <<<<<< This will be used
    Ethernet0      up       up     etp1            N/A
    """
    column_lens = output.splitlines()[len_ofset].split()

    # Parse only lines from "data_ofset_from_start" and if "data_ofset_from_end" exist - then parse till the "data_ofset_from_end"
    data = output.splitlines()[data_ofset_from_start:]
    if data_ofset_from_end:
        data = output.splitlines()[data_ofset_from_start:data_ofset_from_end]

    result_dict = {}
    result_list = []
    for line in data:
        base_position = 0
        internal_result = {}
        for column_len in column_lens:
            new_position = base_position + len(column_len)
            header_name = headers[base_position:new_position].strip()
            internal_result[header_name] = line[base_position:new_position].strip()
            base_position = new_position + column_ofset
        if output_key:
            result_dict[internal_result[output_key]] = internal_result
        else:
            result_list.append(internal_result)

    if output_key:
        return result_dict
    else:
        return result_list


def show_vlan_brief_parser(output):
    """
    This method doing parse for command "show vlan brief" output
    :param output: command "show vlan brief" output which should be parsed
    :return: dictionary with parsed data.

    Example:
    {'40': {'ips': ['4000::1/64', '40.0.0.1/24'],
            'ports': {'Ethernet236': 'tagged', 'PortChannel0002': 'tagged'},
            'dhcp_servers': [], 'proxy_arp': 'disabled'},
    '69': {'ips': ['69.0.0.1/24'..... ]}}
    """
    result_dict = {}

    data_line_index = 4
    vlan_index = 0
    ip_addr_index = 1
    vlan_port_index = 2
    vlan_port_mode_index = 3
    dhcp_server_index = 4
    proxy_arp_index = 5

    # Read data without headers
    data_lines = output.splitlines()[data_line_index:]

    vlan = None
    vlan_ips = []
    vlan_ports = {}
    dhcp_servers = []
    proxy_arp = None

    for line in data_lines:
        # Skip lines like: +-----------+--------------+----- which does not have data, analyze only lines with data
        splited_data_line = line.split('|')[1:]
        if splited_data_line:
            vlan_id = splited_data_line[vlan_index].strip()
            if vlan_id:
                # If next vlan data started - clean previous data
                if vlan != vlan_id:
                    vlan = None
                    vlan_ips = []
                    vlan_ports = {}
                    dhcp_servers = []
                    proxy_arp = None

                vlan = vlan_id
                proxy_arp = splited_data_line[proxy_arp_index].strip()

            vlan_ip = splited_data_line[ip_addr_index].strip()
            vlan_port = splited_data_line[vlan_port_index].strip()
            dhcp_server = splited_data_line[dhcp_server_index].strip()

            if vlan_ip:
                vlan_ips.append(vlan_ip)
            if vlan_port:
                vlan_ports[vlan_port] = splited_data_line[vlan_port_mode_index].strip()
            if dhcp_server:
                dhcp_servers.append(dhcp_server)

            result_dict[vlan] = {'ips': vlan_ips, 'ports': vlan_ports, 'dhcp_servers': dhcp_servers,
                                 'proxy_arp': proxy_arp}

    return result_dict
