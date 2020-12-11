import logging
import multiprocessing
import pytest

from ngts.tools.github_api.github_api import GitHubApi
from ngts.tools.redmine_api.redmine_api import is_redmine_issue_active

logger = logging.getLogger()
IS_SKIP_BY_RM = 'is_skip_by_rm'
RM_REASON = 'rm_reason'
IS_SKIP_BY_GITHUB = 'is_skip_by_github'
GITHUB_REASON = 'github_reason'
IS_SKIP_BY_PLATFORM = 'is_skip_by_platform'
PLATFORM_REASON = 'platform_reason'


def ngts_skip(current_platform, rm_ticket_list=None, github_ticket_list=None, platform_prefix_list=None, operand='or'):
    """
    This method will determinate whether a test case should be skipped or not, based on the input parameters
    Explanation:
    if (redmine or github ticket active) operand (dut platform in platforms_list):
        then skip test
    :param current_platform: string with current platform info
    :param rm_ticket_list: list of Redmine tickets, example: [2382525, 2382527, 2382032, 2202166]
    :param github_ticket_list: list of github issues, example: ['https://github.com/Azure/sonic-buildimage/issues/5635',
          'https://github.com/Azure/sonic-buildimage/issues/6143']
    :param platform_prefix_list: list of platforms on which we should skip test, example: ['msn3700', 'msn2']
    :param operand: 'or' or 'and'
    :return: True in case when need to skip test, else - False
    """
    if not rm_ticket_list:
        rm_ticket_list = []
    if not github_ticket_list:
        github_ticket_list = []
    if not platform_prefix_list:
        platform_prefix_list = []

    manager = multiprocessing.Manager()
    skip_dict = get_default_skip_dict(manager)

    # Run in parallel queries to Redmine, GitHub and DUT
    proc_list = list()
    proc_list.append(multiprocessing.Process(target=is_redmine_tickets_active,
                                                args=(rm_ticket_list, skip_dict,)))
    proc_list.append(multiprocessing.Process(target=is_github_tickets_active,
                                                args=(github_ticket_list, skip_dict,)))
    proc_list.append(multiprocessing.Process(target=is_current_platform_in_skip_platforms_list,
                                                args=(platform_prefix_list, current_platform, skip_dict,)))
    for proc in proc_list:
        proc.start()
    for proc in proc_list:
        proc.join(timeout=60)

    # Get skip states and reasons
    is_skip_by_rm = skip_dict[IS_SKIP_BY_RM]
    rm_reason = skip_dict[RM_REASON]
    is_skip_by_github = skip_dict[IS_SKIP_BY_GITHUB]
    github_reason = skip_dict[GITHUB_REASON]
    is_skip_by_platform = skip_dict[IS_SKIP_BY_PLATFORM]
    platform_reason = skip_dict[PLATFORM_REASON]

    skip_reasons = '\n{}\n{}\n{}'.format(rm_reason, github_reason, platform_reason)
    # Make decision about skipping or not
    eval_expression = '({is_skip_by_rm} or {is_skip_by_github}) {operand} {is_skip_by_platform}'.format(
        is_skip_by_rm=is_skip_by_rm, is_skip_by_github=is_skip_by_github, operand=operand,
        is_skip_by_platform=is_skip_by_platform)
    is_skip = eval(eval_expression)

    if is_skip:
        return pytest.skip(str(skip_reasons))
    return


def get_default_skip_dict(manager):
    skip_dict = manager.dict()
    # Set default states for skips and for reasons
    skip_dict[IS_SKIP_BY_RM] = False
    skip_dict[IS_SKIP_BY_GITHUB] = False
    skip_dict[IS_SKIP_BY_PLATFORM] = False
    skip_dict[RM_REASON] = ''
    skip_dict[GITHUB_REASON] = ''
    skip_dict[PLATFORM_REASON] = ''
    return skip_dict


def is_redmine_tickets_active(rm_ticket_list, skip_state):
    """
    Check if Redmine tickets are active
    :param rm_ticket_list: list of Redmine tickets
    :param skip_state: shared between threads dictionary
    """
    skip_state[IS_SKIP_BY_RM], rm_ticket = is_redmine_issue_active(rm_ticket_list)
    if skip_state[IS_SKIP_BY_RM]:
        skip_state[RM_REASON] = 'Skip reason - Redmine issue: https://redmine.mellanox.com/issues/{}'.format(rm_ticket)


def is_github_tickets_active(github_ticket_list, skip_state):
    """
    Check if GitHub issue are active
    :param github_ticket_list: list of GitHub issues
    :param skip_state: shared between threads dictionary
    """
    # TODO: use credentials from dedicated user
    github = GitHubApi('petrop', 'aaa44d3b783b51dafe17efb31336fd9927948a1a')
    for github_issue in github_ticket_list:
        if github.is_github_issue_active(github_issue):
            skip_state[IS_SKIP_BY_GITHUB] = True
            skip_state[GITHUB_REASON] = 'Skip reason - GitHub issue: {}'.format(github_issue)
            break


def is_current_platform_in_skip_platforms_list(platforms_list, current_platform, skip_state):
    """
    Check if current platform in skip list
    :param platforms_list: list of platforms on which test should skip
    :param current_platform: string with info about current platform
    :param skip_state: shared between threads dictionary
    """
    for platform in platforms_list:
        if platform in current_platform:
            skip_state[IS_SKIP_BY_PLATFORM] = True
            skip_state[PLATFORM_REASON] = 'Skip reason - platform is: {}'.format(platform)
            break
