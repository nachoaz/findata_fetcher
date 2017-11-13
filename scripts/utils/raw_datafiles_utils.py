# raw_datafiles_utils.py

import os

import numpy as np
import pandas as pd

from utils.general_utils import get_qrtr_from_date, \
                                LOGS_DIR, CDATA_DIR


def get_excel_file_df(tkr, mkt, tkrdir, piece):
    "reads excel file corresponding to 'piece', returns as pandas df"
    df = pd.read_excel(tkrdir + '/srow_data/{}_{}.xlsx'.format(tkr, piece))
    df.columns = list(map(get_qrtr_from_date, 
                      list(map(lambda x: str(x).split(' ')[0], df.columns))))
    df.index = map(lambda x: piece[0] + "_" +  x.replace(" ", "_"), df.index)
    df.fillna("NA")

    return df.loc[:, reversed(df.columns)]


def get_excel_files_df(tkr, mkt, tkrdir):
    "returns pandas df made up of excel files stacked, each with a prefix"
    piece_to_df = dict()
    
    for piece in ['income', 'balance', 'cashflow', 'metrics', 'growth']:
        piece_to_df[piece] = get_excel_file_df(tkr, mkt, tkrdir, piece)
        
    return pd.concat(piece_to_df.values())


def get_price_change_pcts_df(tkr, mkt, tkrdir):
    "returns contents of _p_ch_pcts.csv with months as columns"
    p_ch_path = os.path.join(tkrdir, "cp_data/{}_p_ch_pcts.csv".format(tkr))
    pct_df = pd.read_csv(p_ch_path)
    pct_df = pct_df.transpose()
    new_header = pct_df.iloc[0]
    pct_df = pct_df[1:]
    pct_df = pct_df.rename(columns = new_header)
    pct_df.columns = map(get_qrtr_from_date, pct_df.columns)

    return pct_df


def get_tkr_df(tkr, mkt, tkrdir):
    "builds tkr df by concatenating excel data with _p_ch_pcts.csv data"
    excel_files_df = get_excel_files_df(tkr, mkt, tkrdir)
    price_change_pcts_df = get_price_change_pcts_df(tkr, mkt, tkrdir)
    tkr_df = pd.concat([excel_files_df, price_change_pcts_df], join="inner")
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
