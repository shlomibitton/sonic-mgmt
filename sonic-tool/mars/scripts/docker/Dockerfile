FROM debian:buster

ENV APT_KEY_DONT_WARN_ON_DANGEROUS_USAGE=DontWarn
RUN apt-get update

# Install required packages
RUN apt-get install -y libpcre3-dev apt-transport-https ca-certificates curl wget logrotate \
    libc-ares2 libjson-c3 vim systemd procps libreadline7 gnupg2 lsb-release apt-utils openssh-server \
    sudo iproute2 net-tools libaio1 python-dev python-setuptools initscripts mlocate libtinfo-dev \
    less gcc make libssl-dev sqlite3 libsqlite3-dev python-lxml libxml2-dev lldpad vlan tcpdump telnet \
    isc-dhcp-client isc-dhcp-server sqlite fping git bridge-utils iperf3 autoconf linuxptp arping \
    python-pip python-scapy python3-pip tcpreplay snmp ethtool traceroute

RUN pip install remotely
RUN pip3 install daemonize

#Install FRR
RUN curl -s https://deb.frrouting.org/frr/keys.asc | apt-key add -
RUN echo deb https://deb.frrouting.org/frr $(lsb_release -s -c) frr-stable | tee -a /etc/apt/sources.list.d/frr.list

RUN apt-get install -y frr frr-pythontools
ADD docker-start /usr/sbin/docker-start
RUN sed -i 's/bgpd=no/bgpd=yes/g' /etc/frr/daemons
RUN sed -i 's/bfdd=no/bfdd=yes/g' /etc/frr/daemons


# Configure remote connection details
RUN sed -i 's/UsePAM yes/UsePAM no/g' /etc/ssh/sshd_config
RUN sed -i 's/#PermitRootLogin prohibit-password/PermitRootLogin yes/g' /etc/ssh/sshd_config
RUN echo "root:3tango" | chpasswd
RUN echo "root   ALL=(ALL)       ALL" >> /etc/sudoers
RUN ssh-keygen -t dsa -f /etc/ssh/ssh_host_dsa_key


RUN mkdir /var/run/sshd
EXPOSE 22

ENTRYPOINT ["/usr/sbin/docker-start"]
