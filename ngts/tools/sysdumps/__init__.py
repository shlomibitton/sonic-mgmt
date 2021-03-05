import pytest
import logging
import os
import allure
import math


logger = logging.getLogger()


@pytest.fixture(autouse=True)
def store_techsupport(request, topology_obj, dumps_folder, session_id):
    """
    Techsupport creator. Will be executed as part of teardown.
    Due to the fact that this is not the only teardown call and it is used "autouse",
     the call "teardown" not finished yet and can't get the results of "teardown"
    :param request: pytest buildin
    :param topology_obj: topology object fixture
    :param dumps_folder: path to store the logs and sysdump
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

                    dest_file = dumps_folder + '/sysdump_' + request.node.name + '.tar.gz'
                    logger.info('Copy dump {} to log folder {}'.format(remote_dump_path, dumps_folder))
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
