import logging
import re
import os
import json
from infra.engines.ssh.ssh_engine import SSH
from infra.utilities.topology_util import *
from infra.topology_entities.topology_entity_interface import TopologyEntityInterface
from infra.exceptions.entity_exception import TopologyEntityError
#
# create a logger for this class
#
logger = logging.getLogger("host_topology_entity")


class HostTopologyEntity(TopologyEntityInterface):
    """
    HostTopologyEntity
    Store all the information about the host entity in sonic setup.
    creates the host .xml file.
    """

    def __init__(self, ip, username, password, alias, hostname=None, mac=None, set_entity_info=True):
        self.ip = ip
        self.username = username
        self.password = password
        self.alias = alias
        self.engine = SSH(ip=self.ip, username=self.username, password=self.password)
        self.hostname = hostname
        self.mac = mac
        self.ports_info = {}
        self.lldp_connectivity = {}
        if set_entity_info:
            self.set_entity_info()

    def set_entity_info(self):
        """
        Set host entity information:
        hostname, mac, port information, and lldp connectivity information.
        :return: None
        """
        logger.info("Starting setting host entity {}.\n".format(self.ip))
        self.run_lldp()
        self.set_lldptool()
        self.advertise_host_info_via_lldp()
        self.set_hostname()
        self.set_mac()
        self.set_ports_info()
        self.get_lldp_connectivity()

    def run_lldp(self):
        """
        This function runs the lldp demon on host and install service if it need
        :return: None.
        """
        cmd = "lldpad -d"
        output = self.engine.run_cmd(cmd, validate=False)

        if re.search('Command\s*\'lldpad\'\s*not\s*found,\s*but\s*can\s*be\s*installed\s*with', output):
            self.install_service(service='lldpad')
            self.engine.run_cmd(cmd)

    def set_lldptool(self):
        cmd = "lldptool -p"
        output = self.engine.run_cmd(cmd, validate=False)
        if re.search('(lldptool:)\s*\w*\s*(not found)', output):
            self.install_service(service='lldptool')

    def advertise_host_info_via_lldp(self):
        """
        this function will enable the lldptool to advertise to neighbor entity
        the host information such as, hostname, port name etc.
        :return: None
        """
        logger.info("Set lldp parameters on host {}".format(self.ip))
        cmd = "for i in `ls /sys/class/net/ | grep 'enp\|ens\|p1p'`;" \
              "do echo \"enabling lldp for interface: $i\"; " \
              "lldptool set-lldp -i $i adminStatus=rxtx;" \
              "lldptool -T -i $i -V sysName enableTx=yes;" \
              "lldptool -T -i $i -V portDesc enableTx=yes;" \
              "lldptool -T -i $i -V sysDesc enableTx=yes;" \
              "lldptool -T -i $i -V sysCap enableTx=yes;" \
              "lldptool -T -i $i -V mngAddr enableTx=yes;" \
              "done"
        self.engine.run_cmd(cmd)

    def install_service(self, service, tool='yum'):
        """
        install a service on host.
        :param service: service name
        :param tool: tool name
        :return: None, exception is raised if installation has failed
        """
        cmd = '{} install -y {}'.format(tool, service)
        res = self.engine.run_cmd(cmd)
        err = 'No package %s available'.format(service)
        if err in res:
            raise TopologyEntityError('{} installation on host {} failed.'.format(service, self.ip))

    def set_hostname(self):
        """
        set host hostname.
        :return: None
        """
        self.hostname = self.engine.run_cmd('hostname')

    def set_mac(self):
        """
        set host mac address.
        :return: None
        """
        eth0_info = self.engine.run_cmd("ip -j link show eth0")
        eth0_json = json.loads(eth0_info).pop()
        self.mac = eth0_json["address"]

    def set_ports_info(self):
        """
        run and parse "ip link show" command output into ports_info dictionary.
        :return: None, update the host ports_info dictionary.
        In the end of function self.port_info = {
        "24:8a:07:b5:72:81" : { "mac": "24:8a:07:b5:72:81", "if": "enp131s0f1", "id": "enp131s0f1"} ,
        "24:8a:07:b5:72:82" : ...
        }
        ip_link_show_json=
        [{"ifindex":1,"ifname":"lo","flags":["LOOPBACK","UP","LOWER_UP"],"mtu":65536,"qdisc":"noqueue",
        "operstate":"UNKNOWN","linkmode":"DEFAULT","group":"default","txqlen":1000,"link_type":"loopback",
        "address":"00:00:00:00:00:00","broadcast":"00:00:00:00:00:00"},...]
        """
        logger.info("Getting host entity {} ports.\n".format(self.ip))
        ip_link_show_output = self.engine.run_cmd('ip -j link show')
        ip_link_show_json = json.loads(ip_link_show_output)

        for port_dict in ip_link_show_json:
            port_name = port_dict["ifname"]
            if re.match("lo|eth0", port_name):
                continue
            else:
                self.ports_info[port_dict["address"]] = {
                    'mac': port_dict["address"],
                    'if': port_name,
                    'id': port_name}

    def get_lldp_connectivity(self):
        """
        This function update the lldp_connectivity dictionary,
        for each port in host it update the lldp neighbor info for that port.
        :return: None.
        In the end of function self.lldp_connectivity = {
        "24:8a:07:b5:72:81" : { "neighbor_port": "Ethernet1", "neighbor_ip": "10.210.24.186" } ,
        "24:8a:07:b5:72:82" : ...
        }
        """
        logger.info("Getting host entity {} lldp ports information.\n".format(self.ip))
        for port_info_dict in self.ports_info.values():
            port_name = port_info_dict['if']
            port_mac = port_info_dict['mac']
            port_lldp_info = self.get_port_lldp_data(port_name)
            self.lldp_connectivity[port_mac] = port_lldp_info

    def get_port_lldp_data(self, port_name):
        """
        get lldp neighbor connectivity information for host port_name.
        :param port_name: a name of host port, e.g. enp131s0f1
        :return: a dict with the port neighbor port and neighbor device ip.
        for example:
        { "neighbor_port": "etp1", "neighbor_hostname": "r-lionfish-07" }
        """
        port_lldp_output = self.engine.run_cmd('lldptool -i {} -t -n'.format(port_name))
        port_lldp_info = {}
        regex_patterns = {"neighbor_port": "Port\s*Description\s*TLV\s*(.*)\s",
                          "neighbor_hostname": "System\s*Name\s*TLV\s*(.*)\s"}
        for neighbor_info, regex_pattern in regex_patterns.items():
            try:
                neighbor_value = re.search(regex_pattern, port_lldp_output, re.IGNORECASE).group(1)
                port_lldp_info[neighbor_info] = neighbor_value
            except Exception as e:
                msg = "Could not match lldp neigbor information {}" \
                      " for port {} with regex pattern {}.\n " \
                      "Please review this pattern result.\n".format(neighbor_info, port_name, regex_pattern)
                logger.error(msg)
                raise TopologyEntityError(msg)
        return port_lldp_info

    def update_port_alias(self, port_mac, port_alias):
        """
        update the alias for the host port.
        :param port_mac: port mac address, e.g. "24:8a:07:b5:72:81"
        :param port_alias: the alias for this port. e.g. "ha-dut-1"
        :return: None
        """
        self.ports_info[port_mac]['connection_alias'] = port_alias

    def create_entity_xml(self, path):
        """
        create the host .xml file in path.
        :param path: the path where the entity xml file will be.
        :return: None
        """
        logger.info("Create {}.xml file in path {}.".format(self.hostname, path))
        template = get_xml_template('host_template.txt')
        output = template.render(host=self, ports=self.ports_info.values())
        new_entity_xml_file_path = os.path.join(path, '{}.xml'.format(self.hostname))
        create_file(new_entity_xml_file_path, output)
