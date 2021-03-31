class LinuxConsts:
    get_exit_code = 'echo $?'
    exit_code_zero = '0'
    error_exit_code = 1


class TopologyConsts:
    engine = 'engine'
    players = 'players'
    ports = 'ports'
    interconnects = 'interconnects'
    ports_names = 'ports_names'


class NogaConsts:
    attributes = 'attributes'
    Common = 'Common'
    Specific = 'Specific'
    ip = 'ip'
    Topology_Conn = 'Topology Conn.'
    DESCRIPTION = 'DESCRIPTION'
    TYPE_TITLE = 'TYPE_TITLE'
    ID = 'ID'
    Switch = 'Switch'
    VM = 'VM'
    Server = 'Server'
    Port = 'Port'
    IF = 'IF'
    CONN_USER = 'CONN_USER'
    CONN_PASSWORD = 'CONN_PASSWORD'
    relations = 'relations'
    connected_with = 'connected with'
    RES_ID = 'RES_ID'
    Description = 'Description'
    resource_id = 'resource_id'
    CONFIG_FILE = 'config_file'


class SonicConsts:
    ETC_SONIC_PATH = "/etc/sonic"
    CONFIG_DB_JSON = "config_db.json"
    CONFIG_DB_JSON_PATH = "{}/{}".format(ETC_SONIC_PATH, CONFIG_DB_JSON)
    CONFIG_RELOAD = "sudo config reload -y"
    SHOW_LLDP_TABLE = "show lldp table"
    PORT_CONFIG_INI = "port_config.ini"


class ConfigDbJsonConst:
    PORT = 'PORT'
    FEATURE = 'FEATURE'
    LLDP = 'lldp'
    STATUS = 'status'
    ENABLED = 'enabled'
    DEVICE_METADATA = "DEVICE_METADATA"
    LOCALHOST = "localhost"
    TYPE = 'type'
    TOR_ROUTER = 'ToRRouter'
    HOSTNAME = "hostname"
    MAC = "mac"
    HWSKU = "hwsku"
