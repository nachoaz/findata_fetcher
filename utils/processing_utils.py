# processing_utils.py

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
                                mkdir_if_not_exists, \
                                report_and_register_error, \
                                LOGS_DIR, TICDATA_DIR, FEATMAP_DIR


### AUXILARY FUNCTIONS TO COMPUTE DERIVED DATA
def get_mrkcap(mom_df, fund_df):
    mrkcap = mom_df['price'] \
             * fund_df['Weighted Average Shares']
    return mrkcap


def get_entval(mom_df, fund_df):
    entval = fund_df['mrkcap'] \
             + fund_df['Total Debt'] \
             - fund_df['Cash and Equivalents']
    return entval


def get_target(mom_df):
    return 0.5


def get_bnd(mom_df):
    return 0.5


def get_perf(mom_df):
    perf = mom_df['price'].pct_change(12).shift(-12)
    return perf


def get_active(mom_df):
    return 1


def get_month(mom_df):
    return [int(date[-2:]) for date in mom_df.index]


def get_year(mom_df):
    return [int(date[:4]) for date in mom_df.index]


other_fund_cols = (  # colname, colfunct
    ('mrkcap', get_mrkcap),
    ('entval', get_entval))

first_mom_cols = (  # colname, colfunct
    ('target', get_target),
    ('bnd', get_bnd),
    ('perf', get_perf))

last_mom_cols = (  # colname, colfunct
    ('active', get_active),
    ('month', get_month),
    ('year', get_year))


### FUNCTIONS TO GET DATA AND BUILD DATAFRAMES
def get_momentum_df(tic, ticdir, sector):
    """
    Returns momentum features as a Pandas DataFrame, with momentums as
    ratios (percentage changes in price).

    The 'price' column is the price at which one would buy a share of the
    corresponding stock *at the start* of the corresponding month (i.e. it's the
    price of a share at the end of the previous month).

    Similarly, the 'mom1m' column is the percent change that the stock's share
    price has undergone in the one-month period leading up to the start of the
    specified month. (So, it's the price of a share at the end of the previous
    month minus the price of at the end of the month before the previous month
    divided by the price at the end of the month before the previous month).

    The 'mom3m', 'mom6m', and 'mom9m' columns are similarly defined.
    """
    p_ch_path = os.path.join(ticdir, "cp-data", "{}-p-ch-pcts.csv".format(tic))
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


def get_piece_mapped_df(tic, ticdir, piece, piece_map, lag_months=3):
    """
    Returns mapped excel files pandas df.
    NOTE: lag_months allows us to make the statement
    'QX financials won't be avaliable until the start of the month that's
    lag_months after QX ends'
    """
    srow_dir = os.path.join(ticdir, 'srow-data')
    sr_filepath = os.path.join(srow_dir, '{}-{}.xlsx'.format(tic, piece))

    # read stockrow df, mark missing values accordingly
    sr_df = get_stockrow_df(sr_filepath)
    #sr_df.fillna("mSR", inplace=True)  # if missing bc not in .xlsx mark as mSR
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
        #sr_df.iloc[:window-1, list(sr_df.columns).index(feat)] = 'mTM'
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


def get_fundamentals_df(tic, ticdir, feat_map='jda-map', lag_months=3):
    """
    Returns df with mapped excel files as concatenated pandas df.
    """
    feat_map_path = os.path.join(FEATMAP_DIR, feat_map + ".txt")
    feat_map_df = pd.read_csv(feat_map_path, sep='|')

    mapped_dfs = dict()
    for piece in set(feat_map_df.srfile):
        piece_map = feat_map_df[feat_map_df.srfile == piece]
        mapped_dfs[piece] = get_piece_mapped_df(tic, ticdir, piece, piece_map,
                                                lag_months)

    fund_df = pd.concat(mapped_dfs.values(), axis=1)

    # put all ttm feats first, then all mrq, then rest
    l_cols = list()
    m_cols = list()
    r_cols = list()

    for col in fund_df.columns:
        if '_ttm' in col:
            l_cols.append(col)
        elif '_mrq' in col:
            m_cols.append(col)
        else:
            r_cols.append(col)

    fund_df = fund_df.loc[:, l_cols + m_cols + r_cols].copy()

    return fund_df, feat_map_df


def ensure_not_all_fundamentals_missing(tic, mkt, fund_df, lag_months=3):
    assert np.mean(pd.isnull(fund_df).iloc[-lag_months:, :].values) < 0.5, \
           "Too many fundamentals missing for {} ({})".format(tic, mkt)


def get_concatenated_df(tic, mkt, mom_df, fund_df, feat_map_df, lag_months=3):
    # ensure it's not the case that all data from a fundamental source missing
    ensure_not_all_fundamentals_missing(tic, mkt, fund_df, lag_months)

    # drop first 12 rows if these are gonna be mTM
    if 'ttm' in set(feat_map_df.version):
        fund_df = fund_df.iloc[12:,:]

    # drop excess mom_df dates
    mom_df = mom_df.loc[fund_df.index[0]:, :]

    # drop excess fund_df dates
    fund_df = fund_df.loc[:mom_df.index[-1], :]

    # insert other_fund columns
    for colname, colfunct in other_fund_cols:
        fund_df.insert(0, colname, colfunct(mom_df, fund_df))

    # ensure desired order of mrkcap and entval columns
    fund_df = fund_df.loc[:, ['mrkcap', 'entval'] + list(fund_df.columns)[2:]]

    # insert first_mom_cols columns
    for colname, colfunct in first_mom_cols:
        mom_df.insert(0, colname, colfunct(mom_df))

    # insert tic column
    mom_df.insert(0, 'tic', tic)

    # insert last_mom_cols columns
    for colname, colfunct in last_mom_cols:
        mom_df.insert(0, colname, colfunct(mom_df))

    # use tic and mkt to create unique identifier. #TODO: use hashing here?
    mom_df.insert(0, 'gvkey', '1'+tic if mkt == 'nasdaq' else '2'+tic)

    # concatenate dfs
    concatenated_df =  pd.concat([mom_df, fund_df], axis=1)

    # drop columns used to compute mrkcap and entval
    concatenated_df.drop(['Weighted Average Shares', 'Total Debt',
                          'Cash and Equivalents', 'price'], axis=1,
                         inplace=True)

    return concatenated_df


def get_tic_df(tic, mkt, sector, feat_map='jda-map', lag_months=3):
    """
    Gets df with momentum data and (lagged) specified fundamentals.

    Args:
        tic: Ticker of company you want data for.
        mkt: Market of company you want data for.
        sector: Sector of company you want data for.
        feat_map: Feature map to use. See 'README.md' for more details.
        lag_months: Specifies how much to lag fundamentals. Answers the
            question: 'How long should we assume companies take to publish their
            earnings?'

    Returns:
        Pandas DataFrame with corresponding momentum data and fundamentals, as
        would be avaiable at each date.
    """
    ticdir = os.path.join(TICDATA_DIR, mkt, tic)
    mom_df = get_momentum_df(tic, ticdir, sector)
    fund_df, feat_map_df = get_fundamentals_df(tic, ticdir, feat_map,
                                               lag_months)
    concat_df = get_concatenated_df(tic, mkt, mom_df, fund_df, feat_map_df,
                                    lag_months)
    tic_df = concat_df.fillna(method='ffill')
    tic_df.insert(list(tic_df.columns.values).index('tic')+1, 'Sector', sector)
    return tic_df


def write_processed_datafile(tic_tuple, logpath, feat_map='jda-map',
                             lag_months=3):
    tic, mkt, sector = tic_tuple
    status = "Writing processed datafile for {} ({})...".format(tic, mkt)
    try:
        proc_dir = os.path.join(TICDATA_DIR, mkt, tic, 'processed-data')
        mkdir_if_not_exists(proc_dir)
        proc_filepath = os.path.join(proc_dir, '{}-{}-{}.csv'.format(
            tic, feat_map, lag_months))
        tic_df = get_tic_df(tic, mkt, sector, feat_map, lag_months)
        tic_df.to_csv(proc_filepath, index=True)
        print(status + ": SUCCESS")
    except Exception as err:  #TODO: better exception handling here
        report_and_register_error(status, err, logpath)


def get_big_df(tic_dfs, attrs_to_rank=['perf', 'mom1m', 'mom3m',
                                       'mom6m', 'mom9m']):
    """
    Constructs big_df from tic_dfs by percentile-ranking attrs_to_rank.

    Args:
        tic_dfs: A dictionary with tic as key, Pandas DataFrame with tic's data
            through time as value. Note: all dfs must have the same columns
            (attributes), but not necessarily the same rows (dates).
            attrs_to_rank: An iterable that specifies what
            attributes should be percentile-ranked.

    Returns:
        big_df: A Pandas DataFrame with all tic dfs concatenated, with the
            specified attributes percentile-ranked.
    """
    ### make all dfs of same shape
    # prepare dates
    start_end_dates = [(df[~pd.isnull(df.mrkcap)].index[0],
                        df[~pd.isnull(df.mrkcap)].index[-1])
                        for df in tic_dfs.values()]
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
    for key, df in tic_dfs.items():
        df.index = df.index.map(str)
        ext_dfs[key] = pd.concat([df, dates_df], axis=1).drop('ignore', axis=1)

    ## get rankings
    extended_dfs_w_rankings = ext_dfs.copy()

    def get_pctile_rank(arr, val):
        arr_wo_nans = np.array([v for v in arr if not np.isnan(v)])
        if np.isnan(val):
            return np.nan
        else:
            return percentileofscore(arr_wo_nans, val)

    for attr in attrs_to_rank:
        all_tics_vals = np.array([df.loc[:, attr].values
                                  for df in ext_dfs.values()])
        for t in range(len(dates)):
            ranks_for_all_tics = [get_pctile_rank(all_tics_vals[:, t], val)
                                  for val in all_tics_vals[:, t]]
            for tic_num, rank_for_tic in enumerate(ranks_for_all_tics):
                list(extended_dfs_w_rankings.values())[tic_num].loc[:,
                        attr].values[t] = rank_for_tic / 100

    # get rid of rows that are all NaNs because of dates
    dfs_to_concat = list()
    for df, start_end_date in zip(extended_dfs_w_rankings.values(),
                                  start_end_dates):
        df.index = df.index.map(str)
        dfs_to_concat.append(
                df.loc[str(start_end_date[0]):str(start_end_date[1]), :])

    # concatenate everything together and format to return
    big_df = pd.concat(dfs_to_concat, axis=0)
    big_df.index.name = 'date'
    big_df.reset_index(inplace=True)

    return big_df
