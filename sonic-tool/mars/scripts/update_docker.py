#!/usr/bin/env python
"""
Prepare the SONiC testing topology.

This script is executed on the STM node. It establishes SSH connection to the hypervisor (Player) and
run commands on it. Purpose is to prepare the SONiC testing topology using the testbed-cli.sh tool.
"""

# Builtin libs
import argparse
import json
import sys
import time
import traceback
import os
import pathlib
import random
from retry import retry

# Third-party libs
from fabric import Config
from fabric import Connection
from invoke.exceptions import UnexpectedExit

# Home-brew libs
from lib import constants
from lib.utils import parse_topology, get_logger
sys.path.append(str(os.path.join(str(pathlib.Path(__file__).parent.absolute()), "..", "..", "sonic_ngts")))
from infra.constants.constants import LinuxConsts
logger = get_logger("UpdateDocker")

CONTAINER_IFACE = "eth1"
DOCKER_BRIDGE_IFACE = "docker0"


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--dut-name", nargs="?", dest="dut_name", help="The DUT name")
    parser.add_argument("--registry-url", nargs="?", dest="registry_url",
                        help="Docker registry URL. Default: use lib/constants.DOCKER_REGISTRY")
    parser.add_argument("--docker-name", nargs="?", default="sonic-mgmt", dest="docker_name",
                        help="Name of the sonic-mgmt docker. Default: 'sonic-mgmt'")
    parser.add_argument("--docker-tag", nargs="?", default="latest", dest="docker_tag",
                        help="Docker image tag. Default: 'latest'")
    parser.add_argument("--delete_container", nargs="?", dest="delete_container", default=False,
                        help="Force container removal and recreation, even if a docker container with the expected "
                             "image is already running.")
    return parser.parse_args()


def inspect_container(conn, image_name, image_tag, container_name):
    """
    @summary: Inspect the specified docker image and container, gather some basic information.
    @param conn: Fabric connection to the host server.
    @param image_name: Docker image name.
    @param image_tag: Docker image tag.
    @param container_name: Docker container name to be inspected.
    @return: Returns inspection result in a dictionary.
    """
    res = {
        "container_exists": None,
        "container_running": None,
        "container_matches_image": None,
        "image_exists": None
    }

    res["container_exists"] = conn.run("docker ps -a -f name=%s$ --format '{{.Names}}'" % container_name).\
        stdout.strip() == container_name

    image_id = conn.run("docker images --no-trunc %s:%s --format '{{.ID}}'" % (image_name, image_tag)).stdout.strip()
    if len(image_id) > 0:
        res["image_exists"] = True

    if res["container_exists"]:
        container_info = json.loads(conn.run("docker inspect {}".format(container_name)).stdout.strip())
        try:
            res["container_running"] = container_info[0]["State"]["Running"]

            if res["image_exists"]:
                res["container_matches_image"] = image_id == container_info[0]["Image"]
        except (IndexError, KeyError) as e:
            logger.error("Failed to get container info, exception: %s" + repr(e))

    logger.info("Inspection result: %s" % json.dumps(res))
    return res


def gather_facts(conn):
    """
    @summary: Collect some basic facts of the server.
    @param conn: Fabric connection to the host server.
    @return: Returns the gathered facts in a dictionary. Returns None in case of exception.
    """
    facts = None
    try:
        default_iface = conn.run("awk '$2 == 00000000 { print $1 }' /proc/net/route").stdout.strip()
        default_iface_addr = conn.run("ip -4 addr show %s | awk '$1==\"inet\" {print $2}' | cut -d'/' -f1" %
                                      default_iface).stdout.strip()
        macvlan_iface_random_id = random.randint(0, 9999)
        macvlan_iface = "{}p{}".format(default_iface, macvlan_iface_random_id)
        container_iface = CONTAINER_IFACE
        docker_bridge_iface = DOCKER_BRIDGE_IFACE
        docker_bridge_addr = conn.run("ip -4 addr show %s | awk '$1==\"inet\" {print $2}' | cut -d'/' -f1" %
                                      docker_bridge_iface).stdout.strip()
        facts = {
            "default_iface": default_iface,
            "default_iface_addr": default_iface_addr,
            "macvlan_iface": macvlan_iface,
            "container_iface": container_iface,
            "docker_bridge_iface": DOCKER_BRIDGE_IFACE,
            "docker_bridge_addr": docker_bridge_addr
        }
    except UnexpectedExit as e:
        logger.error("Failed to gather facts. Exception: %s" % repr(e))

    return facts


def start_container(conn, container_name, max_retries=3):
    """
    @summary: Try to start an existing container.
    @param conn: Fabric connection to the host server.
    @param container_name: Docker container name.
    @param max_retries: Max number of retries.
    @return: Returns True if starting container succeeded. Returns False if starting failed.
    """
    for i in range(max_retries):
        attempt = i + 1
        logger.info("Try to start container %s, max_retries=%d, attempt=%d" % (container_name, max_retries, attempt))
        try:
            conn.run("docker start %s" % container_name)
            logger.info("Started container %s, max_retries=%d, attempt=%d" % (container_name, max_retries, attempt))
            return True
        except UnexpectedExit as e:
            logger.error("Starting container exception: %s" % repr(e))
        logger.error("Starting container %s failed, max_retries=%d, attempt=%d" %
                     (container_name, max_retries, attempt))
        time.sleep(2)

    logger.error("Failed to start container %s after tried %d times." % (container_name, max_retries))
    return False


def create_and_start_container(conn, image_name, image_tag, container_name, mac_address, facts):
    """
    @summary: Create and start specified container from specified image
    @param conn: Fabric connection to the host server
    @param image_name: Docker image name
    @param image_tag: Docker image tag
    @param container_name: Docker container name to be started
    @param mac_address: MAC address of the container's management interface
    @param facts: Basic facts of the host server. Collected by the function gather_facts.
    """
    container_iface_mac = mac_address

    container_mountpoints_dict = constants.SONIC_MGMT_MOUNTPOINTS.items()
    container_mountpoints_list = []
    for key, value in container_mountpoints_dict:
        if key == "/workspace":
            container_mountpoints_list.append("-v {}:{}:rw".format(key, value))
        else:
            container_mountpoints_list.append("-v {}:{}".format(key, value))

    container_mountpoints = " ".join(container_mountpoints_list)

    logger.info("Try to remove existing docker container anyway")
    conn.run("docker rm -f {CONTAINER_NAME}".format(CONTAINER_NAME=container_name), warn=True)

    if image_tag == "2018":
        cmd_tmplt = "docker run -d -t --cap-add=NET_ADMIN {CONTAINER_MOUNTPOINTS} \
            --name {CONTAINER_NAME} {IMAGE_NAME}:{IMAGE_TAG} start.sh"
    else:
        cmd_tmplt = "docker run -d -t --cap-add=NET_ADMIN {CONTAINER_MOUNTPOINTS} \
            --name {CONTAINER_NAME} {IMAGE_NAME}:{IMAGE_TAG} /bin/bash"
    cmd = cmd_tmplt.format(
        CONTAINER_MOUNTPOINTS=container_mountpoints,
        CONTAINER_NAME=container_name,
        IMAGE_NAME=image_name,
        IMAGE_TAG=image_tag
    )
    conn.run(cmd, warn=True)
    logger.info("Created container, wait a few seconds for it to start")
    time.sleep(5)
    logger.info("Check whether the container is started successfully.")
    container_state = json.loads(conn.run("docker inspect --format '{{json .State}}' %s" % container_name)
                                 .stdout.strip())

    if not container_state["Running"]:
        logger.error("The created container is not started, try to restart it")
        if not start_container(conn, container_name, max_retries=3):
            logger.error("Restart container failed.")
            sys.exit(1)

    validate_docker_is_up(conn, container_name)
    logger.info("Configure container after starting it")

    if not configure_docker_route(conn, container_name, container_iface_mac, facts):
        logger.error("Configure docker container failed.")
        sys.exit(1)

    if constants.DOCKER_SONIC_MGMT_IMAGE_NAME in image_name:
        logger.info("Install extra packages")
        if not install_extra_packages(conn, container_name):
            logger.error("Install extra packages failed.")
            sys.exit(1)

        logger.info("Add required configuration for installing ver_sdk tool on sonic-mgmt")
        conn.run('docker exec --user root {CONTAINER_NAME} bash -c "echo \'export PYTHONPATH=\\"/opt/ver_sdk\\":\\"\\$PYTHONPATH\\"\' >> /root/.bashrc"'
                 .format(CONTAINER_NAME=container_name))
        conn.run('docker exec --user root {CONTAINER_NAME} bash -c "echo \'export PATH=\\"/opt/ver_sdk/bin\\":\\"\\$PATH\\"\' >> /root/.bashrc"'
                 .format(CONTAINER_NAME=container_name))

        if image_tag != "2018":
            # Some of our Jenkins node are still using old sonic-mgmt image. I added tag "2018" for this old version in
            # our internal docker registry. The latest sonic-mgmt image is different with the "2018" image:
            # * By default, root SSH login is disabled.
            # * The default root password is no longer "12345".
            # When the sonic-mgmt image is not the "2018" version, we need to enable root SSH login and reset password.
            logger.info("Extra configuration for root SSH login")
            conn.run("docker exec {CONTAINER_NAME} bash -c \"sudo "
                     "sed -i -E 's/^#?PermitRootLogin.*$/PermitRootLogin yes/g' /etc/ssh/sshd_config\""
                     .format(CONTAINER_NAME=container_name))
            conn.run('docker exec {CONTAINER_NAME} bash -c "sudo /etc/init.d/ssh restart"'
                     .format(CONTAINER_NAME=container_name))
            conn.run("docker exec --user root {CONTAINER_NAME} bash -c \"echo 'root:12345' | chpasswd\""
                     .format(CONTAINER_NAME=container_name))


@retry(Exception, tries=3, delay=10)
def validate_docker_is_up(conn, container_name):
    """
    This function will run a dummy echo command on docker containers,
    In order to validate the container is really up.
    This function purpose is to avoid failures,
    when configuring the docker (during configure_docker_route) and the docker is not up yet.
    :param conn: Fabric connection to the host server
    :param container_name: Docker container name that was started
    :return: raise Exception if docker is not up after all retries failed
    """
    logger.info("Validating docker {CONTAINER_NAME} is up by running dummy echo cmd"
                .format(CONTAINER_NAME=container_name))
    conn.run("docker exec {CONTAINER_NAME} bash -c \"echo \"UP\"\"".format(CONTAINER_NAME=container_name))


def configure_docker_route(conn, container_name, mac_address, facts):
    """
    @summary: Configure docker container.

    For the sonic-mgmt container to get IP address from LAB DHCP server, we need to create a interface on it and run
    'dhclient' to get IP address. Also some route configurations are required.

    @param conn: Fabric connection to the host server
    @param container_name: Docker container name to be started
    @param mac_address: MAC address of the container's management interface
    @param facts: Basic facts of the host server. Collected by the function gather_facts.
    @return: Returns True if configurations are successful. In case of exception, return False.
    """

    try:
        logger.info("Try to configure route and execute dhclient on container")
        default_iface = facts["default_iface"]
        macvlan_iface = facts["macvlan_iface"]
        default_iface_addr = facts["default_iface_addr"]
        container_iface = facts["container_iface"]
        docker_bridge_addr = facts["docker_bridge_addr"]

        logger.info("Get container PID")
        container_pid = conn.run("docker inspect --format '{{.State.Pid}}' %s" % container_name).stdout.strip()

        conn.run("ip link add {MACVLAN_IFACE} link {DEFAULT_IFACE} type macvlan mode bridge"
                 .format(MACVLAN_IFACE=macvlan_iface, DEFAULT_IFACE=default_iface), warn=True)
        conn.run("ip link set dev {MACVLAN_IFACE} netns {CONTAINER_PID}"
                 .format(MACVLAN_IFACE=macvlan_iface, CONTAINER_PID=container_pid))
        conn.run('docker exec {CONTAINER_NAME} bash -c "\
                  sudo ip link set dev {MACVLAN_IFACE} name {CONTAINER_IFACE} && \
                  sudo ip link set dev {CONTAINER_IFACE} up && \
                  sudo ip link set dev {CONTAINER_IFACE} address {CONTAINER_IFACE_MAC}"'
                 .format(CONTAINER_NAME=container_name, MACVLAN_IFACE=macvlan_iface,
                         CONTAINER_IFACE=container_iface, CONTAINER_IFACE_MAC=mac_address))

        conn.run('docker exec {CONTAINER_NAME} bash -c "sudo ip route del default"'
                 .format(CONTAINER_NAME=container_name))
        conn.run('docker exec {CONTAINER_NAME} bash -c "sudo dhclient {CONTAINER_IFACE}"'
                 .format(CONTAINER_NAME=container_name, CONTAINER_IFACE=container_iface))
        conn.run('docker exec {CONTAINER_NAME} bash -c "\
                  sudo ip route add {DEFAULT_IFACE_ADDR} via {DOCKER_BRIDGE_ADDR} dev eth0"'
                 .format(CONTAINER_NAME=container_name, DEFAULT_IFACE_ADDR=default_iface_addr,
                         DOCKER_BRIDGE_ADDR=docker_bridge_addr))

        conn.run('docker exec {CONTAINER_NAME} bash -c "sudo /etc/init.d/ssh restart"'
                 .format(CONTAINER_NAME=container_name))

        logger.info("Successfully configured route and executed dhclient on container")
        return True
    except UnexpectedExit as e:
        logger.error("Exception: %s" % repr(e))
        logger.error("Configure route & dhclient on container failed.")
        return False


def install_extra_packages(conn, container_name):
    """
    @summary: Install extra packages in the docker container.

    @param conn: Fabric connection to the host server
    @param container_name: Docker container name to be started
    @return: Returns True if installation is successful. Otherwise, return False
    """
    try:
        logger.info("Install extra apt packages")
        conn.run('docker exec {CONTAINER_NAME} bash -c "sudo apt-get update"'.format(CONTAINER_NAME=container_name))
        conn.run('docker exec {CONTAINER_NAME} bash -c "sudo apt-get install snmp -y"'
                 .format(CONTAINER_NAME=container_name))
        logger.info("Installed extra apt packages")
        return True
    except UnexpectedExit as e:
        logger.error("Exception: %s" % repr(e))
        logger.error("Install extra packages failed")
        return False


def cleanup_dangling_docker_images(test_server):
    """
    @summary:
     When running docker system prune -a, it will remove both unused and dangling images.
     Therefore any images being used in a container,
     whether they have been exited or currently running, will NOT be affected.
    """
    test_server.run("docker system prune --all -f", warn=True)


def main():

    args = _parse_args()

    registry_url = constants.DOCKER_REGISTRY
    logger.info("Default registry_url=%s" % registry_url)
    if args.registry_url:
        registry_url = args.registry_url
        logger.info("Override default registry_url value, now registry_url=%s" % registry_url)

    docker_tag = args.docker_tag
    docker_name = args.docker_name
    if args.dut_name:
        container_name = '{}_{}'.format(args.dut_name, docker_name)
    else:
        container_name = docker_name

    topo = parse_topology(args.topo)
    test_server_device = topo.get_device_by_topology_id(constants.TEST_SERVER_DEVICE_ID)

    if constants.DOCKER_NGTS_IMAGE_NAME in docker_name:
        docker_host = topo.get_device_by_topology_id(constants.NGTS_DEVICE_ID)
    else:
        docker_host = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)
    mac = docker_host.MAC_ADDRESS

    test_server = Connection(test_server_device.BASE_IP, user=test_server_device.USERS[0].USERNAME,
                             config=Config(overrides={"run": {"echo": True}}),
                             connect_kwargs={"password": test_server_device.USERS[0].PASSWORD})

    facts = gather_facts(test_server)
    if not facts:
        logger.error("Something wrong with gathering basic facts. Please check the test server")
        sys.exit(1)

    logger.info("Pull docker image to ensure that it is up to date")
    test_server.run("docker pull {}/{}:{}".format(registry_url, docker_name, docker_tag))

    logger.info("Check current docker container and image status")
    inspect_res = inspect_container(test_server, "{}/{}".format(registry_url, docker_name), docker_tag, container_name)

    if not inspect_res["image_exists"]:
        logger.error("No docker image. Please check using commands:")
        logger.error("    curl -X GET http://{}/v2/_catalog".format(registry_url, docker_name))
        logger.error("    curl -X GET http://{}/v2/{}/tags/list".format(registry_url, docker_name))
        sys.exit(1)

    delete_container_required = args.delete_container
    if not delete_container_required:
        if inspect_res["container_matches_image"]:
            if inspect_res["container_running"]:
                logger.info("The {} docker container with expected image is running.".format(container_name))
                logger.info("################### DONE ###################")
                sys.exit(0)
            else:
                logger.info("The {} docker container using expected image is stopped. Try to start it")
                if start_container(test_server, container_name, max_retries=3):
                    if configure_docker_route(test_server, container_name, mac, facts):
                        logger.info("################### DONE ###################")
                        sys.exit(0)
                    else:
                        logger.error("Failed to configure routes and dhclient on container. Try to delete and re-create")
                        delete_container_required = True
                else:
                    logger.error("Starting container %s failed. Will delete it and re-create" % container_name)
                    delete_container_required = True

    if inspect_res["container_matches_image"] is False or delete_container_required:
        logger.info("Deleting container")
        test_server.run("docker rm -f {}".format(container_name), warn=True)

    logger.info("Need to create and start sonic-mgmt container")
    create_and_start_container(test_server, "{}/{}".format(registry_url, docker_name), docker_tag, container_name,
                               mac, facts)

    logger.info("Try to delete dangling docker images to save space")
    cleanup_dangling_docker_images(test_server)

    logger.info("################### DONE ###################")


if __name__ == "__main__":
    try:
        main()

    except Exception as e:
        traceback.print_exc()
        sys.exit(LinuxConsts.error_exit_code)
