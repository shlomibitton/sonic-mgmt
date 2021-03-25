import allure
import logging
import pytest
import time
import os
import json
import copy
import tempfile

from retry.api import retry_call


logger = logging.getLogger()
MAX_CRM_UPDATE_TIME = 5
AVAILABLE_TOLERANCE = 0.02


class ValidationParamError(Exception):
    pass


def get_main_crm_stat(env, resource):
    """
    Get crm counters of first table from 'crm show resources all' command
    :param env: pytest fixture
    :param resource: CRM resource name. Supported CRM resources:
        ipv4_route, ipv6_route, ipv4_nexthop, ipv6_nexthop, ipv4_neighbor,
        ipv6_neighbor, nexthop_group_member, nexthop_group, fdb_entry
    """
    crm_resources_all = env.sonic_cli.crm.parse_resources_table(env.dut_engine)
    res = crm_resources_all['main_resources'][resource]
    return int(res['Used Count']), int(res['Available Count'])


def get_acl_crm_stat(env, resource):
    """
    Get crm counters of third table from 'crm show resources all' command
    :param env: pytest fixture
    :param resource: CRM resource name. Supported CRM resources:
        ipv4_route, ipv6_route, ipv4_nexthop, ipv6_nexthop, ipv4_neighbor,
        ipv6_neighbor, nexthop_group_member, nexthop_group, fdb_entry
    """
    crm_resource_acl = env.sonic_cli.crm.parse_resources_table(env.dut_engine)['table_resources']
    if not crm_resource_acl:
        return None

    assert len(crm_resource_acl) == 2, 'Expect 2 entries for ACL table'
    for item in crm_resource_acl:
        if item['Resource Name'] == resource:
            current_used = item['Used Count']
            current_available = item['Available Count']
            break
    else:
        raise Exception('Incorrect CRM resource name specified. Excepted {}. Provided - {}'.format(
            'acl_entry, acl_counter', resource)
            )

    return int(current_used), int(current_available)


def verify_counters(env, resource, used, used_sign, available):
    """
    Verifies used and available counters for specific CRM resource
    :param env: pytest fixture
    :param resource: CRM resource name. For example (ipv4_route, ipv4_nexthop, nexthop_group_member, etc.)
    :param used: expected value of used counter for specific 'res' CRM resource
    :param used_sign: comparison sign of used value. For example ('==', '>=', '<=')
    :param available: expected value of available counter for specific 'res' CRM resource
    :param available_sign: comparison sign of available value. For example ('==', '>=', '<=')
    :return: Raise AssertionError if comparison does not match
    """
    if 'acl' in resource:
        current_used, current_available = get_acl_crm_stat(env, resource)
    else:
        current_used, current_available = get_main_crm_stat(env, resource)

    assert eval('{} {} {}'.format(current_used, used_sign, used)),\
        'Unexpected used count for \'{}\': expected \'{}\' {}; actual received - {}'.format(
            resource, used_sign, used, current_used
        )

    low_treshold = available - int(available * AVAILABLE_TOLERANCE)
    high_treshold = available + int(available * AVAILABLE_TOLERANCE)
    assert low_treshold <= current_available <= high_treshold,\
        'Unexpected available count for \'{}\': expected range {}...{}; actual received - {}'.format(
            resource, low_treshold, high_treshold, current_available
        )


def apply_acl_config(env, entry_num=1):
    """
    Create acl rules defined in config file
    :param env: Test environment object
    :param entry_num: Number of entries required to be created in ACL rule
    """
    base_dir = os.path.dirname(os.path.realpath(__file__))
    acl_rules_file = "acl.json"
    acl_rules_path = os.path.join(base_dir, acl_rules_file)
    dst_dir = "/tmp"

    env.dut_engine.run_cmd("mkdir -p {}".format(dst_dir))

    # Create ACL table
    env.sonic_cli.acl.create_table(env.dut_engine, tbl_name='DATAACL', tbl_type='L3', description='"DATAACL table"',
        stage='ingress')

    if entry_num == 1:
        logger.info("Generating config for ACL rule, ACL table - DATAACL")
        env.dut_engine.copy_file(source_file=acl_rules_path, dest_file=acl_rules_file, file_system=dst_dir,
                overwrite_file=True, verify_file=False)
    elif entry_num > 1:
        acl_config = json.loads(open(acl_rules_path).read())
        acl_entry_template = acl_config["acl"]["acl-sets"]["acl-set"]["dataacl"]["acl-entries"]["acl-entry"]["1"]
        acl_entry_config = acl_config["acl"]["acl-sets"]["acl-set"]["dataacl"]["acl-entries"]["acl-entry"]
        for seq_id in range(2, entry_num + 2):
            acl_entry_config[str(seq_id)] = copy.deepcopy(acl_entry_template)
            acl_entry_config[str(seq_id)]["config"]["sequence-id"] = seq_id

        with tempfile.NamedTemporaryFile(suffix=".json", prefix="acl_config", mode="w") as fp:
            json.dump(acl_config, fp)
            fp.flush()
            logger.info("Generating config for ACL rule, ACL table - DATAACL")

            env.dut_engine.copy_file(source_file=fp.name, dest_file=acl_rules_file, file_system=dst_dir,
                overwrite_file=True, verify_file=False)
    else:
        raise Exception("Incorrect number of ACL entries specified - {}".format(entry_num))

    logger.info("Applying ACL config on DUT")
    env.sonic_cli.acl.apply_config(env.dut_engine, os.path.join(dst_dir, acl_rules_file))


@pytest.mark.build
@pytest.mark.push_gate
@pytest.mark.parametrize('ip_ver,dst,mask', [('4', '2.2.2.0', 24), ('6', '2001::', 126)], ids=['ipv4', 'ipv6'])
@allure.title('Test CRM route counters')
def test_crm_route(env, cleanup, ip_ver, dst, mask):
    """
    Test doing verification of used and available CRM counters for the following resources:
    ipv4_route
    ipv6_route
    """

    vlan_iface = env.vlan_iface_40
    crm_resource = 'ipv{}_route'.format(ip_ver)
    used, available = get_main_crm_stat(env, crm_resource)

    with allure.step('Add route: {}/{} {}'.format(dst, mask, vlan_iface)):
        env.sonic_cli.route.add_route(env.dut_engine, dst, vlan_iface, mask)

    cleanup.append((env.sonic_cli.route.del_route, env.dut_engine, dst, vlan_iface, mask))
    with allure.step('Verify CRM {} counters'.format(crm_resource)):
        retry_call(
            verify_counters, fargs=[env, crm_resource, used+1, '==', available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    cleanup.pop()

    with allure.step('Remove route: {}/{} {}'.format(dst, mask, vlan_iface)):
        env.sonic_cli.route.del_route(env.dut_engine, dst, vlan_iface, mask)

    with allure.step('Verify CRM {} counters'.format(crm_resource)):
        retry_call(
            verify_counters, fargs=[env, crm_resource, used, '==', available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )


@pytest.mark.build
@pytest.mark.push_gate
@pytest.mark.parametrize("ip_ver,neighbor,neigh_mac_addr", [("4", "2.2.2.2", "11:22:33:44:55:66"), ("6", "2001::1", "11:22:33:44:55:66")])
@allure.title('Test CRM neighbor and nexthop counters')
def test_crm_neighbor_and_nexthop(env, cleanup, ip_ver, neighbor, neigh_mac_addr):
    """
    Test doing verification of used and available CRM counters for the following resources:
    ipv4_nexthop
    ipv6_nexthop
    ipv4_neighbor
    ipv6_neighbor
    """
    vlan_iface = env.vlan_iface_40
    nexthop_resource = "ipv{ip_ver}_nexthop".format(ip_ver=ip_ver)
    neighbor_resource = "ipv{ip_ver}_neighbor".format(ip_ver=ip_ver)

    nexthop_used, nexthop_available = get_main_crm_stat(env, nexthop_resource)
    neighbor_used, neighbor_available = get_main_crm_stat(env, neighbor_resource)

    with allure.step('Add neighbor: {} {} {}'.format(neighbor, neigh_mac_addr, vlan_iface)):
        env.sonic_cli.ip.add_ip_neigh(env.dut_engine, neighbor, neigh_mac_addr, vlan_iface)

    cleanup.append((env.sonic_cli.ip.add_ip_neigh, env.dut_engine, neighbor, neigh_mac_addr, vlan_iface))
    with allure.step('Verify CRM {} counters'.format(nexthop_resource)):
        retry_call(
            verify_counters, fargs=[env, nexthop_resource, nexthop_used+1, '>=', nexthop_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    with allure.step('Verify CRM {} counters'.format(neighbor_resource)):
        retry_call(
            verify_counters, fargs=[env, neighbor_resource, neighbor_used+1, '>=', neighbor_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    cleanup.pop()

    with allure.step('Remove neighbor: {} {} {}'.format(neighbor, neigh_mac_addr, vlan_iface)):
        env.sonic_cli.ip.del_ip_neigh(env.dut_engine, neighbor, neigh_mac_addr, vlan_iface)

    with allure.step('Verify CRM {} counters'.format(nexthop_resource)):
        retry_call(
            verify_counters, fargs=[env, nexthop_resource, nexthop_used, '==', nexthop_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    with allure.step('Verify CRM {} counters'.format(neighbor_resource)):
        retry_call(
            verify_counters, fargs=[env, neighbor_resource, neighbor_used, '==', neighbor_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test CRM nexthop and nexthop group counters')
def test_crm_nexthop_group_and_member(env, cleanup):
    """
    Test doing verification of used and available CRM counters for the following resources:
    nexthop_group_member
    nexthop_group
    """
    dst_ip = env.dst_ip
    mask = env.mask
    neigh_69 = env.ip_neigh_69
    neigh_40 = env.ip_neigh_40
    mac_addr_templ = '11:22:33:44:55:{}'
    vlan_69 = env.vlan_iface_69
    vlan_40 = env.vlan_iface_40
    vlan_id_69 = env.vlan_iface_69.replace('Vlan', '')
    vlan_id_40 = env.vlan_iface_40.replace('Vlan', '')
    group_member_res = 'nexthop_group_member'
    group_res = 'nexthop_group'

    group_member_used, group_member_available = get_main_crm_stat(env, group_member_res)
    group_used, group_available = get_main_crm_stat(env, group_res)

    with allure.step('Add neighbors: {} {}'.format(neigh_69, neigh_40)):
        env.sonic_cli.ip.add_ip_neigh(env.dut_engine, neigh_69, mac_addr_templ.format(vlan_id_69), vlan_69)
        env.sonic_cli.ip.add_ip_neigh(env.dut_engine, neigh_40, mac_addr_templ.format(vlan_id_40), vlan_40)
    cleanup.append((env.sonic_cli.ip.del_ip_neigh, env.dut_engine, neigh_69, mac_addr_templ.format(vlan_id_69), vlan_69))
    cleanup.append((env.sonic_cli.ip.del_ip_neigh, env.dut_engine, neigh_40, mac_addr_templ.format(vlan_id_40), vlan_40))

    with allure.step('Add route: {}/{} {}'.format(dst_ip, mask, neigh_69)):
        env.sonic_cli.route.add_route(env.dut_engine, dst_ip, neigh_69, mask)
    with allure.step('Add route: {}/{} {}'.format(dst_ip, mask, neigh_40)):
        env.sonic_cli.route.add_route(env.dut_engine, dst_ip, neigh_40, mask)

    cleanup.append((env.sonic_cli.route.del_route, env.dut_engine, dst_ip, neigh_69, mask))
    cleanup.append((env.sonic_cli.route.del_route, env.dut_engine, dst_ip, neigh_40, mask))

    with allure.step('Verify CRM nexthop_group_member counters'):
        retry_call(
            verify_counters, fargs=[env, group_member_res, group_member_used+2, '==', group_member_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    with allure.step('Verify CRM nexthop_group counters'):
        retry_call(
            verify_counters, fargs=[env, group_res, group_used+1, '==', group_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )

    with allure.step('Delete routes'.format(dst_ip, mask, neigh_40)):
        env.sonic_cli.route.del_route(env.dut_engine, dst_ip, neigh_69, mask)
        env.sonic_cli.route.del_route(env.dut_engine, dst_ip, neigh_40, mask)

    cleanup.clear()

    with allure.step('Verify CRM nexthop_group_member counters'):
        retry_call(
            verify_counters, fargs=[env, group_member_res, group_member_used, '==', group_member_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    with allure.step('Verify CRM nexthop_group counters'):
        retry_call(
            verify_counters, fargs=[env, group_res, group_used, '==', group_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test CRM FDB counters')
def test_crm_fdb_entry(env, cleanup, interfaces):
    """
    Test doing verification of used and available CRM counters for the following resources:
    fdb_entry
    """
    vlan_id = int(env.vlan_iface_40.replace('Vlan', ''))
    iface = interfaces.dut_ha_2
    fdb_resource = 'fdb_entry'
    fdb_clear_cmd = 'fdbclear'

    fdb_used, fdb_available = get_main_crm_stat(env, fdb_resource)
    with allure.step('Adding FDB config'):
        env.sonic_cli.mac.fdb_config("SET", env.dut_engine, vlan_id, iface, 1)
    cleanup.append((env.dut_engine.run_cmd, fdb_clear_cmd))

    with allure.step('Verify CRM {} counters'.format(fdb_resource)):
        retry_call(
            verify_counters, fargs=[env, fdb_resource, fdb_used+1, '==', fdb_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )

    with allure.step('Removing FDB config'):
        env.sonic_cli.mac.fdb_config("DEL", env.dut_engine, vlan_id, iface, 1)

    cleanup.pop()

    with allure.step('Verify CRM {} counters'.format(fdb_resource)):
        retry_call(
            verify_counters, fargs=[env, fdb_resource, fdb_used, '==', fdb_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )


@pytest.mark.build
@pytest.mark.push_gate
@allure.title('Test CRM ACL counters')
def test_crm_acl(env, cleanup):
    """
    Test doing verification of used and available CRM counters for the following resources:
    acl_entry
    acl_counter
    """
    acl_entry_resource = 'acl_entry'
    acl_counter_resource = 'acl_counter'

    with allure.step('Adding basic ACL config'):
        apply_acl_config(env, entry_num=1)
    cleanup.append((env.sonic_cli.acl.delete_config, env.dut_engine))

    acl_entry_used, acl_entry_available = get_acl_crm_stat(env, acl_entry_resource)
    acl_counter_used, acl_counter_available = get_acl_crm_stat(env, acl_counter_resource)

    with allure.step('Add one entry to ACL config'):
        apply_acl_config(env, entry_num=2)

    with allure.step('Verify CRM {} counters'.format(acl_entry_resource)):
        retry_call(
            verify_counters, fargs=[env, acl_entry_resource, acl_entry_used + 2, '==', acl_entry_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    with allure.step('Verify CRM {} counters'.format(acl_counter_resource)):
        retry_call(
            verify_counters, fargs=[env, acl_counter_resource, acl_counter_used + 2, '==', acl_counter_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )

    with allure.step('Remove one entry from ACL config'):
        apply_acl_config(env, entry_num=1)

    with allure.step('Verify CRM {} counters'.format(acl_entry_resource)):
        retry_call(
            verify_counters, fargs=[env, acl_entry_resource, acl_entry_used, '==', acl_entry_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    with allure.step('Verify CRM {} counters'.format(acl_counter_resource)):
        retry_call(
            verify_counters, fargs=[env, acl_counter_resource, acl_counter_used, '==', acl_counter_available],
            tries=MAX_CRM_UPDATE_TIME, delay=1, logger=None
        )
    cleanup.append((env.sonic_cli.acl.delete_config, env))
