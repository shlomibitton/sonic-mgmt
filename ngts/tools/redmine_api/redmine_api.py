import requests


INACTIVE_STATES = ['Fixed', 'Rejected', 'Closed (Rejected)', 'Closed']
ROOT_ISSUE = 'root_issue'
STATUS = 'status'


def is_redmine_issue_active(issues_list):
    """
    Check that at least one issue active
    :param issues_list: issue IDs list, example: [12345, 56789]
    :return: True/False, ISSUE_ID/''
    """
    status, issue = False, ''
    issues_status_dict = get_issues_status(issues_list)
    for issue_id, state in issues_status_dict.items():
        if state not in INACTIVE_STATES:
            status, issue = True, issue_id
            break
    return status, issue


def get_issues_status(issues_list):
    """
    Method which gets issues status from Redmine
    :param issues_list: issue IDs list, example: [12345, 56789]
    :return: issue status_dict, example: {'12345': 'Closed'}
    """
    # TODO: use credentials from dedicated user
    redmine_api_url = 'https://redmine.mellanox.com/issues/mars_statuses.json'
    api_key = 'df18f9458bc323698ce182b4f43f1f0b44daf527'
    headers = {
        'Content-Type': "application/json",
        'X-Redmine-API-Key': api_key
    }
    body = {"ids": issues_list}
    issues_status_response = requests.post(redmine_api_url, json=body, headers=headers).json()

    issues_status_dict = {}
    for issue in issues_list:
        issue_id_str = str(issue)
        if issues_status_response[issue_id_str].get(ROOT_ISSUE):
            issues_status_dict[issue_id_str] = issues_status_response[issue_id_str][ROOT_ISSUE][STATUS]
        else:
            issues_status_dict[issue_id_str] = issues_status_response[issue_id_str][STATUS]

    return issues_status_dict

