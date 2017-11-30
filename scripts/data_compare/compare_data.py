# compare_data.py

import sys
sys.path.append('../')

import pandas as pd

from utils.general_utils import get_qrtr_from_date

pd.set_option('expand_frame_repr', False)


def read_srow_df(df_path):
    srow_df = pd.read_excel(df_path)
    srow_df = srow_df.loc[:, srow_df.columns[::-1]]
    srow_df.columns = list(map(get_qrtr_from_date, 
        [date.split(' ')[0] for date in map(str, srow_df.columns)]))
    return srow_df


def print_comparison_report(cstat_feat, srow_feat, diff):
    if abs(diff) < 5:
        print("'{}' is close to {} (diff: {:0.4f})".format(
            cstat_feat, srow_feat, diff))
    else:
        print("\t- '{}' is not close to {} (diff: {:0.4f})".format(
            cstat_feat, srow_feat, diff))


def check_mrq_map(feats_map, cstat_series, balance_path, eqrtr):
    srow_df = read_srow_df(balance_path)

    for cstat_feat, srow_feat in feats_map.items():
        cstat_val = cstat_series[cstat_feat+'_mrq']*1000000
        srow_val = srow_df.loc[srow_feat][eqrtr]
        diff = ((srow_val - cstat_val) / (srow_val + 0.00001)) * 100
        print_comparison_report(cstat_feat, srow_feat, diff)


def check_ttm_map(feats_map, cstat_series, income_path, sqrtr, eqrtr):
    srow_df = read_srow_df(income_path)

    for cstat_feat, srow_feat in feats_map.items():
        cstat_val = cstat_series[cstat_feat+'_ttm']*1000000
        srow_val = sum(srow_df.loc[srow_feat][sqrtr:eqrtr])
        diff = (srow_val - cstat_val) / srow_val * 100
        print_comparison_report(cstat_feat, srow_feat, diff)


def check_maps(map_kind, curr_month, sqrtr, eqrtr):
    cstat_df = pd.read_csv('sample-data-2.dat', sep=' ', index_col='date')
    cstat_series = cstat_df.loc[curr_month, 'saleq_ttm':]

    income_path = 'IBM_income.xlsx'
    balance_path = 'IBM_balance.xlsx'

    for feats_map, kind in map_kind:
        if kind == 'ttm':
            check_ttm_map(feats_map, cstat_series, income_path, sqrtr, eqrtr)
        else:
            check_mrq_map(feats_map, cstat_series, balance_path, eqrtr)



# trailing twelve months features
ttm_feats_map = {
        'saleq': 'Revenues',
        'cogsq': 'Cost of Revenue',
        'xsgaq': 'Operating Expenses',
        'oiadpq': 'Operating Income',
        'niq': 'Net Income'
        }

# most recent quarter features
mrq_feats_map = {
        'cheq': 'Cash and Equivalents',
        'rectq': 'Trade and Non-Trade Receivables',
        'invtq': 'Inventory',
        'acoq': 'Investments Current',
        'ppentq': 'Property, Plant & Equipment Net',
        'aoq': 'Assets Non-Current',
        'dlcq': 'Debt Current',
        'apq': 'Trade and Non-Trade Payables',
        'txpq': 'Tax Liabilities',
        'lcoq': 'Deferred Revenue',
        'ltq': 'Total Liabilities'
        }

# cross check data available at start of april 2012
curr_month = 201201
sqrtr = '2010-Q4'
eqrtr = '2011-Q3'
maps_to_check = [(ttm_feats_map, 'ttm'), (mrq_feats_map, 'mrq')]

check_maps(maps_to_check, curr_month, sqrtr, eqrtr)

# see which ones most closely match
balance_df = read_srow_df('IBM_balance.xlsx')
cstat_ibm = pd.read_csv('sample_data-2.dat', sep=' ', index_col='date')
cstat_series = cstat_ibm.loc[201204,'saleq_ttm':]

for feat, val in cstat_series['cheq_mrq':].items():
     srow_closest = balance_df.loc[:, eqrtr].index[np.argmin(abs((balance_df.loc[:, eqrtr].values / 1000000) - val))]
     srow_val = balance_df.loc[srow_closest, eqrtr]/1000000
     diff = ((srow_val - val) / (srow_val + 0.00000001)) * 100
     print("'{}' closest to: '{}' (diff: {:0.4f} %)".format(feat, srow_closest, diff))
