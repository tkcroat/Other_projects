# -*- coding: utf-8 -*-
"""
Created on Thu May  4 13:51:32 2017

@author: tkc
"""
import os, sys
import pandas as pd
if 'C:\\Users\\tkc\\Documents\\Python_Scripts\\Other_projects\\Fin' not in sys.path:
    sys.path.append('C:\\Users\\tkc\\Documents\\Python_Scripts\\Other_projects\\Fin')
import fin_functions as fin
import glob
#%%
from importlib import reload
reload(fin)
#%% Update stock quotes in financial projections
os.chdir('C:\\Users\\tkc\\Documents\\Fin\\')
quotes=pd.read_excel('financial_projections.xlsx',sheetname='Quotes')

quotes=fin.lookup_quotes_cnbc(quotes) 
quotes=fin.lookup_TSP(quotes) # TSP lookup scraped from tsp website

fin.writetoxls(quotes, 'Quotes', 'financial_projections.xlsx') # write back to xls quotes tab
#%%  mypay reader (prep for salary info)
fname="C:\\Temp\\myPay.html"
vals=fin.readMyPay(fname)
vals.to_csv('c:\\Temp\myPay.csv')

#%%  Update retirement balances from TSP downloads... requires separate download on each day w/ transactions
os.chdir('C:\Temp') 
tspfiles=glob.glob('*balanceByFun*')

tspfile='C:\\Users\\tkc\\Documents\\Fin\\retirement_accounts.xlsx'
tsp=pd.read_excel(tspfile, sheetname='TSP')

tsp=fin.processBuys(tspfiles, tsp)
tsp=fin.updateTsp(tsp)

fin.writetoxls(tsp, 'TSP', tspfile)
 
# Getting balances via OFX? 
# https://thefinancebuff.com/replacing-microsoft-money-part-5-ofx-scripts.html

# https://wiki.gnucash.org/wiki/OFX_Direct_Connect_Bank_Settings