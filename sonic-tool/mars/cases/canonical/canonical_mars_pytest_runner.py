#!/usr/bin/env python

# Built-in modules
import sys
import os

# Local modules
from reg2_wrapper.common.error_code import ErrorCode
from reg2_wrapper.utils.parser.cmd_argument import RunningStage
from reg2_wrapper.test_wrapper.standalone_wrapper import StandaloneWrapper

sigterm_h_path = os.path.normpath(os.path.join(os.path.split(__file__)[0], "../sig_term_handler"))
sys.path.append(sigterm_h_path)
from handler_mixin import TermHandlerMixin


class RunPytest(TermHandlerMixin, StandaloneWrapper):

    def configure_parser(self):
        super(RunPytest, self).configure_parser()

        # Client arguments
        self.add_cmd_argument("--setup_name", required=True, dest="setup_name",
                              help="Specify setup name, for example: SONiC_tigris_r-tigris-06")
        self.add_cmd_argument("--test_script", required=True, dest="test_script",
                              help="Path to the test script, example: /workspace/tests/")
        self.add_cmd_argument("--raw_options", nargs="?", default="", dest="raw_options",
                              help="All the other options that to be passed to py.test")

    def run_commands(self):
        rc = ErrorCode.SUCCESS

        cmd = 'pytest --setup_name={} {} {}'.format(self.setup_name, self.raw_options, self.test_script)

        for epoint in self.EPoints:
            dic_args = self._get_dic_args_by_running_stage(RunningStage.RUN)
            dic_args["epoint"] = epoint
            for i in xrange(self.num_of_processes):
                epoint.Player.putenv("PYTHONPATH", "/devts/")
                epoint.Player.run_process(cmd, shell=True, disable_realtime_log=False, delete_files=False)

        for player in self.Players:
            rc = player.wait() or rc
            player.remove_remote_test_path(player.testPath)
        return rc


if __name__ == "__main__":
    run_pytest = RunPytest("RunPytest")
    run_pytest.execute(sys.argv[1:])
