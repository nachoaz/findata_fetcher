# write-datfile.py
"""
Concatenates the processed-datafiles of the tickers listed in `ticlist`,
percentile-ranks `attrs_to_get_rankings_for`, writes .dat file. (Selects the
processed-datafiles by their `feat_map` and their `lag_months`.)
"""

import os
import argparse
import sys
sys.path.append('../')

import pandas as pd

from utils.general_utils import get_tic_data_from_ticlist,\
                                mkdir_if_not_exists,\
                                rm_file_if_exists,\
                                report_and_register_error,\
                                LOGS_DIR, TICDATA_DIR
from utils.processing_utils import get_big_df


def main(ticlist, feat_map, lag_months, attrs_to_rank):
    dat_dir = os.path.join(os.path.dirname(TICDATA_DIR), "dat-files")
    mkdir_if_not_exists(dat_dir)
    datfilename = "-".join([ticlist, feat_map, str(lag_months)]) + ".dat"
    datfilepath = os.path.join(dat_dir, datfilename)

    tic_dfs = dict()
    tic_data = get_tic_data_from_ticlist(ticlist)

    logpath = os.path.join(LOGS_DIR, "write-datfile-log-" + ticlist)
    rm_file_if_exists(logpath)

    if tic_data:
        print("Fetching ticker processed datafiles...")
    else:
        print("No tickers found.")

    for tic, mkt, _ in tic_data:
        status = "Fetching data for {} ({})...".format(tic, mkt)
        try:
            proc_dir = os.path.join(TICDATA_DIR, mkt, tic, 'processed-data')
            proc_filepath = os.path.join(proc_dir, '{}-{}-{}.csv'.format(
                tic, feat_map, lag_months))
            tic_dfs[(tic, mkt)] = pd.read_csv(proc_filepath, index_col=0)
            print(status + ": SUCCESSFUL")
        except Exception as err:  #TODO: neater exception management here
            report_and_register_error(status, err, logpath)

    big_df = get_big_df(tic_dfs)
    big_df.to_csv(datfilepath, sep=' ', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
            "ticlist",
            help="specifies which tickers to concatenate into .dat file.")

    parser.add_argument(
            "feat_map",
            help="specifies which stockrow datapoints to use, what name they"
                 " should get, and what form they should be in (ttm or mrq).")

    parser.add_argument(
            "-lm", "--lag_months",
            help="specifies how many months to lag fundamentals",
            default=3)

    parser.add_argument(
            "-atr", "--attr_to_rank",
            help="the names of the attributes we want percentile-ranked",
            default=['perf', 'mom1m', 'mom3m', 'mom6m', 'mom9m'],
            nargs="*")

    args = parser.parse_args()
    main(args.ticlist, args.feat_map, args.lag_months, args.attr_to_rank)
