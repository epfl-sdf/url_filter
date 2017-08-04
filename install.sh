#!/bin/bash

virtFold="venvURL"
sudo apt-get install python3-dev python3-pip libffi-dev libssl-dev
sudo pip install virualenv
rm -rf $virtFold
virtualenv -p /usr/bin/python3 venvURL
source $virtFold/bin/activate 
pip3 install mitmproxy
pip3 install beautifulsoup4
deactivate
