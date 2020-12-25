# -*- coding: utf-8 -*-
"""
Created on Thu May  4 13:51:32 2017

@author: tkc
"""
import os, sys
import pandas as pd
if 'C:\\Users\\kcroa\\KC_Code\\Other_projects\\Fin' not in sys.path:
    sys.path.append('C:\\Users\\kcroa\\KC_Code\\Other_projects\\Fin')
if 'C:\\Users\\kcroa\\KC_Code\\Other_projects' not in sys.path:
    sys.path.append('C:\\Users\\kcroa\\KC_Code\\Other_projects')

import fin_functions as fin
import glob

import Other_projects.gsheet_functions as gs

#%% Update stock quotes in financial projections
# Pull quote df and symbol names from fin_projections (google sheet)
sheetID = '13bVS-Q7-D2Yz0lDN7qojVoYuM7oZbQcIqau52-rTXqw'
pyGsheet, quotes = gs.readProcessGsheet(sheetID, **{'title':'Quotes'})

quotes=fin.lookup_quotes_cnbc(quotes) 
quotes=fin.lookup_TSP(quotes) # TSP lookup scraped from tsp website
quotes=fin.lookup_TSP(quotes)
fin.updateGsheetQuotes(pyGsheet, quotes)  # Write updated quotes back to pyGsheet

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