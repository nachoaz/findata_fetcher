# download_data_utils.py

import os
import sys
sys.path.append('../')
import time
import requests

from utils.general_utils import report_and_register_error
from misc.errors.my_errors import HTTPResponseNotOkException


def download_file_from_url(url, filepath):
    """Downloads file at url, saves at filepath."""
    time.sleep(3)
    response = requests.get(url)
    if response.status_code == 200:
        with open(filepath, 'wb') as f:
            f.write(response.content)
    elif response.status_code == 404:
        raise HTTPResponseNotOkException("HTTP Status 404: Not Found.")
    else:
        raise HTTPResponseNotOkException(
                "HTTP Status: {}".format(response.status_code))


def download_and_report_outcome(url, filepath, logpath, stat_pre):
    """
    Downloads file at url if necessary, reports outcome in terminal screen.
    If there's an error, it's registered in logpath.
    """
    try:
        download_file_from_url(url, filepath)
        print(stat_pre + ": SUCCESSFUL")
    except HTTPResponseNotOkException as e:
        report_and_register_error(stat_pre, e, logpath)
