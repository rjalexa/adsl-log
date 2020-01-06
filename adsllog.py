"""A program to monitor your ADSL speed and warn you if it degrades.

Please consult the requirements.txt file to setup necessary Gmail account.
You should change the TD value to your normal ADSL Download speed in Mbps
and the TU value for your normal ADSL upload speed in Mbps.
You should also customize the two (sender and receiver) emails.
"""
import json
import subprocess
import yagmail
from datetime import datetime
import time
import sys
from pathlib import Path  # python >= 3.4
import socket

# Customize the following for your own values
TD = 210  # Threshold for download speed alert (if below)
TU = 28  # Threshold for upload speed alert (if below)
SENDER_EMAIL = "rjaalerts@gmail.com"  # A less secure Gmail account
RECEIVER_EMAIL = "gogonegro@gmail.com"  # The desired email recipient (any)
# usually you do not need to change any the following
TL = 0  # Threshold for packet loss alert (if exceeded)
DEFAULT_TEST_FREQUENCY = 24  # How many hours between normal line tests
SPEEDTEST_CLI = "/usr/local/bin/speedtest"  # full path of Speedtest CLI
SPEEDTEST_CONVERT_FACTOR = 125000  # convert speed from Ookla to MBits
REMOTE_SERVER = "www.google.com"


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


def send_errmsg(subject, testtime, json_data, frequency):
    """Send an email to desired server with speedtest warning."""
    sender = SENDER_EMAIL
    receiver = RECEIVER_EMAIL
    body = f"""
Your {json_data["isp"]} ADSL line performance is currently
below the threshold of DL:{TD} or UL:{TU} or losing packets.

Download: {json_data["download"]["bandwidth"]/124950:3.1f} Mbps
Upload  : {json_data["upload"]["bandwidth"]/124950:2.1f} Mbps

Tested on {json_data["server"]["name"]} server with
{json_data["packetLoss"]:3.3f} packet loss and {json_data["ping"]["latency"]} ping.
Timestamp (UTC): {testtime}
Retrying in {frequency} hours.
"""
    yag = yagmail.SMTP(sender)
    # Following is just to debug, will use subject and body later
    yag.send(to=receiver, subject=subject, contents=body)


def set_frequency(down, up, loss):
    """Depending on the speed degradation change email frequency.

    The returned frequency is expressed in hours.
    """
    down_degradation = down / TD
    up_degradation = up / TU
    degradation = min(down_degradation, up_degradation)
    if degradation <= 0.1:
        return 1
    elif (degradation > 0.1) and (degradation <= 0.4):
        return 3
    elif (degradation > 0.4) and (degradation <= 0.8):
        return 4
    elif (degradation > 0.8) and (degradation <= 0.9):
        return 6
    else:
        return DEFAULT_TEST_FREQUENCY


def main():
    """Use OOKLA's speedtest CLI to monitor ADSL line performance.

    Log measured speeds to STDOUT.
    If the UL or DL or packet losss values are below thresholds
    then send an email to warn.
    """
    # first check the speedtest CLI is where we want
    st_cli = Path(SPEEDTEST_CLI)
    if not st_cli.is_file():
        print("{SPEEDTEST_CLI} command not found. Program quitting!\n")
        sys.exit(2)

    while True:
        testtime = datetime.now()
        # test if internet is reachable (can change in time)
        if is_internet_up(REMOTE_SERVER):
            # if internet is reachable perform the speedtest
            j_d = st_json()
            # prepare values for logging
            down_speed = j_d["download"]["bandwidth"] / SPEEDTEST_CONVERT_FACTOR
            up_speed = j_d["upload"]["bandwidth"] / SPEEDTEST_CONVERT_FACTOR
            speedtest_values_string = (
                f"DL:{down_speed:3.1f} Mbps UL:{up_speed:2.1f} Mbps PL:{j_d['packetLoss']}"
            )
            # prepare values for anomaly email sending
            subject_td = subject_tu = subject_tl = ""
            anomalies = 0
            # now check if there are anomalies
            if down_speed < TD:
                subject_td = f"DL:{down_speed:3.1f}"
                anomalies += 1
            if up_speed < TU:
                subject_tu = f"UL:{up_speed:2.1f}"
                anomalies += 1
            if j_d["packetLoss"] > TL:
                subject_tl = f'PL:{j_d["packetLoss"]:3.0f}'
                anomalies += 1
            # if there are anomalies send the email
            if anomalies > 0:
                # set the proper test frequency depending on severity of degradation
                test_frequency = set_frequency(down_speed, up_speed, j_d["packetLoss"])
                subject = f"ADSL warning: {subject_td} {subject_tu} {subject_tl} exceeded threshold."
                send_errmsg(subject, testtime, j_d, test_frequency)
                diagnostic_string = "DEGRADED"
                email_action_string = "Email sent."
            else:
                test_frequency = DEFAULT_TEST_FREQUENCY
                email_action_string = "Email not sent."
                diagnostic_string = "NORMAL"
        else:
            # Internet host cannot be resolved/reached
            test_frequency = 1
            email_action_string = "Email not sent."
            diagnostic_string = "NO INTERNET"
            speedtest_values_string = "NO CONNECTIVITY"
        print(
            f"{testtime} - {speedtest_values_string} - Diagnosis: {diagnostic_string} - Next in {test_frequency} hours. - {email_action_string}"
        )
        # depending on found ADSL quality loop after waiting some time
        time.sleep(60 * 60 * test_frequency)


if __name__ == "__main__":
    main()
