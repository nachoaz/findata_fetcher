# download_data_utils.py

import os
import sys
sys.path.append('../')
import time
import requests

import numpy as np
import pandas as pd

from utils.general_utils import get_year_endmonth_from_qrtr, \
                                get_stockrow_df, \
                                get_dict_from_df_cols, \
                                LOGS_DIR, CDATA_DIR

def download_xlsx_file(url, filepath):
    """downloads xlsx file at url, saves at filepath"""
    time.sleep(3)
    response = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(response.content)


def update_xlsx_file(file_to_update, file_to_use):
    """updates file_to_update with whatever contents are new in file_to_use."""
    df_to_update = get_stockrow_df(file_to_update)
    df_to_use = get_stockrow_df(file_to_use)
