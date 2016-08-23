#!/usr/bin/env bash

echo "Update Ubuntu ..."
apt-get install software-properties-common
# apt-add-repository ppa:ansible/ansible -y
apt-get update >/dev/null 2>&1
apt-get -y upgrade >/dev/null 2>&1

echo "Install pip ..."
apt-get install -y python-pip
apt-get install -y build-essential
apt-get install -y python-dev

echo "Install virtualenv ..."
pip install virtualenv

echo "Install git ..."
apt-get install -y git
