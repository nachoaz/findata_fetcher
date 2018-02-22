# create_ticlist_file_from_screener_result.py
"""
Creates ticlist_file from screener result files. Screener result files must be
.csv files; the name of each of these must begin with the market in which the
tickers listed in that file are sold, and the file must contain (at least) the
columns 'Ticker' and 'Sector'.
"""

import os
import sys
import argparse

import pandas as pd

sys.path.append('../')
from utils.general_utils import FINDATA_FETCHER_ROOT, TICLIST_DIR


SCR_RES_DIR = os.path.join(FINDATA_FETCHER_ROOT, 'data', 'screener-results')


def main(ticlist_filename, *scr_res_filenames):
    processed_dfs = list()
    for scr_res_filename in scr_res_filenames:
        # note name of scr_res_file must be of form MKT_other_stuff.csv
        mkt = scr_res_filename[:scr_res_filename.find('_')].upper()
        scr_res_filepath = os.path.join(SCR_RES_DIR, scr_res_filename)
        df = pd.read_csv(scr_res_filepath)
        filtered_df = df.query("Sector != 'Financial'").filter(
                items=['Ticker', 'Sector'])
        filtered_df['Sector'] = filtered_df['Sector'].apply(
                lambda x: x.replace(' ', '_'))
        filtered_df.insert(1, 'Market', mkt)
        processed_dfs.append(filtered_df)

    ticlist_file_df = pd.concat(processed_dfs)
    ticlist_filepath = os.path.join(TICLIST_DIR, ticlist_filename)
    ticlist_file_df.to_csv(ticlist_filepath, sep=' ', index=False)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
            "ticlist_filename",
            help="the name you'd like the produced ticlist_file to have")

    parser.add_argument(
            "scr_res_filenames",
            help="the names of the screener result files you'd like the"
                 " ticlist_file to be built from.",
            nargs='*')

    args = parser.parse_args()
    main(args.ticlist_filename, *args.scr_res_filenames)
