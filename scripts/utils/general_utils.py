# general_utils.py

import os
import sys
import csv
from collections import Counter
from itertools import compress

import pandas as pd

import urllib.request
import datetime

CUR = os.path.abspath('.')
PROJ_DIR = '/'.join(CUR.split('/')[:CUR.split('/').index('findata_fetcher')+1])
LOGS_DIR = PROJ_DIR + '/scripts/logs'
CLIST_DIR = PROJ_DIR + '/data/company_lists'
CDATA_DIR = PROJ_DIR + '/data/company_data'


def listdir_nohidden(path):
    """Returns non-hidden contents of directory at path as a generator."""
    return (i for i in os.listdir(path) if not i.startswith('.'))


def mkdir_if_not_exists(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def rm_file_if_exists(filepath):
    if os.path.isfile(filepath):
        os.remove(filepath)


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
    def get_q_range(year):
        if is_first_year(year):
            q_range = range(4, 4-counts[year], -1)
        else:
            q_range = range(counts[year], 0, -1)
        return q_range

    new_cols = [str(year) + '-Q' + str(qrtr_num)
                for year in sorted(set(years), reverse=True)
                for qrtr_num in get_q_range(year)]
    df.columns = new_cols[:df.shape[1]]

    # ensure df's columns go from less recent to most recent
    df = df.loc[:, df.columns[::-1]]
    return df


def report_and_register_error(stat_pre, e, logpath):
    print(stat_pre + ": FAILED")
    print('\t\t* ' + str(e))
    with open(logpath, 'a') as f:
        f.write(stat_pre + ": FAILED\n")
        f.write('\t\t* ' + str(e) + '\n')


def get_tkrs_from_clist(clist):
    "Returns contents of clist.csv as a sorted list"
    clist_filepath = os.path.join(CLIST_DIR, "{}.csv".format(clist))

    if os.path.isfile(clist_filepath):
        with open(clist_filepath, 'r') as f:
            reader = csv.reader(f)
            tkrs = list(reader)

        tkrs = [a_list[0] for a_list in tkrs]

    else:
        tkrs = list()

    return sorted(tkrs)


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
