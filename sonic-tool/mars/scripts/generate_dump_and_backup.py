#!/usr/bin/env python
"""
After regression testing is done, this script should be executed to generate dump on DUT and backup the dump to netdisk.

This script is executed on the STM node. It establishes SSH connection to the DUT and run commands on it. Purpose is to
generate dump and back up the dump for later analysis.
"""

# Builtin libs
import argparse
import os

# Third-party libs
from fabric import Config
from fabric import Connection
from fabric.transfer import Transfer

# Home-brew libs
from lib import constants
from lib.utils import parse_topology, get_logger

logger = get_logger("DumpBackup")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--since", nargs="?", dest="since", default="12 hours ago",
                        help="Collect logs and core files since given date. Default: '12 hours ago'")
    parser.add_argument("--dest", nargs="?", dest="dest",
                        help="Destination folder for backup dump. Default: use lib/constants.DUT_LOG_BACKUP_PATH")
    parser.add_argument("--session-id", dest="session_id", help="Current MARS session_id")
    return parser.parse_args()


def main():

    args = _parse_args()

    backup_location = args.dest if args.dest else constants.DUT_LOG_BACKUP_PATH
    session_id = args.session_id

    topo = parse_topology(args.topo)
    dut_device = topo.get_device_by_topology_id(constants.DUT_DEVICE_ID)

    dut = Connection(dut_device.BASE_IP, user=dut_device.USERS[0].USERNAME,
                     config=Config(overrides={"run": {"echo": True}}),
                     connect_kwargs={"password": dut_device.USERS[0].PASSWORD})

    logger.info("Generating dump on sonic")
    res = dut.sudo("generate_dump -s '%s'" % args.since)
    dump_file = res.stdout.strip().splitlines()[-1]
    logger.info("Generated dump %s on DUT" % dump_file)

    hostname = dut.run("hostname").stdout.strip()

    backup_folder = os.path.join(backup_location, hostname + "_setup")
    if not os.path.isdir(backup_folder):
        dut.local("mkdir %s" % backup_folder)

    session_folder = os.path.join(backup_folder, session_id)
    if not os.path.isdir(session_folder):
        dut.local("mkdir %s" % session_folder)

    logger.info("Backup the generated dump to %s" % session_folder)
    dut_scp = Transfer(dut)
    dut_scp.get(dump_file, local=os.path.join(session_folder, os.path.basename(dump_file)))

    logger.info("################### DONE ###################")


if __name__ == "__main__":
    main()
