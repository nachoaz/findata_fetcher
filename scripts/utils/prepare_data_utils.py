# prepare_data_utils.py

import os
import sys
sys.path.append('../')

import numpy as np
import pandas as pd
from collections import Counter
from scipy.stats import percentileofscore

from utils.general_utils import get_year_endmonth_from_qrtr, \
                                get_dict_from_df_cols, \
                                get_stockrow_df, \
                                LOGS_DIR, CDATA_DIR


def get_momentum_df(tkr, tkrdir):
    """
    Returns momentum features as a Pandas DataFrame, with momentums as
    ratios (percentage changes in price).

    The 'price' column is the price at which one would buy a share of the
    corresponding stock *at the start* of the specified month (i.e. it's the
    price of a share at the end of the previous month).

    Similarly, the 'mom1m' column is the percent change that that stock's share
    price has undergone in the one-month period leading up to the start of the
    specified month. (So, it's the price of a share at the end of the previous
    month minus the price of at the end of the month before the previous month
    divided by the price at the end of the month before the previous month).

    The 'mom3m', 'mom6m', and 'mom9m' columns are similarly defined.
    """
    p_ch_path = os.path.join(tkrdir, "cp_data", "{}_p_ch_pcts.csv".format(tkr))
    pct_df = pd.read_csv(p_ch_path)
    pct_df = pct_df.transpose()
    pct_df.columns = pd.to_datetime(pct_df.loc['date'])
    pct_df.columns = pct_df.columns.to_period('M').to_timestamp('M')
    pct_df = pct_df.drop(['date'])
    df_to_ret = pct_df.copy()
    df_to_ret.index = ['price', 'mom1m', 'mom3m', 'mom6m', 'mom9m']
    df_to_ret.columns = [str(col.year).zfill(4) + str(col.month).zfill(2)
                         for col in df_to_ret.columns]
    df_to_ret = df_to_ret.shift(1, axis=1)
    df_to_ret = df_to_ret.transpose().loc[:,['mom1m', 'mom3m', 'mom6m', 'mom9m',
                                             'price']]
    return df_to_ret


def get_piece_mapped_df(tkr, tkrdir, piece, piece_map, lag_months=3):
    """
    returns mapped excel files pandas df.
    NOTE: lag_months allows us to make the statement
    'QX financials won't be avaliable until the start of the month that's
    lag_months after QX ends'
    """
    srow_dir = os.path.join(tkrdir, 'srow_data')
    sr_filepath = os.path.join(srow_dir, '{}_{}.xlsx'.format(tkr, piece))

    # read stockrow df, mark missing values accordingly
    sr_df = get_stockrow_df(sr_filepath)
    sr_df.fillna("mSR", inplace=True)  # if missing bc not in .xlsx mark as mSR
    sr_df.columns = map(get_year_endmonth_from_qrtr, sr_df.columns)
    sr_df = sr_df.transpose()

    # rename and shave off whatever not wanted
    sr_df_copy = sr_df.copy()

    if piece == 'income':
        needed_cols= ['Weighted Average Shares']
    elif piece == 'balance':
        needed_cols = ['Total Debt', 'Cash and Equivalents']
    else:
        needed_cols = []

    sr_df.rename(get_dict_from_df_cols(piece_map, 'srfile_feat', 'mdfile_feat'),
                 axis=1, inplace = True)
    sr_df = pd.concat([sr_df_copy.loc[:, needed_cols],
                       sr_df.loc[:, piece_map.mdfile_feat.values]], axis=1)

    # get data in correct version
    for feat, version in get_dict_from_df_cols(piece_map, 'mdfile_feat',
                                               'version').items():
        if 'ttm' in version:
            window = 4
        elif 'tnm' in version:
            window = 3
        elif 'tsm' in version:
            window = 2
        elif 'mrq' in version:
            window = 1

        sr_df[feat] = sr_df[feat].rolling(window=window).sum()
        # if missing bc can't roll back mark as mTM (missing trailing months)
        sr_df.iloc[:window-1, list(sr_df.columns).index(feat)] = 'mTM'
        sr_df = sr_df.rename(index=str, columns={feat: feat + '_' + version
                                        if 'implicit' not in version else feat})

    # stretch to include dates in between quarter starts
    date_range = pd.date_range(pd.to_datetime(sr_df.index[0], format='%Y%m'),
                               pd.to_datetime(sr_df.index[-1], format='%Y%m')
                               + pd.DateOffset(months=lag_months*2),
                               freq='M')
    dates = [str(d.year).zfill(4) + str(d.month).zfill(2) for d in date_range]
    dates_df = pd.DataFrame(['na']*len(dates), columns=['ignore'], index=dates)
    sr_df = pd.concat([sr_df, dates_df], axis=1).drop('ignore', axis=1)
    sr_df.fillna(method='ffill', inplace=True)

    # apply lag to make data realistic
    sr_df = sr_df.shift(lag_months)

    return sr_df


def get_fundamentals_df(tkr, tkrdir, mom_df, feat_map='jda_map.txt'):
    "Returns df with mapped excel files as concatenated pandas df."
    feat_map_df = pd.read_csv('feature_mappings/{}'.format(feat_map), sep='|')
    mapped_dfs = dict()

    for piece in set(feat_map_df.srfile):
        piece_map = feat_map_df[feat_map_df.srfile == piece]
        mapped_dfs[piece] = get_piece_mapped_df(tkr, tkrdir, piece, piece_map)

    f_df = pd.concat(mapped_dfs.values(), axis=1)

    # put all ttm feats first, then all mrq, then rest
    l_cols = list()
    m_cols = list()
    r_cols = list()

    for col in f_df.columns:
        if '_ttm' in col:
            l_cols.append(col)
        elif '_mrq' in col:
            m_cols.append(col)
        else:
            r_cols.append(col)

    f_df = f_df.loc[:, l_cols + m_cols + r_cols]

    # get mktcap using mom_df
    mrkcap = mom_df.loc[f_df.index[0]:,:]['price'] \
             * f_df['Weighted Average Shares']
    mom_df['mrkcap'] = mrkcap

    # get entval
    entval = mom_df.mrkcap \
            + f_df.loc[:, 'Total Debt'] \
            - f_df.loc[:, 'Cash and Equivalents']
    mom_df['entval'] = entval

    # drop first 12 rows if these are gonna be mTM
    if 'ttm' in set(feat_map_df.version):
        f_df = f_df.iloc[12:,:]

    # drop columns us to compute mktcap and entval
    f_df.drop(['Weighted Average Shares', 'Total Debt', 'Cash and Equivalents'],
              axis=1, inplace=True)

    # drop excess mom_df dates
    mom_df = mom_df.loc[f_df.index[0]:, :]

    return mom_df, f_df


def attach_other_cols(tkr, mkt, fund_df, mom_df):
    tkr_df = pd.concat([mom_df.drop('price', axis=1), fund_df], axis=1)
    tkr_df.index.rename('date', inplace=True)

    tkr_df.insert(0, 'target', 0.5)

    tkr_df.insert(0, 'bnd', 0.5)  # to be determined later

    perf = mom_df.loc[:, 'price'].pct_change(12).shift(-12)
    tkr_df.insert(0, 'perf', perf)

    tkr_df.insert(0, 'tic', tkr)

    tkr_df.insert(0, 'active', 1)

    tkr_df.insert(0, 'month', [int(date[-2:]) for date in tkr_df.index])

    tkr_df.insert(0, 'year', [int(date[:4]) for date in tkr_df.index])

    # use tkr and mkt to create unique identifier. #TODO: use hashing here
    tkr_df.insert(0, 'gvkey', '1'+tkr if mkt == 'nasdaq' else '2'+tkr)

    return tkr_df


def get_tkr_df(tkr, mkt, feat_map='jda_map.txt', lag_months=3):
    tkrdir = os.path.join(CDATA_DIR, mkt, tkr)
    mom_df = get_momentum_df(tkr, tkrdir)
    mom_df, fund_df = get_fundamentals_df(tkr, tkrdir, mom_df, feat_map)
    tkr_df = attach_other_cols(tkr, mkt, fund_df, mom_df)
    return tkr_df


def get_big_df(tkr_dfs):

    ### make all dfs of same shape
    # prepare dates
    start_end_dates = [(df.index[0], df.index[-1]) for df in tkr_dfs.values()]
    start_dates, end_dates = zip(*start_end_dates)
    abs_start = min(start_dates)
    abs_end = max(end_dates)
    date_range = pd.date_range(pd.to_datetime(abs_start, format='%Y%m'),
                               pd.to_datetime(abs_end, format='%Y%m')
                               + pd.DateOffset(months=1),
                               freq='M')
    dates = [str(d.year).zfill(4) + str(d.month).zfill(2) for d in date_range]
    dates_df = pd.DataFrame(['na']*len(dates), columns=['ignore'], index=dates)

    # extend dfs
    ext_dfs = dict()
    for key, df in tkr_dfs.items():
        ext_dfs[key] = pd.concat([df, dates_df], axis=1).drop('ignore', axis=1)

    ### get rankings
    attrs_to_get_rankings_for = ['perf', 'mom1m', 'mom3m', 'mom6m', 'mom9m']
    extended_dfs_w_rankings = ext_dfs.copy()

    def get_pctile_rank(arr, val):
        arr_wo_nans = np.array([v for v in arr if not np.isnan(v)])
        if np.isnan(val):
            return np.nan
        else:
            return percentileofscore(arr_wo_nans, val)
        
    for attr in attrs_to_get_rankings_for:
        all_tkrs_vals = np.array([df.loc[:, attr].values 
                                  for df in ext_dfs.values()])
        for t in range(len(dates)):
            ranks_for_all_tkrs = [get_pctile_rank(all_tkrs_vals[:, t], val)
                                  for val in all_tkrs_vals[:, t]]
            for tkr_num, rank_for_tkr in enumerate(ranks_for_all_tkrs):
                list(extended_dfs_w_rankings.values())[tkr_num].loc[:,
                        attr].values[t] = rank_for_tkr / 100

    # concatenate everything together
    dfs_to_concat = [df.loc[start_end_date[0]:start_end_date[1], :]
                     for df, start_end_date in
                     zip(extended_dfs_w_rankings.values(), start_end_dates)]
    big_df = pd.concat(dfs_to_concat, axis=0)

    # get rid of rows that are all NaNs because of dates

    big_df.index.name = 'date'
    big_df.reset_index(inplace=True)

    return big_df
