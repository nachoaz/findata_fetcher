# download_data_utils.py

import os
import sys
sys.path.append('../')
import time
import requests

from utils.general_utils import report_and_register_error


def download_file_from_url(url, filepath):
    """Downloads xlsx file at url, saves at filepath."""
    time.sleep(3)
    response = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(response.content)


def download_and_report_outcome(url, filepath, logpath, stat_pre, overwrite):
    """
    Downloads file at url if necessary, reports outcome in terminal screen.
    If there's an error, it's registered in logpath.
    """
    if not os.path.isfile(filepath) or overwrite:
        try:
            download_file_from_url(url, filepath)
            print(stat_pre + ": SUCCESSFUL")
        except requests.HTTPError as e:
            report_and_register_error(stat_pre, e, logpath)
    else:
        print("\t- {} already exists.".format(filepath))
