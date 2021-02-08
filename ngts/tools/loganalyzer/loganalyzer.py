import sys
import logging
import os
import re
import time
import pprint

from .log_parser import DutLogAnalyzer
from os.path import join, split
from os.path import normpath

logger = logging.getLogger()

DUT_LOGANALYZER_MODULE = os.path.join(os.path.dirname(__file__), "log_parser.py")
EXTRACT_LOG_MODULE = os.path.join(os.path.dirname(__file__), "extract_log.py")
COMMON_MATCH = join(split(__file__)[0], "loganalyzer_common_match.txt")
COMMON_IGNORE = join(split(__file__)[0], "loganalyzer_common_ignore.txt")
COMMON_EXPECT = join(split(__file__)[0], "loganalyzer_common_expect.txt")
SYSLOG_TMP_FOLDER = "/tmp/syslog"


class LogAnalyzerError(Exception):
    """Raised when loganalyzer found matches during analysis phase."""
    def __repr__(self):
        return pprint.pformat(self.message)


class LogAnalyzer:
    def __init__(self, dut_engine, marker_prefix, dut_run_dir="/tmp", start_marker=None):
        self.dut_engine = dut_engine
        self.dut_run_dir = dut_run_dir
        self.extracted_syslog = os.path.join(self.dut_run_dir, "syslog")
        self.marker_prefix = marker_prefix.replace(" ", "_")
        # use existing syslog msg as marker to search in logs instead of writing a new one
        self.start_marker = start_marker
        self.dut_loganalyzer = DutLogAnalyzer(self.marker_prefix, False, start_marker=self.start_marker)

        self.match_regex = []
        self.expect_regex = []
        self.ignore_regex = []
        self.expected_matches_target = 0
        self._markers = []
        self.fail = True

    def _add_end_marker(self, marker):
        """
        @summary: Add stop marker into syslog on the DUT.

        @return: True for successfull execution False otherwise
        """
        dest_file = "loganalyzer.py"
        self.dut_engine.copy_file(source_file=DUT_LOGANALYZER_MODULE, dest_file=dest_file, file_system=self.dut_run_dir,
            overwrite_file=True, verify_file=False)

        cmd = "python {run_dir}/loganalyzer.py --action add_end_marker --run_id {marker}".format(run_dir=self.dut_run_dir, marker=marker)

        logger.info("Adding end marker '{}'".format(marker))
        self.dut_engine.run_cmd(cmd)

    def __call__(self, **kwargs):
        """
        Pass additional arguments when the instance is called
        """
        self.fail = kwargs.get("fail", True)
        self.start_marker = kwargs.get("start_marker", None)
        return self

    def __enter__(self):
        """
        Store start markers which are used in analyze phase.
        """
        self._markers.append(self.init())

    def __exit__(self, *args):
        """
        Analyze syslog messages.
        """
        self.analyze(self._markers.pop(), fail=self.fail)

    def _verify_log(self, result):
        """
        Verify that total match and expected missing match equals to zero or raise exception otherwise.
        Verify that expected_match is not equal to zero when there is configured expected regexp in self.expect_regex list
        """
        if not result:
            raise LogAnalyzerError("Log analyzer failed - no result.")
        if result["total"]["match"] != 0 or result["total"]["expected_missing_match"] != 0:
            raise LogAnalyzerError(result)

        # Check for negative case
        if self.expect_regex and result["total"]["expected_match"] == 0:
            raise LogAnalyzerError(result)

        # if the number of expected matches is provided
        if (self.expect_regex and (self.expected_matches_target > 0)
           and result["total"]["expected_match"] != self.expected_matches_target):
            raise LogAnalyzerError(result)

    def update_marker_prefix(self, marker_prefix):
        """
        @summary: Update configured marker prefix
        """
        self.marker_prefix = marker_prefix.replace(' ', '_')
        return self._setup_marker()

    def load_common_config(self):
        """
        @summary: Load regular expressions from common files, which are localted in folder with legacy loganalyzer.
                  Loaded regular expressions are used by "analyze" method to match expected text in the downloaded log file.
        """
        self.match_regex = self.dut_loganalyzer.create_msg_regex([COMMON_MATCH])[1]
        self.ignore_regex = self.dut_loganalyzer.create_msg_regex([COMMON_IGNORE])[1]
        self.expect_regex = self.dut_loganalyzer.create_msg_regex([COMMON_EXPECT])[1]

    def parse_regexp_file(self, src):
        """
        @summary: Get regular expressions defined in src file.
        """
        return self.dut_loganalyzer.create_msg_regex([src])[1]

    def run_cmd(self, callback, *args, **kwargs):
        """
        @summary: Initialize loganalyzer, execute function and analyze syslog.

        @param callback: Python callable or function to be executed.
        @param args: Input arguments for callback function.
        @param kwargs: Input key value arguments for callback function.

        @return: Callback execution result
        """
        marker = self.init()
        fail = kwargs.pop("fail", True)
        try:
            call_result = callback(*args, **kwargs)
        except Exception as err:
            logger.error("Error during callback execution:\n{}".format(err))
            logger.info("Log analysis result\n".format(self.analyze(marker, fail=fail)))
            raise err
        self.analyze(marker, fail=fail)

        return call_result

    def init(self):
        """
        @summary: Add start marker into syslog on the DUT.

        @return: True for successfull execution False otherwise
        """
        logger.info("Loganalyzer init")

        dest_file = "loganalyzer.py"
        self.dut_engine.copy_file(source_file=DUT_LOGANALYZER_MODULE, dest_file=dest_file, file_system=self.dut_run_dir,
            overwrite_file=True, verify_file=False)

        return self._setup_marker()

    def _setup_marker(self):
        """
        Adds the marker to the syslog
        """
        start_marker = ".".join((self.marker_prefix, time.strftime("%Y-%m-%d-%H:%M:%S", time.gmtime())))
        cmd = "python {run_dir}/loganalyzer.py --action init --run_id {start_marker}".format(run_dir=self.dut_run_dir, start_marker=start_marker)

        logger.info("Adding start marker '{}'".format(start_marker))
        self.dut_engine.run_cmd(cmd)
        return start_marker

    def analyze(self, marker, fail=True):
        """
        @summary: Extract syslog logs based on the start/stop markers and compose one file. Download composed file, analyze file based on defined regular expressions.

        @param marker: Marker obtained from "init" method.
        @param fail: Flag to enable/disable raising exception when loganalyzer find error messages.

        @return: If "fail" is False - return dictionary of parsed syslog summary, if dictionary can't be parsed - return empty dictionary. If "fail" is True and if found match messages - raise exception.
        """
        logger.info("Loganalyzer analyze")
        analyzer_summary = {"total": {"match": 0, "expected_match": 0, "expected_missing_match": 0},
                            "match_files": {},
                            "match_messages": {},
                            "expect_messages": {},
                            "unused_expected_regexp": []
                            }
        tmp_folder = ".".join((SYSLOG_TMP_FOLDER, time.strftime("%Y-%m-%d-%H:%M:%S", time.gmtime())))
        marker = marker.replace(' ', '_')
        self.dut_loganalyzer.run_id = marker

        if not self.start_marker:
            start_string = 'start-LogAnalyzer-{}'.format(marker)
        else:
            start_string = self.start_marker
        logger.info('Marker = {}'.format(start_string))

        try:
            # Disable logrotate cron task
            self.dut_engine.run_cmd("sudo sed -i 's/^/#/g' /etc/cron.d/logrotate")

            logger.info("Waiting for logrotate from previous cron task run to finish")
            # Wait for logrotate from previous cron task run to finish
            end = time.time() + 60
            while time.time() < end:
                output = self.dut_engine.run_cmd("sudo pgrep -f logrotate")
                if len(output.split()) != 1:
                    time.sleep(5)
                    continue
                else:
                    break
            else:
                logger.error("Logrotate from previous task was not finished during 60 seconds")

            # Add end marker into DUT syslog
            self._add_end_marker(marker)

            # On DUT extract syslog files from /var/log/ and create one file by location - /tmp/syslog
            logger.info('Extract log on DUT into \'{}\''.format(self.extracted_syslog))
            self.extract_log(directory='/var/log', file_prefix='syslog', start_string=start_string, target_filename=self.extracted_syslog)
        finally:
            # Enable logrotate cron task back
            self.dut_engine.run_cmd("sudo sed -i 's/^#//g' /etc/cron.d/logrotate")

        # Wait extracted file created
        attempt = 5
        for counter in range(attempt):
            if self.file_exist(self.extracted_syslog):
                break
            time.sleep(1)
        else:
            logger.warning('Extracted file was not created - \'{}\''.format(self.extracted_syslog))

        # Download extracted logs from the DUT to the temporal folder
        logger.info('Download extracted file into \'{}\''.format(tmp_folder))
        self.save_extracted_log(dest=tmp_folder)

        # Remove extracted file on DUT
        self.remove_extracted_log()

        match_messages_regex = re.compile('|'.join(self.match_regex)) if len(self.match_regex) else None
        ignore_messages_regex = re.compile('|'.join(self.ignore_regex)) if len(self.ignore_regex) else None
        expect_messages_regex = re.compile('|'.join(self.expect_regex)) if len(self.expect_regex) else None

        analyzer_parse_result = self.dut_loganalyzer.analyze_file_list([tmp_folder], match_messages_regex, ignore_messages_regex, expect_messages_regex)
        # Print syslog file content and remove the file
        with open(tmp_folder) as fo:
            logger.info("Syslog content:\n\n{}".format(fo.read()))

        logger.info('Remove temporal file \'{}\''.format(tmp_folder))
        os.remove(tmp_folder)

        total_match_cnt = 0
        total_expect_cnt = 0
        expected_lines_total = []
        unused_regex_messages = []

        for key, value in analyzer_parse_result.items():
            matching_lines, expecting_lines = value
            analyzer_summary["total"]["match"] += len(matching_lines)
            analyzer_summary["total"]["expected_match"] += len(expecting_lines)
            analyzer_summary["match_files"][key] = {"match": len(matching_lines), "expected_match": len(expecting_lines)}
            analyzer_summary["match_messages"][key] = matching_lines
            analyzer_summary["expect_messages"][key] = expecting_lines
            expected_lines_total.extend(expecting_lines)

        # Find unused regex matches
        for regex in self.expect_regex:
            for line in expected_lines_total:
                if re.search(regex, line):
                    break
            else:
                unused_regex_messages.append(regex)
        analyzer_summary["total"]["expected_missing_match"] = len(unused_regex_messages)
        analyzer_summary["unused_expected_regexp"] = unused_regex_messages

        if fail:
            self._verify_log(analyzer_summary)
        else:
            return analyzer_summary

    def save_extracted_log(self, dest):
        """
        @summary: Download extracted syslog file to the test execution host.

        @param dest: File path to store downloaded log file.
        """
        folder, src_file = os.path.split(self.extracted_syslog)
        self.dut_engine.copy_file(source_file=src_file, dest_file=dest, file_system=folder,
            overwrite_file=True, verify_file=False, direction='get', disable_md5=True)

    def remove_extracted_log(self):
        """
        @summary: Removes extracted log file from DUT
        """
        cmd = 'sudo rm -f {}'.format(self.extracted_syslog)
        logger.info('Remove extracted log file from DUT \'{}\''.format(self.extracted_syslog))
        self.dut_engine.run_cmd(cmd)

    def file_exist(self, path):
        """
        @summary: Check if file exists

        @param path: Path to the file which should be checked
        """
        cmd = 'ls -l {} > /dev/null 2>&1; echo $?'.format(path)
        output = self.dut_engine.run_cmd(cmd)
        if int(output) == 0:
            return True
        else:
            return False

    def extract_log(self, directory, file_prefix, start_string, target_filename):
        """
        @summary: Runs 'extract_log.py' module on DUT which creates combined log file

        @param directory: name of a directory with target log files
        @param file_prefix: prefix of a target log files
        @param start_string: string which is used as a start tag for extracting log information
        @param target_filename: file name where the extracted lines will be saved
        """
        module_name = os.path.split(EXTRACT_LOG_MODULE)[-1]
        dut_module_path = os.path.join(self.dut_run_dir, module_name)
        cmd = "sudo python3 {} -d \'{}\' -p \'{}\' -s \'{}\' -t \'{}\'".format(dut_module_path, directory, file_prefix,
                                                                               start_string, target_filename)

        self.dut_engine.copy_file(source_file=EXTRACT_LOG_MODULE, dest_file=module_name, file_system=self.dut_run_dir,
            overwrite_file=True, verify_file=False)
        self.dut_engine.run_cmd(cmd)
