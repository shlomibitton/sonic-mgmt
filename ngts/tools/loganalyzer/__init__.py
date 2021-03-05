import logging
import pytest
import os
import time

from .loganalyzer import LogAnalyzer

logger = logging.getLogger()
TEMP_IGNORE = os.path.join(os.path.dirname(__file__), "loganalyzer_temporal_ignore.txt")
LOCAL_LOGS_DIR_TEMPLATE = "/tmp/test_run-{}"
LOG_FILE_NAME = "syslog"


def pytest_addoption(parser):
    parser.addoption("--disable_loganalyzer", action="store_true", default=False,
                     help="disable loganalyzer analysis for 'loganalyzer' fixture")


@pytest.fixture(autouse=True)
def loganalyzer(topology_obj, request, loganalyzer_log_folder):
    if request.config.getoption("--disable_loganalyzer") or "disable_loganalyzer" in request.keywords:
        logger.info("Log analyzer is disabled")
        yield
        return

    marker = None
    dut_engine = topology_obj.players['dut']['engine']
    hostname = topology_obj.players['dut']['cli'].chassis.get_hostname(dut_engine)

    # Force rotate logs
    dut_engine.run_cmd(
        "sudo /usr/sbin/logrotate -f /etc/logrotate.conf > /dev/null 2>&1"
        )

    log_path = loganalyzer_log_folder

    loganalyzer = LogAnalyzer(dut_engine=dut_engine, marker_prefix=request.node.name)
    logger.info("Add start marker into DUT syslog")
    marker = loganalyzer.init(log_folder=log_path, log_file=LOG_FILE_NAME)
    logger.info("Loading log analyzer configs")
    # Read existed common regular expressions located with legacy loganalyzer module
    loganalyzer.load_common_config()

    yield loganalyzer

    # Skip LogAnalyzer if case is skipped
    if "rep_call" in request.node.__dict__ and request.node.rep_call.skipped:
        return
    loganalyzer.analyze(marker)

@pytest.fixture(autouse=True)
def loganalyzer_load_temporal_ignore(loganalyzer):
    """
    Extend loganalyzer common ignore regexp by custom regexps if such defined.
    """
    if loganalyzer:
        ignore_reg_exp = loganalyzer.parse_regexp_file(src=TEMP_IGNORE)
        loganalyzer.ignore_regex.extend(ignore_reg_exp)
    yield

@pytest.fixture(autouse=True)
def loganalyzer_log_folder(log_folder, session_id, request):
    log_path = None
    # If MARS run, store syslog in shared location
    if session_id:
        if log_folder:
            # Store syslog in shared location in case of MARS run
            log_path = os.path.join(log_folder, request.node.name)
            os.makedirs(log_path, exist_ok=True)
        else:
            logger.error("'log_folder' fixure is empty - {}".format(log_folder))
    # If manual run, store syslog in /tmp folder of the running host
    else:
        log_path = LOCAL_LOGS_DIR_TEMPLATE.format(time.strftime("%Y-%m-%d-%H:%M:%S", time.gmtime()))
        log_path = os.path.join(log_path, request.node.name)
        os.makedirs(log_path, exist_ok=True)
    logger.info("Loganalyzer log folder - '{}'".format(log_path))
    return log_path
