# prepare_data.py

import os
import argparse

import pandas as pd

from utils.general_utils import get_tkrs_from_clist, \
                                report_and_register_error, \
                                rm_file_if_exists, \
                                mkdir_if_not_exists, \
                                LOGS_DIR, CDATA_DIR
from utils.prepare_data_utils import get_tkr_df


def main(clist_pofix, feat_map, lag_months):

    dat_dir = os.path.join(os.path.dirname(CDATA_DIR), "dat_files")
    mkdir_if_not_exists(dat_dir)
    dat_filepath = os.path.join(dat_dir, "{}_{}_{}.dat".format(clist_pofix,
        feat_map.strip(".txt"), lag_months))

    tkr_dfs = dict()

    for mkt in ["nasdaq", "nyse"]:
        clist = "{}_{}".format(mkt, clist_pofix)
        tkrs = get_tkrs_from_clist(clist)

        logpath = os.path.join(LOGS_DIR, "prepare_data_log_" + clist)
        rm_file_if_exists(logpath)

        if tkrs:
            print("\nAppending data for {}...".format(mkt))
        else:
            print("\nNo tkrs found for {}...".format(mkt))

        for tkr in tkrs:
            stat_pre = "Appending data for {} ({})...".format(tkr, mkt)
            try:
                tkr_dfs[(tkr, mkt)] = get_tkr_df(tkr, mkt, feat_map, lag_months)
                print(stat_pre + ": SUCCESSFUL")
            except Exception as err:
                report_and_register_error(stat_pre, err, logpath)

    big_df = get_big_df(tkr_dfs)
    big_df.to_csv(dat_filepath, sep=' ', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
            "clist_pofix",
            help="specifies which postfix to use to determine company lists")

    parser.add_argument(
            "feat_map",
            help="""specifies which stockrow datapoints to use, what name they
                    should get, and what form they should be in (ttm or
                    mrq).""")

    parser.add_argument(
            "-lm", "--lag_months",
            help="specifies how many months to lag fundamentals",
            default=3)

    args = parser.parse_args()
    main(args.clist_pofix, args.feat_map, args.lag_months)
