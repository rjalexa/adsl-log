# adsl-log
Log performance of your ADSL connection

This program will use Ookla's speedtest command line interface (which can be found at https://www.speedtest.net/apps/cli)
and use it hourly to log your ADSL performance to a log file.

It will write an INFO message when line speeds and packet loss are in the normal range.

It will write a WARNING message when the upload, download or packet loss are below a given threshold.

It will write an ERROR message when the Internet connection does not work properly at all.

The normal upload, download and packet loss values can be customized at the beginning of the code. Another customization you might want to do is changing the default test frequency (currently 1 hour) to suit your needs (0.0167 would yield roughly one test per minute).

Only prerequisites are having an installed copy of Ookla's Speedtest CLI and a working Internet connection and the installed Python libraries as per the code's import section.

Tested on MacOS and should work just the same for Linux and other Unices with Python 3.x

To use it on Windows currently you must change the ping parameter from -c to -n within the is_internet_up function.

To launch it as a background process in Linux/MacOS you could use the following incantation:
nohup python adsllog.py & and would find it running with ps -ef | grep adsllog.py
