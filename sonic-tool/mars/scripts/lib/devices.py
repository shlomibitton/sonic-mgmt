import json
import os
import re
from datetime import datetime

from fabric import Config
from fabric import Connection

from utils import get_logger

class LinuxDeviceBase(object):

    def __init__(self, ip, username, password):
        ip_port = ip.split(":")
        if len(ip_port) == 2:
            self.ip = ip_port[0]
            self.port = ip_port[1]
        else:
            self.ip = ip
            self.port = 22
        self.connection = Connection(self.ip, port=self.port, user=username, config=Config(overrides={"run": {"echo": True}}),
                                     connect_kwargs={"password": password})

    def run(self, *args, **kwargs):
        return self.connection.run(*args, **kwargs)


class SonicDevice(LinuxDeviceBase):

    CRITICAL_SERVICES = ["swss", "syncd", "database", "teamd", "bgp", "pmon", "lldp"]

    def __init__(self, ip, username, password):
        LinuxDeviceBase.__init__(self, ip, username, password)
        self.logger = get_logger("SONiCDevice")

    def _parse_column_ranges(self, hint_line, hint_char="-"):

        if [True for c in hint_line if c not in hint_char + " "]:
            return []

        column_ranges = []
        prev_c = " "
        for i, c in enumerate(hint_line):
            if c == hint_char:
                if c != prev_c:
                    column_start = i
                if i == len(hint_line) - 1:
                    column_end = i + 1
                    column_ranges.append((column_start, column_end))
            else:
                if c != prev_c:
                    column_end = i
                    column_ranges.append((column_start, column_end))
            prev_c = c
        return column_ranges

    def show_interface_status(self):
        output_lines = self.run("show interface status").stdout.strip().splitlines()

        if len(output_lines) < 3:
            return []

        column_name_line = output_lines[0]
        column_indication_line = output_lines[1]

        if len(column_indication_line) < 3:
            return []

        if not re.match('^[ -]*$', column_indication_line):
            return []

        column_ranges = self._parse_column_ranges(column_indication_line)

        res = []
        header_line = output_lines[0]
        for line in output_lines[2:]:
            intf_status = {}
            for start, end in column_ranges:
                intf_status[header_line[start:end].strip().lower()] = line[start:end].strip()
            res.append(intf_status)

        return res

    def get_platform_info(self):
        facts = {}
        platform_info = self.run("show platform summary").stdout.strip().splitlines()
        for line in platform_info:
            if line.startswith("Platform:"):
                facts["platform"] = line.split(":")[1].strip()
            elif line.startswith("HwSKU:"):
                facts["hwsku"] = line.split(":")[1].strip()
            elif line.startswith("ASIC:"):
                facts["asic_type"] = line.split(":")[1].strip()
        return facts

    @property
    def issu_enabled(self):
        facts = self.get_platform_info()

        platform = facts["platform"]
        hwsku = facts["hwsku"]

        sai_profile = "/usr/share/sonic/device/%s/%s/sai.profile" % (platform, hwsku)
        cmd = "basename $(cat {} | grep SAI_INIT_CONFIG_FILE | cut -d'=' -f2)".format(sai_profile)
        sai_xml_filename = self.run(cmd).stdout.strip()
        sai_xml_path = "/usr/share/sonic/device/{}/{}/{}".format(platform, hwsku, sai_xml_filename)

        pattern = "<issu-enabled> *1 *<\/issu-enabled>"
        output = self.run('egrep "%s" %s | wc -l' % (pattern, sai_xml_path)).stdout.strip()
        return True if output == "1" else False

    def get_service_props(self, service, props=["ActiveState", "SubState"]):
        """
        @summary: Use 'systemctl show' command to get detailed properties of a service. By default, only get
            ActiveState and SubState of the service.
        @param service: Service name.
        @param props: Properties of the service to be shown.
        @return: Returns a dictionary containing properties of the specified service, for example:
            {
                "ActivateState": "active",
                "SubState": "running"
            }
        """
        props = " ".join(["-p %s" % prop for prop in props])
        output = self.run("systemctl %s show %s" % (props, service)).stdout.strip()
        result = {}
        for line in output.splitlines():
            fields = line.split("=")
            if len(fields) >= 2:
                result[fields[0]] = fields[1]
        return result

    def is_service_fully_started(self, service):
        """
        @summary: Check whether a SONiC specific service is fully started.

        The last step in the starting script of all SONiC services is to run "docker wait <service_name>". This command
        will not exit unless the docker container of the service is stopped. We use this trick to determine whether
        a SONiC service has completed starting.

        @param service: Name of the SONiC service
        """
        try:
            # TODO "docker wait xx" is no longer valid. Use "docker ps".
            output = self.run('docker ps --format "{{.ID}} {{.Names}} {{.Status}}" --filter "name=%s"' % service)
            if output.stdout.strip():
                return True
            else:
                return False
        except:
            return False

    def critical_services_status(self):
        """
        @summary: Get status of all critical services
        @return: Return a dict. Key is service name. Value is True or False depends on status of the service.
        """
        result = {}
        for service in self.CRITICAL_SERVICES:
            result[service] = self.is_service_fully_started(service)

        self.logger.debug("Status of critical services: %s" % str(result))
        return result

    def critical_services_fully_started(self):
        """
        @summary: Check whether all the SONiC critical services have started
        """
        result = {}
        for service in self.CRITICAL_SERVICES:
            result[service] = self.is_service_fully_started(service)

        self.logger.debug("Status of critical services: %s" % str(result))
        return all(result.values())

    def get_up_time(self):
        uptime_text = self.run("uptime -s").stdout.strip()
        return datetime.strptime(uptime_text, "%Y-%m-%d %H:%M:%S")

    def get_now_time(self):
        now_time = self.run('date +"%Y-%m-%d %H:%M:%S"').stdout.strip()
        return datetime.strptime(now_time, "%Y-%m-%d %H:%M:%S")

    def get_uptime(self):
        return self.get_now_time() - self.get_up_time()


class SonicMgmtDevice(LinuxDeviceBase):

    def __init__(self, ip, username, password, repo_path):
        LinuxDeviceBase.__init__(self, ip, username, password)
        self.repo_path = repo_path

    def run_ansible(self, module_name, inventory, host_pattern, module_args=""):
        with self.connection.cd(os.path.join(self.repo_path, "ansible")):
            cmd = "ansible -o -m {MODULE_NAME} -i {INVENTORY} {HOST_PATTERN} {MODULE_ARGS}"
            cmd = cmd.format(MODULE_NAME=module_name, INVENTORY=inventory, HOST_PATTERN=host_pattern,
                             MODULE_ARGS=module_args)
            res = self.run(cmd)
            res.ansible_result = json.loads(re.sub("^[^{]*", "", res.stdout.splitlines()[-1]))
            return res

    def run_playbook(self, cmd):
        with self.connection.cd(os.path.join(self.repo_path, "ansible")):
            return self.run(cmd)
