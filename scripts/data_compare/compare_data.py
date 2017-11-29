# compare_data.py

import sys
sys.path.append('../')

import numpy as np
import pandas as pd

from utils.general_utils import get_qrtr_from_date

pd.set_option('expand_frame_repr', False)


def read_srow_df(df_path):
    srow_df = pd.read_excel(df_path)
    srow_df = srow_df.loc[:, srow_df.columns[::-1]]
    srow_df.columns = list(map(get_qrtr_from_date, 
        [date.split(' ')[0] for date in map(str, srow_df.columns)]))
    return srow_df


def check_map(feats_map, row_cstat_ibm, srow_df, sqrtr, eqrtr):
    for cstat_feat, srow_feat in feats_map.items():
        cstat_val = row_cstat_ibm[cstat_feat].values[0]*1000000
        srow_val = sum(srow_df.loc[srow_feat][sqrtr:eqrtr])
        diff = (srow_val - cstat_val) / srow_val * 100
        if np.isclose(cstat_val, srow_val):
            print("YES! {} is close to {}.".format(cstat_feat, srow_feat))
        else:
            print("{} is not close to {}.".format(cstat_feat, srow_feat))

        print("diff: {:0.4f".format(diff))

# define dataframes
ibm_income = read_srow_df('IBM_income.xlsx')
cstat_ibm = pd.read_csv('sample-data-2.dat', sep=' ', index_col='date')
row_cstat_ibm = cstat_ibm.loc['201204':'201204','saleq_ttm':]

# check trailing twelve months features
ttm_feats_map = {
        'saleq_ttm': 'Revenues',
        'cogsq_ttm': 'Cost of Revenue',
        'xsgaq_ttm': 'Operating Expenses',
        'oiadpq_ttm': 'Operating Income',
        'niq_ttm': 'Net Income'
        }
check_map(ttm_feats_map, row_cstat_ibm, ibm_income, '2011-Q1', '2011-Q4')

# check most recent quarter features
mrq_feats_map = {
        }
