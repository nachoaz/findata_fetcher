# prepare_data.py

import os
import argparse
import sys
sys.path.append('../')

import pandas as pd

from utils.general_utils import LOGS_DIR, CDATA_DIR, get_tkrs_from_clist
from utils.prepare_data_utils import get_tkr_df


def main(clist_pofix, feat_map, lag_months, overwrite):

    tkr_dfs = dict()

    for mkt in ["nasdaq", "nyse"]:
        clist = "{}_{}".format(mkt, clist_pofix)
        tkrs = get_tkrs_from_clist(clist)

        logpath = os.path.join(LOGS_DIR, "prepare_data_log_" + clist)
        if os.path.exists(logpath):
            os.remove(logpath)

        if tkrs:
            print("\nAppending data for {}...".format(mkt))
        else:
            print("\nNo tkrs found for {}...".format(mkt))

        for tkr in tkrs:
            stat_pre = "Appending data for {} ({})...".format(tkr, mkt)
            try:
                tkr_dfs[(tkr, mkt)] = get_tkr_df(tkr, mkt, feat_map, lag_months)
                print(stat_pre + ' SUCCESS!')
            except Exception as err:
                print(stat_pre + ' FAILED')
                print(err)

    big_df = pd.concat(tkr_dfs.values())
