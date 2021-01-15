# Builtin libs
import argparse
import time

# Third-party libs
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.devices import SonicDevice
from lib.utils import parse_topology, get_logger

logger = get_logger("ReconfigureDUT")
CONFIG_RELOAD_DELAY = 600

def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--dut-name", required=True, dest="dut_name",
                        help="Name of the dut")
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--preset", required=True, dest="preset",
                        help="The preset for SONiC configuration, for example: t1, l2")
    parser.add_argument("--hwsku", dest="hwsku", help="Specify the DUT's HWSKU")

    return parser.parse_args()


if __name__ == "__main__":
    args = _parse_args()

    topo = parse_topology(args.topo)

    dut_device = topo.get_device_by_topology_id(constants.DUT_DEVICE_ID)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)

    dut = SonicDevice(dut_device.BASE_IP, dut_device.USERS[0].USERNAME, dut_device.USERS[0].PASSWORD)

    command = "sudo sonic-cfggen -H -k {} -p --preset {} > /tmp/config_db.json".format(args.hwsku, args.preset)
    dut.run(command)
    dut.run("sudo cp /tmp/config_db.json /etc/sonic/config_db.json")
    res = dut.run("sudo config reload -y")


    if res.exited:
        logger.error("The config reload failed!")
    else:
        time.sleep(CONFIG_RELOAD_DELAY)