from ngts.cli_wrappers.common.vrf_clis_common import VrfCliCommon


class SonicVrfCli(VrfCliCommon):
    @staticmethod
    def add_vrf(engine, vrf):
        """
        This method creates VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be created
        :return: command output
        """
        return engine.run_cmd("sudo config vrf add {}".format(vrf))

    @staticmethod
    def del_vrf(engine, vrf):
        """
        This method deletes VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be deleted
        :return: command output
        """
        return engine.run_cmd("sudo config vrf del {}".format(vrf))

    @staticmethod
    def add_interface_to_vrf(engine, interface, vrf):
        """
        This method moves interface from default VRF to specific
        :param engine: ssh engine object
        :param interface: interface name which should be moved
        :param vrf: vrf name to which move interface
        :return: command output
        """
        return engine.run_cmd("sudo config interface vrf bind {} {}".format(interface, vrf))

    @staticmethod
    def del_interface_from_vrf(engine, interface, vrf):
        """
        This method moves interface from specific VRF to default
        :param engine: ssh engine object
        :param interface: interface name which should be moved
        :param vrf: vrf name from which move interface
        :return: command output
        """
        return engine.run_cmd("sudo config interface vrf unbind {}".format(interface))
