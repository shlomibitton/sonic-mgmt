from ngts.cli_wrappers.interfaces.interface_general_clis import GeneralCliInterface


class GeneralCliCommon(GeneralCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass

    @staticmethod
    def verify_cmd_rc(engine, error_message):
        rc = engine.run_cmd('echo $?')
        assert int(rc) == 0, error_message

    @staticmethod
    def start_service(engine, service):
        output = engine.run_cmd('sudo service {} start'.format(service))
        GeneralCliCommon.verify_cmd_rc(engine, 'Unable to start service {}'.format(service))
        return output

    @staticmethod
    def stop_service(engine, service):
        output = engine.run_cmd('sudo service {} stop'.format(service))
        GeneralCliCommon.verify_cmd_rc(engine, 'Unable to stop service {}'.format(service))
        return output
