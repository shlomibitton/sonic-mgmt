import pytest
import pathlib
import os
import logging

from ngts.constants.constants import InfraConst


logger = logging.getLogger()

ENV_SESSION_ID = 'SESSION_ID'
ENV_LOG_FOLDER = 'LOG_FOLDER'
CASES_DUMPS_DIR = 'cases_dumps'
CASES_SYSLOG_DIR = 'cases_syslog'


@pytest.fixture(scope='session')
def session_id():
    """
    Get MARS session id from environment variables
    :return: session id
    """
    session_id = os.environ.get(ENV_SESSION_ID, '')
    logger.info("SESSION_ID = '{}'".format(session_id))
    return session_id

@pytest.fixture(scope='session')
def dumps_folder(setup_name, session_id):
    """
    Get test artifact folder from environment variables or create according to setup parameters.
    Relies on 'session_id' fixture.
    :return: dumps folder
    """
    env_log_folder = os.environ.get(ENV_LOG_FOLDER)
    if not env_log_folder:  # default value is empty string, defined in steps file
        env_log_folder = create_result_dir(setup_name, session_id, CASES_DUMPS_DIR)
    return env_log_folder

@pytest.fixture(scope='session')
def log_folder(setup_name, session_id):
    """
    Get test artifact folder from environment variables or create according to setup parameters.
    Relies on 'session_id' fixture.
    :return: log folder
    """
    env_log_folder = os.environ.get(ENV_LOG_FOLDER)
    if not env_log_folder:  # default value is empty string, defined in steps file
        env_log_folder = create_result_dir(setup_name, session_id, CASES_SYSLOG_DIR)
    return env_log_folder

def create_result_dir(setup_name, session_id, suffix_path_name):
    """
    Create directory for test artifacts in shared location
    :param setup_name: name of the setup
    :param session_id: MARS session id
    :param suffix_path_name: End part of the directory name
    :return: created directory path
    """
    folder_path = '/'.join([InfraConst.REGRESSION_SHARED_RESULTS_DIR, setup_name, session_id, suffix_path_name])
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
    logger.info("Created folder - {}".format(folder_path))
    return folder_path
