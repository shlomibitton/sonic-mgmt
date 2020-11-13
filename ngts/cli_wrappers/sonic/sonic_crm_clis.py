import re
import logging

from ngts.cli_wrappers.common.crm_clis_common import CrmCliCommon
from ngts.cli_util.cli_parsers import generic_sonic_output_parser

logger = logging.getLogger()


class CrmThresholdTypeError(Exception):
    pass

class CrmThresholdValueError(Exception):
    pass

class CrmThresholdResourceError(Exception):
    pass


class CRMHelper:
    """ Helper class for 'SonicCrmCli' class """
    @staticmethod
    def validate_threshold_type(th_type):
        theshold_types = ['percentage', 'used', 'free']

        if not th_type in theshold_types:
            raise CrmThresholdTypeError('Unsupported threshold type: \'{}\''.format(th_type))

    @staticmethod
    def validate_threshold_value(value):
        if not isinstance(value, int):
            raise CrmThresholdValueError('Value is not an integer type: {} {}'.format(value, type(value)))
        if not(0 <= value <= 100):
            raise CrmThresholdValueError('Value is out of range 0..100: \'{}\''.format(value))

    @classmethod
    def set_threshold_type(cls, engine, template, th_type):
        cls.validate_threshold_type(th_type)

        cmd = ' '.join([template, 'type', th_type])
        engine.run_cmd(cmd)

    @classmethod
    def set_threshold_value(cls, engine, template, value_type, value):
        cls.validate_threshold_value(value)

        cmd = ' '.join([template, value_type, str(value)])
        engine.run_cmd(cmd)

    @staticmethod
    def configure_threshold(engine, template, th_type=None, low=None, high=None):
        if th_type:
            CRMHelper.set_threshold_type(engine, template, th_type)
        if low:
            CRMHelper.set_threshold_value(engine, template, 'low', low)
        if high:
            CRMHelper.set_threshold_value(engine, template, 'high', high)


class SonicCrmCli(CrmCliCommon):
    thresholds_cmd = 'crm config thresholds'

    @staticmethod
    def set_threshold_ip(engine, ip_ver, resource, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'ipv4/ipv6' 'neighbor', 'nexthop' or 'route' resources
        SONiC CLI configuration examples:
        crm config thresholds ipv4 --help
            neighbor  nexthop   route

        crm config thresholds ipv6 --help
            neighbor  nexthop   route

        crm config thresholds ipv4 route type percentage
        :param engine: ssh engine object
        :param ip_ver: IP version 4 or 6 to choose beatween 'ipv4' or 'ipv6' CRM resources
        :param resource: crm 'ipv4/6' available resources - 'neighbor', 'nexthop' or 'route'
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        resources = ['neighbor', 'nexthop', 'route']
        if resource not in resources:
            raise CrmThresholdResourceError(
                'Unsupported resource specified - \'{}\'\nExpected - {}'.format(
                    resource, resources
                )
            )

        template = ' '.join([SonicCrmCli.thresholds_cmd, 'ipv{}'.format(ip_ver), resource])
        CRMHelper.configure_threshold(engine, template, th_type, low, high)

    @staticmethod
    def set_threshold_nexthop_group(engine, resource, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'nexthop group' resources.
        SONiC CLI command examples:
        crm config thresholds nexthop group --help
            Commands:
                member  CRM configuration for nexthop group member...
                object  CRM configuration for nexthop group resource

        crm config thresholds nexthop group member type percentage
        crm config thresholds nexthop group object low 5
        :param engine: ssh engine object
        :param resource: crm 'ipv4/6' available resources - 'neighbor', 'nexthop' or 'route'
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        resources = ['member', 'object']
        if resource not in resources:
            raise CrmThresholdResourceError(
                'Unsupported resource specified - \'{}\'\nExpected - {}'.format(
                    resource, resources
                )
            )

        template = ' '.join([SonicCrmCli.thresholds_cmd, 'nexthop group', resource])
        CRMHelper.configure_threshold(engine, template, th_type, low, high)

    @staticmethod
    def set_threshold_acl(engine, resource, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'acl' resources
        SONiC CLI command examples:
        crm config thresholds acl table type percentage
        crm config thresholds acl group counter type percentage
        crm config thresholds acl group type percentage
        :param engine: ssh engine object
        :param resource: crm 'ipv4/6' available resources - 'neighbor', 'nexthop' or 'route'
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        resources = ['table', 'group', 'group counter', 'group entry']
        if resource not in resources:
            raise CrmThresholdResourceError(
                'Unsupported resource specified - \'{}\'\nExpected - {}'.format(
                    resource, resources
                )
            )

        template = ' '.join([SonicCrmCli.thresholds_cmd, 'acl', resource])
        CRMHelper.configure_threshold(engine, template, th_type, low, high)

    @staticmethod
    def set_threshold_fdb(engine, th_type=None, low=None, high=None):
        """
        Configure CRM thresholds for 'fdb' resource
        SONiC CLI command examples:
        crm config thresholds fdb --help
            high  CRM high threshod configuration
            low   CRM low threshod configuration
            type  CRM threshod type configuration
        :param engine: ssh engine object
        :param th_type: crm threshold type: 'percentage', 'used' or 'free'
        :param low: crm low threshold 0..100
        :param high: crm high threshold 0..100
        """
        template = ' '.join([SonicCrmCli.thresholds_cmd, 'fdb'])
        CRMHelper.configure_threshold(engine, template, th_type, low, high)

    @staticmethod
    def get_polling_interval(engine):
        """
        Return configured CRM polling interval
        :param engine: ssh engine object
        """
        return int(engine.run_cmd('crm show summary | awk \'{print $3}\'').strip())

    @staticmethod
    def set_polling_interval(engine, interval):
        """
        Configure CRM polling interval
        :param engine: ssh engine object
        :param interval: crm polling interval in seconds
        """
        engine.run_cmd('crm config polling interval {}'.format(interval))

    @staticmethod
    def parse_thresholds_table(engine):
        """
        Parse output of 'crm show thresholds all'
        :param engine: ssh engine object
        """
        result = {}
        values_started = False
        output = engine.run_cmd("crm show thresholds all").split('\n')
        lines = [line for line in output if line != '']
        for line in lines:
            if "---" in line:
                values_started = True
                continue
            elif values_started:
                res_name, th_type, low, high = line.split()
                result[res_name] = {'type': th_type, 'low': low, 'high': high}

        return result

    @staticmethod
    def parse_resources_table(engine):
        """
        Run output of 'crm show resources all'
        :param engine: ssh engine object
        """
        result = {"main_resources": {}, "acl_resources": [], "table_resources": []}
        output = engine.run_cmd("crm show resources all").split('\n')

        current_table = 0   # Totally 3 tables in the command output
        for line in output:
            if len(line.strip()) == 0:
                continue
            if "---" in line:
                current_table += 1
                continue
            if current_table == 1:      # content of first table, main resources
                fields = line.split()
                if len(fields) == 3:
                    result["main_resources"][fields[0]] = {"used": int(fields[1]), "available": int(fields[2])}
            if current_table == 2:      # content of the second table, acl resources
                fields = line.split()
                if len(fields) == 5:
                    result["acl_resources"].append({"stage": fields[0], "bind_point": fields[1],
                        "resource_name": fields[2], "used_count": int(fields[3]), "available_count": int(fields[4])})
            if current_table == 3:      # content of the third table, table resources
                fields = line.split()
                if len(fields) == 4:
                    result["table_resources"].append({"table_id": fields[0], "resource_name": fields[1],
                        "used_count": int(fields[2]), "available_count": int(fields[3])})

        return result
