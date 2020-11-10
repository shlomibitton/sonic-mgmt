import threading
import allure


def parallel_config_runner(topology_obj, config):
    """
    Method which are running configuration for hosts and dut in parallel
    :param topology_obj: topology object fixture
    :param config: configuration dictionary, example: {'ha', ['uname -a', 'ip a'], 'hb': ['ifconfig']}
    """
    threads_list = []

    for player_alias, cmd_list in config.items():
        engine = topology_obj.players[player_alias]['engine']
        # Attach executed commands to Allure report
        commands_list = convert_list_of_commands_to_string(cmd_list)
        allure.attach(bytes(commands_list, 'utf-8'), player_alias, allure.attachment_type.TEXT)
        # Create threads for each host config
        thread = threading.Thread(target=engine.run_cmd_set, args=(cmd_list,))
        threads_list.append(thread)

    for th in threads_list:
        th.start()

    for th in threads_list:
        th.join()


def convert_list_of_commands_to_string(commands_list):
    """
    This method doing convertation for list object to string, later on it can be used for attach to allure report
    :param commands_list: list with commands
    :return: string with commands
    """
    result = ''
    for line in commands_list:
        result += '{}\n'.format(line)
    return result
