#!/usr/bin/env python
"""
Update configuration files inside sonic-mgmt repo with entries for new setups obtained from Noga.

This script is executed on the STM node. It establishes SSH connection to the test server and
run command on it. It uses the following script - 'sonic-tool/sonic_ngts/scripts/update_sonic_mgmt.py'
"""

import argparse
import os

from fabric import Config
from fabric import Connection

from lib import constants
from lib.utils import parse_topology, get_logger

logger = get_logger("TuneConfigs")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--dut-name", required=True, dest="dut_name", help="The DUT name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo on sonic-mgmt docker container.")
    return parser.parse_args()


def get_topo_dir(topo_file):
    prefix = os.path.split(os.path.normpath(topo_file))[0]
    topo_dir_path = prefix[prefix.find("conf/topo"): ]

    return os.path.join("/auto/sw_regression/system/SONIC/MARS", topo_dir_path)


if __name__ == "__main__":
    logger.info("Update sonic-mgmt inventory files with new setup info to be able to run image deploy")

    args = _parse_args()

    workspace_path = args.workspace_path
    sonic_mgmt_repo_name = "sonic-mgmt"
    sonic_tool_repo_name = "sonic-tool"
    sonic_mgmt_repo_path = os.path.join(workspace_path, sonic_mgmt_repo_name)
    sonic_tool_repo_path = os.path.join(workspace_path, sonic_tool_repo_name)

    topo_file = args.topo
    topo_obj = parse_topology(topo_file)

    sonic_mgmt_container_info = topo_obj.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)
    print('sonic_mgmt_repo_path : {}'.format(sonic_mgmt_repo_path))

    sonic_mgmt_container = Connection(sonic_mgmt_container_info.BASE_IP, user=sonic_mgmt_container_info.USERS[0].USERNAME,
                                      config=Config(overrides={"run": {"echo": True}}),
                                      connect_kwargs={"password": sonic_mgmt_container_info.USERS[0].PASSWORD})
    cmd = "PYTHONPATH={mgmt_repo}/sonic-tool/sonic_ngts {ngts_path} {mgmt_repo}/sonic-tool/sonic_ngts/scripts/update_sonic_mgmt.py --dut=\"{dut}\" --mgmt_repo=\"{mgmt_repo}\" \
            --topo_dir=\"{topo_dir}\"".format(ngts_path=constants.NGTS_PATH_PYTHON, dut=args.dut_name, mgmt_repo=sonic_mgmt_repo_path,
                                              topo_dir=get_topo_dir(topo_file))
    sonic_mgmt_container.run(cmd)
