# do_everyting.py
"""
Takes care of downloading whatever needs to be downloaded, writing cp datafiles,
writing processed datafiles, and using all of that to build the datfile
(all of this corresponding to a specific ticlist, feat_map, and
"""
import argparse

import download_ticker_data, write_cp_datafiles, write_processed_datafiles,\
       write_datfile


def main(ticlist, feat_map, quandl_api_key, lag_months, overwrite, attr_to_rank):
    # var_vals = [
    #         ('ticlist', ticlist),
    #         ('feat_map', feat_map),
    #         ('quandl_api_key', quandl_api_key),
    #         ('lag_months', lag_months),
    #         ('overwrite', overwrite),
    #         ('attr_to_rank', attr_to_rank)]

    # for var, val in var_vals:
    #     print("{} is: {}".format(var, val))
    download_ticker_data.main(ticlist, quandl_api_key, overwrite)
    write_cp_datafiles.main(ticlist, overwrite)
    write_processed_datafiles.main(ticlist, feat_map, lag_months)
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

    args = parser.parse_args()
    main(args.ticlist, args.feat_map, args.quandl_key, args.lag_months,
         args.overwrite, args.attr_to_rank)
