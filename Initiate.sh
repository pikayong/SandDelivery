#!/bin/bash

sudo apt update
sudo apt install python3
sudo apt-get install python3-pip
sudo apt install postgresql postgresql-client
sudo -u postgres createuser -d -R -S $USER
createdb $USER
sudo apt install python3-pip libldap2-dev libpq-dev libsasl2-dev python3-cffi
pip install -r requirements.txt
sudo apt install npm
sudo npm install -g rtlcss
python3 odoo-bin --addons-path=addons -d mydb --without-demo=True
