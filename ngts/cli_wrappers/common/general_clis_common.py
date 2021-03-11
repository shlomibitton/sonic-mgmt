from ngts.cli_wrappers.interfaces.interface_general_clis import GeneralCliInterface


class GeneralCliCommon(GeneralCliInterface):
    """
    This class hosts methods which are implemented identically for Linux and SONiC
    """
    def __init__(self):
        pass

    @staticmethod
    def start_service(engine, service):
        output = engine.run_cmd('sudo service {} start'.format(service), validate=True)
        return output

    @staticmethod
    def stop_service(engine, service):
        output = engine.run_cmd('sudo service {} stop'.format(service), validate=True)
        return output
