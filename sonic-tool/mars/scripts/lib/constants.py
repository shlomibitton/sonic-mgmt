
SONIC_MARS_BASE_PATH = "/.autodirect/sw_regression/system/SONIC/MARS"

SONIC_MGMT_DEVICE_ID = "SONIC_MGMT"
NGTS_PATH_PYTEST = "/ngts_venv/bin/pytest"
NGTS_PATH_PYTHON = "/ngts_venv/bin/python"
TEST_SERVER_DEVICE_ID = "TEST_SERVER"
NGTS_DEVICE_ID = "NGTS"
DUT_DEVICE_ID = "DUT"

DOCKER_SONIC_MGMT_IMAGE_NAME = "docker-sonic-mgmt"
DOCKER_NGTS_IMAGE_NAME = "docker-ngts"

SONIC_MGMT_REPO_URL = "http://10.7.77.140:8080/switchx/sonic/sonic-mgmt"
SONIC_MGMT_MOUNTPOINTS = {
    '/.autodirect/mswg/projects': '/.autodirect/mswg/projects',
    '/auto/sw_system_project': '/auto/sw_system_project',
    '/auto/sw_system_release': '/auto/sw_system_release',
    '/auto/sw_regression/system/SONIC/MARS': '/auto/sw_regression/system/SONIC/MARS',
    '/workspace': '/workspace',
    '/.autodirect/LIT/SCRIPTS': '/.autodirect/LIT/SCRIPTS'
}

VER_SDK_PATH = "/opt/ver_sdk"
EXTRA_PACKAGE_PATH_LIST = ["/usr/lib64/python2.7/site-packages"]

TOPO_ARRAY = ("t0", "t1", "t1-lag", "ptf32", "t0-64", "t1-64-lag")
REBOOT_TYPES = {
    "reboot": "reboot",
    "fast-reboot": "fast-reboot",
    "warm-reboot": "warm-reboot"
}

DOCKER_REGISTRY = "harbor.mellanox.com/sonic"

DUT_LOG_BACKUP_PATH = "/.autodirect/sw_system_project/sonic/dut_logs"
