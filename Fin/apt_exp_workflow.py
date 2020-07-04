# -*- coding: utf-8 -*-
"""
Functions to track/ match apartment expense google sheet with other expenses from 
mint and/or credit card annual transaction downloads;
ensure that all expenses are properly tracked before tax time
Created on Sun Mar  5 14:10:40 2017

@author: tkc
"""

import os
import sys
import pandas as pd
if 'C:\\Users\\Kevin\\KC_code\\Other\\Fin' not in sys.path:
    sys.path.append('C:\\Users\\Kevin\\KC_code\\Other\\Fin')
import apt_exp_functions as aptexp

import gsheet_functions as gs # read/write/process from google sheets

#%% Read apt_expenses google sheet
sheetID ='15oCMTf7eXZCOq9HH3Os4qJFTzFTaJq5UZuJOhFMy0-E' # apt 2019 exp

aptPySheet, Aptexp = gs.readProcessGsheet(sheetID, **{'filters':['Vendor'], 
    'floats':['Amount', 'Repairs','Improvement', 'Supplies', 'Other', 'Home repair'], 
    'strings':['Acct'], 'dates':['Date']})  # first arg contains rows, cols, title

# Load mint csv file for given year
mint = pd.read_csv("C:\\Users\\Kevin\\Documents\\Fin\\Other\\mint_transactions_2019.csv")

mint = aptexp.processMint(mint)

#%% Cross-matching complete mint expenses set against apt exp

props, units = aptexp.splitSummarize(Aptexp) # report on expenses by unit and property (incl. splits)

aptexp.plotUnitExpense(Aptexp)

#%% Summarize expenses by type/ unit

#%% Using complete mint file, ensure all appropr. exp are in aptExp (mark as masked)
# Confirm and mark duplicates (both files)
colset=['Date','Acct','Amount']
# Move chk # to Notes field

# Finding missing info
match=mint[mint['Vendor'].str.contains('lowe', case=False)]

match=mint[(mint['Vendor'].str.contains('Lowe', case=False)) & (mint['Date']==datetime(2019,4,9))]
#%%
finPath='C:\\Users\\Kevin\\Documents\\Fin\\Other\\'
# Load CC bills ... Temp section needed for 2019 pre-mint
ccpath='C:\\Users\\Kevin\\Documents\\Fin\\credit_card_bills\\'
ink=aptexp.loadProcessCC(ccpath+"chase_ink_2019.csv")
chase = aptexp.loadProcessCC(ccpath+"Qualls_chase_2019.csv",**{'Acct':9555})
disc = aptexp.loadProcessCC(ccpath+"Qualls_discover_2019.csv",**{'Acct':1037})
disc2 = aptexp.loadProcessCC(ccpath+"Kevin_discover_2019.csv",**{'Acct':9534})
allCC=aptexp.combineCCBills([ink,chase,disc,disc2]) # first creation

allCC.to_csv(ccpath+'CCexpenses_2019.csv', index=False)

allCC=pd.read_csv(ccpath+'CCexpenses_2019.csv') # reload
# remove non-apt categories, etc.
allCC=aptexp.cleanCCtransactions(allCC)

# Searching for specific CC transaction
match =allCC[allCC['Vendor'].str.contains('baba', case=False)]

# Find unique apt expenses from allCC (that should be added to mint)
early=allCC[allCC['Date'] < mint.Date.min()]
mint=mint.append(early, ignore_index=True)
mint=mint.sort_values(['Date','Vendor'])
mint.to_csv("C:\\Users\\Kevin\\Documents\\Fin\\Other\\mint_transactions_2019.csv", index=False)

late=allCC[allCC['Date'] >= early.Date.max()]
# Try to find entries from late missing from mint.csv (heavily overlapped period)
test=pd.merge(late, mint, how='left', on=['Amount','Vendor','Date'], suffixes=('','2'))
test=test[pd.isnull(test['Acct2'])] # drops obvious matches (627 left)
test=test[mint.columns.tolist()]
test=pd.merge(late, mint, how='left', on=['Amount','Date'], suffixes=('','2'))

matches=test[pd.notnull(test['Acct2'])] # Date/Amount matches... these look OK
test=test[pd.isnull(test['Acct2'])] # 

# Now look for unique transactions in allCC ... maybe a few in 
# Will have mint csv, google apt expenses and cc_expenses csv (e.g. from Chase for 2019 only)
# Mint categories should be accurate, CC auto-categorization doesn't matter (not used after 2019)
both=mint.append(allCC, ignore_index=True)

dups=both[both.duplicated(['Date','Vendor','Amount'], keep=False)]
# For 2019 processing, make unique merge of CC and mint?
# or just process separately and ensure no misses from both?

# Manually handle duplicates that'd screw up merge, mark "YD"

# Confirm and mark duplicates (both files)
colset=['Date','Acct','Amount']

# Save 
allCC.to_csv(finPath+'CCexpenses_2019.csv', index=False)

# Manually handle duplicated transactions (screws up left merg)
colset=['Date','Acct','Amount']
# Cross-matching/identification of same transactions
Goodmatch=pd.merge(allCC, Aptexp, how='inner', on=['Date','Acct','Amount'], suffixes=('','2'))

# searching for specific substring all cols
result =cc[cc.apply(lambda row: row.astype(str).str.contains('USPS').any(), axis=1)]
# searching for specific substring all cols
result = cc[cc['Amount']==64.82]

#%%
# load apt expenses sheet
os.chdir('C:\\Users\\tkc\\Documents\\Fin\\taxes')

CCfiles={'1848':"C:\\Users\\tkc\\Documents\\Fin\\credit_card_bills\\chase_ink.xls",
'9555':"C:\\Users\\tkc\\Documents\\Fin\\credit_card_bills\\Qualls_Chase.xls",
'9534':"C:\\Users\\tkc\\Documents\\Fin\\credit_card_bills\\discover_bills.xls",
'1037':"C:\\Users\\tkc\\Documents\\Fin\\credit_card_bills\\qualls_discover_bills.xls"
}
HDr=pd.read_excel('C:\\Users\\tkc\Documents\\Fin\\taxes\\Receipts\\HD_receipts_log.xlsx', sheetname='HD')

#%% Load/ handle alias accts, etc
Aptexp, CCbills=loadexpenses(2018, CCfiles) 
# Change identical Chase ink #s 1848, 9553, 1830 in Aptexp
Aptexp['Acct']=Aptexp['Acct'].replace('9553','1848')
Aptexp['Acct']=Aptexp['Acct'].replace('1830','1848')

# Drop those explicitly marked as included (useful for split transactions)
CCbills=CCbills[CCbills['Matched']!='Split']
Aptexp=Aptexp[Aptexp['Matched']!='Split'] # drop split transactions manually identified
#%% Finding individual 
CCbills.Acct.unique()
Aptexp.Acct.unique()

Test=CCbills[pd.isnull(CCbills['Date'])]
Test=CCbills[CCbills.Acct=='1037']
Test=CCbills[CCbills.Vendor.str.contains("Advance", case=False)]
Test=CCbills[CCbills.Amount==310]
Test=CCbills[ (CCbills.Vendor.str.contains("home", case=False) ) & (CCbills.Amount==14.28) ]
#%%Aptexp`
# Cross-checking CCbills vs apt exp  
CCbills=CCbills.reset_index(drop=True)
Goodmatch=pd.merge(CCbills, Aptexp, how='inner', on=['Date','Acct','Amount'], suffixes=('','2'))

#%% find CC
CCcols=CCbills.columns
CConly= CCbills.merge(Aptexp.drop_duplicates(), on=['Date','Acct','Amount'], how='left', suffixes=('','_2'), indicator=True)
CConly=CConly[CConly['_merge']=='left_only']
CConly=CConly[CCcols]

aptCols=Aptexp.columns
Aptonly= Aptexp.merge(CCbills.drop_duplicates(), on=['Date','Acct','Amount'], how='left', suffixes=('','_2'), indicator=True)
Aptonly=Aptonly[Aptonly['_merge']=='left_only']
Aptonly=Aptonly[aptCols]
#%%
# Find and fix date errors (in apt_expenses)
Test=pd.merge(CConly, Aptonly, on=['Acct','Amount'], how='inner', suffixes=('','_2'))
# Find and fix account # errors (in apt_expenses)
Test=pd.merge(CConly, Aptonly, on=['Date','Amount'], how='inner', suffixes=('','_2'))
# Check for possible amount entry errors / split transactions, etc/
Test=pd.merge(CConly, Aptonly, on=['Date','Acct'], how='inner', suffixes=('','_2'))
Test=Test.sort_values(['Date'])
# Now concat both, sort by date and examine
skipaccts=['cash','Mom','store credit'] 
Aptonly=Aptonly[~Aptonly['Acct'].isin(skipaccts)]
Aptonly=Aptonly[~Aptonly['Acct'].str.contains('comm', case=False)] # skip commerce accounts
Aptonly.to_csv('apt_exp_only.csv', index=False)
CConly=CConly.sort_values(['Date'])
CConly=CConly[['Date', 'Acct', 'Vendor','Comments', 'Amount', 'Category', 'Included','Subtotals', ]]
CConly.to_csv('CC_only.csv', index=False)

#%% Grouping of expenses by unit/repair, improve, etc.
Aptexp, CCbills=loadexpenses(2018, CCfiles) # Reload all of apt expenses
Aptexp.Unit.unique()
units={'Ars':['24A','24','26','26A','ARS'], '28':['28'], 'Mag':['Mag','Mag1E','Mag1W','Mag2E','Mag2W'], 
       "Pot":['Pot','44','44A'],'all':['all'] }
cols=['Amount', 'Repair', 'Improve','Supplies', 'Other', 'Home']
sumByUnits(Aptexp, units, cols)
grouped=Aptexp.groupby(['Unit'])

Aptexp.groupby(['Unit'])['Amount'].sum()
mytab=Aptexp.groupby(['Unit'])['Repair','Improve','Supplies','Other','Home'].sum()

Aptexp[['Repair','Improve','Supplies']].sum()
unitgroups=[ [']]
#%%
Both=pd.concat([CConly,Aptonly], ignore_index=True)
Both.sort_values(['Date','Amount'])

Both=pd.merge(Apt18, CCbills, how='inner', on=['Acct','Amount'], suffixes=('1','2'))
Both=pd.merge(Apt18, CCbills, how='inner', on=['Date','Amount'], suffixes=('1','2'))


All=pd.merge(Apt18, CCbills, how='outer', on=['Date','Acct','Amount'], suffixes=('1','2'))


Unmatch=All[ (pd.notnull(All['Vendor1'])) & (pd.notnull(All['Vendor2']))

thismask=(pd.notnull(All['Vendor1'])) & (pd.notnull(All['Vendor2']))
Unmatched=All.loc[~thismask]

Unmatched=Unmatched[Unmatched['Acct'].str.contains(mystr, regex=True)]
Unmatched=Unmatched.sort_values(['Date'])
Unmatched.to_csv('unmatched.csv', index=False)