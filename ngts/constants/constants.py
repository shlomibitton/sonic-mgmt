class SonicConst:
    DOCKERS_LIST = ['swss', 'syncd', 'bgp', 'teamd', 'pmon', 'lldp', 'dhcp_relay']

    CPU_RAM_CHECK_PROCESS_LIST = ['sx_sdk', 'syncd', 'redis-server', 'snmpd', 'zebra', 'bgpd', 'bgpcfgd', 'bgpmon',
                                  'fpmsyncd', 'orchagent', 'ntpd', 'neighsyncd', 'vlanmgrd', 'intfmgrd', 'portmgrd',
                                  'buffermgrd', 'vrfmgrd', 'nbrmgrd', 'vxlanmgrd', 'sensord']

    SONIC_CONFIG_FOLDER = '/etc/sonic/'
    PORT_CONFIG_INI = 'port_config.ini'
    CONFIG_DB_JSON = 'config_db.json'
    CONFIG_DB_JSON_PATH = SONIC_CONFIG_FOLDER + CONFIG_DB_JSON
    MINIGRAPH_XML = 'minigraph.xml'
    MINIGRAPH_XML_PATH = SONIC_CONFIG_FOLDER + MINIGRAPH_XML


class InfraConst:
    HTTP_SERVER = 'http://fit69'
    MARS_TOPO_FOLDER_PATH = '/auto/sw_regression/system/SONIC/MARS/conf/topo/'
    REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/SONIC/MARS/results'

    MYSQL_SERVER = '10.208.1.11'
    MYSQL_USER = 'sonic'
    MYSQL_PASSWORD = 'sonic11'
    MYSQL_DB = 'sonic'


class LinuxConsts:
    error_exit_code = 1
    linux = 'linux'


class TopologyConsts:
    engine = 'engine'
    players = 'players'
    ports = 'ports'
    interconnects = 'interconnects'
    ports_names = 'ports_names'


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
