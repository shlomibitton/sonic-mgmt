class SonicAclCli:

    @staticmethod
    def create_table(engine, tbl_name, tbl_type, description, stage, ports=None):
        """
        Creates ACL table from SONIC
        :param engine: ssh engine object
        :param tbl_name: ACL table name
        :param tbl_type: ACL table type [L3, MIRROR, MIRROR_DSCP, etc.]
        :param description: ACL table description
        :param stage: ACL table stage [ingress|egress]
        :param ports: The list of ports to which this ACL table is applied, if None - all ports will be used
        :return: command output
        """
        cmd = 'sudo config acl add table {name} {type} --description={description} --stage={stage}'\
            .format(name=tbl_name, type=tbl_type, description=description, stage=stage, ports=ports)
        if ports:
            ports = ','.join(ports)
            cmd += ' --ports={}'.format(ports)

        return engine.run_cmd(cmd)

    @staticmethod
    def apply_config(engine, cfg_path):
        """
        On DUT applies ACL config defined in file 'cfg_path'
        :param engine: ssh engine object
        :param cfg_path: Path to the ACL config file stored on DUT
        :return: command output
        """
        return engine.run_cmd("acl-loader update full {}".format(cfg_path))

    @staticmethod
    def delete_config(engine):
        """
        On DUT removes currect ACL configuration
        :param engine: ssh engine object
        :return: command output
        """
        return engine.run_cmd('acl-loader delete')
