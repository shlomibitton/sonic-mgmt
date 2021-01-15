from infra.noga import noga
from infra.constants.constants import NogaConsts, TopologyConsts
from infra.engines.ssh import ssh_engine
from infra.generic.generic_structures import AttrDict


def get_topology(setup_name, engines=True):
    """
    Get topology for setup
    :param setup_name: example: SONiC_tigris_r-tigris-04
    :param engines: If you need to have engines for players - True, else False
    :return: topology object
    """
    topology = {}
    players, ports = get_topology_entities(setup_name)
    ports_interconnects = get_ports_interconnects(ports)
    ports_names = get_port_to_name_matching(ports)

    if engines:
        for player in players:
            ip = players[player][NogaConsts.attributes][NogaConsts.Specific][NogaConsts.ip]
            username = players[player][NogaConsts.attributes][NogaConsts.Topology_Conn][NogaConsts.CONN_USER]
            password = players[player][NogaConsts.attributes][NogaConsts.Topology_Conn][NogaConsts.CONN_PASSWORD]
            players[player][TopologyConsts.engine] = ssh_engine.SSH(ip, username, password)

    # Convert each player dict to object
    for player in players:
        players[player] = AttrDict(players[player])

    topology.update({TopologyConsts.players: AttrDict(players), TopologyConsts.ports: ports,
                     TopologyConsts.interconnects: ports_interconnects, TopologyConsts.ports_names: ports_names})

    return AttrDict(topology)


def get_topology_entities(setup_name):
    """
    Get devices for setup(hosts, switches and ports)
    :param setup_name: example: SONiC_tigris_r-tigris-04
    :return: 2 dictionaries - first contain players, second - ports
    """
    players = {}
    ports = {}
    player_types_list = [NogaConsts.Switch, NogaConsts.VM, NogaConsts.Server]

    for item in noga.get_noga_resource(resource_name=setup_name):
        item_data = noga.get_noga_resource_data(resource_id=item[NogaConsts.ID])
        if item[NogaConsts.TYPE_TITLE] in player_types_list:
            players[item[NogaConsts.DESCRIPTION]] = item_data
        elif item[NogaConsts.TYPE_TITLE] == NogaConsts.Port:
            ports[item[NogaConsts.DESCRIPTION]] = item_data

    return players, ports


def get_ports_interconnects(ports):
    """
    Get peer port
    :param ports: object with all ports in current setup
    :return: peer port
    """
    interconnects = {}
    for port_name, port_info in ports.items():
        peer_port = get_peer_port_alias_name(port_info[NogaConsts.resource_id])
        interconnects[port_name] = peer_port
    return interconnects


def get_peer_port_alias_name(resource_id):
    """
    Get peer port alias name
    :param resource_id: NOGA device ID
    :return: peer port alias name
    """
    port_data = noga.get_noga_resource_data(resource_id=resource_id)
    peer_port_id = port_data[NogaConsts.relations][NogaConsts.connected_with][0][NogaConsts.RES_ID]
    port_data = noga.get_noga_resource_data(resource_id=peer_port_id)
    peer_port_name = port_data[NogaConsts.attributes][NogaConsts.Common][NogaConsts.Description]
    return peer_port_name


def get_port_to_name_matching(ports):
    """
    Get port alias to porn name mapping
    :param ports: object with all ports in current setup
    :return: port to physical name matching
    """
    port_names = {}
    for port_name, port_info in ports.items():
        port_data = noga.get_noga_resource_data(resource_id=port_info[NogaConsts.resource_id])
        port_names[port_name] = port_data[NogaConsts.attributes][NogaConsts.Specific][NogaConsts.IF]
    return port_names


def get_switch_engine(switch_ip):
    """
    :param switch_ip: a switch ip, e.g. 10.210.24.193
    :return: an ssh engine of the switch
    """
    switch_data = noga.get_noga_resource_data(ip_address=switch_ip)
    ip = switch_data[NogaConsts.attributes][NogaConsts.Specific][NogaConsts.ip]
    username = switch_data[NogaConsts.attributes][NogaConsts.Topology_Conn][NogaConsts.CONN_USER]
    password = switch_data[NogaConsts.attributes][NogaConsts.Topology_Conn][NogaConsts.CONN_PASSWORD]
    return ssh_engine.SSH(ip, username, password)


def get_switch_config_files_dir_path(switch_ip):
    """
    :param switch_ip: a switch ip, e.g. 10.210.24.193
    :return: a path to the directory where the configuration files for the switch are.
    """
    switch_data = noga.get_noga_resource_data(ip_address=switch_ip)
    config_files_dir_path = switch_data[NogaConsts.attributes][NogaConsts.Specific][NogaConsts.CONFIG_FILE]
    return config_files_dir_path
