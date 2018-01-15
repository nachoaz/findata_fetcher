# p_change_pcts_utils.py

import os

import pandas as pd

from utils.general_utils import mkdir_if_not_exists


def write_adj_cp_csv_get_df(adj_cppath, quandlpath, logpath):
    stat_pre = "\t- Writing {}".format(adj_cppath)
    try:
        df = pd.read_csv(quandlpath)
        df_to_write = df.loc[:, ['Date', 'Adj. Close']]
        df_to_write.columns = ['date', 'price']
        df_to_write.to_csv(adj_cppath, index=False)
        print(stat_pre + ': SUCCESSFUL')

    except FileNotFoundError:
        df_to_write = None
        status = stat_pre + ": FAILED (file not found)."
        print(status)
        with open(logpath, 'a') as f:
            f.write(status + "\n")
            
    return df_to_write


def get_prices_df(adj_cp_df, periodicity='monthly'):
    """
    Returns df with price at end of business period (for all available business
    dates). For example: to get df with price at the business-end-date of every
    month, specify `periodicity='monthly'`.
    """
    prices_df = adj_cp_df.set_index('date')
    prices_df.index = pd.to_datetime(prices_df.index)
    
    if periodicity == 'monthly':
        prices_df = prices_df.resample('BM').apply(lambda x: x[-1])

    return prices_df


def get_p_ch_pcts_df(adj_cp_df):
    "Returns p_ch_pcts_df for given adj_cp_df."
    prices_df = get_prices_df(adj_cp_df)

    for col, periods in [
            ('pct_ch_one', 1),
            ('pct_ch_three', 3),
            ('pct_ch_six', 6),
            ('pct_ch_nine', 9)]:
        prices_df[col] = pd.DataFrame(prices_df['price']).pct_change(periods)

    prices_df.reset_index(inplace=True)

    return prices_df


def write_p_ch_pcts_csv(adj_cp_df, p_ch_pctspath, logpath):
    "Writes tkr_p_ch_pcts.csv for tkr."
    stat_pre = '\t- Writing {}'.format(p_ch_pctspath)

    try:
        p_ch_pcts_df = get_p_ch_pcts_df(adj_cp_df)
        p_ch_pcts_df.to_csv(p_ch_pctspath, index=False)
        print(stat_pre + ': SUCCESSFUL')

    except AttributeError:
        status = stat_pre + ": FAILED (adj_cp file not found)."
        print(status)
        with open(logpath, 'a') as g:
            g.write(status + '\n')


def write_adj_cps_and_p_ch_pcts_csvs(tkr, tkrdir, logpath, overwrite):
    "Writes adj_cp.csv and p_ch_pcts.csv if they don't already exist."
    # create cp_data directory if not already existent
    cp_datadir = os.path.join(tkrdir, "cp_data")
    mkdir_if_not_exists(cp_datadir)

    # define necessary paths
    quandlpath = os.path.join(tkrdir, "quandl_data", tkr + "_quandl.csv")
    adj_cppath = os.path.join(cp_datadir, tkr + "_adj_cp.csv")
    p_ch_pctspath = os.path.join(cp_datadir, tkr + "_p_ch_pcts.csv")

    # write adj_cp.csv (if necessary) and get adj_cp_df
    if os.path.isfile(adj_cppath):
        if overwrite:
            adj_cp_df = write_adj_cp_csv_get_df(adj_cppath, quandlpath, logpath)
        else:
            print("\t- {} already exists.".format(adj_cppath))
            adj_cp_df = pd.read_csv(adj_cppath, header=0, 
                                    names=['date', 'price'])
    else:
        adj_cp_df = write_adj_cp_csv_get_df(adj_cppath, quandlpath, logpath)

    # write p_ch_pcts_csv
    if os.path.isfile(p_ch_pctspath):
        if overwrite:
            write_p_ch_pcts_csv(adj_cp_df, p_ch_pctspath, logpath)
        else:
            print("\t- {} already exists.".format(p_ch_pctspath))
    else:
        write_p_ch_pcts_csv(adj_cp_df, p_ch_pctspath, logpath)
