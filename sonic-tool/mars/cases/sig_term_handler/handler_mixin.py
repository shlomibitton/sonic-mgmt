import time
import os

from mlxlib.common import files
from rpyc.utils.classic import connect, download
from reg2_wrapper.common.error_code import ErrorCode

class TermHandlerMixin(object):
    def __init__(self, name):
        super(TermHandlerMixin, self).__init__(name)

    def _kill_handler(self, sig, frm):
        """
        Used for overloading existed signal handler of TestWrapper class with adding storing logs for terminated run.
        """
        player = self.Players[0]
        self.Logger.info("Termination signal handler started")
        pid_index = 0
        proc_stdout_index = 0

        for process in player.processes[:]:
            run_log_file_name = player.process_logger[player.pids[pid_index]][proc_stdout_index]
            local_dir_path = os.path.join(files.get_mlxtmp_dir(), self.session_id)
            local_tmp_file = os.path.join(local_dir_path, "term_log.txt")
            try:
                if not os.path.exists(local_dir_path):
                    os.mkdir(local_dir_path)

                conn = connect(player.player_ip)
                download(conn, run_log_file_name, local_tmp_file)

                with open(local_tmp_file) as outfile:
                    output = outfile.read()

                self.Logger.info(output)

                if os.path.exists(local_tmp_file):
                    os.remove(local_tmp_file)
            except Exception as err:
                self.Logger.error("Unable to load test cases run logs from the player: {}".format(err))
        super(TermHandlerMixin, self)._kill_handler(sig, frm)
