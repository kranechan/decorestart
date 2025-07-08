# 🔁 TP-Link Deco X50 5G Router Monitor & Auto-Rebooter

TP-Link Deco X50 5G experiences intermittent "Red Light of Death" (RLoD), causing all devices to disconnect from the internet. To address this issue, I have developed a Python automation solution deployable on a Raspberry PI or a running computer. This system continuously monitors internet connectivity and, if the internet is lost, it will logs into Deco X50 5G router’s web interface and reboots it using a headless Selenium browser.

---

## ✅ Features

- ⚡ Headless Selenium automation (Chromium/Chrome)
- 🔐 Router password stored securely in an external file
- ⏱ Randomized polling interval (min/max)
- 🌐 Fully configurable router reboot URL and ping target
- 💽 Logs to console and file
- 🛠 Runs on Windows, macOS, Linux and Raspberry Pi

---

## 🚀 Quick Start
### 1. Clone this repo
```bash
git clone https://github.com/kranechan/decorestart.git
cd decorestart
```
### 2. (Optional) Create & activate a Python virtual environment
```bash
python3 -m venv venv
source venv/bin/activate     # Windows: venv\Scripts\activate
```
### 3. Install dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```
### 4. Create your credentials file
```bash
echo "YOUR_ROUTER_PASSWORD" > cred.txt
chmod 600 cred.txt
```
### 5. Run the monitor with defaults
```bash
python deco5g_monitor.py
```

Use the built-in help to list and override any options:

```bash
python deco5g_monitor.py --help
```

## ⚙️ Command-Line Options
```text
usage: deco5g_monitor.py [-h]
                         [--cred-file CRED_FILE]
                         [--router-url ROUTER_URL]
                         [--remote REMOTE]
                         [--interval-min INTERVAL_MIN]
                         [--interval-max INTERVAL_MAX]
                         [--log-file LOG_FILE]

Ping a host; if unreachable, reboot router via its web UI.

optional arguments:
  -h, --help
                        show this help message and exit
  --cred-file CRED_FILE
                        Path to file containing router password
                        (default: ./cred.txt)
  --router-url ROUTER_URL
                        Full URL of your router’s reboot page
                        (default: http://192.168.1.1/webpages/index.html#reboot)
  --remote REMOTE       Host to test connectivity
                        (default: one.one.one.one)
  --interval-min INTERVAL_MIN
                        Minimum seconds between checks
                        (default: 10)
  --interval-max INTERVAL_MAX
                        Maximum seconds between checks
                        (default: 60)
  --log-file LOG_FILE   Path to log file
                        (default: ./event.log)
```

## 💻 Setup on a PC (Windows / macOS / Linux)
### 1. Install Python 3.10+
- Windows/macOS: Download from [python.org](python.org)
- Debian/Ubuntu:
```bash
sudo apt update
sudo apt install python3 python3-venv python3-pip
```

### 2. Clone & prepare
```bash
git clone https://github.com/kranechan/decorestart.git
cd decorestart
python3 -m venv venv
source venv/bin/activate    # Windows: venv\Scripts\activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Add your router password
```bash
echo "YOUR_ROUTER_PASSWORD" > cred.txt
chmod 600 cred.txt
```

### 4. Execute
```bash
python deco5g_monitor.py
# option to run with configuration/command line:
# python monitor.py \
# --cred-file "/home/pi/decorestart/cred.txt" \
# --remote "one.one.one.one"
#
# *Replace '\' (MacOS) with '^' (Windows CMD) or '`' (PowerShell) to move the terminal to next line
```

## 🍓 Raspberry Pi Setup
### 1. System update & install
```bash
sudo apt update && sudo apt upgrade -y
sudo apt install -y \
  python3 python3-venv python3-pip \
  chromium-browser chromium-chromedriver
```

### 2. Clone & venv
```bash
git clone https://github.com/kranechan/decorestart.git
cd decorestart #important for next step
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Credentials & run
```bash
echo "YOUR_ROUTER_PASSWORD" > cred.txt
chmod 600 cred.txt
python3 deco5g_monitor.py
# option to run with configuration/command line:
# python3 monitor.py \
# --cred-file "/home/pi/decorestart/cred.txt" \
# --remote "one.one.one.one"
```

Pi-specific flags are already enabled in the script for stability (`--no-sandbox`, `--disable-dev-shm-usage`, `--disable-gpu`).


## 🔁 Auto-Start on Boot (systemd)
### 1. Create /etc/systemd/system/decorestart.service:

```ini
[Unit]
Description=Deco 5G Network Monitor
After=network.target

[Service]
Type=simple
# Replace 'pi' with your actual username if different
User=pi
WorkingDirectory=/home/pi/decorestart
ExecStart=/home/pi/decorestart/venv/bin/python3 deco5g_monitor.py \
  --cred-file /home/pi/decorestart/cred.txt
Restart=on-failure
Environment=PATH=/home/pi/decorestart/venv/bin:/usr/bin:/bin
# to run without virtual environment replace ExecStart and Environment to the following:
#ExecStart=/usr/bin/python3 /home/pi/decorestart/deco5g_monitor.py \
#  --cred-file /home/pi/decorestart/cred.txt
#Environment=PATH=/usr/bin:/bin


[Install]
WantedBy=multi-user.target
```

### 2. Enable and start the service:

```bash
sudo systemctl daemon-reload
sudo systemctl enable decorestart
sudo systemctl start decorestart
```

### Check live logs:
```bash
journalctl -u decorestart -f
```

## 🐳 Docker (Optional)
**Dockerfile:**

```dockerfile
FROM python:3.11-slim

RUN apt-get update && apt-get install -y \
    chromium-browser chromium-chromedriver \
  && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt deco5g_monitor.py cred.txt ./
RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "deco5g_monitor.py"]
```

**Build & run:**

```bash
docker build -t decorestart .
docker run -v $(pwd)/cred.txt:/app/cred.txt decorestart
```

## 📦 requirements.txt
```text
selenium>=4.8.0,<5.0.0
webdriver-manager>=3.8.6,<4.0.0
```

© 2025 Krane Chan