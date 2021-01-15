#!/usr/bin/env python

# Built-in modules
import sys

# Local modules
from reg2_wrapper.test_wrapper.standalone_wrapper import StandaloneWrapper


class RunAnsiblePlaybook(StandaloneWrapper):

    def get_prog_path(self):
        # remote_test_path - re-define, because by default MARS provide this variable and it point to /tmp/mars_tests/
        self.remote_test_path = '{}/sonic-tool/mars/cases/community'.format(self.sonic_mgmt_path)
        return "bash ./run_ansible_playbook.sh"

    def configure_parser(self):
        super(RunAnsiblePlaybook, self).configure_parser()

        # Client arguments
        self.add_cmd_argument('--raw_args', help='All the args that to be passed to ansible-playbook', default="",
                              value_only=True)
        self.add_argument("--sonic-mgmt-dir", required=True, dest="sonic_mgmt_path",
                              help="Specify dir of the sonic-mgmt repo on player (sonic-mgmt container), for example: \
                                    /root/mars/workspace/sonic-mgmt")


if __name__ == "__main__":
    run_ansible = RunAnsiblePlaybook("RunAnsiblePlaybook")
    run_ansible.execute(sys.argv[1:])
