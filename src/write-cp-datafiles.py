# write_cp_datafiles.py
"Writes company-list-independent data: adj_cp.csv, p_ch_pcts.csv"

import os
import argparse
import sys

sys.path.append('../')
from utils.general_utils import get_tic_data_from_ticlist, \
                                rm_file_if_exists, \
                                mkdir_if_not_exists, \
                                LOGS_DIR, TICDATA_DIR
from utils.p_ch_pcts_utils import write_adj_cps_and_p_ch_pcts_csvs


def main(ticlist, overwrite):
    # get list of tkrs to write cp_datafiles for
    tic_data = get_tic_data_from_ticlist(ticlist)

    # remove logfile
    logpath = os.path.join(LOGS_DIR, "write-cp-datafiles-log-" + ticlist)
    rm_file_if_exists(logpath)

    # fill cp_data directories with cp_datafiles
    if tic_data:
        print("Writing datafiles...")
    else:
        print("No tickers found.")

    for tic, mkt, _ in tic_data:
        ticdir = os.path.join(TICDATA_DIR, mkt, tic)

        # write cp_datafiles
        print("Writing datafile for {} ({})...".format(tic, mkt))
        write_adj_cps_and_p_ch_pcts_csvs(tic, ticdir, logpath, overwrite)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "ticlist",
        help="specifies which list of tickers to write price data for")

    parser.add_argument(
        "-o", "--overwrite",
        help="overwrite adj-cp.csv, p-ch-pcts.csv or not",
        action="store_true")

    args = parser.parse_args()
    main(args.ticlist, args.overwrite)
