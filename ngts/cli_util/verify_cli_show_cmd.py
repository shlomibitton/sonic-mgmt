import re

import allure


def verify_show_cmd(cmd_output, expected_output_list):
    """
    :param cmd_output: the command output
    i.e.,
    Name       VID  Member           Mode
    -------  -----  ---------------  --------
    Vlan500    500  Ethernet124      tagged
    Vlan600    600  Ethernet124      tagged
    Vlan690    690  Ethernet124      tagged
    Vlan691    691  Ethernet124      tagged
    Vlan700    700  PortChannel0001  untagged
    Vlan700    700  Ethernet0        tagged
    Vlan700    700  Ethernet124      tagged
    Vlan800    800  Ethernet0        tagged

    :param expected_output_list: a list of tuples composed of regular expression and match value
    indicting if regex is expect to appear or not appear in the output
    i.e., [('Vlan700\\s+700\\s+Ethernet124\\s+tagged', True),
           ('Vlan700\\s+700\\s+Ethernet0\\s+tagged', True),
           ('Vlan800\\s+800\\s+Ethernet0\\s+tagged', True)]
    :return: raise assertion error if expected output is not matched
    """
    with allure.step('Verifying output'):
        for reg_exp, expected_match_value in expected_output_list:
            actual_match_res = re.search(reg_exp, cmd_output, re.IGNORECASE) is not None
            msg = 'Assertion Error : Regex expression: {}, expected match result: {}, actual match result: {}'\
                .format(reg_exp, expected_match_value, actual_match_res)
            assert actual_match_res == expected_match_value, msg
