import re
import logging

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


class SonicCrmCli:
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
        output = engine.run_cmd("crm show thresholds all")
        result = generic_sonic_output_parser(output, headers_ofset=2,
                                             len_ofset=3,
                                             data_ofset_from_start=4,
                                             data_ofset_from_end=-1,
                                             column_ofset=2,
                                             output_key='Resource Name')
        return result

    @staticmethod
    def parse_resources_table(engine):
        """
        Run output of 'crm show resources all'
        :param engine: ssh engine object
        """
        result = {'main_resources': {}, 'acl_resources': [], 'table_resources': []}
        output = engine.run_cmd("crm show resources all")
        result['main_resources'] = generic_sonic_output_parser(output, headers_ofset=2,
                                                               len_ofset=3,
                                                               data_ofset_from_start=4,
                                                               data_ofset_from_end=-33,
                                                               column_ofset=2,
                                                               output_key='Resource Name')
        result['acl_resources'] = generic_sonic_output_parser(output, headers_ofset=17, len_ofset=18,
                                                              data_ofset_from_start=19,
                                                              data_ofset_from_end=-7,
                                                              column_ofset=2,
                                                              output_key=None)
        result['table_resources'] = generic_sonic_output_parser(output, headers_ofset=44, len_ofset=45,
                                                                data_ofset_from_start=46,
                                                                data_ofset_from_end=-1,
                                                                column_ofset=2,
                                                                output_key=None)
        return result
