import os
import sys
import csv
from itertools import compress

import pandas as pd

import urllib.request
from datetime import datetime

CUR = os.path.abspath('.')
PROJ_DIR = '/'.join(CUR.split('/')[:CUR.split('/').index('findata_fetcher')+1])
LOGS_DIR = PROJ_DIR + '/scripts/logs'
CLIST_DIR = PROJ_DIR + '/data/company_lists'
CDATA_DIR = PROJ_DIR + '/data/company_data'


def get_tkrs_from_clist(clist):
    "returns contents of clist.csv as a sorted list"
    if os.path.exists(CLIST_DIR + '/{}.csv'.format(clist)):
        with open(CLIST_DIR + '/{}.csv'.format(clist), 'r') as f:
            reader = csv.reader(f)
            tkrs = list(reader)

        tkrs = [a_list[0] for a_list in tkrs]

    else:
        tkrs = list()

    return sorted(tkrs)


def get_qrtr_from_date(date):
    "returns quarter in format of 2008-Q1"
    year, month, _ = map(int, date.split('-'))
    qrtr_num = month // 4 + 1
    return str(year) + '-Q' + str(qrtr_num)


def get_qrtr_dates_btwn_sdate_edate(sdate, edate):
    "returns end date of each quarter from sdate to edate, if it's in [s, e]"
    qrtr_dates = list()
    years = range(int(sdate[:4]), int(edate[:4])+1)

    for year in years:
        qrtr_dates.extend([str(year)+'-03-31', str(year)+'-06-30',
                           str(year)+'-09-30', str(year)+'-12-31'])

    sqrtr_num = int(sdate.split('-')[1]) // 4 + 1
    eqrtr_num = int(edate.split('-')[1]) // 4 + 1

    def date_in_range(date, sdate, edate):
        'returns true if date in [s, e] (inclusive)'
        in_range = datetime.strptime(sdate, '%Y-%m-%d') \
                <= datetime.strptime(date, '%Y-%m-%d') \
                <= datetime.strptime(edate, '%Y-%m-%d')
        return in_range

    dates_to_return = list()
    for date in qrtr_dates:
        if date_in_range(date, sdate, edate):
            dates_to_return.append(date)

    return dates_to_return
