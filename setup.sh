#!/bin/bash

#  Updating apt index
sudo apt -y update

#  Installing software
sudo apt -y install nginx hostapd dnsmasq
sudo DEBIAN_FRONTEND=noninteractive apt install -y netfilter-persistent iptables-persistent

#  Installing dependencies
sudo apt-get -y install libhdf5-dev libhdf5-serial-dev libhdf5-103
sudo apt-get -y install libqtgui4 libqtwebkit4 libqt4-test python3-pyqt5
sudo apt-get -y install libatlas-base-dev
sudo apt-get -y install libjasper-dev

#  Creating python virtual environment
python3 -m venv env
sleep 1
source env/bin/activate

#  Installing pip requirements
python3 -m pip install --upgrade pip
python3 -m pip install -r requirements.txt

#  Setting up image database
python3 image_db.py

#  Creating nginx server block and enabling it
sudo rm /etc/nginx/sites-enabled/default
sudo echo "server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
    }
}" > /etc/nginx/sites-available/server
sudo ln /etc/nginx/sites-available/server /etc/nginx/sites-enabled/

#  Creating systemd unit file and enabling it
sudo echo "[Unit]
Description=AutoPrez Service
After=network.target

[Service]
User=root
WorkingDirectory=/home/pi/auto_presenter
ExecStartPre=/bin/sleep 5
ExecStart=/home/pi/auto_presenter/env/bin/python main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target" > /etc/systemd/system/server.service
sudo systemctl daemon-reload
sudo systemctl enable server.service
sudo systemctl start server.service

#  Unmasking and enabling hostapd for access point
sudo systemctl unmask hostapd
sudo systemctl enable hostapd

#  Updating dhcpcd configuration
sudo mv /etc/dhcpcd.conf /etc/dhcpcd.conf.old
sudo echo "hostname
clientid
persistent
option rapid_commit
option domain_name_servers, domain_name, domain_search, host_name
option classless_static_routes
option interface_mtu
require dhcp_server_identifier
slaac private
interface wlan0
    static ip_address=192.168.4.1/24
    nohook wpa_supplicant" > /etc/dhcpcd.conf

#  Enabling and configure routing
sudo echo "# https://www.raspberrypi.org/documentation/configuration/wireless/access-point-routed.md
# Enable IPv4 routing
net.ipv4.ip_forward=1" > /etc/sysctl.d/routed-ap.conf
sudo iptables -t nat -A POSTROUTING -o wlan1 -j MASQUERADE
sudo netfilter-persistent save

#  Updating dnsmasq configuration
sudo mv /etc/dnsmasq.conf /etc/dnsmasq.conf.old
sudo echo "interface=wlan0 # Listening interface
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
                # Pool of IP addresses served via DHCP
domain=wlan     # Local wireless DNS domain
address=/gw.wlan/192.168.4.1
                # Alias for this router" > /etc/dnsmasq.conf

#  Set country code
sudo rfkill unblock wlan
echo "country_code=US
interface=wlan0
ssid=RASPINET
hw_mode=g
channel=7
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase=razzledazzle
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP" > /etc/hostapd/hostapd.conf
