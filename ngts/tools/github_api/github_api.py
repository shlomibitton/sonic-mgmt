import requests
import requests_cache
import logging


logger = logging.getLogger()

CACHE_EXPIRATION_TIMEOUT = 21600
CACHE_FILE_PATH = '/tmp/github_api_cache'
requests_cache.install_cache(CACHE_FILE_PATH, expire_after=CACHE_EXPIRATION_TIMEOUT)


class GitHubApi:
    """
    This class allows user to query github issues status
    Usage example:
    github = GitHubApi('user', 'api_token')
    github.is_github_issue_active(github_issue)
    """

    def __init__(self, github_username, api_token):
        self.auth = (github_username, api_token)

    @staticmethod
    def get_github_issue_api_url(issue_url):
        """
        Get correct github api URL based on browser URL from user
        :param issue_url: github issue url
        :return: github issue api url
        """
        return issue_url.replace('github.com', 'api.github.com/repos')

    def make_github_request(self, url):
        """
        Send API request to github
        :param url: github api url
        :return: dictionary with data
        """
        response = requests.get(url, auth=self.auth)
        return response.json()

    def is_github_issue_active(self, issue_url):
        """
        Check that issue active or not
        :param issue_url:  github issue URL
        :return: True/False
        """
        issue_url = self.get_github_issue_api_url(issue_url)
        response = self.make_github_request(issue_url)
        if response.get('state') == 'closed':
            if self.is_duplicate(response):
                logger.warning('GitHub issue: {} looks like duplicate and was closed. Please re-check and ignore'
                               'the test on the parent issue'.format(issue_url))
            return False
        return True

    @staticmethod
    def is_duplicate(issue_data):
        """
        Check if issue duplicate or note
        :param issue_data: github response dict
        :return: True/False
        """
        for label in issue_data['labels']:
            if 'duplicate' in label['name'].lower():
                return True
        return False
