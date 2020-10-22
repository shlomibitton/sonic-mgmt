"""

conftest.py

Defines the methods and fixtures which will be used by pytest

"""

import pytest
import logging
import os
import requests
import base64
import time

from infra.tools.topology_tools.topology_setup_utils import get_topology_by_setup_name
from ngts.cli_wrappers.sonic.sonic_cli import SonicCli
from ngts.cli_wrappers.linux.linux_cli import LinuxCli

logger = logging.getLogger()


def pytest_addoption(parser):
    """
    Parse pytest options
    :param parser: pytest buildin
    """
    logger.info('Parsing pytest options')
    parser.addoption('--setup_name', action='store', required=True, default=None,
                     help='Setup name, example: sonic_tigris_r-tigris-06')


@pytest.fixture(scope='session')
def setup_name(request):
    """
    Method for get setup name from pytest arguments
    :param request: pytest buildin
    :return: setup name
    """
    return request.config.getoption('--setup_name')


@pytest.fixture(scope='session', autouse=True)
def topology_obj(setup_name):
    """
    Fixture which create topology object before run tests and doing cleanup for ssh engines after test executed
    :param setup_name: example: sonic_tigris_r-tigris-06
    """
    logger.debug('Creating topology object')
    topology = get_topology_by_setup_name(setup_name, slow_cli=False)
    update_topology_with_cli_class(topology)
    yield topology
    logger.debug('Cleaning-up the topology object')
    for player_name, player_attributes in topology.players.items():
        player_attributes['engine'].disconnect()


def update_topology_with_cli_class(topology):
    # TODO: determine player type by topology attribute, rather than alias
    for player_key, player_info in topology.players.items():
        if player_key == 'dut':
            player_info['cli'] = SonicCli()
        else:
            player_info['cli'] = LinuxCli()


def pytest_sessionfinish(session, exitstatus):
    """
    Pytest hook which are executed after all tests before exist from program
    :param session: pytest buildin
    :param exitstatus: pytest buildin
    """
    generate_allure_report(session)


# TODO move all allure related logic to some separate place, do not leave it here in conftest.py
def generate_allure_report(pytest_session_obj):
    """
    This method create new project on allure server, upload test results to server and generate report
    :param pytest_session_obj: pytest buildin session object
    """
    allure_dir = pytest_session_obj.config.known_args_namespace.allure_report_dir
    allure_server = 'http://10.209.102.53:5050'  # TODO define somewhere allure server as constant
    project_id = (str(time.time()).replace('.', ''))
    if allure_dir:
        create_project_on_allure_server(allure_server, project_id)
        upload_results_to_allure_server(allure_dir, allure_server, project_id)
        generate_report_on_allure_server(allure_server, project_id)
    else:
        logger.error('Can not upload allure results to server, allure report folder not provided,'
                     'please provide pytest argument --alluredir')


def create_project_on_allure_server(allure_server, project_id):
    """
    This method creates new project on allure server
    :param allure_server: allure server URL, example: 'http://10.209.102.53:5050'
    :param project_id: allure project ID(name), example: '213435435' or 'custom_name'
    """
    data = {'id': project_id}

    logger.info('Creating project {} on allure server'.format(project_id))
    response = requests.post('{}/allure-docker-service/projects'.format(allure_server), json=data,
                             headers={'Content-type': 'application/json'})
    if response.status_code != 201:
        logger.error('Failed to create project on allure server, error: {}'.format(response.content))


def upload_results_to_allure_server(allure_dir, allure_server, project_id):
    """
    This method uploads files from allure results folder to allure server
    :param allure_dir: path to allure folder, example '/tmp/allure'
    :param allure_server: allure server URL, example: 'http://10.209.102.53:5050'
    :param project_id: allure project ID(name), example: '213435435' or 'custom_name'
    """
    data = {'results': get_allure_files_content(allure_dir)}

    logger.info('Sending allure results to allure server')
    response = requests.post(allure_server + '/allure-docker-service/send-results?project_id=' + project_id,
                             json=data, headers={'Content-type': 'application/json'})
    if response.status_code != 200:
        logger.error('Failed to upload results to allure server, error: {}'.format(response.content))


def get_allure_files_content(allure_dir):
    """
    This method create list with content of allure report folder
    :param allure_dir: path to allure folder, example '/tmp/allure'
    :return: list with allure folder content, example [{'file1': 'file content'}, {'file2': 'file2 content'}]
    """
    files = os.listdir(allure_dir)
    results = []

    for file in files:
        result = {}
        file_path = allure_dir + "/" + file
        if os.path.isfile(file_path):
            try:
                with open(file_path, "rb") as f:
                    content = f.read()
                    if content.strip():
                        b64_content = base64.b64encode(content)
                        result['file_name'] = file
                        result['content_base64'] = b64_content.decode('UTF-8')
                        results.append(result)
            finally:
                f.close()
    return results


def generate_report_on_allure_server(allure_server, project_id):
    """
    This method generate report on allure server and print in logs URL for allure report
    :param allure_server: allure server URL, example: 'http://10.209.102.53:5050'
    :param project_id: allure project ID(name), example: '213435435' or 'custom_name'
    """
    logger.info('Generation report on allure server')
    response = requests.get(allure_server + '/allure-docker-service/generate-report?project_id=' + project_id,
                            headers={'Content-type': 'application/json'})

    if response.status_code != 200:
        logger.error('Failed to generate report on allure server, error: {}'.format(response.content))
    else:
        report_url = response.json()['data']['report_url']
        logger.info('Allure report URL: {}'.format(report_url))
