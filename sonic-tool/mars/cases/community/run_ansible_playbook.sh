#!/bin/bash

set -euo pipefail

cd /root/mars/workspace/sonic-mgmt/ansible

# Ansible depends on the $HOME environment variable to determine SSH ControlPath location.
#     -o 'ControlPath=/root/mars/workspace/sonic-mgmt/ansible/$HOME/.ansible/cp/ansible-ssh-%h-%p-%r'
# The test wrapper is executed in a context without $HOME environment variable. The workaround is to explicitly
# define one here:
export HOME="/root"
export ANSIBLE_CACHE_PLUGIN=memory
echo "Current home dir: ${HOME}"

echo "New current directory: $(pwd)"
echo "Arguments:"
echo $@

echo "Start to run ansible-playbook..."
ansible-playbook $@ -e allow_recover=true

