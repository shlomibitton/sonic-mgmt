import logging
import pytest
import os

from .loganalyzer import LogAnalyzer

logger = logging.getLogger()
TEMP_IGNORE = os.path.join(os.path.dirname(__file__), "loganalyzer_temporal_ignore.txt")


def pytest_addoption(parser):
    parser.addoption("--disable_loganalyzer", action="store_true", default=False,
                     help="disable loganalyzer analysis for 'loganalyzer' fixture")


@pytest.fixture(autouse=True)
def loganalyzer(topology_obj, request):
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

    loganalyzer = LogAnalyzer(dut_engine=dut_engine, marker_prefix=request.node.name)
    logger.info("Add start marker into DUT syslog")
    marker = loganalyzer.init()
    logger.info("Load config and analyze log")
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
