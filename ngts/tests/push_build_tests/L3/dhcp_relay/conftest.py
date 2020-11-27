import pytest
import os

from ngts.cli_wrappers.sonic.sonic_dhcp_relay_clis import SonicDhcpRelayCli
from ngts.cli_wrappers.linux.linux_route_clis import LinuxRouteCli
from ngts.config_templates.vlan_config_template import VlanConfigTemplate
from ngts.config_templates.ip_config_template import IpConfigTemplate
from ngts.config_templates.route_config_template import RouteConfigTemplate
from ngts.config_templates.dhcp_relay_config_template import DhcpRelayConfigTemplate


@pytest.fixture(scope='package', autouse=True)
def dhcp_server_configuration(topology_obj):
    """
    Pytest fixture which are doing configuration fot dhcp server
    :param topology_obj: topology object fixture
    """
    dhcpd_conf_name = 'dhcpd.conf'
    dhcpd_conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dhcpd_conf_name)

    hbdut1 = topology_obj.ports['hb-dut-1']
    dutha2 = topology_obj.ports['dut-ha-2']
    hadut2 = topology_obj.ports['ha-dut-2']

    hb_engine = topology_obj.players['hb']['engine']
    hb_engine.copy_file(src=dhcpd_conf_path, dst=dhcpd_conf_name, workdir='/etc/dhcp/')

    # VLAN config which will be used in test
    vlan_config_dict = {
        'dut': [{'vlan_id': 690, 'vlan_members': [{dutha2: 'trunk'}]},
                {'vlan_id': 691, 'vlan_members': [{dutha2: 'trunk'}]}],
        'ha': [{'vlan_id': 690, 'vlan_members': [{hadut2: None}]},
               {'vlan_id': 691, 'vlan_members': [{hadut2: None}]}]
    }

    # IP config which will be used in test
    ip_config_dict = {
        'dut': [{'iface': 'Vlan690', 'ips': [('69.0.1.1', '24')]},
                {'iface': 'Vlan691', 'ips': [('69.1.0.1', '24')]}]
    }

    # Static route config which will be used in test
    static_route_config_dict = {
        'hb': [{'dst': '69.0.1.0', 'dst_mask': 24, 'via': ['69.0.0.1']},
               {'dst': '69.1.0.0', 'dst_mask': 24, 'via': ['69.0.0.1']}]
    }

    # DHCP Relay config which will be used in test
    dhcp_relay_config_dict = {
        'dut': [{'vlan_id': 690, 'dhcp_servers': ['69.0.0.2']},
                # Second DHCP relay for check bug: https://github.com/Azure/sonic-buildimage/issues/6053
                {'vlan_id': 691, 'dhcp_servers': ['69.0.0.2']}
        ]
    }

    VlanConfigTemplate.configuration(topology_obj, vlan_config_dict)
    IpConfigTemplate.configuration(topology_obj, ip_config_dict)
    RouteConfigTemplate.configuration(topology_obj, static_route_config_dict)
    DhcpRelayConfigTemplate.configuration(topology_obj, dhcp_relay_config_dict)

    # Create dhclient.conf with timeout of 10 sec
    ha_engine = topology_obj.players['ha']['engine']
    ha_engine.run_cmd('echo "timeout 10;" > dhclient.conf')

    dhcp_ifaces = 'bond0.69'
    hb_engine.run_cmd('sed -e "s/INTERFACESv4=\\"\\"/INTERFACESv4=\\"{}\\"/g" -i /etc/default/isc-dhcp-server'.format(dhcp_ifaces))
    hb_engine.run_cmd('/etc/init.d/isc-dhcp-server restart')

    yield

    ha_engine.run_cmd('rm -f dhclient.conf')
    hb_engine.run_cmd('sed -e "s/INTERFACESv4=\\"{}\\"/INTERFACESv4=\\"\\"/g" -i /etc/default/isc-dhcp-server'.format(dhcp_ifaces))

    DhcpRelayConfigTemplate.cleanup(topology_obj, dhcp_relay_config_dict)
    RouteConfigTemplate.cleanup(topology_obj, static_route_config_dict)
    IpConfigTemplate.cleanup(topology_obj, ip_config_dict)
    VlanConfigTemplate.cleanup(topology_obj, vlan_config_dict)


@pytest.fixture(scope='class')
def configure_additional_dhcp_server(topology_obj):
    dhcpd_conf_name = 'dhcpd.conf'
    dhcpd_template_conf_name = 'dhcpd_additional.conf'
    dhcpd_conf_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), dhcpd_template_conf_name)

    ha_engine = topology_obj.players['ha']['engine']
    dut_engine = topology_obj.players['dut']['engine']

    ha_engine.copy_file(src=dhcpd_conf_path, dst=dhcpd_conf_name, workdir='/etc/dhcp/')

    ha_engine.run_cmd('sed -e "s/INTERFACESv4=\\"\\"/INTERFACESv4=\\"bond0\\"/g" -i /etc/default/isc-dhcp-server')
    ha_engine.run_cmd('/etc/init.d/isc-dhcp-server restart')
    SonicDhcpRelayCli.add_dhcp_relay(dut_engine, 690, '30.0.0.2')
    SonicDhcpRelayCli.add_dhcp_relay(dut_engine, 691, '30.0.0.2')
    LinuxRouteCli.add_route(ha_engine, '69.0.1.0', '30.0.0.1', '24')
    LinuxRouteCli.add_route(ha_engine, '69.1.0.0', '30.0.0.1', '24')

    yield

    ha_engine.run_cmd('sed -e "s/INTERFACESv4=\\"bond0\\"/INTERFACESv4=\\"\\"/g" -i /etc/default/isc-dhcp-server')
    SonicDhcpRelayCli.del_dhcp_relay(dut_engine, 690, '30.0.0.2')
    SonicDhcpRelayCli.del_dhcp_relay(dut_engine, 691, '30.0.0.2')
    LinuxRouteCli.del_route(ha_engine, '69.0.1.0', '30.0.0.1', '24')
    LinuxRouteCli.del_route(ha_engine, '69.1.0.0', '30.0.0.1', '24')
