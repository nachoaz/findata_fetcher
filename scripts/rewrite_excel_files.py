# rewrite_excel_files.py

from collections import Counter

import os
import numpy as np
import pandas as pd

from utils.general_utils import CDATA_DIR, get_stockrow_df


# what should be renamed: what to rename it
renaming_maps = {
    'income': {
        'Earning Before Interest & Taxes (EBIT)': 'EBIT',
        'Earnings Before Interest, Taxes & Depreciation Amortization (EBITDA)':\
                'EBITDA',
        'Earnings per Basic Share': 'EPS',
        'Earnings per Diluted Share': 'EPS Diluted'
        },
    'balance': {
        },
    'cashflow': {
        'Depreciation, Amortization & Accretion': 'Depreciation & Amortization',
        'Net Cash Flow from Operations': 'Operating Cash Flow',
        'Net Cash Flow from Investing': 'Investing Cash Flow',
        'Net Cash Flow from Financing': 'Financing Cash Flow'
        },
    'metrics': {
        'Free Cash Flow per Share': 'FCF per Share',
        'Tangible Assets Book Value per Share': 'Tangible Book Value per Share'
        },
    'growth': {
        'Earnings per Basic Share Growth': 'EPS Growth',
        'Earnings per Diluted Share Growth': 'EPS Diluted Growth'
        }
    }


# format: ([interchangable, rows, in, order, of what, to take], what to call it)
redundant_rows = {
    'income': [
        (['Revenues (USD)', 'Revenues'], 'Revenues'),
        (['Earning Before Interest & Taxes (USD)',
          'Earning Before Interest & Taxes (EBIT)'], 
         'Earning Before Interest & Taxes (EBIT)'),
        (['Earnings per Basic Share (USD)', 'Earnings per Basic Share'], 
          'Earnings per Basic Share'),
        (['Net Income Common Stock (USD)', 'Net Income Common Stock'], 
        'Net Income Common Stock')],
    'balance': [
        (['Cash and Equivalents (USD)', 'Cash and Equivalents'], 
        'Cash and Equivalents'),
        (['Shareholders Equity (USD)', 'Shareholders Equity'], 
        'Shareholders Equity'),
        (['Total Debt (USD)', 'Total Debt'], 'Total Debt')],
    'cashflow': [],
    'metrics': [],
    'growth': []
    }

rows_to_drop = {
    'income': [],
    'balance': [],
    'cashflow': [],
    'metrics': ['EBITDA Margin', 'Profit Margin', 'Average Days of Receivables',
                'Average Days of Payables', 'Days of Inventory on Hand',
                'Account Receivables Turnover', 'Account Payables Turnover',
                'Inventory Turnover', 'Share Dilution Ratio',
                'Earnings Before Interest, Taxes & Depreciation Amortization
                (USD)', 'EBIT Margin', 'Free Cash Flow Margin'],
    'growth': ['Revenue Growth']
    }

rows_to_add = {
    'income': ['Consolidated Income', 'EBIT Margin', 'EBITDA Margin', \
               'Profit Margin', 'Revenue Growth', 'Free Cash Flow Margin'],
    'balance': ['Cash and Short Term Investments'],
    'cashflow': [],
    'metrics': ['Total Debt To Total Assets'],
    'growth': ['Book Value per Share Growth', 
                'Dividends per Basic Common Share Growth']
    }


def listdir_nohidden(path):
    """Returns non-hidden contents of directory at path as a generator."""
    return (i for i in os.listdir(path) if not i.startswith('.'))


def ensure_rows_are_redundant(df, r_rows, piece, tkr):
    """
    Makes sure interxable rows are indeed redundant in df. Raises
    AssertionError if not.
    """
    my_isclose = lambda *args : np.isclose(*args) or np.any(np.isnan([*args]))
    vmy_isclose = np.vectorize(my_isclose)
    assert np.all(vmy_isclose(*df.loc[r_rows].values)), \
           "Rows ({}) are not redudnant for {} of {}".format(r_rows, piece, tkr)


def drop_other_rows_rename_row_to_keep(df, r_rows, name):
    """Finds row to keep (leftmost available on r_rows), drops all others."""
    is_available = lambda df, row : not all(np.isnan(df.loc[row])) \
                                    and not all(df.loc[row] == 0)
    available_rows = (row for row in r_rows if is_available(df, row))
    row_to_keep = next(available_rows)    
    df.drop([row for row in r_rows if row != row_to_keep], inplace=True)
    df.rename({row_to_keep : name}, inplace=True)


def remove_redundant_rows(df, piece, tkr):
    """Removes redundant rows inplace, in accordance to redundant_rows"""
    rows = redundant_rows[piece]
    for r_rows, name in rows:
        ensure_rows_are_redundant(df, r_rows, piece, tkr)
        drop_other_rows_rename_row_to_keep(df, r_rows, name) 


def drop_rows_to_drop(df, piece):
    """Removes rows that are still in df and should be dropped."""
    rows = rows_to_drop[piece]
    df.drop(rows, inplace=True)


def add_rows_to_add(df, piece):
    """Adds rows that need to be added to df in order to match new format."""
    rows = rows_to_add[piece]
    for row in rows: df.loc[row] = np.array([np.nan]*len(df.columns))
    

def rewrite_excel_file_for_tkr(tkrdir, piece):
    """
    Rewrites excel file corresponding to piece to abide by current stockrow.com
    format. Redundant rows are dropped and rows that should be renamed are
    renamed in accordance to renaming_map (global variable).
    """
    tkr = os.path.basename(tkrdir)
    xlpath = os.path.join(tkrdir, "srow_data", "{}_{}.xlsx".format(tkr, piece))
    df = pd.read_excel(xlpath)

    # remove redunant rows and rename rows that should be renamed
    remove_redundant_rows(df, piece, tkr)
    rmap = renaming_maps[piece]
    df.rename(rmap, inplace=True)

    # drop rows that aren't present in the new format, add rows that are but
    # aren't in the old format
    drop_rows_to_drop(df, piece)
    add_rows_to_add(df, piece)

    # save file
    df.to_excel(xlpath, columns=list(map(lambda x: str(x).split(' ')[0],
                                         df.columns)))


def main():
    mkts = listdir_nohidden(CDATA_DIR)

    for mkt in mkts:
        tkrs = listdir_nohidden(os.path.join(CDATA_DIR, mkt))
        for tkr in tkrs:
            tkrdir = os.path.join(CDATA_DIR, mkt, tkr)
            for piece in ('income', 'balance', 'cashflow', 'metrics', 'growth'):
                try:
                    rewrite_excel_file_for_tkr(tkrdir, piece)
                    print("Rewrote {} file for {}".format(piece, tkr))
                except TypeError:
                    print("Error rewriting {} file for {}".format(piece, tkr))


if __name__ == '__main__':
    main()
