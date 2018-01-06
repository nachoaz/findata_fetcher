# general_utils.py

import os
import sys
import csv
from collections import Counter
from itertools import compress

import pandas as pd

import urllib.request
from datetime import datetime

CUR = os.path.abspath('.')
PROJ_DIR = '/'.join(CUR.split('/')[:CUR.split('/').index('findata_fetcher')+1])
LOGS_DIR = PROJ_DIR + '/scripts/logs'
CLIST_DIR = PROJ_DIR + '/data/company_lists'
CDATA_DIR = PROJ_DIR + '/data/company_data'


def mkdir_if_not_exists(dirpath):
    if not os.path.exists(dirpath):
        os.makedirs(dirpath)


def get_stockrow_df(sr_filepath):
    "returns excel file as pandas df, with YYYY-QX as cols"
    df = pd.read_excel(sr_filepath)

    # ensure df's columns go from more recent to less recent
    if df.columns[0] < df.columns[-1]:
        df = df.loc[:, df.columns[::-1]]

    years = [col.year for col in df.columns]
    counts = Counter(years)

    def get_q_range(year):
        is_first_year = lambda year : year == sorted(set(years))[0]
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
    "returns contents of clist.csv as a sorted list"
    clist_file = CLIST_DIR + '/{}.csv'.format(clist)
    if os.path.exists(clist_file):
        with open(clist_file, 'r') as f:
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
