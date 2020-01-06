"""A program to monitor your ADSL speed and warn you if it degrades.

You should change the TD value to your normal ADSL Download speed in Mbps
and the TU value for your normal ADSL upload speed in Mbps.

Prerequisites:
a) an installed version of Ookla's CLI client defined
in the SPEEDTEST_CLI constant hereunder
b) the following Python 3.x modules
c) obvisouly an active internet connected host
"""
import json
import subprocess
import time
import sys
from pathlib import Path  # python >= 3.4
import socket
import logging

# Customize the following for your own values
TD = 210  # Threshold for download speed alert (if below)
TU = 28  # Threshold for upload speed alert (if below)
SPEEDTEST_CLI = "/usr/local/bin/speedtest"  # full path of Speedtest CLI
LOG_NAME = "adsllog.log"
# usually you do not need to change any the following
TL = 0  # Threshold for packet loss alert (if exceeded)
DEFAULT_TEST_FREQUENCY = 1  # How many hours between normal line tests
SPEEDTEST_CONVERT_FACTOR = 125000  # convert speed from Ookla to MBits
REMOTE_SERVER = "www.google.com"
#  setup logging
log_file_handler = logging.FileHandler(LOG_NAME)
log_formatter = logging.Formatter(
    "%(asctime)s;%(levelname)s;%(message)s", "%Y-%m-%d %H:%M:%S"
)
log_file_handler.setFormatter(log_formatter)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
# add file handler to logger
logger.addHandler(log_file_handler)


def is_internet_up(hostname):
    """Test if DNS is working and google can be pinged.

    Unfortunately the parameter to ping is OS specific with the
    current -c good for *nix and MacOS but for Win it should be
    changed to -n.
    """
    try:
        # see if we can resolve the host name -- tells us if there is
        # a DNS listening
        host = socket.gethostbyname(hostname)
        # connect to the host -- tells us if the host is actually
        # reachable
        s = socket.create_connection((host, 80), 2)
        s.close()
        return True
    except Exception:
        pass
    return False


def st_json():
    """Run Ookla's speedtest and return JSON data."""
    process = subprocess.Popen(
        [SPEEDTEST_CLI, "-f", "json"], stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )
    stdout, stderr = process.communicate()
    if stderr:
        return False
    else:
        json_data = json.loads(stdout)
        return json_data


def main():
    """Use OOKLA's speedtest CLI to monitor ADSL line performance.

    Log measured speeds to STDOUT.
    If the UL or DL or packet losss values are below thresholds
    then send an email to warn.
    """
    print(
        f"Starting to log ADSL line performance to {LOG_NAME} file every {DEFAULT_TEST_FREQUENCY} hours.\n"
    )
    # first check the speedtest CLI is where we want
    st_cli = Path(SPEEDTEST_CLI)
    if not st_cli.is_file():
        print("{SPEEDTEST_CLI} command not found. Program quitting!\n")
        sys.exit(2)

    while True:
        # test if internet is reachable (can change in time)
        if is_internet_up(REMOTE_SERVER):
            # if internet is reachable perform the speedtest
            j_d = st_json()
            # prepare values for logging
            down_speed = j_d["download"]["bandwidth"] / \
                SPEEDTEST_CONVERT_FACTOR
            up_speed = j_d["upload"]["bandwidth"] / SPEEDTEST_CONVERT_FACTOR
            packet_loss = j_d["packetLoss"]
            test_server = j_d["server"]["host"]
            speedtest_values_string = f"{down_speed:3.1f};{up_speed:2.1f};{packet_loss};host:{test_server}"
            # check if there are anomalies
            if down_speed < TD or up_speed < TU or packet_loss > TL:
                logger.warning(f"{speedtest_values_string}")
            else:
                logger.info(f"{speedtest_values_string}")
        else:
            # Internet host cannot be resolved/reached
            speedtest_values_string = "0;0;-1"
            logger.error(f"{speedtest_values_string}")
        # depending on found ADSL quality loop after waiting some time
        time.sleep(60 * 60 * DEFAULT_TEST_FREQUENCY)


if __name__ == "__main__":
    main()
