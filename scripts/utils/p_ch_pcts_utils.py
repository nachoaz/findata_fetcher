# p_change_pcts_utils.py

import os

import numpy as np
import pandas as pd

from utils.general_utils import get_qrtr_dates_btwn_sdate_edate, \
                                CDATA_DIR


def write_adj_cps_csv(tkr, mkt, tkrdir, logpath, overwrite):
    "writes adj_cp from quandl_file if adj_cp file doesn't already exist"
    quandl_dir = os.path.join(tkrdir, "quandl_data")
    quandl_filepath = os.path.join(quandl_dir, "{}_quandl.csv".format(tkr))
    adj_cp_filepath = os.path.join(tkrdir, "cp_data/{}_adj_cp.csv".format(tkr))

    stat_pre = '\t- Writing {}'.format(adj_cp_filepath)

    if not os.path.exists(adj_cp_filepath) or overwrite:
        try:
            df = pd.read_csv(quandl_filepath)
            df_to_write = df.loc[:, ['Date', 'Adj. Close']]
            df_to_write.columns = ['date', 'price']
            df_to_write.to_csv(adj_cp_filepath, index=False)
            print(stat_pre + ': SUCCESSFUL')

        except:
            print(stat_pre + ': FAILED')
            with open(logpath, 'a') as f:
                f.write(stat_pre + ": FAILED\n")

    else:
        print("\t- {} already exists.".format(adj_cp_filepath))


def get_prices_df(tkr, mkt):
    "returns prices_df for tkr (for all available dates), using forward fill"
    tkr_adj_cp_path = CDATA_DIR + '/{0}/{1}/cp_data/{1}_adj_cp.csv'.format(mkt, tkr)
    prices_df = pd.read_csv(tkr_adj_cp_path, header=0, names=['date', 'price'])

    sdate = prices_df.iloc[-1]['date']
    edate = prices_df.iloc[0]['date']
    full_df = pd.DataFrame(pd.date_range(sdate, edate), columns=['date'])
    full_df['price'] = np.array([np.nan]*len(full_df))

    for i in prices_df.index:
        full_df.loc[full_df['date'] == prices_df.ix[i]['date'], 'price'] = prices_df.ix[i]['price']

    full_df = full_df.fillna(method='ffill')

    return full_df, sdate, edate


def get_p_ch_pcts_df(tkr, mkt):
    "returns p_ch_pcts_df for tkr"
    #TODO make this pretty in 80 lines (see pandas slicing)
    prices_df, sdate, edate = get_prices_df(tkr, mkt)

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


def write_tkr_p_ch_pcts_csv(tkr, mkt, tkrdir, logpath, overwrite):
    "writes tkr_p_ch_pcts.csv for tkr, if it doesn't already exist"
    p_ch_pctspath = os.path.join(tkrdir, "cp_data/{}_p_ch_pcts.csv".format(tkr))
    stat_pre = '\t- Writing {}'.format(p_ch_pctspath)

    if not os.path.exists(p_ch_pctspath) or overwrite:
        try:
            p_ch_pcts_df = get_p_ch_pcts_df(tkr, mkt)
            p_ch_pcts_df.to_csv(p_ch_pctspath, index=False)
            print(stat_pre + ': SUCCESSFUL')

        except:
            print(stat_pre + ': FAILED')
            with open(logpath, 'a') as g:
                g.write(stat_pre + ': FAILED' + '\n')
    
    else:
        print("\t- {} already exists".format(p_ch_pctspath))

