# do_everyting.py
"""
Takes care of downloading whatever needs to be downloaded, writing cp datafiles,
writing processed datafiles, and using all of that to build the datfile
(all of this corresponding to a specific ticlist, feat_map, and
"""
import os
import argparse
import sys
sys.path.append('../')

from multiprocessing import Pool
from progress.bar import Bar

from download_ticker_data import download_tic_srow_data,\
                                 download_tic_quandl_csv
import write_datfile
from utils.general_utils import mkdir_if_not_exists,\
                                rm_file_if_exists,\
                                get_tic_data_from_ticlist,\
                                LOGS_DIR, TICDATA_DIR
from utils.p_ch_pcts_utils import write_adj_cps_and_p_ch_pcts_csvs
from utils.processing_utils import write_processed_datafile


def get_logpaths(ticlist, feat_map, lag_months):
    logpaths_tuple = (
        os.path.join(LOGS_DIR, "download-company-data-log-{}".format(ticlist)),
        os.path.join(LOGS_DIR, "write-cp-datafiles-log-" + ticlist),
        os.path.join(LOGS_DIR, "-".join(["write-processed-datafiles-log",
                                         ticlist, feat_map, str(lag_months)]))
        )
    for logpath in logpaths_tuple:
        rm_file_if_exists(logpath)

    return logpaths_tuple


def download_data(tic_tuple, logpath, quandl_key, overwrite):
    tic, mkt, _ = tic_tuple
    ticdir = os.path.join(TICDATA_DIR, mkt, tic)

    print('Fetching data for {} ({})...'.format(tic, mkt))
    download_tic_srow_data(tic, ticdir, logpath, overwrite)
    download_tic_quandl_csv(tic, ticdir, logpath, overwrite, quandl_key)


def do_fetch_job(tic_tuple, args, logpaths):
    _, feat_map, quandl_key, lag_months, overwrite, attr_to_rank = args

    downloads_logpath,\
           cp_logpath,\
         proc_logpath = logpaths
         
    download_data(tic_tuple, downloads_logpath, quandl_key, overwrite)
    write_adj_cps_and_p_ch_pcts_csvs(tic_tuple, cp_logpath, overwrite)
    write_processed_datafile(tic_tuple, proc_logpath, feat_map, lag_months)


def main(args):
    ticlist, feat_map, _, lag_months, overwrite, attr_to_rank = args
    logpaths = get_logpaths(ticlist, feat_map, lag_months)

    tic_tuples = get_tic_data_from_ticlist(ticlist)
    if tic_tuples:
        print("Starting entire data fetching process...")
    else:
        print("No tickers found.\n")

    # create market directories
    mkts = set(tup[1] for tup in tic_tuples)
    for mkt in mkts:
        mkdir_if_not_exists(os.path.join(TICDATA_DIR, mkt))

    # fetch data
    inputs = [(tic_tuple, args, logpaths) for tic_tuple in tic_tuples]
    pool = Pool()
    bar = Bar('Processing', max=len(inputs))
    for i in pool.starmap(do_fetch_job, inputs):
        bar.next()
    bar.finish()

    # write datfile
    write_datfile.main(ticlist, feat_map, lag_months, attr_to_rank)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()

    parser.add_argument(
            "ticlist",
            help="specifies which list of tickers to download data for")

    parser.add_argument(
            "feat_map",
            help="specifies which stockrow datapoints to use, what name they"
                  " should get, and what form they should be in (ttm or mrq)")

    parser.add_argument(
            "quandl_key",
            help="quanld api key")

    parser.add_argument(
            "-lm", "--lag_months",
            help="specifies how many months to lag_months fundamentals",
            default=3)

    parser.add_argument(
            "-o", "--overwrite",
            help="overwrite excel files and quandl csv or not",
            action="store_true")

    parser.add_argument(
            "-atr", "--attr_to_rank",
            help="the names of the attributes we want percentile-ranked",
            default=['perf', 'mom1m', 'mom3m', 'mom6m', 'mom9m'],
            nargs="*")

    parsed_args = parser.parse_args()
    args = (parsed_args.ticlist, parsed_args.feat_map, parsed_args.quandl_key,
            parsed_args.lag_months, parsed_args.overwrite, 
            parsed_args.attr_to_rank)
    main(args)
