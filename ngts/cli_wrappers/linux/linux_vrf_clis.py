from ngts.cli_wrappers.common.vrf_clis_common import VrfCliCommon


class LinuxVrfCli(VrfCliCommon):
    @staticmethod
    def add_vrf(engine, vrf):
        """
        This method create VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be created
        :return: command output
        """
        raise NotImplementedError

    @staticmethod
    def del_vrf(engine, vrf):
        """
        This method deletes VRF
        :param engine: ssh engine object
        :param vrf: vrf name which should be deleted
        :return: command output
        """
        raise NotImplementedError

    @staticmethod
    def add_interface_to_vrf(engine, interface, vrf):
        """
        This method move interface from default VRF to specific
        :param engine: ssh engine object
        :param interface: interface name which should be moved
        :param vrf: vrf name to which move interface
        :return: command output
        """
        raise NotImplementedError

    @staticmethod
    def del_interface_from_vrf(engine, interface, vrf):
        """
        This method move interface from specific VRF to default
        :param engine: ssh engine object
        :param interface: interface name which should be moved
        :param vrf: vrf name from which move interface
        :return: command output
        """
        raise NotImplementedError
