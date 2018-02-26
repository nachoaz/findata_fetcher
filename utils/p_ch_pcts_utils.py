# p_change_pcts_utils.py

import os

import pandas as pd

from utils.general_utils import mkdir_if_not_exists, TICDATA_DIR


def write_adj_cp_csv_get_df(adj_cppath, quandlpath, logpath):
    """
    Writes .csv file containing the time series of adjusted close prices at the
    end of every day (for all available days), as provided by Quandl.

    (So bascially it builds TIC-adj-cp.csv by taking TIC-quandl.csv and keeping
    only 'Date' and 'Adj. Close' columns.)

    Returns contents of this .csv file as a Pandas DataFrame if it can be built.
    Otherwise returns None.
    """
    stat_pre = "\t- Writing {}".format(adj_cppath)
    try:
        df = pd.read_csv(quandlpath)
        df_to_write = df[['Date', 'Adj. Close']]
        df_to_write.columns = ['date', 'price']
        df_to_write.to_csv(adj_cppath, index=False)
        print(stat_pre + ': SUCCESSFUL')

    except FileNotFoundError:
        df_to_write = None
        status = stat_pre + ": FAILED (quandl file not found)."
        print(status)
        with open(logpath, 'a') as f:
            f.write(status + "\n")

    return df_to_write


def get_prices_df(adj_cp_df, periodicity='monthly'):
    """
    Returns Pandas DataFrame with price at end of business period (for all
    available buisiness dates). For example: to get df with price at the
    business-end-date of every month, specify `periodicity='monthly'`.

    Args:
        adj_cp_df: Pandas DataFrame with columns 'date' and 'price' housing a
            date and its corresponding adjusted close price.
        periodicity: Specifies the periodicity that you want your price_df to
            have (every month, every week, every day, etc.). Currently only
            supports 'monthly'.

    Returns:
        prices_df: Pandas DataFrame with price at end of business period (for
            all available business dates).
    """
    prices_df = adj_cp_df.set_index('date')
    prices_df.index = pd.to_datetime(prices_df.index)

    if periodicity == 'monthly':
        prices_df = prices_df.resample('BM').apply(lambda x: x[-1])

    return prices_df


def get_p_ch_pcts_df(adj_cp_df):
    """
    Returns p_ch_pcts_df for given adj_cp_df.

    Args:
        adj_cp_df: Pandas DataFrame with columns 'date' and 'price' housing teh
        date and its corresponding adjusted close price.

    Returns:
        p_ch_pcts_df: Pandas DataFrame with columns 'date', 'price',
        'pct_ch_one', 'pct_ch_three', 'pct_ch_six', 'pct_ch_nine', with the
        'pct_ch_' columns housing the percent change over one, three, six, and
        nine periods (currently only 'monthly' periodicity is implemented).
    """
    prices_df = get_prices_df(adj_cp_df, periodicity='monthly')

    for col, periods in [
            ('pct_ch_one', 1),
            ('pct_ch_three', 3),
            ('pct_ch_six', 6),
            ('pct_ch_nine', 9)]:
        prices_df[col] = pd.DataFrame(prices_df['price']).pct_change(periods)

    prices_df.reset_index(inplace=True)

    return prices_df


def write_p_ch_pcts_csv(adj_cp_df, p_ch_pctspath, logpath):
    "Writes tic_p_ch_pcts.csv for tic."
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

    except KeyError:
        status = stat_pre + ": FAILED (KeyError -- unable to build prices_df)."
        print(status)
        with open(logpath, 'a') as g:
            g.write(status + '\n')


def write_adj_cps_and_p_ch_pcts_csvs(tic_tuple, logpath, overwrite):
    "Writes adj_cp.csv and p_ch_pcts.csv if they don't already exist."
    tic, mkt, _ = tic_tuple
    ticdir = os.path.join(TICDATA_DIR, mkt, tic)
    # create cp_data directory if not already existent
    cp_datadir = os.path.join(ticdir, "cp-data")
    mkdir_if_not_exists(cp_datadir)

    # define necessary paths
    quandlpath = os.path.join(ticdir, "quandl-data", tic + "-quandl.csv")
    adj_cppath = os.path.join(cp_datadir, tic + "-adj-cp.csv")
    p_ch_pctspath = os.path.join(cp_datadir, tic + "-p-ch-pcts.csv")

    print("Writing price datafiles for {} ({})...".format(tic, mkt))
    # write adj_cp.csv (if necessary) and get adj_cp_df
    if os.path.isfile(adj_cppath) and not overwrite:
        print("\t- {} already exists.".format(adj_cppath))
        adj_cp_df = pd.read_csv(adj_cppath, header=0, names=['date', 'price'])
    else:
        adj_cp_df = write_adj_cp_csv_get_df(adj_cppath, quandlpath, logpath)

    # write p_ch_pcts_csv
    if os.path.isfile(p_ch_pctspath) and not overwrite:
        print("\t- {} already exists.".format(p_ch_pctspath))
    else:
        write_p_ch_pcts_csv(adj_cp_df, p_ch_pctspath, logpath)
