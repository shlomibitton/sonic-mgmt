import pytest
import logging
import os
import allure
import math
import pathlib

logger = logging.getLogger()

REGRESSION_SHARED_RESULTS_DIR = '/auto/sw_regression/system/SONIC/MARS/results'
ENV_SESSION_ID = 'SESSION_ID'
ENV_LOG_FOLDER = 'LOG_FOLDER'
CASES_DUMPS_DIR = 'cases_dumps'


@pytest.fixture(scope='session')
def session_id():
    """
    Get MARS session id from environment variables
    :return: session id
    """
    return os.environ.get(ENV_SESSION_ID, '')


@pytest.fixture(scope='session')
def log_folder(setup_name, session_id):
    """
    Get log folder from environment variables or create according to setup parameters
    :return: log folder
    """
    env_log_folder = os.environ.get(ENV_LOG_FOLDER)
    if not env_log_folder:  # default value is empty string, defined in steps file
        env_log_folder = create_dumps_dir(setup_name, session_id)
    return env_log_folder


@pytest.fixture(autouse=True)
def store_techsupport(request, topology_obj, log_folder, session_id):
    """
    Techsupport creator. Will be executed as part of teardown.
    Due to the fact that this is not the only teardown call and it is used "autouse",
     the call "teardown" not finished yet and can't get the results of "teardown"
    :param request: pytest buildin
    :param topology_obj: topology object fixture
    :param log_folder: path to store the logs and sysdump
    :param session_id: MARS session id
    """
    yield

    if request.node.rep_setup.passed and request.node.rep_call.failed:
        if session_id:
                with allure.step('The test case has failed, generating a sysdump'):
                    dut_cli_object = topology_obj.players['dut']['cli']
                    dut_engine = topology_obj.players['dut']['engine']
                    duration = get_test_duration(request)
                    remote_dump_path = dut_cli_object.general.generate_techsupport(dut_engine, duration)

                    dest_file = log_folder + '/sysdump_' + request.node.name + '.tar.gz'
                    logger.info('Copy dump {} to log folder {}'.format(remote_dump_path, log_folder))
                    dut_engine.copy_file(source_file=remote_dump_path,
                                         dest_file=dest_file,
                                         file_system='/',
                                         direction='get',
                                         overwrite_file=True,
                                         verify_file=False)
                    os.chmod(dest_file, 0o777)
        else:
            logger.info('###  Session ID was not provided, assuming this is manual run,'
                        ' sysdump will not be created  ###')


def get_test_duration(request):
    """
    Get duration of test case. Init time + test body time + 60 seconds
    :param request: pytest buildin
    :return: integer, test duration
    """
    return math.ceil(request.node.rep_setup.duration) + math.ceil(request.node.rep_call.duration) + 60


def create_dumps_dir(setup_name, session_id):
    """
    Create directory for cases dumps in shared location
    :param setup_name: name of the setup
    :param session_id: MARS session id
    :return: directory for cases dumps
    """
    folder_path = '/'.join([REGRESSION_SHARED_RESULTS_DIR, setup_name, session_id, CASES_DUMPS_DIR])
    pathlib.Path(folder_path).mkdir(parents=True, exist_ok=True)
    return folder_path
