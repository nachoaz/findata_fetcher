# rewrite_excel_files.py

import os
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
        },
    'metrics': {
        },
    'growth': {
        }
    }


# format: ((interchangable, rows, in, order, of what, to take), what to call it)
redundant_rows = {
    'income': [
        (['Revenues (USD)', 'Revenues'], 'Revenues'),
        (['Earning Before Interest & Taxes (USD)',
          'Earning Before Interest & Taxes (EBIT)',
          'Earnings before Tax'], 'Earning Before Interest & Taxes (EBIT)'),
        (['Earnings per Basic Share (USD)', 'Earnings per Basic Share'], 
          'Earnings per Basic Share')],
    'balance': [],
    'cashflow': [],
    'metrics': [],
    'growth': []
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


def rewrite_excel_file_for_tkr(tkrdir, piece):
    """
    Rewrites excel file corresponding to piece, dropping redunant rows and
    renaming rows that should be renamed.
    """
    tkr = os.path.basename(tkrdir)
    xlpath = os.path.join(tkrdir, "srow_data", "{}_{}.xlsx".format(tkr, piece))

    df = get_stockrow_df(xlpath)
    remove_redundant_rows(df, piece, tkr)
    rmap = renaming_maps[piece]
    df.rename(rmap)
    
    
def rewrite_excel_files_for_tkr(tkrdir):
    """
    Rewrites excel files for tkr to abide by current stockrow.com format.
    Translation is done in accordance with renaming_map (global variable).
    """
    for piece in ('income', 'balance', 'cashflow', 'metrics', 'growth'):
        rewrite_excel_file(tkrdir, piece)


def main():
    mkts = listdir_nohidden(CDATA_DIR)

    for mkt in mkts:
        tkrs = listdir_nohidden(os.path.join(CDATA_DIR, mkt))
        for tkr in tkrs:
            rewrite_excel_files_for_tkr(tkr)


if __name__ == '__main__':
    main()
