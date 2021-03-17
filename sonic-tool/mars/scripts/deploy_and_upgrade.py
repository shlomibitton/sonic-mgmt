#!/usr/bin/env python
"""
Prepare the SONiC testing topology.

This script is executed on the STM node. It establishes SSH connection to the sonic-mgmt docker container (Player) and
run commands on it. Purpose is to prepare the SONiC testing topology using the testbed-cli.sh tool.
"""

# Builtin libs
import argparse
import os
import random
import re
import socket
import sys
import contextlib
import subprocess
import logging
import BaseHTTPServer
import shutil
import json
import time
from multiprocessing.pool import ThreadPool

# Third-party libs
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.utils import parse_topology, get_logger

logger = get_logger("DeployUpgrade")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--dut-name", required=True, dest="dut_name", help="The DUT name")
    parser.add_argument("--sonic-topo", required=True, dest="sonic_topo",
                        help="The topo for SONiC testing, for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--base-version", required=True, dest="base_version",
                        help="URL or path to the SONiC image. Firstly upgrade switch to this version.")
    parser.add_argument("--upgrade_type", nargs="?", default="sonic", dest="upgrade_type")
    parser.add_argument("--target-version", nargs="?", default="", dest="target_version",
                        help="URL or path to the SONiC image. If this argument is specified, upgrade switch to this \
                              version after upgraded to the base_version. Default: ''")
    parser.add_argument('--log_level', dest='log_level', default=logging.INFO, help='log verbosity')
    parser.add_argument("--upgrade-only", nargs="?", default="no", dest="upgrade_only",
                        help="Specify whether to skip topology change and only do upgrade. Default: 'no'")
    parser.add_argument("--reboot", nargs="?", default="no", choices=["no", "random"] + constants.REBOOT_TYPES.keys(),
                        dest="reboot", help="Specify whether reboot the switch after deploy. Default: 'no'")
    parser.add_argument("--repo-name", dest="repo_name", help="Specify the sonic-mgmt repository name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo on sonic-mgmt docker container.")
    parser.add_argument("--port-number", nargs="?", default="", dest="port_number",
                        help="Specify the test setup's number of ports. Default: ''")
    parser.add_argument("--wjh-deb-url", help="Specify url to WJH debian package",
                        dest="wjh_deb_url", default="")
    parser.add_argument("--recover_by_reboot", help="If post validation install validation has failed, "
                                                    "reboot the dut and run post validation again."
                                                    "This flag might be useful when the first boot has failed due to fw upgrade timeout",
                        dest="recover_by_reboot", default=True, action='store_true')
    parser.add_argument("--serve_files", help="Specify whether to run http server on the runnning machine and serve the installer files"
                                              "Note: this option is not supported when running from a docker without ip",
                        dest="serve_files", default=False, action='store_true')

    return parser.parse_args()


class ImageHTTPRequestHandler(BaseHTTPServer.BaseHTTPRequestHandler):
    """
    @summary: HTTP request handler class, for serving SONiC image files over HTTP.
    """
    served_files = {}

    def do_GET(self):
        """
        @summary: Handling HTTP GET requests.
        """
        if self.path == "/favicon.ico":
            self.send_error(404, "No /favicon.ico")
            return None

        if self.path not in self.served_files.keys():
            self.send_error(404, "Requested URL is not found")
            return None

        f = self.send_head(self.path)
        if f:
            shutil.copyfileobj(f, self.wfile)
            f.close()

    def send_head(self, request_path):
        """
        @summary: Send HTTP header
        @param request_path: Path of the HTTP Request
        """
        served_file = self.served_files[request_path]
        if not os.path.isfile(served_file):
            self.send_error(404, "File %s not found for /%s" % (served_file, request_path))
            return None

        try:
            f = open(served_file, "rb")
        except IOError:
            self.send_error(404, "Read file %s failed" % served_file)
            return None
        self.send_response(200)
        self.send_header("Content-type", "application/octet-stream")
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.end_headers()
        return f


def separate_logger(func):
    """
    Decorator which run method in silent mode(redirect stdout and stderr to file) without print output,
    output will be printed only in case of failure or in case of using logger
    """
    @contextlib.contextmanager
    def redirect_stdout_stderr(std_data_file_name):
        original_out = sys.stdout
        original_err = sys.stderr
        try:
            with open(std_data_file_name, 'w') as logdata:
                sys.stdout = logdata
                sys.stderr = logdata
                yield
        finally:
            sys.stdout = original_out
            sys.stderr = original_err

    def get_std_data(std_data_filename):
        with open(std_data_filename) as data:
            return data.read()

    def wrapper(*args, **kwargs):
        method_name = func.__name__
        dut_name = kwargs.get('dut_name')
        std_data_filename = "/tmp/{}_{}.log".format(method_name, dut_name)

        logger.info('#' * 100)
        logger.info('Running method: {}'.format(method_name))
        logger.info('#' * 100)

        try:
            with redirect_stdout_stderr(std_data_filename):
                func(*args, **kwargs)
            logger.debug(get_std_data(std_data_filename))
        except Exception as err:
            logger.error(get_std_data(std_data_filename))
            raise Exception(err)
        finally:
            logger.info('#' * 100)
            logger.info('Finished run for method: {}'.format(method_name))
            logger.info('#' * 100)

    return wrapper


def start_http_server(served_files):
    """
    @summary: Use ThreadPool to start a HTTP server
    @param served_files: Dictionary of the files to be served. Dictionary format:
        {"/base_version": "/.autodirect/sw_system_release/sonic/201811-latest-sonic-mellanox.bin",
         "/target_version": "/.autodirect/sw_system_release/sonic/master-latest-sonic-mellanox.bin"}
    """
    logger.info("Try to serve files over HTTP:\n%s" % json.dumps(served_files, indent=4))
    ImageHTTPRequestHandler.served_files = served_files
    httpd = BaseHTTPServer.HTTPServer(("", 0), ImageHTTPRequestHandler)

    def run_httpd():
        httpd.serve_forever()

    pool = ThreadPool()
    pool.apply_async(run_httpd)
    time.sleep(5)  # The http server needs couple of seconds to startup
    logger.info("Started HTTP server on STM to serve files %s over http://%s:%s" %
                (str(served_files), httpd.server_name, httpd.server_port))
    return httpd


def prepare_images(base_version, target_version, serve_file):
    """
    Method which starts HTTP server if need and share image via HTTP
    """
    image_urls = {"base_version": "", "target_version": ""}

    if serve_file:
        serve_files_over_http(base_version, target_version, image_urls)
    else:
        set_image_path(base_version, "base_version", image_urls)
        if target_version:
            set_image_path(target_version, "target_version", image_urls)

    for image_role in image_urls:
        logger.info('Image {image_role} URL is:{image}'.format(image_role=image_role, image=image_urls[image_role]))
    return image_urls


def serve_files_over_http(base_version, target_version, image_urls):
    served_files = {}
    verify_file_exists(base_version)
    served_files["/base_version"] = base_version
    if target_version:
        verify_file_exists(target_version)
        served_files["/target_version"] = target_version

    httpd = start_http_server(served_files)
    http_base_url = "http://{}:{}".format(httpd.server_name, httpd.server_port)
    for served_file_path in served_files:
        image_urls[served_file_path.lstrip("/")] = http_base_url + served_file_path


def set_image_path(image_path, image_key, image_dict):
    if is_url(image_path):
        path = image_path
    else:
        verify_file_exists(image_path)
        logger.info("Image {} path is:{}".format(image_key, os.path.realpath(image_path)))
        path = get_installer_url_from_nfs_path(image_path)
    image_dict[image_key] = path


def is_url(image_path):
    return re.match('https?://', image_path)


def get_installer_url_from_nfs_path(image_path):
    http_base = 'http://fit69.mtl.labs.mlnx'
    verify_image_stored_in_nfs(image_path)
    image_path = get_image_path_in_new_nfs_dir(image_path)
    return "{http_base}{image_path}".format(http_base=http_base, image_path=image_path)


def verify_file_exists(image_path):
    is_file = os.path.isfile(image_path)
    assert is_file, "Cannot access Image {}: no such file.".format(image_path)


def verify_image_stored_in_nfs(image_path):
    nfs_base_path = '\/auto\/|\/\.autodirect\/'
    is_located_in_nfs = re.match(r"^({nfs_base_path}).+".format(nfs_base_path=nfs_base_path), image_path)
    assert is_located_in_nfs, "The Image must be located under {nfs_base_path}".\
        format(nfs_base_path=nfs_base_path)


def get_image_path_in_new_nfs_dir(image_path):
    return re.sub(r"^\/\.autodirect\/", "/auto/", image_path)

@separate_logger
def generate_minigraph(ansible_path, mgmt_docker_engine, dut_name, sonic_topo, port_number):
    """
    Method which doing minigraph generation
    """
    with mgmt_docker_engine.cd(ansible_path):
        logger.info("Generating minigraph")
        cmd = "./testbed-cli.sh gen-mg {SWITCH}-{TOPO} lab vault".format(SWITCH=dut_name, TOPO=sonic_topo)
        if port_number:
            cmd += " -e port_number={}".format(port_number)
        logger.info("Running CMD: {}".format(cmd))
        mgmt_docker_engine.run(cmd)


@separate_logger
def recover_topology(ansible_path, mgmt_docker_engine, hypervisor_engine, dut_name, sonic_topo):
    """
    Method which doing recover for VMs and topo in case of community setup
    """
    logger.info("Recover VMs in case there are VMs down or crashed")
    with mgmt_docker_engine.cd(ansible_path):
        header_line = mgmt_docker_engine.run("head -n 1 ./testbed.csv").stdout.strip()
        headers = header_line.split(',')
        server_index = headers.index('server')
        vms_number = mgmt_docker_engine.run(
            "grep {SWITCH}-{TOPO}, ./testbed.csv | cut -f{SERVER_INDEX} -d',' | grep -o -E [0-9]+"
            .format(SWITCH=dut_name, TOPO=sonic_topo, SERVER_INDEX=server_index + 1)).stdout.strip()
        vms_ping_res = mgmt_docker_engine.run("ansible -m ping -i veos vms_{}".format(vms_number), warn=True)
    if vms_ping_res.failed:
        down_vms = []
        for line in vms_ping_res.stdout.splitlines():
            if "UNREACHABLE" in line:
                try:
                    down_vm = re.search("VM[0-9]+", line).group(0)
                    down_vms.append(down_vm)
                except AttributeError as e:
                    logger.error("Unable to extract VM name from line: %s" % line)
                    logger.error("Exception: %s" + repr(e))

        hypervisor_engine.run("virsh list")
        for vm in down_vms:
            hypervisor_engine.run("virsh destroy {}".format(vm), warn=True)
        hypervisor_engine.run("virsh list")

        with mgmt_docker_engine.cd(ansible_path):
            cmd = "./testbed-cli.sh start-vms server_{} vault".format(vms_number)
            logger.info("Running CMD: {}".format(cmd))
            mgmt_docker_engine.run(cmd)

    logger.info("Continue preparing topology for SONiC testing")
    with mgmt_docker_engine.cd(ansible_path):
        logger.info("Remove all topologies. This may increase a chance to deploy a new one successful")
        for topology in constants.TOPO_ARRAY:
            logger.info("Remove topo {}".format(topology))
            cmd = "./testbed-cli.sh remove-topo {SWITCH}-{TOPO} vault".format(SWITCH=dut_name, TOPO=topology)
            logger.info("Running CMD: {}".format(cmd))
            mgmt_docker_engine.run(cmd, warn=True)

        logger.info("Add topology")
        cmd = "./testbed-cli.sh add-topo {SWITCH}-{TOPO} vault".format(SWITCH=dut_name, TOPO=sonic_topo)
        logger.info("Running CMD: {}".format(cmd))
        mgmt_docker_engine.run(cmd)


@separate_logger
def install_image(ansible_path, mgmt_docker_engine, dut_name, sonic_topo, image_url, upgrade_type='onie'):
    """
    Method which doing installation of image on DUT via ONIE or via SONiC cli
    """
    logger.info("Upgrade switch using SONiC upgrade playbook using upgrade type: {}".format(upgrade_type))
    with mgmt_docker_engine.cd(ansible_path):
        cmd = 'ansible-playbook -i inventory --limit {dut}-{topo} upgrade_sonic.yml ' \
              '-e "upgrade_type={upgrade_type}" -e "image_url={image_url}" -vvvvv'.format(dut=dut_name,
                                                                                          topo=sonic_topo,
                                                                                          upgrade_type=upgrade_type,
                                                                                          image_url=image_url)
        logger.info("Running CMD: {}".format(cmd))
        mgmt_docker_engine.run(cmd)


@separate_logger
def deploy_minigprah(ansible_path, mgmt_docker_engine, dut_name, sonic_topo, recover_by_reboot):
    """
    Method which doing minigraph deploy on DUT
    """
    with mgmt_docker_engine.cd(ansible_path):
        cmd = "ansible-playbook -i inventory --limit {SWITCH}-{TOPO} deploy_minigraph.yml " \
              "-e dut_minigraph={SWITCH}.{TOPO}.xml -b -vvv".format(SWITCH=dut_name, TOPO=sonic_topo)
        logger.info("Running CMD: {}".format(cmd))
        if recover_by_reboot:
            try:
                logger.info("Deploying minigraph")
                return mgmt_docker_engine.run(cmd)
            except Exception:
                logger.warning("Failed in Deploying minigraph")
                logger.warning("Performing a reboot and retrying")
                reboot_validation(ansible_path, mgmt_docker_engine, "reboot", dut_name, sonic_topo)
        logger.info("Deploying minigraph")
        return mgmt_docker_engine.run(cmd)


@separate_logger
def apply_canonical_config(topo, dut_name, ngts_engine):
    """
    Method which call script: sonic_split_configuration_script.py with args
    """
    setup_name_index = -2
    sonic_mgmt_path = '/workspace/{setup_name}/sonic-mgmt/'
    setup_name = topo.split('/')[setup_name_index]
    dut_ip = socket.gethostbyname(dut_name)
    sonic_mgmt_dir = sonic_mgmt_path.format(setup_name=setup_name)
    cmd = "PYTHONPATH=/devts:{sonic_mgmt_dir} python3 {sonic_mgmt_dir}ngts/scripts/sonic_split_configuration_script.py --switch {dut_ip} " \
          "--setup_name {setup_name} --noga".format(sonic_mgmt_dir=sonic_mgmt_dir, dut_ip=dut_ip, setup_name=setup_name)

    res = ngts_engine.run(cmd)
    if res.failed:
        raise Exception(
            "Encountered an error during application of configuration files on the DUT, please review the - error logs")
    logger.info("apply_canonical_config finished successfully")

@separate_logger
def post_install_check(ansible_path, mgmt_docker_engine, dut_name, sonic_topo):
    """
    Method which doing post install checks: check ports status, check dockers status, etc.
    """
    with mgmt_docker_engine.cd(ansible_path):
        post_install_validation = "ansible-playbook -i inventory --limit {SWITCH}-{TOPO} post_upgrade_check.yml -e topo={TOPO} " \
              "-b -vvv".format(SWITCH=dut_name, TOPO=sonic_topo)
        logger.info("Performing post-install validation by running: {}".format(post_install_validation))
        return mgmt_docker_engine.run(post_install_validation)


@separate_logger
def reboot_validation(ansible_path, mgmt_docker_engine, reboot, dut_name, sonic_topo):
    """
    Method which doing reboot validation
    """
    if reboot == "random":
        reboot_type = random.choice(constants.REBOOT_TYPES.values())
    else:
        reboot_type = constants.REBOOT_TYPES[reboot]

    with mgmt_docker_engine.cd(ansible_path):
        logger.info("Running reboot type: {}".format(reboot_type))
        reboot_res = mgmt_docker_engine.run("ansible-playbook test_sonic.yml -i inventory --limit {SWITCH}-{TOPO} \
                                     -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} \
                                     -e testcase_name=reboot -e reboot_type={REBOOT_TYPE} -vvv".format(SWITCH=dut_name,
                                                                                                       TOPO=sonic_topo,
                                                                                                       REBOOT_TYPE=reboot_type),
                                            warn=True)
        logger.warning("reboot type: {} failed".format(reboot_type))
        logger.debug("reboot type {} failure results: {}".format(reboot_type, reboot_res))
        logger.info("Running reboot type: {} after {} failed".format(constants.REBOOT_TYPES["reboot"], reboot_type))
        if reboot_res.failed and reboot != constants.REBOOT_TYPES["reboot"]:
           reboot_res = mgmt_docker_engine.run("ansible-playbook test_sonic.yml -i inventory --limit {SWITCH}-{TOPO} \
                            -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} -e testcase_name=reboot \
                            -e reboot_type={REBOOT_TYPE} -vvv".format(SWITCH=dut_name, TOPO=sonic_topo,
                                                                      REBOOT_TYPE=constants.REBOOT_TYPES["reboot"]),
                                   warn=True)
           logger.info("reboot type: {} result is {}"
                       .format(constants.REBOOT_TYPES["reboot"], reboot_res))


@separate_logger
def install_wjh(ansible_path, mgmt_docker_engine, dut_name, sonic_topo, wjh_deb_url):
    """
    Method which doing WJH installation on DUT
    """
    logger.info("Starting installation of SONiC what-just-happened")
    with mgmt_docker_engine.cd(ansible_path):
        mgmt_docker_engine.run("ansible-playbook install_wjh.yml -i inventory --limit {SWITCH}-{TOPO} \
                        -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} \
                        -e wjh_deb_url={PATH} -vvv".format(SWITCH=dut_name, TOPO=sonic_topo,
                                                           PATH=wjh_deb_url))


def main():

    logger.info("Deploy SONiC testing topology and upgrade switch")

    args = _parse_args()

    workspace_path = args.workspace_path
    repo_name = args.repo_name
    repo_path = os.path.join(workspace_path, repo_name)
    ansible_path = os.path.join(repo_path, "ansible")
    logger.setLevel(args.log_level)

    topo = parse_topology(args.topo)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)
    hypervisor_device = topo.get_device_by_topology_id(constants.TEST_SERVER_DEVICE_ID)

    mgmt_docker_engine = Connection(sonic_mgmt_device.BASE_IP, user=sonic_mgmt_device.USERS[0].USERNAME,
                                    config=Config(overrides={"run": {"echo": True}}),
                                    connect_kwargs={"password": sonic_mgmt_device.USERS[0].PASSWORD})

    hypervisor_engine = Connection(hypervisor_device.BASE_IP, user=hypervisor_device.USERS[0].USERNAME,
                                   config=Config(overrides={"run": {"echo": True}}),
                                   connect_kwargs={"password": hypervisor_device.USERS[0].PASSWORD})

    image_urls = prepare_images(args.base_version, args.target_version, args.serve_files)

    if args.upgrade_only and re.match(r"^(no|false)$", args.upgrade_only, re.I):
        recover_topology(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine,
                         hypervisor_engine=hypervisor_engine, dut_name=args.dut_name, sonic_topo=args.sonic_topo)

    install_image(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                  sonic_topo=args.sonic_topo, image_url=image_urls["base_version"], upgrade_type=args.upgrade_type)

    generate_minigraph(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                       sonic_topo=args.sonic_topo, port_number=args.port_number)

    # For Canonical setups do not apply minigraph - just apply configs from shared location
    if args.sonic_topo == 'ptf-any':
        ngts_device = topo.get_device_by_topology_id(constants.NGTS_DEVICE_ID)
        ngts_docker_engine = Connection(ngts_device.BASE_IP, user=ngts_device.USERS[0].USERNAME,
                                        config=Config(overrides={"run": {"echo": True}}),
                                        connect_kwargs={"password": ngts_device.USERS[0].PASSWORD})
        apply_canonical_config(topo=args.topo, dut_name=args.dut_name, ngts_engine=ngts_docker_engine)
    else:
        deploy_minigprah(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                         sonic_topo=args.sonic_topo, recover_by_reboot=args.recover_by_reboot)

    post_install_check(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                       sonic_topo=args.sonic_topo)

    if image_urls["target_version"]:
        logger.info("Target version is defined, upgrade switch again to the target version.")

        install_image(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                      sonic_topo=args.sonic_topo, image_url=image_urls["target_version"], upgrade_type='sonic')

        post_install_check(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                           sonic_topo=args.sonic_topo)

    if args.reboot and args.reboot != "no":
        reboot_validation(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, reboot=args.reboot,
                          dut_name=args.dut_name, sonic_topo=args.sonic_topo)

    if args.wjh_deb_url:
        install_wjh(ansible_path=ansible_path, mgmt_docker_engine=mgmt_docker_engine, dut_name=args.dut_name,
                    sonic_topo=args.sonic_topo, wjh_deb_url=args.wjh_deb_url)


if __name__ == "__main__":
    main()
