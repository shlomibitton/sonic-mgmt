import netaddr
import ipaddress


def generate_mac(num):
    """ Generate list of MAC addresses in format XX-XX-XX-XX-XX-XX """
    mac_list = list()
    for mac_postfix in range(1, num + 1):
        mac_list.append(str(netaddr.EUI(mac_postfix)))
    return mac_list


def get_bpf_filter_for_ipv6_address(ipv6_address, offset, base_proto='ip6', is_filter_part_of_another_filter=False):
    """
    This method generates a bpf filter for IPv6 address inside in packet
    :param ipv6_address: ipv6 address which we need to match inside in packet
    :param offset: ipv6 address field offset in packet
    :param base_proto: base protocol, inside in it we will look for ipv6 address using offset
    :param is_filter_part_of_another_filter: if True - then at the begin of filter will be added " and ...."
    :return: string with tcpdump filter
    """
    two_bytes_size = 2

    ipv6_address_long = ipaddress.IPv6Address(ipv6_address).exploded
    ipv6_address_long_part1 = ipv6_address_long.split(':')[0]
    ipv6_address_long_part2 = ipv6_address_long.split(':')[1]
    ipv6_address_long_part3 = ipv6_address_long.split(':')[2]
    ipv6_address_long_part4 = ipv6_address_long.split(':')[3]
    ipv6_address_long_part5 = ipv6_address_long.split(':')[4]
    ipv6_address_long_part6 = ipv6_address_long.split(':')[5]
    ipv6_address_long_part7 = ipv6_address_long.split(':')[6]
    ipv6_address_long_part8 = ipv6_address_long.split(':')[7]

    if is_filter_part_of_another_filter:
        tcpdump_filter = ' and {}[{}:{}] == 0x{}'.format(base_proto, offset, two_bytes_size, ipv6_address_long_part1)
    else:
        tcpdump_filter = '{}[{}:{}] == 0x{}'.format(base_proto, offset, two_bytes_size, ipv6_address_long_part1)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 2, two_bytes_size, ipv6_address_long_part2)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 4, two_bytes_size, ipv6_address_long_part3)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 6, two_bytes_size, ipv6_address_long_part4)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 8, two_bytes_size, ipv6_address_long_part5)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 10, two_bytes_size, ipv6_address_long_part6)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 12, two_bytes_size, ipv6_address_long_part7)
    tcpdump_filter += ' and {}[{}:{}] == 0x{}'.format(base_proto, offset + 14, two_bytes_size, ipv6_address_long_part8)

    return tcpdump_filter
