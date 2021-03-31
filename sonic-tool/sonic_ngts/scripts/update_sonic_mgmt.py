import argparse
import csv
import os
import xml.etree.ElementTree as ET
import logging
import re
import sys
import shutil

from collections import OrderedDict
from xml.etree.ElementTree import Element

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.path.pardir)))
from infra.noga.noga import get_noga_resource_data

logger = logging.getLogger(__name__)

TESTBED_CSV_ROW = OrderedDict([("# conf-name", None), ("group-name", "vm-t1"), ("topo", "ptf-any"),
                                ("ptf_image_name", "docker-ptf-mlnx"), ("ptf", "ptf-dummy"),
                                ("ptf_ip", "1.1.1.1/16"), ("ptf_ipv6", ""), ("server", None), ("vm_base", "VM0000"),
                                ("dut", None), ("comment", "Mellanox {} testbed")])

class CONF_FILES:
    def __init__(self, sonic_mgmt):
        self.testbed_csv = "{sonic_mgmt}/ansible/testbed.csv".format(sonic_mgmt=sonic_mgmt)
        self.veos = "{sonic_mgmt}/ansible/veos".format(sonic_mgmt=sonic_mgmt)
        self.lab = "{sonic_mgmt}/ansible/lab".format(sonic_mgmt=sonic_mgmt)
        self.inventory = "{sonic_mgmt}/ansible/inventory".format(sonic_mgmt=sonic_mgmt)
        self.lab_connection_graph = "{sonic_mgmt}/ansible/files/lab_connection_graph.xml".format(sonic_mgmt=sonic_mgmt)
        self.minigraph_facts = "{sonic_mgmt}/ansible/library/minigraph_facts.py".format(sonic_mgmt=sonic_mgmt)

    def __getattribute__(self, name):
        return object.__getattribute__(self, name)


class TestbedCSV:
    """
    @summary: Class which adds entry to the 'testbed.csv' file
    """
    def __init__(self, csv_file, testbed_csv_row):
        self.row_template = OrderedDict(testbed_csv_row)
        self.testbed_csv = csv_file

    def entry_exists(self, dut_name):
        """
        Ensure entry with specified DUT exists in 'ansible/testbed.csv' file
        @param dut_name: DUT name
        """
        with open(self.testbed_csv) as testbed_file:
            csv_reader = csv.DictReader(testbed_file)
            if any([dut_name in row["# conf-name"] for row in csv_reader]):
                return True
            else:
                return False

    def add_testbed_entry(self):
        """
        Add new entry to the testbed.csv file
        Entry example:
        r-lionfish-07-ptf-any,vm-t1,ptf-any,docker-ptf-mlnx,ptf-dummy,1.1.1.1/16,,server_54,VM0000,r-lionfish-07,Mellanox MTR testbed
        """
        with open(self.testbed_csv, "a+") as testbed_file:
            csv_writer = csv.DictWriter(testbed_file, fieldnames=self.row_template.keys())
            csv_writer.writerow(self.row_template)


class Inventory:
    """
    @summary: Class to add entry to the 'inventory' file
    """
    def __init__(self, inventory):
        self.inventory_path = inventory
        self.inventory_buff = self.read()

    def read(self):
        """
        Read and return content of 'ansible/inventory' file
        """
        with open(self.inventory_path) as inv_file:
            buff = inv_file.read()
        return buff

    def entry_exists(self, dut_name):
        """
        Ensure entry with specified DUT exists in 'ansible/inventory' file
        @param dut_name: DUT name
        """
        with open(self.inventory_path) as inventory_file:
            for line in inventory_file.read().splitlines():
                if dut_name in line:
                    return True
        return False

    def add_entry(self, dut_name, hwsku, console, pdu_host):
        """
        Add new entries to the inventory file
        Entry example:
        r-lionfish-07-ptf-any
        r-lionfish-07-ptf-any  ansible_host=r-lionfish-07  sonic_version=v2  sonic_hwsku=ACS-MSN3420 \
            serial_console="ssh -l rcon:7034 10.208.0.49" ptf_host=ptf-dummy ptf_portmap="" pdu_host=pdu-10-208-0-186
        """
        buff = ""
        sonic_latest_entry = "ansible_host={dut_name}  sonic_version=v2  sonic_hwsku={hwsku} \
            serial_console=\"{console}\" ptf_host=ptf-dummy ptf_portmap=\"\" pdu_host={pdu_host}"
        tb_topo = "{dut_name}-ptf-any\n{dut_name}".format(dut_name=dut_name)
        dev_topo = "{dut_name}-ptf-any {sonic_latest}\n{dut_name} {sonic_latest}".format(dut_name=dut_name,
                sonic_latest=sonic_latest_entry.format(dut_name=dut_name, hwsku=hwsku, console=console, pdu_host=pdu_host))
        pdu_line = "{} ansible_host={} protocol=snmp".format(pdu_host, pdu_host[4:].replace('-', '.'))
        for line in self.inventory_buff.splitlines():
            if "[lab]" in line:
                buff += line + "\n"
                buff += tb_topo + "\n"
            elif "[sonic_latest]" in line:
                buff += line + "\n"
                buff += dev_topo + "\n"
            elif "[pdu]" in line:
                if pdu_line not in self.inventory_buff:
                    buff += line + "\n"
                    buff += pdu_line + "\n"
            else:
                buff += line + "\n"
        with open(self.inventory_path, "w", 0o0600) as inv_file:
            inv_file.write(buff)


class Veos:
    """
    @summary: Class to read max server ID from the 'veos' file.
    """
    def __init__(self, veos_file):
        self.veos = veos_file
        self.veos_buff = self.read()

    def read(self):
        """
        Read and return content of 'ansible/veos' file
        """
        with open(self.veos) as veos_file:
            data = veos_file.read()
        return data

    def get_max_id(self):
        """
        Get max server ID defined in 'servers:children' section
        """
        srv_buff = []
        for line in self.veos_buff.split():
            if "[servers:children]" in line:
                srv_buff.append(line)
                continue
            if srv_buff:
                if "[" in line:
                    break
                srv_buff.append(line)
        return int(srv_buff[-1].strip("server_"))

    def add_entry(self, srv_host):
        """
        Add new entry to the veos file
        """
        new_veos = ""
        srv_id = self.get_max_id() + 1

        srv_children = "[server_{srv_id}:children]\nvm_host_{srv_id}\nvms_{srv_id}".format(srv_id=srv_id)
        srv_vars = "[server_{srv_id}:vars]\nhost_var_file=host_vars/{srv_host}.yml".format(srv_id=srv_id,
                srv_host=srv_host.upper())
        vm_host = "[vm_host_{srv_id}]\n{srv_host_file} ansible_host={srv_host}".format(srv_id=srv_id,
                srv_host_file=srv_host.upper(), srv_host=srv_host)
        vms = "[vms_{srv_id}]".format(srv_id=srv_id)
        main_block = "\n\n".join([srv_children, srv_vars, vm_host, vms])
        new_veos += self.veos_buff
        new_veos += main_block
        
        with open(self.veos, "w") as veos_file:
            veos_file.write(new_veos)


class Lab:
    """
    @summary: Class to add entry to the 'lab' file.
    """
    def __init__(self, lab_path):
        self.lab_path = lab_path
        self.lab_buff = self.read()

    def read(self):
        """
        Read and return content of 'ansible/lab' file
        """
        with open(self.lab_path) as lab_file:
            buff = lab_file.read()
        return buff

    def add_entry(self, dut_name, ansible_host, hwsku, iface_speed):
        """
        Add new entry to the lab file
        Entry example:
        r-lionfish-07      ansible_host=10.210.25.107 ansible_hostv6="fe80::e42:a1ff:fe44:44c0" sonic_version=v2 \
            hwsku="ACS-MSN3420" iface_speed=25000  mgmt_subnet_mask_length=22 vm_base=VM0000
        """
        buff = ""
        lab_template = "{dut_name}      ansible_host={ansible_host} ansible_hostv6=\"fe80::e42:a1ff:fe44:44c0\" sonic_version=v2 hwsku=\"{hwsku}\" iface_speed={speed}  mgmt_subnet_mask_length=22 vm_base=VM0000"
        lab_entry = lab_template.format(dut_name=dut_name, ansible_host=ansible_host,
            hwsku=hwsku, speed=iface_speed)
        for line in self.lab_buff.splitlines():
            if "[sonic_latest]" in line:
                buff += line + "\n"
                buff += lab_entry + "\n"
            else:
                buff += line + "\n"

        with open(self.lab_path, "w", 0o0600) as lab_file:
            lab_file.write(buff)


class MinigraphFacts:
    def __init__(self, mgmt_minigraph_path):
        self.mgmt_minigraph_path = mgmt_minigraph_path
        self.stub_mgmt_minigraph_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), "minigraph_facts.py")

    def write_minigraph_facts(self):
        shutil.copyfile(self.stub_mgmt_minigraph_path, self.mgmt_minigraph_path)


def connection_gr_add_entry(file_path, hostname, hwsku):
    """
    @summary: Add entry to the 'lab_connection_graph.xml' file
    Entry example:
    <Devices>
    ...
    <Device Hostname="r-mgtswh-136" HwSku="TestServ" Type="Server"/>
    </Devices>
    """
    tree = ET.parse(file_path)
    root = tree.getroot()

    for upper_item in root.getchildren():
        if upper_item.tag == "PhysicalNetworkGraphDeclaration":
            for inner_item in upper_item.getchildren():
                if inner_item.tag == "Devices":
                    devices = inner_item
                    break
    if any([item.get("Hostname") == hostname for item in devices]):
        logger.warning("{} - Entry for '{}' already exists".format(file_path, hostname))
    else:
        devices.append(Element("Device", {"Hostname": hostname, "HwSku": hwsku, "Type": "DevSonic"}))
        tree.write(file_path)


def get_hwsku_from_noga_res(noga_resource):
    """
    @summary: Parse HWSKU value from Noga HWSKU string
    """
    hwsku = None
    hwsku = noga_resource["attributes"]["Specific"]["switch_type"]
    for item in hwsku.split():
        if re.findall("\d{4}", item):
            hwsku = item
            break
    else:
        logger.error("HWSKU has unexpected format: {}".format(hwsku))
    return hwsku


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--dut", help="DUT name", type=str, required=True)
    parser.add_argument("--mgmt_repo", help="Path to the sonic-mgmt repo", type=str, required=True)
    parser.add_argument("--topo_dir", help="Path to the topology folder of current DUT", type=str, required=True)
    args = parser.parse_args()

    dut_name = args.dut
    mgmt_repo = args.mgmt_repo
    topo_dir = args.topo_dir

    conf_files = CONF_FILES(mgmt_repo)
    testbed_csv = TestbedCSV(conf_files.testbed_csv, TESTBED_CSV_ROW)
    veos = Veos(conf_files.veos)
    lab = Lab(lab_path=conf_files.lab)
    inv = Inventory(conf_files.inventory)
    mg_facts = MinigraphFacts(conf_files.minigraph_facts)

    noga_resource = get_noga_resource_data(resource_name=dut_name)
    hwsku = get_hwsku_from_noga_res(noga_resource)

    if testbed_csv.entry_exists(dut_name=dut_name):
        logger.warning("{} - Entry for '{}' DUT already exists. Skip configuration.".format(conf_files.testbed_csv, dut_name))
    else:
        testbed_csv.row_template["# conf-name"] = dut_name + "-ptf-any"
        testbed_csv.row_template["server"] = "server_{}".format(veos.get_max_id())
        testbed_csv.row_template["dut"] = dut_name
        testbed_csv.row_template["comment"] = testbed_csv.row_template["comment"].format(noga_resource["attributes"]["Common"]["Site"])

        # Update testbed.csv
        testbed_csv.add_testbed_entry()

        # Update ansible/lab
        lab.add_entry(dut_name=dut_name, ansible_host=noga_resource["attributes"]["Specific"]["ip"],
            hwsku=hwsku, iface_speed=25000)

        # Update lab_connection_graph.xml
        connection_gr_add_entry(conf_files.lab_connection_graph, dut_name, hwsku)

        # Update inventory
        pdu_host = noga_resource["attributes"]["Specific"]["pdu"]
        try:
            pdu_host = "pdu-" + pdu_host.split('/')[0].replace('.', '-')
        except Exception:
            logger.error("PDU has unexpected format, using value from NOGA: {}".format(pdu_host))
        inv.add_entry(dut_name, hwsku, noga_resource["attributes"]["Specific"]["serial_connection_command"], pdu_host)

        # Update minigraph_facts.py
        mg_facts.write_minigraph_facts()
