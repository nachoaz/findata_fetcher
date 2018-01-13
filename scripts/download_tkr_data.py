# download_tkr_data.py
"pulls data from stockrow.com and quandl for tkrs for which download is pending"

import os
import argparse

import time
import requests
import urllib.request

from utils.general_utils import get_tkrs_from_clist, \
                                rm_file_if_exists, \
                                mkdir_if_not_exists, \
                                report_and_register_error, \
                                LOGS_DIR, CDATA_DIR

from utils.download_data_utils import download_file_from_url

                                
def download_tkr_srow_data(tkr, tkrdir, logpath, overwrite):
    "Downloads data from srow tkr (in .xlsx format), if not already present."
    srow_dir = os.path.join(tkrdir, 'srow_data')
    mkdir_if_not_exists(srow_dir)

    base = "https://stockrow.com/api/companies/{}".format(tkr)

    ppiece_to_piece = [
          ('Income Statement', 'income'),
          ('Balance Sheet', 'balance'),
          ('Cash Flow', 'cashflow'),
          ('Metrics', 'metrics'),
          ('Growth', 'growth')]

    for ppiece, piece in ppiece_to_piece:
      url = base + "/financials.xlsx?dimension=MRQ&section={}".format(ppiece)
      filepath = os.path.join(srow_dir, "{}_{}.xlsx".format(tkr, piece))
      stat_pre = "\t- Writing {}".format(filepath)

      download_and_report_outcome(url, filepath, logpath, stat_pre, overwrite)


def download_tkr_quandl_csv(tkr, tkrdir, logpath, overwrite, quandl_key):
    "Downloads data from quandl for given tkr (in .csv format)."
    quandl_dir = os.path.join(tkrdir, 'quandl_data')
    mkdir_if_not_exists(quandl_dir)

    base = 'https://www.quandl.com/api/v3/datasets/WIKI'
    url = base + '/{}.csv?api_key={}'.format(tkr, quandl_key)
    filepath = os.path.join(quandl_dir, "{}_quandl.csv".format(tkr))

    stat_pre = "\t- Writing {}".format(filepath)

    download_and_report_outcome(url, filepath, logpath, stat_pre, overwrite)


def main(clist_pofix, quandl_key, overwrite):
    """
    Downloads fundamentals as excel files from stockrow, daily trading data as a
    .csv from quandl, for tkrs listed in the specified clists. (Each clist is
    derived from the clist_pofix, and corresponds to different markets.)
    """
    mkdir_if_not_exists(LOGS_DIR)
    mkdir_if_not_exists(CDATA_DIR)

    for mkt in ['nasdaq', 'nyse']:
        # get list of tkrs to fetch data for
        clist = "{}_{}".format(mkt, clist_pofix)
        tkrs = get_tkrs_from_clist(clist)

        # remove logfile
        logfile_basename = "download_company_data_log_{}".format(clist)
        logpath = os.path.join(LOGS_DIR, logfile_basename)
        rm_file_if_exists(logpath)
        
        # ensure market directory within CDATA_DIR exists (to house tkr data)
        mkdir_if_not_exists(os.path.join(CDATA_DIR, mkt))

        # fill that market directory with tkr data
        if tkrs:
            print("\nDownloading data for {}...".format(mkt))
        else:
            print("\nNo tkrs found for {}.\n".format(mkt))

        for tkr in tkrs:
            tkrdir = os.path.join(CDATA_DIR, mkt, tkr)

            print('Fetching data for {} ({})...'.format(tkr, mkt))
            download_tkr_srow_data(tkr, tkrdir, logpath, overwrite)
            download_tkr_quandl_csv(tkr, tkrdir, logpath, overwrite, quandl_key)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "clist_pofix",
        help="specifies which postfix to use to determine company lists")

    parser.add_argument(
        "quandl_key",
        help="quanld api key")

    parser.add_argument(
        "-o", "--overwrite",
        help="overwrite excel files and quandl csv or not",
        action="store_true")

    args = parser.parse_args()
    main(args.clist_pofix, args.quandl_key, args.overwrite)
