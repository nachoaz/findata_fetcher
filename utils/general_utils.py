# general_utils.py

import os
import sys
import csv
from collections import Counter
from itertools import compress

import pandas as pd

import urllib.request
import datetime

FINDATA_FETCHER_ROOT = os.environ['FINDATA_FETCHER_ROOT']
LOGS_DIR = os.path.join(FINDATA_FETCHER_ROOT, 'misc', 'logs')
TICLIST_DIR = os.path.join(FINDATA_FETCHER_ROOT, 'data', 'ticker-lists')
TICDATA_DIR = os.path.join(FINDATA_FETCHER_ROOT, 'data', 'ticker-data')
FEATMAP_DIR = os.path.join(FINDATA_FETCHER_ROOT, 'data', 'feature-mappings')


def listdir_nohidden(path):
    """Returns non-hidden contents of directory at path as a generator."""
    return (i for i in os.listdir(path) if not i.startswith('.'))


def mkdir_if_not_exists(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def rm_file_if_exists(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)


def report_and_register_error(status, e, logpath):
    print(status + ": FAILED")
    print('\t\t* ' + str(e))
    with open(logpath, 'a') as f:
        f.write(status + ": FAILED\n")
        f.write('\t\t* ' + str(e) + '\n')


def get_tic_data_from_ticlist(ticlist):
    "Returns contents of ticlist.csv as a list of_tuples"
    ticlist_filepath = os.path.join(TICLIST_DIR, "{}.dat".format(ticlist))
    tic_data = list()
    
    if os.path.isfile(ticlist_filepath):
        with open(ticlist_filepath, 'r') as f:
            reader = csv.reader(f, delimiter=' ')
            tic_data = list(reader)

    tic_data = [tuple(data_list) for data_list in tic_data[1:]]

    return tic_data


def srow_df_poorly_formatted(df):
    """
    Returns true if stockrow df poorly formatted (missing data and/or has
    mislabeled columns.
    """
    has_unnamed_columns = any(['Unnamed' in str(col) for col in df.columns])
    theres_gaps = False

    if not has_unnamed_columns:
        try:
            years = [col.year for col in df.columns]
        except:
            years = [int(col.split('-')[0]) for col in df.columns]

        counts = Counter(years)
        is_first_year = lambda year : year == sorted(set(years))[0]
        is_last_year = lambda year : year == sorted(set(years))[-1]
        theres_gaps = sum([1 if count != 4 \
                               and not (is_first_year(year) \
                               or is_last_year(year)) \
                             else 0 for year, count in counts.items()]) >= 1

    return has_unnamed_columns or theres_gaps


def normalize_coldates(df):
    """
    Converts columns of df to be such that they're the end-of-quarter date
    that they're closest to.
    """
    def get_closest_quarter(target):
        """From https://goo.gl/TzLV2w"""
        # candidate list, nicely enough none of these
        # are in February, so the month lengths are fixed
        candidates = [
            datetime.date(target.year - 1, 12, 31),
            datetime.date(target.year, 3, 31),
            datetime.date(target.year, 6, 30),
            datetime.date(target.year, 9, 30),
            datetime.date(target.year, 12, 31),
        ]
        # take the minimum according to the absolute distance to
        # the target date.
        return min(candidates, key=lambda d: abs(target - d))

    if all([isinstance(col, pd._libs.tslib.Timestamp) for col in df.columns]):
        pass
    elif all([isinstance(col, datetime.date) for col in df.columns]):
        df.columns = [pd.Timestamp(col) for col in df.columns]
    elif all([isinstance(col, str) for col in df.columns]):
        df.columns = [pd.Timestamp(datetime.date(*map(int, col.split('-')))) \
                      for col in df.columns]
    else:
        raise Exception("Unable to normalize coldates.")

    df.columns = list(map(get_closest_quarter,
                          [col.date() for col in df.columns]))


def get_stockrow_df(sr_filepath):
    "returns excel file as pandas df, with YYYY-QX as cols"
    df = pd.read_excel(sr_filepath)

    # make sure column dates are normalized
    normalize_coldates(df)

    # make sure df is not poorly formatted
    assert not srow_df_poorly_formatted(df), \
           "df at {} is poorly formatted.".format(sr_filepath)

    # make sure df's columns go from more recent to less recent
    if df.columns[0] < df.columns[-1]:
        df = df.loc[:, df.columns[::-1]]

    # get columns in year-quarter format
    def get_quarter_from_date(date):
        return pd.Timestamp(date).quarter

    new_cols = [str(col.year) + '-Q' + str(get_quarter_from_date(col))
                for col in df.columns]
    df.columns = new_cols

    # ensure df's columns go from less recent to most recent
    df = df.loc[:, df.columns[::-1]]
    return df


def get_year_endmonth_from_qrtr(qrtr):
    year, qrtr_num = qrtr.split('-')

    if qrtr_num == 'Q1':
        month = '03'
    elif qrtr_num == 'Q2':
        month = '06'
    elif qrtr_num == 'Q3':
        month = '09'
    elif qrtr_num == 'Q4':
        month = '12'

    return year + month


def get_dict_from_df_cols(df, keycol, valcol):
    "returns dict from pandas dataframe columns as specified"
    return pd.Series(df.loc[:,valcol].values, index=df.loc[:, keycol]).to_dict()
