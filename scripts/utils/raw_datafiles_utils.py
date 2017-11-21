# raw_datafiles_utils.py

import os

import pandas as pd


def get_excel_file_df(tkr, mkt, tkrdir, piece):
    "reads excel file corresponding to 'piece', returns as pandas df"
    df = pd.read_excel(tkrdir + '/srow_data/{}_{}.xlsx'.format(tkr, piece))
    df.columns = df.columns.to_period('M').to_timestamp('M')
    df.index = map(lambda x: piece[0] + "_" + x.replace(" ", "_"), df.index)
    df.fillna("mSR", inplace=True)  # if missing bc absent in .xlsx mark as mSR
    return df


def get_excel_df(tkr, mkt, tkrdir):
    "returns pandas df made up of excel files stacked, each with a prefix"
    piece_to_df = dict()

    for piece in ['income', 'balance', 'cashflow', 'metrics', 'growth']:
        piece_to_df[piece] = get_excel_file_df(tkr, mkt, tkrdir, piece)

    return pd.concat(piece_to_df.values())


def get_p_ch_pcts_df(tkr, mkt, tkrdir):
    "returns contents of _p_ch_pcts.csv with months as columns"
    p_ch_path = os.path.join(tkrdir, "cp_data/{}_p_ch_pcts.csv".format(tkr))
    pct_df = pd.read_csv(p_ch_path)
    pct_df = pct_df.transpose()
    pct_df.columns = pd.to_datetime(pct_df.loc['date'])
    pct_df.columns = pct_df.columns.to_period('M').to_timestamp('M')
    pct_df = pct_df.drop(['date'])
    pct_df.index = ['price', 'mom1m', 'mom3m', 'mom6m', 'mom9m']

    return pct_df


def get_tkr_df(tkr, mkt, tkrdir):
    "builds tkr df by concatenating excel data with _p_ch_pcts.csv data"
    excel_df = get_excel_df(tkr, mkt, tkrdir)
    p_ch_pcts_df = get_p_ch_pcts_df(tkr, mkt, tkrdir)
    tkr_df = pd.concat([excel_df, p_ch_pcts_df]).loc[:, excel_df.columns[-1]:]
    tkr_df = tkr_df.fillna(method='ffill', axis=1)

    # shift columns to have data be info that'd be available at start of month
    tkr_df.columns = tkr_df.columns.shift(1)
    
    tkr_df.columns = tkr_df.columns.strftime('%Y%m')
    tkr_df.drop('price', inplace=True)

    return tkr_df


def write_tkr_datafile_csv(tkr, mkt, tkrdir, logpath, overwrite):
    "writes tkr_datafile.csv for tkr at dfile_path"
    dfile_path = os.path.join(tkrdir, '{}_datafile.csv'.format(tkr))
    stat_pre = '\t- Writing {}'.format(dfile_path)

    if not os.path.exists(dfile_path) or overwrite:
        try:
            tkr_df = get_tkr_df(tkr, mkt, tkrdir)
            tkr_df.to_csv(dfile_path, index=True)
            print(stat_pre + ': SUCCESSFUL')

        except:
            print(stat_pre + ': FAILED')
            with open(logpath, 'a') as g:
                g.write(stat_pre + ': FAILED\n')

    else:
        print("\t- {} already exists".format(dfile_path))
