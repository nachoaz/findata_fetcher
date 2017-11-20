# write_raw_datafiles.py
'writes company-list-independent data: adj_cp.csv, p_ch_pcts.csv, datafile.csv'

import os
import argparse
import sys
sys.path.append('../')

from utils.general_utils import get_tkrs_from_clist, \
                                LOGS_DIR, CDATA_DIR

from utils.p_ch_pcts_utils import write_adj_cps_and_p_ch_pcts_csvs

from utils.raw_datafiles_utils import write_tkr_datafile_csv


def main(clist_pofix, overwrite):

    for mkt in ["nasdaq", "nyse"]:
        clist = "{}_{}".format(mkt, clist_pofix)
        tkrs = get_tkrs_from_clist(clist)

        logpath = os.path.join(LOGS_DIR, "write_raw_datafiles_log_"+clist)
        if os.path.exists(logpath):
            os.remove(logpath)

        if tkrs:
            print("\nWriting datafiles for {}...".format(mkt))
        else:
            print("\nNo tkrs found for {}.".format(mkt))

        for tkr in tkrs:
            print("Writing datafile for {} ({})...".format(tkr, mkt))
            tkrdir = os.path.join(CDATA_DIR, "{}/{}".format(mkt, tkr))

            cp_datadir = os.path.join(tkrdir, "cp_data")
            if not os.path.exists(cp_datadir):
                os.mkdir(cp_datadir)

            write_adj_cps_and_p_ch_pcts_csvs(tkr, tkrdir, logpath, overwrite)
            write_tkr_datafile_csv(tkr, mkt, tkrdir, logpath, overwrite)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "clist_pofix",
        help="specifies which postfix to use to determine company lists")

    parser.add_argument(
        "-o", "--overwrite",
        help="overwrite adj_cp.csv, p_ch_pcts.csv, datafile.csv or not",
        action="store_true")

    args = parser.parse_args()
    main(args.clist_pofix, args.overwrite)
