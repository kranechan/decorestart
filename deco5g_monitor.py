#!/usr/bin/env python3
"""
deco5g_monitor.py

Continuously checks internet connectivity and auto-reboots a local router
via its web interface when the connection drops.
"""

import argparse
import logging
import random
import signal
import socket
import sys
import time
from dataclasses import dataclass, field
from datetime import timedelta
from pathlib import Path
from threading import Event
from typing import Optional

from selenium import webdriver
#from selenium.webdriver.chrome.service import Service
#from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import WebDriverWait


# ------------------------------------------------------------------------------
# CONFIGURATION
# ------------------------------------------------------------------------------
@dataclass
class Config:
    """All runtime settings, with defaults and CLI overrides."""
    cred_file:    Path             = Path("cred.txt")
    router_url:   str              = "http://192.168.1.1/webpages/index.html#reboot"
    remote_host:  str              = "one.one.one.one"
    poll_min:     int              = 10
    poll_max:     int              = 60
    headless:     bool             = True
    log_file:     Path             = Path("event.log")

    password:     str = field(init=False, repr=False)

    def load_password(self) -> None:
        """Read router password (first token) from cred_file."""
        if not self.cred_file.exists():
            raise FileNotFoundError(f"Credentials file not found: {self.cred_file}")
        tokens = self.cred_file.read_text().strip().split()
        if not tokens:
            raise ValueError(f"No password found in {self.cred_file}")
        self.password = tokens[0]


# ------------------------------------------------------------------------------
# ROUTER REBOOTER
# ------------------------------------------------------------------------------
class RouterRebooter:
    """Handles the Selenium-driven reboot sequence."""
    def __init__(self, cfg: Config):
        self.cfg = cfg

    def reboot(self) -> None:
        opts = webdriver.ChromeOptions()
        if self.cfg.headless:
            opts.add_argument("--headless")
        # Pi‐friendly flags
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--start-maximized")

        #ChromeDriverManager() may not work with raspberry pi 3 plus - taken out
        #service = Service(ChromeDriverManager().install())
        #driver = webdriver.Chrome(service=service, options=opts)

        driver = webdriver.Chrome(options=opts)
        wait = WebDriverWait(driver, self.cfg.poll_max)

        logging.info("→ Opening router reboot page")
        driver.get(self.cfg.router_url)

        # 1) Log in
        wait.until(EC.visibility_of_element_located((By.ID, "local-login-pwd")))
        pwd_input = driver.find_element(
            By.XPATH, "//input[contains(@class,'password-text')]"
        )
        pwd_input.send_keys(self.cfg.password)
        driver.find_element(By.ID, "local-login-button").click()

        # 2) Trigger reboot
        wait.until(EC.visibility_of_element_located((By.ID, "reboot-view")))
        reboot_btn = driver.find_element(By.ID, "reboot-button")
        driver.execute_script("arguments[0].scrollIntoView(true);", reboot_btn)
        reboot_btn.click()

        # 3) Confirm
        wait.until(EC.element_to_be_clickable((By.ID, "global-confirm-btn-ok"))).click()
        wait.until(EC.visibility_of_element_located((By.ID, "reboot-msg")))

        driver.quit()
        logging.info("→ Reboot initiated")


# ------------------------------------------------------------------------------
# MONITORING SERVICE
# ------------------------------------------------------------------------------
class Monitor:
    """
    Orchestrates connectivity checks and, on failure, reboots the router.
    """
    def __init__(self, cfg: Config):
        self.cfg = cfg
        self._stop = Event()
        self._last_up = time.monotonic()
        signal.signal(signal.SIGINT,  self._on_exit)
        signal.signal(signal.SIGTERM, self._on_exit)

    def _on_exit(self, *_):
        logging.info("Shutdown requested; exiting…")
        self._stop.set()

    @staticmethod
    def _is_connected(host: str, timeout: float = 2.0) -> bool:
        """Quick TCP check to port 80 of the remote host."""
        try:
            addr = socket.gethostbyname(host)
            with socket.create_connection((addr, 80), timeout):
                return True
        except OSError:
            return False

    @staticmethod
    def _format_uptime(seconds: float) -> str:
        td = timedelta(seconds=int(seconds))
        days, rem = td.days, td.seconds
        hrs, rem = divmod(rem, 3600)
        mins, secs = divmod(rem, 60)
        return f"{days}d {hrs}h {mins}m {secs}s"

    def run(self) -> None:
        rebooter = RouterRebooter(self.cfg)
        logging.info("▶ Starting monitor loop")
        while not self._stop.is_set():
            try:
                if not self._is_connected(self.cfg.remote_host):
                    uptime = self._format_uptime(time.monotonic() - self._last_up)
                    logging.warning(f"✖ Connection lost (was up {uptime}), rebooting…")
                    rebooter.reboot()
                    self._stop.wait(timeout=self.cfg.poll_min) #delay to let router restart

                    while not self._stop.is_set():
                        if self._is_connected(self.cfg.remote_host):
                            break
                        time.sleep(5)

                    self._last_up = time.monotonic()
                    logging.info("✔ Router back online; uptime counter reset")

                #else:
                    #logging.debug("✓ Connection OK") #taken out to not over-log

            except Exception:
                logging.exception("‼️ Error during monitoring cycle")

            wait = random.randint(self.cfg.poll_min, self.cfg.poll_max)
            #logging.debug(f"⏱ Sleeping {wait}s before next check") #taken out to not over-log
            self._stop.wait(timeout=wait)

        logging.info("■ Monitor loop terminated")


# ------------------------------------------------------------------------------
# ENTRYPOINT & CLI
# ------------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="Ping a host; if unreachable, reboot router via its web UI."
    )
    p.add_argument(
        "--cred-file", type=Path, default=Config.cred_file,
        help="Path to file containing router password."
    )
    p.add_argument(
        "--router-url", default=Config.router_url,
        help="Full URL of your router's reboot page."
    )
    p.add_argument(
        "--remote", default=Config.remote_host,
        help="Hostname to test connectivity against."
    )
    p.add_argument(
        "--interval-min", type=int, default=Config.poll_min,
        help="Minimum seconds between connectivity checks."
    )
    p.add_argument(
        "--interval-max", type=int, default=Config.poll_max,
        help="Maximum seconds between connectivity checks."
    )
    p.add_argument(
        "--log-file", type=Path, default=Config.log_file,
        help="Path to log file."
    )
    return p.parse_args()


def main():
    args = parse_args()
    cfg = Config(
        cred_file   = args.cred_file,
        router_url  = args.router_url,
        remote_host = args.remote,
        poll_min    = args.interval_min,
        poll_max    = args.interval_max,
        log_file    = args.log_file,
    )

    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s | %(asctime)s | %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(cfg.log_file),
        ],
    )

    try:
        cfg.load_password()
    except Exception as e:
        logging.critical(f"❌ Failed to load credentials: {e}")
        sys.exit(1)

    Monitor(cfg).run()


if __name__ == "__main__":
    main()