# cross-checking apt expenses
import pandas as pd
from datetime import datetime, timedelta
import os
import glob
from lxml import html
import itertools as it
from operator import itemgetter
import numpy as np
import matplotlib.pyplot as plt

import gsheet_functions as gs
# Determine TSP shares & price on purchase day
# need BalanceByFund for all dates incl previous


#%%
def matchDuplTrans(allCC, Aptexp, colset):
    '''  
    '''
    # remove drop transactions (unrelated categories)
    ccsub=allCC[ (allCC['Matched']=='') | (pd.isnull(allCC['Matched']))]
    ccdups=ccsub[ccsub.duplicated(colset, keep=False)]
    aptdups=Aptexp[Aptexp.duplicated(colset, keep=False)]
    indsCC=[]
    indsExp=[]
    # Process each duplicated subgroup 
    grouped=ccdups.groupby(colset)
    for cols, gr in grouped:
        

def matchTransactions(allCC, Aptexp, colset):
    '''
    
    Testing  colset=['Date','Acct','Amount']
    '''
    # Duplicated transaction in either set will screw up indexing after joins
    dups=allCC[allCC.duplicated(colset, keep=False)]
    Goodmatch=pd.merge(allCC, Aptexp, how='left', on=['Date','Acct','Amount'], suffixes=('','2'))
    # Write back 'Y' in matched for each pair in allCC and in Aptexp
    ccgroup = allCC.groupby(colset)
        
    
#%%
    [i for i in mycols if i not in df.columns]
    [i for i in df.columns if i not in mycols]
    
    
        
#%%

HDlog=pd.read_excel('C:\\Users\\tkc\Documents\\Fin\\taxes\\Receipts\\HD_receipts_log.xlsx', sheetname='HD')
apt17=pd.read_excel('C:\\Users\\tkc\Documents\\Fin\\taxes\\apt_expenses2017.xlsx', sheetname='apt2017')


rlog=HDlog[mycols]
mycols=['Date','Vendor','Total']
tlog17=apt17[mycols]

diff=pd.concat([rlog, tlog17], ignore_index=True)
diff=diff.drop_duplicates(keep=False)
diff=diff.sort_values(['Date','Total'])
diff.to_csv('test.csv', index=False)
rlog['Date']=rlog['Date'].to_pydatetime()

rlog['Date']=rlog['Date'].apply(lambda x:x.to_pydatetime())


os.chdir('C:\\Users\\tkc\\Documents\\Fin\\credit_card_bills')
qd=pd.read_excel('qualls_discover_bills.xls')
qd=qd[pd.notnull(qd['Date'])]

qd=qd[qd['Date']>datetime.date(2017,1,1)]

qd['Date'].dt.year.values[0]

qd['Date']=pd.to_datetime(qd['Date'])

qd['Date']=qd['Date'].apply(lambda x:pd.to_datetime(x).strftime('%I:%M %p'))

qd['Date']=qd['Date'].apply(lambda x:pd.to_datetime(x), format='%y/%m/%d')

qd['Date']=pd.to_datetime(qd['Date'], format='%y/%m/%d')

df[col]=pd.to_datetime(df[col], format='%d%b%Y:%H:%M')

# Parsing TIAA transactions  

finstr='Vanguard Total Bond Market Index Fund Institutional36.4401$10.6800$301.30$87.88$389.18Vanguard Small-Cap Index Fund Institutional2.1937$63.8700$108.47$31.64$140.11Vanguard Total International Stock Index Fund Institutional1.3157$106.4800$108.47$31.64$140.11Vanguard REIT Index Fund Institutional8.5864$18.1300$120.52$35.15$155.67Vanguard Total Stock Market Index Fund Institutional12.3862$59.0700$566.44$165.21$731.65'

Tiaa=pd.read_excel('retirement_accounts.xls', sheetname='TIAA_temp')
templ=pd.read_excel('retirement_accounts.xls', sheetname='TIAA')

mycols=['Date', 'Type', 'Total amt', '% ROTH', 'USshares',
       'USprice', 'USdiv_sh', 'Smallcapshares',
       'Smallcapprice', 'VSCIX div/sh', 'VTSNX (global) shares', 'VTSNX price',
       'VGTSX div/sh', 'VBTIX (bonds) shares', 'VBTIX price', 'VBTIX div/sh',
       'VGSNX (REIT) shares', 'VGSNX price', 'VGSNX div/sh', 'VITSX balance',
       'VSCIX balance', 'VTSNX balance', 'VBTIX balance', 'VGSNX balance']


funds=['Bond','Small-cap','International','REIT','Total Stock']
abbrev=[']
for i, val in enumerate(funds):
    match=Tiaa[Tiaa['INVESTMENT'].str.contains(val, case=False)]

def parsefinstr(finstr):
    '''  '''
    finstr=finstr.replace('Vanguard Total Bond Market Index Fund Institutional','Bonds ')
    finstr=finstr.replace('Vanguard Small-Cap Index Fund Institutional',' Smallcap ')
    finstr=finstr.replace('Vanguard Total International Stock Index Fund Institutional',' Global ')
    finstr=finstr.replace('Vanguard REIT Index Fund Institutional',' REIT ')
    finstr=finstr.replace('Vanguard Total Stock Market Index Fund Institutional',' US ')
    finstrs=finstr.split(' ')
    Labels=[i for i in finstr if i[0].isdigit()]


        
