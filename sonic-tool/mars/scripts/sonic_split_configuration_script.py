#!/auto/app/Python-3.6.2/bin/python

import argparse
import logging
import sys
import traceback
import re
import os
import pathlib
import json
from jinja2 import Environment, FileSystemLoader
from retry import retry
from shutil import copyfile
sys.path.append(str(os.path.join(str(pathlib.Path(__file__).parent.absolute()),"..","..","sonic_ngts")))
from infra.engines.ssh.ssh_engine import SSH
from infra.topology_tools.topology_reader import get_switch_engine, get_switch_config_files_dir_path
from infra.constants.constants import LinuxConsts, ConfigDbJsonConst, SonicConsts
logger = logging.getLogger("sonic_split_configuration_script")


def set_logger(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')


def init_parser():
    description = ('Functionality of the script: \n'
                   '1. Get switch ip.\n'
                   'Use case #1:\n'
                   '    2. Get port_config.ini and config_db.json file from shared '
                   '       location specified on switch resource on Noga.\n'
                   '    3. load the files from shared location into the switch and reload.'
                   'Use case #2:\n'
                   '    2. Get port_config.ini file from path specified by user.\n'
                   '    3. align initial switch configuration file with port_config.ini.\n'
                   '    4. load modified initial switch configuration on to the switch.\n'
                   '    5. reload.\n')

    parser = argparse.ArgumentParser(description=description)

    group = parser.add_mutually_exclusive_group()

    group.add_argument('-ini', '--port_config_ini', dest='port_config_ini',
                       help='A .ini file with the information about all the ports in the setup\n,'
                            'see example files in path mars/scripts/port_config.ini_files')

    group.add_argument('-n', '--noga', dest='noga_configuration_files', action='store_true',
                       help='Take port_config.ini and config_db.json files from switch resource on noga.')

    parser.add_argument('--basic', dest='is_basic_config', action='store_true',
                        help='configure basic_port_config.ini and basic_config_db.json files on switch.')

    parser.add_argument('-s', '--switch', dest='switch_ip',
                        help='SONiC switch ip, e.g. 10.210.25.102')

    parser.add_argument('--setup_name', dest='setup_name', default=None, help='SONiC switch ip, e.g. 10.210.25.102')

    parser.add_argument('-p', '--password', dest='switch_password',
                        help='SONiC switch password, e.g. YourPaSsWoRd', default="YourPaSsWoRd")

    parser.add_argument('-u', '--username', dest='switch_username',
                        help='SONiC switch username, e.g. admin', default="admin")

    parser.add_argument('--hostname', dest='switch_hostname',
                        help='SONiC switch hostname, e.g. r-leopard-32', default="")

    parser.add_argument('--hwsku', default=None)

    parser.add_argument('-c', '--configuration_path_dst', dest='configuration_path_dst',
                        help='the new config_db.json and port_config.ini will be saved in this directory path.',
                        default=str(os.path.join(str(pathlib.Path(__file__).parent.absolute()))))

    parser.add_argument('-l', '--log_level', dest='log_level', default=logging.INFO, help='log verbosity')

    args, unknown = parser.parse_known_args()

    if unknown:
        raise Exception("unknown argument(s): {}".format(unknown))
    return args


def apply_base_configuration(args):
    """
    :param args: the script arguments
    :return: None, configure the switch ports and reload
    """
    if args.noga_configuration_files:
        if args.setup_name is None:
            raise Exception("Please provide valid setup name for switch {}.\n".format(args.switch_ip))
        apply_base_configuration_from_noga(args)
    else:
        apply_base_configuration_from_user(args)


def apply_base_configuration_from_noga(args):
    """
    :param args: the script arguments
    :return: None, load to switch port_config.ini and config_db.json,
             taken from the shared location specified on noga switch
             resource and reload the switch
    """
    engine, config_files_dir_path = get_switch_resource_from_noga(args)
    platform, hwsku = get_platform_and_hwsku_from_switch(engine, args)
    port_config_ini_path, config_db_json_path, minigraph_xml_path = get_configuration_files_paths(args, config_files_dir_path)
    load_configuration_files_to_switch(engine, port_config_ini_path, config_db_json_path, platform, hwsku)
    load_minigraph_xml_to_switch(engine, minigraph_xml_path)
    reload_switch(engine)


def apply_base_configuration_from_user(args):
    """
    :param args: the script arguments
    :return: None, get port_config.ini file from path specified by user and load it to switch'
                   align initial switch configuration file with port_config.ini,
                   load modified initial switch configuration on to the switch,
                   reload the switch.
    """
    validate_configuration_path_dst(args.configuration_path_dst)
    engine, port_config_ini_path = get_switch_resource_from_user(args)
    platform, hwsku = get_platform_and_hwsku_from_switch(engine, args)
    hostname = engine.run_cmd("hostname") if not args.switch_hostname else args.switch_hostname
    init_config_db_json = get_init_config_db_from_switch(engine, hwsku)
    port_configuration_dict = get_port_config_ini_ports_configuration(port_config_ini_path)
    updated_init_config_db = load_port_configuration_into_initial_switch_configuration(init_config_db_json,
                                                                                       port_configuration_dict,
                                                                                       hostname)
    save_port_config_ini_file(args)
    config_db_path = save_config_db(args, updated_init_config_db)
    save_minigraph_xml(args, hwsku, hostname)
    load_configuration_files_to_switch(engine, port_config_ini_path, config_db_path, platform, hwsku)
    reload_switch(engine)


def get_switch_resource_from_noga(args):
    """
    build ssh engine and takes the configuration files dir path from noga switch resource.
    :param args: script arguments
    :return: ssh engine to switch and path to the configuration files
    """
    engine = get_switch_engine(args.switch_ip)
    config_files_dir_path = '/auto/sw_regression/system/SONIC/MARS/conf/topo/{}'.format(args.setup_name)
    return engine, config_files_dir_path


def get_switch_resource_from_user(args):
    """
    build ssh engine and takes the port_config.ini path from user arguments.
    :param args: script arguments
    :return:  ssh engine to switch and path to port_config.ini file
    """
    engine = SSH(ip=args.switch_ip, username=args.switch_username, password=args.switch_password)
    return engine, args.port_config_ini


def get_platform_and_hwsku_from_switch(engine, args):
    """
    :param engine: ssh engine of switch
    :param args: parsed script arguments
    :return: the platform and hwsku of switch, e.g. platform = x86_64-mlnx_msn3800-r0 , hwsku =  ACS-MSN3800
    """
    logger.info("Getting switch Platform and HwSKU")
    output = engine.run_cmd("show platform summary")
    platform = re.search("Platform:\s*(.*)", output, re.IGNORECASE).group(1)
    hwsku = args.hwsku if args.hwsku is not None else re.search("HwSKU:\s*(.*)", output, re.IGNORECASE).group(1)
    return platform, hwsku


def get_configuration_files_paths(args, config_files_dir_path):
    """
    :param args:  the script arguments
    :param config_files_dir_path: the path to where the files are located
    :return: the basic/with splits configuration files path
    """
    if args.is_basic_config:
        port_config_ini_path = os.path.join(str(config_files_dir_path), "basic_{}".format(SonicConsts.PORT_CONFIG_INI))
        config_db_json_path = os.path.join(str(config_files_dir_path), "basic_{}".format(SonicConsts.CONFIG_DB_JSON))
    else:
        port_config_ini_path = os.path.join(str(config_files_dir_path), SonicConsts.PORT_CONFIG_INI)
        config_db_json_path = os.path.join(str(config_files_dir_path), SonicConsts.CONFIG_DB_JSON)
    minigraph_xml_path = os.path.join(str(config_files_dir_path), SonicConsts.MINIGRAPH_XML)
    return port_config_ini_path, config_db_json_path, minigraph_xml_path


def get_init_config_db_from_switch(engine, hwsku):
    """
    :param engine:  ssh engine of switch
    :param hwsku: the hwsku of switch, e.g. ACS-MSN3800
    :return: a json object of the init config_db.json of switch
    """
    init_config_db = engine.run_cmd("sonic-cfggen -k {} -H -j /etc/sonic/init_cfg.json --print-data".format(hwsku))
    init_config_db_json = json.loads(init_config_db)
    return init_config_db_json


def get_port_config_ini_ports_configuration(port_config_ini_path):
    """
    :param port_config_ini_path: path to valid port_config.ini file, mars/scripts/port_config.ini
    :return: a dict representing the port_config.ini info, e.g.
    { "Ethernet0": {
            "alias": "etp1",
            "index": "1",
            "lanes": "0,1,2,3",
            "speed": "10000",
            "admin_status": "up"
        }, ...
    }
    """
    with open(port_config_ini_path, 'r') as file:
        file_content = file.read()
        file.close()
    port_configuration_pattern = "(Ethernet\d+)\s*([\d+,]*\d*)\s*(etp\d+\w*)\s*(\d+)\s*(\d+)"
    port_configuration_list = re.findall(port_configuration_pattern, file_content, re.IGNORECASE)
    port_configuration_dict = get_port_configuration_as_dict(port_configuration_list)
    return port_configuration_dict


def get_port_configuration_as_dict(port_configuration_list):
    """
    :param port_configuration_list: a list of tupules representing the port_config.ini info,
    e.g. [ ("Ethernet0","etp1","0,1,2,3","10000"),...]
    :return: a dict representing the port_config.ini info, e.g.
    { "Ethernet0": {
            "alias": "etp1",
            "index": "1",
            "lanes": "0,1,2,3",
            "speed": "10000",
            "admin_status": "up"
        }, ...
    }
    """
    port_configuration_dict = {}
    for port_configurtion_tuple in port_configuration_list:
        name, lanes, alias, index, speed = port_configurtion_tuple
        port_configuration_dict[name] = {
            "alias": alias,
            "index": index,
            "lanes": lanes,
            "speed": speed,
            "admin_status": "up"
        }
    return port_configuration_dict


def load_port_configuration_into_initial_switch_configuration(init_config_db_json, port_configuration_dict, switch_hostname):
    """
    :param init_config_db_json: a json of the initial config_db.json file
    :param port_configuration_dict: a dict representing the port_config.ini info, e.g.
    { "Ethernet0": {
            "alias": "etp1",
            "index": "1",
            "lanes": "0,1,2,3",
            "speed": "10000",
            "admin_status": "up"
        }, ...
    }
    :return: an updated json of the initial config_db.json file
    """
    init_config_db_json = load_to_config_db_port_config_ini_ports(init_config_db_json, port_configuration_dict)
    init_config_db_json = set_lldp(init_config_db_json)
    init_config_db_json = remove_redundant_port(init_config_db_json, port_configuration_dict)
    init_config_db_json = set_switch_hostname(init_config_db_json, switch_hostname)
    return init_config_db_json


def load_to_config_db_port_config_ini_ports(init_config_db_json, port_configuration_dict):
    """
    :param init_config_db_json: a json of the initial config_db.json file
    :param port_configuration_dict: a dict representing the port_config.ini info, e.g.
    { "Ethernet0": {
            "alias": "etp1",
            "index": "1",
            "lanes": "0,1,2,3",
            "speed": "10000",
            "admin_status": "up"
        }, ...
    }
    :return: an updated json of the initial config_db.json file
    where the port_config.ini info is loaded to the config_db.json file.
    """
    logger.info("Load ports configuration from port_config.ini in to initial config_db json.")
    for port_name, port_info_dict in port_configuration_dict.items():
        if init_config_db_json[ConfigDbJsonConst.PORT].get(port_name):
            init_config_db_json[ConfigDbJsonConst.PORT][port_name].update(port_info_dict)
        else:
            init_config_db_json[ConfigDbJsonConst.PORT][port_name] = port_info_dict
    return init_config_db_json


def set_lldp(init_config_db_json):
    """
    :param init_config_db_json: a config_db.json file
    :return:  an updated json of the initial config_db.json file
    where the lldp is enabled
    """
    init_config_db_json[ConfigDbJsonConst.FEATURE][ConfigDbJsonConst.LLDP] = \
        {ConfigDbJsonConst.STATUS: ConfigDbJsonConst.ENABLED}
    return init_config_db_json


def remove_redundant_port(init_config_db_json, port_configuration_dict):
    """
    :param init_config_db_json: a json of the initial config_db.json file
    :param port_configuration_dict: a dict representing the port_config.ini info, e.g.
    { "Ethernet0": {
            "alias": "etp1",
            "index": "1",
            "lanes": "0,1,2,3",
            "speed": "10000",
            "admin_status": "up"
        }, ...
    }
    :return: an updated json of the initial config_db.json file where there are no
    irrelevant ports that do not appear in th port_config.ini file.
    """
    removed_ports = []
    for port_name, port_info_dict in init_config_db_json[ConfigDbJsonConst.PORT].items():
        if not port_configuration_dict.get(port_name):
            removed_ports.append(port_name)
    for port_name in removed_ports:
        init_config_db_json[ConfigDbJsonConst.PORT].pop(port_name)
    return init_config_db_json


def set_switch_hostname(init_config_db_json, switch_hostname):
    init_config_db_json[ConfigDbJsonConst.DEVICE_METADATA][ConfigDbJsonConst.LOCALHOST][ConfigDbJsonConst.HOSTNAME] = switch_hostname
    return init_config_db_json


def save_port_config_ini_file(args):
    file_name = 'basic_port_config.ini' if args.is_basic_config else 'port_config.ini'
    dst = os.path.join(args.configuration_path_dst, file_name)
    copyfile(args.port_config_ini, dst)


def save_config_db(args, config_db_json):
    """
    :param args: script parsed arguments
    :param config_db_json: an updated json of the initial config_db.json file
    :return: the config_db.json file path
    """
    file_name = 'basic_config_db.json' if args.is_basic_config else 'config_db.json'
    config_db_path = os.path.join(args.configuration_path_dst, file_name)
    logger.info("Save config_db with port configuration on to {}".format(config_db_path))
    with open(config_db_path, "w") as outfile:
        json.dump(config_db_json, outfile, indent=1)
    sleep_until_file_created(config_db_path)
    return config_db_path


def save_minigraph_xml(args, hwsku, hostname):
        """
        create the minigarph.xml file in path.
        :param args: script parsed arguments
        :param hwsku: switch hwsku
        :param hostname: switch hostname
        :return: None
        """
        p = os.path.join(str(pathlib.Path(__file__).parent.absolute()), 'minigraph_xml_files')
        file_loader = FileSystemLoader(str(p))
        env = Environment(loader=file_loader)
        env.trim_blocks = True
        env.lstrip_blocks = True
        env.rstrip_blocks = True
        template = env.get_template("{}_minigraph.xml".format(hwsku))
        file_contents = template.render(hostname=hostname)
        file_path = os.path.join(args.configuration_path_dst, 'minigraph.xml')
        f = open(file_path, "w+")
        f.write(file_contents)
        f.close()


@retry(Exception, tries=6, delay=10)
def sleep_until_file_created(file_path):
    """
    :param file_path: path to file to be created, e.g. mars/scripts/config_db.json
    :return: None, raise exception if file was not created
    """
    if not os.path.exists(file_path):
        raise Exception("file is still not created")
    else:
        logger.info("File was created in path {}.".format(file_path))


def load_configuration_files_to_switch(engine, port_config_ini_path, config_db_path, platform, hwsku):
    load_port_config_ini_to_switch(engine, port_config_ini_path, platform, hwsku)
    load_config_db_to_switch(engine, config_db_path)


@retry(Exception, tries=5, delay=2)
def load_port_config_ini_to_switch(engine, port_config_ini_path, platform, hwsku):
    """
    load the port_config.ini to switch
    :param engine:  ssh engine of switch
    :param port_config_ini_path: path to valid port_config.ini file, mars/scripts/port_config.ini
    :param platform: platform of switch, e.g.  x86_64-mlnx_msn3800-r0
    :param hwsku: hwsku of switch, e.g.  ACS-MSN3800
    :return: None
    """
    logger.info("Load port_config.ini on to switch.")
    switch_config_ini_path = "/usr/share/sonic/device/{}/{}/{}".format(platform, hwsku, SonicConsts.PORT_CONFIG_INI)
    engine.copy_file_to_host(src_path=port_config_ini_path, dst_path=switch_config_ini_path, copy_to_tmp=True)


@retry(Exception, tries=5, delay=2)
def load_config_db_to_switch(engine, config_db_path):
    """
    load the config_db.json to switch.
    :param engine:  ssh engine of switch
    :param config_db_path: path to saved config_db.json, e.g. mars/scripts/config_db.json
    :return: None
    """
    logger.info("Load modified initial config_db.json on to switch {}.".format(SonicConsts.CONFIG_DB_JSON_PATH))
    engine.copy_file_to_host(src_path=config_db_path, dst_path=SonicConsts.CONFIG_DB_JSON_PATH, copy_to_tmp=True)


@retry(Exception, tries=5, delay=2)
def load_minigraph_xml_to_switch(engine, minigraph_xml_path):
    """
    load the minigraph.xml to switch.
    :param engine:  ssh engine of switch
    :param minigraph_xml_path: path to saved minigraph.xml, e.g. mars/scripts/minigraph.xml
    :return: None
    """
    logger.info("Load minigraph.xml on to switch {}.".format(SonicConsts.MINIGRAPH_XML_PATH))
    engine.copy_file_to_host(src_path=minigraph_xml_path, dst_path=SonicConsts.MINIGRAPH_XML_PATH, copy_to_tmp=True)


@retry(Exception, tries=3, delay=10)
def reload_switch(engine):
    """
    :param engine: ssh engine of switch
    :return: None, raise exception if switch reload failed
    """
    logger.info("Reload Switch")
    res = engine.run_cmd(SonicConsts.CONFIG_RELOAD, max_loops=1000)
    # We can not check exit code because switch stuck for some time after reload config, we check for specific string
    if re.search("Job.*failed|exited.*error.*code", res, re.IGNORECASE) or "Reinitializing monit daemon" not in res:
        raise Exception("Reload of switch with split configuration has failed.")


def validate_configuration_path_dst(configuration_path_dst):
    """
    Creates the path if doesn't exist.
    :param configuration_path_dst: a path where new config_db.json and port_config.ini will be saved at.
    :return: None
    """
    if not os.path.exists(configuration_path_dst):
        os.system("sudo mkdir {}".format(configuration_path_dst))
    os.system("sudo chmod 777 {}".format(configuration_path_dst))

#######################################################################
#    Main function                                                  ###
#######################################################################


if __name__ == '__main__':
    try:
        args = init_parser()
        set_logger(args.log_level)
        apply_base_configuration(args)
        logger.info('Script Finished!')

    except Exception as e:
        traceback.print_exc()
        sys.exit(LinuxConsts.error_exit_code)
