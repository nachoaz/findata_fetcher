# write-processed-datafiles.py
"""
Writes TIC-feat_map-lag_months.csv files for tickers in specified ticlist,
using `feat_map` feature map and lagging by `lag_months` months.
"""
import os
import argparse
import sys

sys.path.append('../')
from utils.general_utils import get_tic_data_from_ticlist, \
                                rm_file_if_exists, LOGS_DIR
from utils.processing_utils import write_processed_datafile


def main(ticlist, feat_map, lag_months):
    logpath = os.path.join(LOGS_DIR, "_".join(["write-processed-datafiles-log",
                                               ticlist, feat_map,
                                               str(lag_months)]))
    rm_file_if_exists(logpath)

    tic_data = get_tic_data_from_ticlist(ticlist)

    if tic_data:
        print("Writing processed datafiles...")
    else:
        print("No tkrs found.")

    for tic_tuple in tic_data:
        write_processed_datafile(tic_tuple, logpath, feat_map, lag_months)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
            "ticlist",
            help="specifies list of tickers to write processed datafiles for")

    parser.add_argument(
            "feat_map",
            help="specifies which stockrow datapoints to use, what name they"
                  " should get, and what form they should be in (ttm or mrq)")

    parser.add_argument(
            "-lm", "--lag_months",
            help="specifies how many months to lag_months fundamentals",
            default=3)

    args = parser.parse_args()
    main(args.ticlist, args.feat_map, args.lag_months)
