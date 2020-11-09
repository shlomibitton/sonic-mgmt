class StubEngine:
    """
    Class which emulate engine object
    """
    def __init__(self):
        self.commands_list = []

    def run_cmd(self, cmd):
        """
        Method emulates API for run_cmd method from real engine, but instead of run command
        it save cmd to self.commands_list
        :param cmd: command which we are going to execute
        """
        self.commands_list.append(cmd)
