#!/usr/bin/env python

import argparse
import logging
import sys
import traceback
import yaml
import os
import subprocess
import pathlib

sys.path.append(str(os.path.join(str(pathlib.Path(__file__).parent.absolute()), "..")))

from infra.topology_entities.topology_manager import TopologyManager
from infra.constants.constants import LinuxConsts
logger = logging.getLogger("sonic_setup_bringup")

STM_IP = "10.209.104.53"


def set_logger(log_level):
    logging.basicConfig(level=log_level,
                        format='%(asctime)s %(name)-12s %(levelname)-8s %(message)s',
                        datefmt='%m-%d %H:%M')


def init_parser():
    description = ('Functionality of the script: \n'
                   '1. Get switch connectivity via LLDP protocol.\n'
                   '2. Get additional information from switch.\n'
                   '   (number of ports in setup, switches/hosts names and IPs, type, HwSku.\n'
                   '3. Export setup information to Noga (connectivity, aliases and additional information).\n'
                   '4. create .setup file for setup.\n')

    parser = argparse.ArgumentParser(description=description)
    parser.add_argument('-f', '--arguments_file', dest='arguments_file',
                         help='A yaml file with the information about all the entities in the setup\n,'
                              'see example file sonic_setup_arguments.yaml')
    parser.add_argument('-l', '--log_level', dest='log_level', default=logging.INFO, help='log verbosity')
    parser.add_argument('-s', '--setup_name', dest='setup_name', default=None,
                        help='Specify setup name if setup name should be name differently than '
                             'sonic_<switch_type>_<switch_hostname>')
    parser.add_argument('-g', '--setup_group', dest='setup_group', default="SONiC_Canonical",
                        help='Specify setup group, if group is different than SONiC_Canonical')

    args, unknown = parser.parse_known_args()

    if unknown:
        raise Exception("unknown argument(s): {}".format(unknown))
    return args


def get_arguments_from_yaml_file(file_path):
    with open(file_path) as file:
        args = yaml.load(file, Loader=yaml.Loader)
        file.close()
    return args


def import_setup_to_noga(topology_dir_name, setup_name, setup_group):
    """
    Will import connectivity between switches based on created topology.xml to NOGA
    :param topology_dir_name: Name of directory with .xml files
    :param setup_name: the setup name in noga, e.g. SONiC_tigris_r-tigris-06
    :param setup_group: the group the setup belong to in Noga, i.e. SONiC_Canonical
    """
    cmd = "/mswg/projects/swvt/Noga/import_mars_topology.sh -f {}/topology.xml -n {} -g" \
          " Sagi -s {} -S MTR".format(topology_dir_name, setup_name, setup_group)
    rc = os.system(cmd)
    if rc:
        logger.error('failed to import setup to Noga')
        logger.error('CMD: {}'.format(cmd))


def scp_file_to_stm(file_path):
    """
    will copy given file to stm
    :param file_path: path to file to copy
    :return: None
    """
    cmd = 'sshpass -p "3tango" scp {} root@{}:/tmp'.format(file_path, STM_IP)
    logger.info("Copy to STM. CMD: %s" % cmd)
    os.system(cmd)


def import_aliases_to_noga(noga_json_file_path):
    """
    run the import alises to noga script on stm
    :param noga_json_file_path: path to the json file containing the aliases for the setup
    :return: None
    """
    logger.info("Import aliases to Noga")
    # copy JSON file & 'import to noga' script to STM
    scp_file_to_stm(noga_json_file_path)
    scp_file_to_stm("{}/import_aliases_to_noga.py".format(str(pathlib.Path(__file__).parent.absolute())))

    # Update Noga according to JSON topology
    remote_cmd = "python2.7 /tmp/import_aliases_to_noga.py --json {}".format(noga_json_file_path)
    cmd = "sshpass -p {} ssh -o 'StrictHostKeyChecking no' -t {}@{} '{}'".format("3tango", "root", STM_IP, remote_cmd)
    logger.info("CMD: %s" % cmd)
    try:
        subprocess.check_output(cmd, shell=True)
    except Exception as e:
        raise Exception("Import aliases to Noga has failed.\n please verify in Noga all setup entities "
                        "were named correctly,\n and try to run: \"{}\" on stm {} again.\n Script Error: {}"
                        .format(remote_cmd, STM_IP, e))

#######################################################################
#    Main function                                                  ###
#######################################################################


if __name__ == '__main__':
    try:
        args = init_parser()
        set_logger(args.log_level)
        setup_args_dict = get_arguments_from_yaml_file(args.arguments_file)
        tm = TopologyManager(setup_args_dict, args.setup_name)
        tm.create_topology_files()
        tm.creat_json_file_to_noga()
        import_setup_to_noga(tm.topology_dir_path, tm.setup_name, args.setup_group)
        tm.create_setup_files()
        import_aliases_to_noga(tm.noga_json_file_path)
        logger.info('Script Finished!')

    except Exception as e:
        traceback.print_exc()
        sys.exit(LinuxConsts.error_exit_code)
