# download_tkr_data.py
"pulls data from stockrow.com and quandl for tkrs for which download is pending"

import os
import argparse

import requests
import urllib.request

from utils.general_utils import get_tkrs_from_clist, \
                                mkdir_if_not_exists, \
                                report_and_register_error, \
                                LOGS_DIR, CDATA_DIR


def download_tkr_srow_data(tkr, tkrdir, logpath, overwrite):
    "downloads data from srow tkr (in .xlsx format), if not already present"
    srow_dir = os.path.join(tkrdir, 'srow_data')
    mkdir_if_not_exists(srow_dir)

    base = "https://stockrow.com/api/companies/{}".format(tkr)

    piece_to_ppiece = {
            'Income Statement': 'income',
            'Balance Sheet': 'balance',
            'Cash Flow': 'cashflow',
            'Metrics': 'metrics',
            'Growth': 'growth'}

    for piece, ppiece in piece_to_ppiece.items():
        url = base + "/financials.xlsx?dimension=MRQ&section={}".format(piece)
        xlsx_filepath = os.path.join(srow_dir, "{}_{}.xlsx".format(tkr, ppiece))

        stat_pre = "\t- Writing {}".format(xlsx_filepath)

        if not os.path.exists(xlsx_filepath) or overwrite:
            try:
                response = requests.get(url)
                with open(xlsx_filepath, 'wb') as f:
                    f.write(response.content)
                print(stat_pre + ": SUCCESSFUL")

            except requests.HTTPError as e:
                report_and_register_error(stat_pre, e, logpath)

        else:
            print("\t- {} already exists.".format(xlsx_filepath))


def download_tkr_quandl_csv(tkr, tkrdir, logpath, overwrite, quandl_key):
    "downloads data from quandl for given tkr (in .csv format)"
    quandl_dir = os.path.join(tkrdir, 'quandl_data')
    mkdir_if_not_exists(quandl_dir)

    base = 'https://www.quandl.com/api/v3/datasets/WIKI/'
    url = base + '{}.csv?api_key={}'.format(tkr, quandl_key)
    quandl_filepath = os.path.join(quandl_dir, "{}_quandl.csv".format(tkr))

    stat_pre = "\t- Writing {}".format(quandl_filepath)

    if not os.path.exists(quandl_filepath) or overwrite:
        try:
            urllib.request.urlretrieve(url, quandl_filepath)
            print(stat_pre + ": SUCCESSFUL")

        except urllib.request.HTTPError as e:
            report_and_register_error(stat_pre, e, logpath)

    else:
        print("\t- {} already exists.".format(quandl_filepath))


def main(clist_pofix, quandl_key, overwrite):

    mkdir_if_not_exists(LOGS_DIR)
    mkdir_if_not_exists(CDATA_DIR)

    for mkt in ['nasdaq', 'nyse']:
        # get list of tkrs to fetch data for
        clist = "{}_{}".format(mkt, clist_pofix)
        tkrs = get_tkrs_from_clist(clist)

        # remove logfile
        logpath = LOGS_DIR + "/download_company_data_log_{}".format(clist)
        if os.path.exists(logpath):
            os.remove(logpath)
        
        # ensure market directory within CDATA_DIR exists (to house tkr data)
        mkdir_if_not_exists(CDATA_DIR + '/{}/'.format(mkt))

        # fill that market directory with tkr data
        if tkrs:
            print("\nDownloading data for {}...".format(mkt))
        else:
            print("\nNo tkrs found for {}.\n".format(mkt))

        for tkr in tkrs:
            tkrdir = CDATA_DIR + '/{}/{}'.format(mkt, tkr)

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
