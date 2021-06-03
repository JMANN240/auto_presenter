# **AutoPrez**

## automatic presentation creation

AutoPrez is used to generate presentation images automatically. It is fully customizable, and works with any color of tracker.

---

## Pertinent Files

### - main.py: The main file that will be run, has all features (tracking, servo control, serving, etc.).

### - mirror.py: A minimal webserver/camera application to mirror what the camera sees to the client device.

---

## Installation

### ***To perform a quick default installation that should work on most RasPiOS Buster installations, run `sudo bash setup.sh`. To go through the steps yourself, follow the instructions below.***

#### *Note: you will still have to manually enable the camera and I2C with raspi-config.* 

#### *Note: The default SSID is "RASPINET" and the defulat password is "razzledazzle".*

---

It is recommended to complete this in a virtual environment, which can be created with
`python3 -m venv ENVIRONMENT_NAME`
and activated with 
`source ENVIRONMENT_NAME/bin/activate`
The required python modules are in requirements.txt and can be installed with
`python3 -m pip install -r requirements.txt`

OpenCV-Python needs to be installed as well. The preferred method is following the *How to pip install OpenCV on Raspberry Pi* section of [this site](https://www.pyimagesearch.com/2018/09/19/pip-install-opencv/). If you have trouble with this you can [build it from the source](https://docs.opencv.org/master/d2/de6/tutorial_py_setup_in_ubuntu.html) but most of the time it is as simple as installing a few dependencies and then using pip.

Finally, image_db.py will need to be run to set up the database for uploading and loading images.

It is recommended to use Nginx as a reverse proxy to serve the web interface, systemd to autostart the python script, and hostapd/dnsmasq to serve an access point/route connections ([more here](https://www.raspberrypi.org/documentation/configuration/wireless/access-point-routed.md))

#### *Note: make sure to substitute any eth0 with wlan1 if you plan on using a second wireless interface rather than ethernet*

The Nginx configuration file should be located in /etc/nginx/sites-enabled and should contain something similar to 

```nginx
server {
    listen 80;
    server_name _;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

And the systemd configuration should be located in /etc/systemd/system and should contain something similar to

```
[Unit]
Description=AutoPrez Service
After=network.target

[Service]
User=root
WorkingDirectory=/path/to/auto_presenter
ExecStartPre=/bin/sleep 5
ExecStart=/path/to/python/interpreter main.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Once the systemd config file is present, run 

`sudo systemctl daemon-reload && sudo systemctl enable server.service && sudo systemctl start server.service`

---

## Hardware/Software

This project was completed on a [Raspberry Pi 4](https://www.amazon.com/gp/product/B07TXKY4Z9/ref=ppx_yo_dt_b_asin_title_o01_s00?ie=UTF8&psc=1) using a [pan-tilt camera mount](https://www.amazon.com/Arducam-Upgraded-Camera-Platform-Raspberry/dp/B08PK9N9T4/ref=sr_1_3?dchild=1&keywords=arducam+pan+tilt&qid=1622581574&sr=8-3) and the [Raspberry Pi Camera v2](https://www.amazon.com/Raspberry-Pi-Camera-Module-Megapixel/dp/B01ER2SKFS/ref=sr_1_3?dchild=1&keywords=raspberry+pi+camera+v2&qid=1622581623&sr=8-3) and runs on python 3.7.3, nginx 1.14.2, hostapd 2.8, and dnsmasq 2.8
