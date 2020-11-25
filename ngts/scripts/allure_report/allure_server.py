import time
import logging
import os
import requests
import base64

logger = logging.getLogger()


def get_time_stamp_str():
    """
    This method return string with current time
    :return: string, example: 16063138520755782
    """
    current_time = time.time()
    current_time_without_dot = str(current_time).replace('.', '')
    return current_time_without_dot


class AllureServer:
    def __init__(self, allure_server_ip, allure_server_port, allure_report_dir, project_id=get_time_stamp_str()):
        self.allure_report_dir = allure_report_dir
        self.base_url = 'http://{}:{}/allure-docker-service'.format(allure_server_ip, allure_server_port)
        self.project_id = project_id
        self.http_headers = {'Content-type': 'application/json'}

    def generate_allure_report(self):
        """
        This method creates new project on allure server, uploads test results to server and generates report
        """
        self.create_project_on_allure_server()
        self.upload_results_to_allure_server()
        self.generate_report_on_allure_server()

    def create_project_on_allure_server(self):
        """
        This method creates new project on allure server
        """
        data = {'id': self.project_id}
        url = self.base_url + '/projects'

        logger.info('Creating project {} on allure server'.format(self.project_id))
        response = requests.post(url, json=data, headers=self.http_headers)
        if response.raise_for_status():
            logger.error('Failed to create project on allure server, error: {}'.format(response.content))

    def upload_results_to_allure_server(self):
        """
        This method uploads files from allure results folder to allure server
        """
        data = {'results': self.get_allure_files_content()}
        url = self.base_url + '/send-results?project_id=' + self.project_id

        logger.info('Sending allure results to allure server')
        response = requests.post(url, json=data, headers=self.http_headers)
        if response.raise_for_status():
            logger.error('Failed to upload results to allure server, error: {}'.format(response.content))

    def get_allure_files_content(self):
        """
        This method creates a list all files under allure report folder
        :return: list with allure folder content, example [{'file1': 'file content'}, {'file2': 'file2 content'}]
        """
        files = os.listdir(self.allure_report_dir)
        results = []

        for file in files:
            result = {}
            file_path = self.allure_report_dir + "/" + file
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

    def generate_report_on_allure_server(self):
        """
        This method would generate the report on the remote allure server and display the report URL in the log
        """
        logger.info('Generating report on allure server')
        url = self.base_url + '/generate-report?project_id=' + self.project_id
        response = requests.get(url, headers=self.http_headers)

        if response.raise_for_status():
            logger.error('Failed to generate report on allure server, error: {}'.format(response.content))
        else:
            report_url = response.json()['data']['report_url']
            logger.info('Allure report URL: {}'.format(report_url))
