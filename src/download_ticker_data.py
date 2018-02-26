# download_tic_data.py
"Pulls data from stockrow.com and quandl for tics for which download is pending"

import os
import argparse
import sys
sys.path.append('../')

from utils.general_utils import get_tic_data_from_ticlist, \
                                rm_file_if_exists, \
                                mkdir_if_not_exists, \
                                LOGS_DIR, TICDATA_DIR
from utils.download_data_utils import download_and_report_outcome

def download_tic_srow_data(tic, ticdir, logpath, overwrite):
    "Downloads data from srow tic (in .xlsx format), if not already present."
    srow_dir = os.path.join(ticdir, 'srow-data')
    mkdir_if_not_exists(srow_dir)

    base = "https://stockrow.com/api/companies/{}".format(tic)

    opiece_to_piece = [
          ('Income Statement', 'income'),
          ('Balance Sheet', 'balance'),
          ('Cash Flow', 'cashflow'),
          ('Metrics', 'metrics'),
          ('Growth', 'growth')]

    for opiece, piece in opiece_to_piece:
        url = base + "/financials.xlsx?dimension=MRQ&section={}".format(opiece)
        filepath = os.path.join(srow_dir, "{}-{}.xlsx".format(tic, piece))
        status = "\t- Writing {}".format(filepath)

        if not os.path.isfile(filepath) or overwrite:
            download_and_report_outcome(url, filepath, logpath, status)
        else:
            print("\t- {} already exists.".format(filepath))


def download_tic_quandl_csv(tic, ticdir, logpath, overwrite, quandl_key):
    "Downloads data from quandl for given tic (in .csv format)."
    quandl_dir = os.path.join(ticdir, 'quandl-data')
    mkdir_if_not_exists(quandl_dir)

    base = 'https://www.quandl.com/api/v3/datasets/WIKI'
    url = base + '/{}.csv?api_key={}'.format(tic, quandl_key)
    filepath = os.path.join(quandl_dir, "{}-quandl.csv".format(tic))

    status = "\t- Writing {}".format(filepath)

    if not os.path.isfile(filepath) or overwrite:
        download_and_report_outcome(url, filepath, logpath, status)
    else:
        print("\t- {} already exists.".format(filepath))


def main(ticlist, quandl_key, overwrite):
    """
    Downloads fundamentals as excel files from stockrow and daily trading data
    as a .csv from quandl, for tics listed in the specified ticlist.
    """
    mkdir_if_not_exists(LOGS_DIR)
    mkdir_if_not_exists(TICDATA_DIR)

    # remove logfile
    logfile_basename = "download-company-data-log-{}".format(ticlist)
    logpath = os.path.join(LOGS_DIR, logfile_basename)
    rm_file_if_exists(logpath)

    # get list of tics to fetch data for
    tic_data = get_tic_data_from_ticlist(ticlist)

    # fill that market directory with tic data
    if tic_data:
        print("Downloading data ...")
    else:
        print("No tickers found.\n")

    for tic, mkt, _ in tic_data:
        # ensure market directory within TICDATA_DIR exists (to house tic data)
        mkdir_if_not_exists(os.path.join(TICDATA_DIR, mkt))
        ticdir = os.path.join(TICDATA_DIR, mkt, tic)

        print('Fetching data for {} ({})...'.format(tic, mkt))
        download_tic_srow_data(tic, ticdir, logpath, overwrite)
        download_tic_quandl_csv(tic, ticdir, logpath, overwrite, quandl_key)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
        "ticlist",
        help="specifies which list of tickers to download data for")

    parser.add_argument(
        "quandl_key",
        help="quanld api key")

    parser.add_argument(
        "-o", "--overwrite",
        help="overwrite excel files and quandl csv or not",
        action="store_true")

    args = parser.parse_args()
    main(args.ticlist, args.quandl_key, args.overwrite)
