# p_change_pcts_utils.py

import os

import numpy as np
import pandas as pd

from utils.general_utils import get_qrtr_dates_btwn_sdate_edate


def write_and_get_adj_cp_csv(adj_cppath, quandl_path, logpath):
    stat_pre = "\t- Writing {}".format(adj_cppath)
    try:
        df = pd.read_csv(quandl_path)
        df_to_write = df.loc[:, ['Date', 'Adj. Close']]
        df_to_write.columns = ['date', 'price']
        df_to_write.to_csv(adj_cppath, index=False)
        print(stat_pre + ': SUCCESSFUL')

    except:
        df_to_write = None
        print(stat_pre + ': FAILED')
        with open(logpath, 'a') as f:
            f.write(stat_pre + ": FAILED\n")

    return df_to_write


def get_prices_df(adj_cp_df, adj_cppath):
    "returns prices_df for tkr (for all available dates), using forward fill"
    if adj_cp_df is None:
        prices_df = pd.read_csv(adj_cppath, header=0, names=['date', 'price'])
    else:
        prices_df = adj_cp_df

    sdate = prices_df.iloc[-1]['date']
    edate = prices_df.iloc[0]['date']
    dates = pd.date_range(sdate, edate).astype(str)
    full_df = pd.DataFrame(dates, columns=['date'])

    full_df = full_df.merge(prices_df, on='date', how='left')
    full_df = full_df.fillna(method='ffill')

    return full_df, sdate, edate


def get_p_ch_pcts_df(adj_cp_df, adj_cppath):
    "returns p_ch_pcts_df for tkr"
    # TODO make this pretty in 80 lines (see pandas slicing)
    prices_df, sdate, edate = get_prices_df(adj_cp_df, adj_cppath)

    price_ch_pcts = list()
    q_edates = get_qrtr_dates_btwn_sdate_edate(sdate, edate)

    for i in range(4, len(q_edates)):
        curr_price = prices_df.loc[prices_df['date'] == q_edates[i]]['price'].values[0]

        prev_three_price = prices_df.loc[prices_df['date'] == q_edates[i-1]]['price'].values[0]
        prev_six_price = prices_df.loc[prices_df['date'] == q_edates[i-2]]['price'].values[0]
        prev_nine_price = prices_df.loc[prices_df['date'] == q_edates[i-3]]['price'].values[0]
        prev_twelve_price = prices_df.loc[prices_df['date'] == q_edates[i-4]]['price'].values[0]

        pct_ch_three = (curr_price - prev_three_price) / prev_three_price * 100
        pct_ch_six = (curr_price - prev_six_price) / prev_six_price * 100
        pct_ch_nine = (curr_price - prev_nine_price) / prev_nine_price * 100
        pct_ch_twelve = (curr_price - prev_twelve_price) / prev_twelve_price * 100

        price_ch_pcts.append((q_edates[i], pct_ch_three, pct_ch_six, 
                              pct_ch_nine, pct_ch_twelve))

    df_columns = ['date', 'pct_ch_three', 'pct_ch_six',
                  'pct_ch_nine', 'pct_ch_twelve']

    price_ch_pcts_df = pd.DataFrame(price_ch_pcts, columns=df_columns)

    return price_ch_pcts_df


def write_p_ch_pcts_csv(logpath, p_ch_pctspath, adj_cp_df, adj_cppath):
    "writes tkr_p_ch_pcts.csv for tkr, if it doesn't already exist"
    stat_pre = '\t- Writing {}'.format(p_ch_pctspath)

    try:
        p_ch_pcts_df = get_p_ch_pcts_df(adj_cp_df, adj_cppath)
        p_ch_pcts_df.to_csv(p_ch_pctspath, index=False)
        print(stat_pre + ': SUCCESSFUL')

    except:
        print(stat_pre + ': FAILED')
        with open(logpath, 'a') as g:
            g.write(stat_pre + ': FAILED' + '\n')


def write_adj_cps_and_p_ch_pcts_csvs(tkr, tkrdir, logpath, overwrite):
    "writes adj_cp.csv and p_ch_pcts.csv if the don't already exist"
    quandl_dir = os.path.join(tkrdir, "quandl_data")
    quandl_path = os.path.join(quandl_dir, "{}_quandl.csv".format(tkr))
    adj_cppath = os.path.join(tkrdir, "cp_data/{}_adj_cp.csv".format(tkr))
    p_ch_pctspath = os.path.join(tkrdir, "cp_data/{}_p_ch_pcts.csv".format(tkr))

    # write adj_cp.csv
    if not os.path.exists(adj_cppath) or overwrite:
        adj_cp_df = write_and_get_adj_cp_csv(adj_cppath, quandl_path, logpath)
    else:
        print("\t- {} already exists.".format(adj_cppath))

    # write p_ch_pcts_csv
    if not os.path.exists(p_ch_pctspath) or overwrite:
        write_p_ch_pcts_csv(logpath, p_ch_pctspath, adj_cp_df, adj_cppath)
    else:
        print("\-t {} already exists.".format(p_ch_pctspath))
