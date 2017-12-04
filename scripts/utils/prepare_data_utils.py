# prepare_data_utils.py

import os
import sys
sys.path.append('../')

import pandas as pd

from utils.general_utils import get_year_endmonth_from_qrtr, \
                                get_dict_from_df_cols, \
                                LOGS_DIR, CDATA_DIR


def get_stockrow_df(sr_filepath):
    "returns excel file as pandas df, with YYYY-QX as cols"
    df = pd.read_excel(sr_filepath)

    # ensure df's columns go from more recent to less recent
    if df.columns[0] < df.columns[-1]:
        df = df.loc[:, df.columns[::-1]]

    years = [col.year for col in df.columns]
    latest_year_count = years.count(years[0])
    new_cols = [str(year) + '-Q' + str(qrtr_num)
                for year in sorted(set(years), reverse=True) 
                for qrtr_num in range(4, 0, -1)]
    df.columns = new_cols[:df.shape[1]]

    # ensure df's columns go from less recent to most recent
    df = df.loc[:, df.columns[::-1]]
    return df


def get_momentum_df(tkr, tkrdir):
    "returns momentum features df, with momentums as ratios"
    p_ch_path = os.path.join(tkrdir, "cp_data/{}_p_ch_pcts.csv".format(tkr))
    pct_df = pd.read_csv(p_ch_path)
    pct_df = pct_df.transpose()
    pct_df.columns = pd.to_datetime(pct_df.loc['date'])
    pct_df.columns = pct_df.columns.to_period('M').to_timestamp('M')
    pct_df = pct_df.drop(['date'])
    pct_df.index = ['price', 'mom1m', 'mom3m', 'mom6m', 'mom9m']
    df_to_ret = pct_df.copy()
    df_to_ret.columns = [str(col.year).zfill(4) + str(col.month).zfill(2) 
                         for col in df_to_ret.columns]
    df_to_ret = df_to_ret.shift(1, axis=1)
    df_to_ret = df_to_ret.transpose().drop('price', axis=1)
    return df_to_ret, pct_df


def get_piece_mapped_df(tkr, tkrdir, piece, piece_map, lag_months=3):
    """
    returns mapped excel files pandas df. 
    NOTE: lag_months allows us to make the statement
    'QX financials won't be avaliable until the start of the month that's 
    lag_months after QX ends'
    """
    srow_dir = os.path.join(tkrdir, 'srow_data')
    sr_filepath = os.path.join(srow_dir, '{}_{}.xlsx'.format(tkr, piece))

    # read stockrow df, take wanted features, rename those to have wanted names
    sr_df = get_stockrow_df(sr_filepath).loc[piece_map.srfile_feat.values, :]
    sr_df = sr_df.rename(get_dict_from_df_cols(piece_map, 'srfile_feat', 
                                               'mdfile_feat'))
    sr_df.fillna("mSR", inplace=True)  # if missing bc not in .xlsx mark as mSR

    sr_df.columns = map(get_year_endmonth_from_qrtr, sr_df.columns)
    sr_df = sr_df.transpose()

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
    sr_df = sr_df.shift(lag_months).iloc[lag_months+2:,:]

    return sr_df


def get_fundamentals_df(tkr, tkrdir, feat_map='jda_map.txt'):
    "returns df with mapped excel files as concatenated pandas df"
    feat_map_df = pd.read_csv('feature_mappings/{}'.format(feat_map), sep='|')
    mapped_dfs = dict()

    for piece in set(feat_map_df.srfile):
        piece_map = feat_map_df[feat_map_df.srfile == piece]
        mapped_dfs[piece] = get_piece_mapped_df(tkr, tkrdir, piece, piece_map)

    # put all ttm feats first, then all mrq, then rest
    f_df = pd.concat(mapped_dfs.values(), axis=1)

    l_cols = list()
    r_cols = list()

    for col in f_df.columns:
        if ('_ttm' in col) or ('_mrq' in col):
            l_cols.append(col)
        else:
            r_cols.append(col)

    f_df = f_df.loc[:, l_cols + r_cols]
        
    return f_df


def attach_other_cols(tkr, mf_df, pct_df, target='ebit_ttm'):
    tkr_df = mf_df.copy()
    tkr_df.index.rename('date', inplace=True)
    
    tkr_df.rename(index=str, columns={target:'target'}, inplace=True)
    target_s = tkr_df['target']
    tkr_df.drop(labels=['target'], axis=1, inplace=True)
    tkr_df.insert(0, 'target', target_s)

    tkr_df.insert(0, 'bnd', 0.5)  # to be determined later

    perf = pct_df.loc['price'].pct_change(12).shift(-(12-1))
    perf.index = [str(date.year) + str(date.month).zfill(2) for date in
            perf.index]
    tkr_df.insert(0, 'perf', perf)
    
    tkr_df.insert(0, 'tic', tkr)

    tkr_df.insert(0, 'active', 1)

    tkr_df.insert(0, 'month', [int(date[-2:]) for date in tkr_df.index])

    tkr_df.insert(0, 'year', [int(date[:4]) for date in tkr_df.index])

    tkr_df.insert(0, 'gvkey', 60661)  # ignore this, it's an id for compustat

    return tkr_df


def get_tkr_df(tkr, mkt, feat_map='jda_map.txt', lag_months=3):
    tkrdir = '/'.join([CDATA_DIR, mkt, tkr])
    fund_df = get_fundamentals_df(tkr, tkrdir, feat_map)
    mom_df, pct_df = get_momentum_df(tkr, tkrdir)
    mf_df = pd.concat([mom_df, fund_df], axis=1).loc[fund_df.index[0]:, :]
    tkr_df = attach_other_cols(tkr, mf_df, pct_df)
    return tkr_df
