# p_change_pcts_utils.py

import os

import pandas as pd


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


def get_prices_df(adj_cp_df, adj_cppath, periodicity='monthly'):
    "returns prices_df (for all available business month dates)"
    if adj_cp_df is None:
        prices_df = pd.read_csv(adj_cppath, header=0, names=['date', 'price'])
    else:
        prices_df = adj_cp_df

    prices_df = prices_df.set_index('date')
    prices_df.index = pd.to_datetime(prices_df.index)
    
    if periodicity == 'monthly':
        prices_df = prices_df.resample('BM').apply(lambda x: x[-1])

    return prices_df


def get_p_ch_pcts_df(adj_cp_df, adj_cppath):
    "returns p_ch_pcts_df for tkr"
    prices_df = get_prices_df(adj_cp_df, adj_cppath)

    for col, periods in [
            ('pct_ch_one', 1),
            ('pct_ch_three', 3),
            ('pct_ch_six', 6),
            ('pct_ch_nine', 9)]:
        prices_df[col] = pd.DataFrame(prices_df['price']).pct_change(periods)

    prices_df.reset_index(inplace=True)

    return prices_df


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
        adj_cp_df = None

    # write p_ch_pcts_csv
    if not os.path.exists(p_ch_pctspath) or overwrite:
        write_p_ch_pcts_csv(logpath, p_ch_pctspath, adj_cp_df, adj_cppath)
    else:
        print("\t- {} already exists.".format(p_ch_pctspath))
