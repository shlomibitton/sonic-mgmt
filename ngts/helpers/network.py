import netaddr

def generate_mac(num):
    """ Generate list of MAC addresses in format XX-XX-XX-XX-XX-XX """
    mac_list = list()
    for mac_postfix in range(1, num + 1):
        mac_list.append(str(netaddr.EUI(mac_postfix)))
    return mac_list
