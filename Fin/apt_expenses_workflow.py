# -*- coding: utf-8 -*-
"""
Functions to track/ match apartment expense google sheet with other expenses from 
mint and/or credit card annual transaction downloads;
ensure that all expenses are properly tracked before tax time
Created on Sun Mar  5 14:10:40 2017

@author: tkc
"""

import os
import pandas as pd

import apt_expense_functions as aptexp

#%% Read apt_expenses google sheet
sheetID ='15oCMTf7eXZCOq9HH3Os4qJFTzFTaJq5UZuJOhFMy0-E' # apt 2019 exp
tokenFile="C:\\Users\\Kevin\\KC_code\\Google_API\\token.pickle"
aptPySheet, Aptexp = readAptExp(sheetID, tokenFile)

# Load mint csv file for given year
mint = pd.read_csv("C:\\Users\\Kevin\\Documents\\Fin\\Other\\mint_transactions_2019.csv")
mint['Date']=mint['Date'].apply(lambda x: convertDate(x))

# Load CC bills
ink=loadProcessCC("C:\\Users\\Kevin\\Documents\\Fin\\Other\\chase_ink_2019.csv")
chase = loadProcessCC("C:\\Users\\Kevin\\Documents\\Fin\\Other\\Qualls_chase_2019.csv",**{'Acct':9555})
disc = loadProcessCC("C:\\Users\\Kevin\\Documents\\Fin\\Other\\Qualls_discover_2019.csv",**{'Acct':1037})
disc2 = loadProcessCC("C:\\Users\\Kevin\\Documents\\Fin\\Other\\Kevin_discover_2019.csv",**{'Acct':9534})
allCC=combineCCBills([ink,chase,disc,disc2])

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