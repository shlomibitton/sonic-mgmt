import pytest
import logging

logger = logging.getLogger()


@pytest.fixture(scope='session')
def disable_ssh_client_alive_interval(topology_obj):
    """
    Pytest fixture which are disabling ClientAliveInterval(set it to 0), for prevent SSH session disconnection
    after 15 min without activity. After chagned sshd config, we do service ssh restart and reconnect ssh engine
    :param topology_obj: topology object fixture
    """
    engine = topology_obj.players['dut']['engine']
    engine.run_cmd('sudo sed -i "s/ClientAliveInterval 900/ClientAliveInterval 0/g" /etc/ssh/sshd_config')
    engine.run_cmd('sudo service ssh restart')
    engine.disconnect()
    engine.get_engine()

    yield

    engine.run_cmd('sudo sed -i "s/ClientAliveInterval 0/ClientAliveInterval 900/g" /etc/ssh/sshd_config')
    engine.run_cmd('sudo service ssh restart')
