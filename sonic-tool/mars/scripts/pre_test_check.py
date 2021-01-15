# Builtin libs
import argparse
import os

# Third-party libs
import yaml
from fabric import Config
from fabric import Connection

# Home-brew libs
from lib import constants
from lib.devices import SonicDevice
from lib.utils import parse_topology, get_logger

logger = get_logger("PreTestCheck")


def _parse_args():
    # Parse arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--topo", dest="topo", help="Path to the MARS topology configuration file")
    parser.add_argument("--test-name", required=True, dest="test_name",
                        help="Specify the test name in case file, <Test><name>this_name</name></Test>")
    parser.add_argument("--sonic-topo", required=True, dest="sonic_topo",
                        help="The topo for SONiC testing, for example: t0, t1, t1-lag, ptf32, ...")
    parser.add_argument("--repo-name", dest="repo_name", help="Specify the sonic-mgmt repository name")
    parser.add_argument("--workspace-path", dest="workspace_path",
                        help="Specify the location of sonic-mgmt repo")
    return parser.parse_args()


def topology_check(conn, test_name, topology, repo_path):
    """
    @summary: Check if the current test supports the current topology.
    @param conn: Fabric connection to the sonic-mgmt container.
    @param test_name: Name of the current test.
    @param topology: The current topology.
    @param repo_path: Path of the sonic-mgmt repo.
    """
    testcases_path = os.path.join(repo_path, "ansible/roles/test/vars/testcases.yml")

    testcases = yaml.safe_load(conn.run("cat %s" % testcases_path).stdout.strip())

    try:
        if topology not in testcases["testcases"][test_name]["topologies"]:
            # The dynamic tag feature of MARS is used here.
            # Reference: https://wikinox.mellanox.com/pages/viewpage.action?pageId=57770047
            # The trick is to print something with format "@@mars_ignore_tag@@: my_dynamic_tag"
            # MARS would be able to match this magic pattern in logs and generate a dynamic tag.
            # When a test does not support the current topology, the case should be skipped. Otherwise the checking
            # in the script will fail the test and give a false alarm. So, it is better to check topology in pre-test
            # block and skip the test if the topology is not applicable.
            # My implementation is to generate a tag named TAG_TOPOLOGY_NOT_APPLICABLE in pre-test block. In the DB
            # definition file, add below to <Case> definition:
            #     <Case>
            #         <ignore>
            #             <ignore_by_tag> TAG_TOPOLOGY_NOT_APPLICABLE </ignore_by_tag>
            #         </ignore>
            #     </Case>
            # This implementation also required the case file to have correct test name. The test name defined in
            # <Test><name></name><Test> must be the test case name in the ansible/roles/test/vars/testcases.yml.
            logger.info("@@mars_ignore_tag@@: TAG_TOPOLOGY_NOT_APPLICABLE")
    except KeyError as e:
        logger.error("Unable to check current topology against supported topologies of current test.")
        logger.error("Exception: %s" % repr(e))


def issu_check(dut):
    """
    @summary: Check if ISSU is enabled on the device. If yes, print ignore tag TAG_ISSU_DISABLED
    @param dut: Instance of SonicDevice.
    """
    if not dut.issu_enabled:
        logger.info("@@mars_ignore_tag@@: TAG_ISSU_DISABLED")


if __name__ == "__main__":
    args = _parse_args()

    repo_path = os.path.join(args.workspace_path, args.repo_name)

    topo = parse_topology(args.topo)
    dut_device = topo.get_device_by_topology_id(constants.DUT_DEVICE_ID)
    sonic_mgmt_device = topo.get_device_by_topology_id(constants.SONIC_MGMT_DEVICE_ID)

    dut = SonicDevice(dut_device.BASE_IP, dut_device.USERS[0].USERNAME, dut_device.USERS[0].PASSWORD)
    sonic_mgmt = Connection(sonic_mgmt_device.BASE_IP, user=sonic_mgmt_device.USERS[0].USERNAME,
                            config=Config(overrides={"run": {"echo": True}}),
                            connect_kwargs={"password": sonic_mgmt_device.USERS[0].PASSWORD})
    topology_check(sonic_mgmt, args.test_name, args.sonic_topo, repo_path)

    issu_check(dut)
