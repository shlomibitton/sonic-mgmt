#!/usr/bin/env python
"""
Teardown SONiC extensions.

This script is executed on the STM node. It establishes SSH connection to the sonic-mgmt docker container (Player) and
run commands on it. Purpose is to teardown SONiC extensions.
"""

# Builtin libs
import argparse
import os
import re

# Third-party libs
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.utils import parse_topology


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--dut-name", required=True, dest="dut_name", help="The DUT name")
    parser.add_argument("--sonic-topo", required=True, dest="sonic_topo",
                        help="The topo for SONiC testing, for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--repo-name", dest="repo_name", help="Specify the sonic-mgmt repository name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo on sonic-mgmt docker container.")
    parser.add_argument("--wjh-package-name", help="Specify WJH package name",
                        dest="wjh_package_name", default="")
    return parser.parse_args()


def main():
    args = _parse_args()

    topo = parse_topology(args.topo)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)

    sonic_mgmt = Connection(sonic_mgmt_device.BASE_IP, user=sonic_mgmt_device.USERS[0].USERNAME,
                            config=Config(overrides={"run": {"echo": True}}),
                            connect_kwargs={"password": sonic_mgmt_device.USERS[0].PASSWORD})

    workspace_path = args.workspace_path
    repo_name = args.repo_name
    repo_path = os.path.join(workspace_path, repo_name)
    ansible_path = os.path.join(repo_path, "ansible")

    if args.wjh_package_name:
        with sonic_mgmt.cd(ansible_path):
            sonic_mgmt.run("ansible-playbook teardown_extensions.yml -i inventory --limit {SWITCH}-{TOPO} \
                                            -e testbed_name={SWITCH}-{TOPO} -e testbed_type={TOPO} \
                                            -e wjh_package_name={NAME} -vvv"
                                            .format(SWITCH=args.dut_name, TOPO=args.sonic_topo, NAME=args.wjh_package_name))


if __name__ == "__main__":
    main()
