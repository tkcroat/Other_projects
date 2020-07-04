# -*- coding: utf-8 -*-
"""
Created on Sun Mar  5 16:17:02 2017

@author: tkc
"""

from datetime import datetime, timedelta
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

def cleanCCtransactions(allCC):
    ''' Mark as drop various non-apt related categories (but keep all in master sheet)
    args: allCC - merged file w/ all cc transactions from 2x chase, 2x discover, mint, etc.
    Entire sheet is being returned (w/o category removal... just adding drop to matched category)
    '''
    if not isinstance(allCC.iloc[0]['Date'], datetime):
        allCC['Date']=allCC['Date'].apply(lambda x:convertDate(x))
    # Mark nan rows as drop 
    ccnan=allCC[pd.isnull(allCC.Category)]
    ccnan['Matched']='Drop'
    allCC.loc[ccnan.index, ccnan.columns]=ccnan
    ''' Choose only apt-related categories
    keepcols=['Bills & Utilities', 'Repair & Maintenance', 
       'Miscellaneous', 'Gas','Shopping', 
       'Merchandise & Inventory', 'Fees & Adjustments', 'Merchandise',
       'Automotive', 'Home', 'Home Improvement',
       'Office & Shipping', 'Professional Services','Services']
    '''
    dropcols=['Entertainment','Food & Drink', 'Health & Wellness','Groceries',
     'Payments and Credits','Personal','Travel','Gifts & Donations',
     'Awards and Rebate Credits','Supermarkets','Gasoline','Travel/ Entertainment',
     'Restaurants','Education','Medical Services']
    ccdrop=allCC[allCC.Category.isin(dropcols)]
    ccdrop['Matched']='Drop'
    allCC.loc[ccdrop.index, ccdrop.columns]=ccdrop
    return allCC

def processMint(mint):
    ''' Std reformatting of mint csv as exported, incl date format, columns rename/adjust
    rename accounts to match apt expenses, etc.
    '''
    mint['Matched']=''
    mint=mint.rename(columns={'Account Name':'Acct','Description':'Vendor'})
    mint['Date']=mint['Date'].apply(lambda x: convertDate(x))
    # Standardize account names (to match apt exp. and others)
    mycols=['Date', 'Acct', 'Vendor', 'Amount', 'Category', 'Matched','Notes']
    mint=mint[mycols]
    def renameAcct(val):
        # Standardize account name
        accts={'Chase Ink Kevin':1848, 'Discover':1037, 'Qualls Chase 9555':9555, 
        'Commerce Apt Checking':'apt chk','Commerce Kevin Checking':'kevin chk', 
        'CommerceBasic Checking':'Becky chk','Interest Checking':'chk', 'Chase Ink Becky':1848}
        if val in accts.keys():
            return accts.get(val)
        else:
            return val
    # Rename accounts as above
    mint.Acct=mint.Acct.apply(lambda x: renameAcct(x))
    return mint

def convertDate(val):
    if isinstance(val, datetime): # true for datetime or pd.timestamp
        try:
            return val.to_pydatetime().date() # for pandas timestamp
        except:
            try:
                return val.date()  # for datetime.datetime
            except:
                return val # already datetime
    else: # likely string
        # Simple date converter
        for sep in ['-','/']:
            try:
                # try various separators
                t1, t2, t3=[int(i) for i in val.split(sep)]
                # year can be first or last
                if t1>999: # year first ... YYYY MM DD
                    return datetime(t1, t2, t3).date()
                elif t3>999: # MM DD YYYY
                    return datetime(t3, t1, t2).date()
                elif t1<100 and t2<100 and t3<100:
                    # very likely MM DD YY
                    return datetime(t3+2000, t1, t2).date()
                else: 
                    pass
            except:
                pass
    return val
   
def loadProcessCC(ccFname, **kwargs):
    ''' Process and sync cols for different CC accts (from csv)
    args:
        ccFname: full path to CC csv file
    kwargs={'Acct':1037}
    
    ccFname='C:\\Users\\Kevin\\Documents\\Fin\\credit_card_bills\\chase_ink_2019.csv'
    '''
    df=pd.read_csv(ccFname)
    mycols=['Date', 'Acct','Vendor', 'Amount', 'Category', 'Matched', 'Notes']
    df=df.rename(columns={'Card':'Acct','Transaction Date':'Date','Trans. Date':'Date'
            ,'Memo':'Notes','Description':'Vendor'})
    df['Matched']=''
    if 'Acct' not in df.columns and 'Acct' in kwargs:
        df['Acct']=kwargs.get('Acct')
    missing=[i for i in mycols if i not in df.columns]
    for col in missing:
        df[col]=''
    df=df[mycols]
    # convert date
    df['Date']=df['Date'].apply(lambda x:convertDate(x))  
    return df

def combineCCBills(CClist):
    ''' Combine CC bills csv files to single df
    args:
        CClist - list of dataframes already loadprocessed
    '''
    df=pd.DataFrame()
    for cc in CClist:
        df=df.append(cc, ignore_index=True)
    df=df.sort_values(['Date','Vendor'])
    df=df.reset_index(drop=True)
    return df

def processSplits(Aptexp):
    ''' Split up expenses (24/26) by duplicating rows and dividing amount 50/50
    
    '''
    # split and summarize expenses by unit
    Aptexp=Aptexp[pd.notnull(Aptexp['Unit'])]
    Aptexp['Unit']=Aptexp['Unit'].astype(str)
    splits=Aptexp[Aptexp['Unit'].str.contains('/')].copy()
    splits2=splits.copy()

    for col in ['Amount','Repairs','Improvement', 'Supplies', 'Other', 'Home repair']:
        splits[col]=splits[col]/2
        splits2[col]=splits[col]/2
    splits['Unit']=splits['Unit'].str.split('/').str[0]
    splits2['Unit']=splits['Unit'].str.split('/').str[1]
    # remove split values
    myExps=Aptexp[~Aptexp.index.isin(splits.index)].copy()
    myExps=myExps.append(splits, ignore_index=True)
    myExps=myExps.append(splits2, ignore_index=True)
    return myExps

def plotUnitExpense(Aptexp):
    ''' Time series unit Expenses by month ... colored line plot showing progress of 
    various projects... can start on arb. month and 
    '''
    myExps=processSplits(Aptexp)
    myExps['Month']=myExps['Date'].apply(lambda x: x.month)
    # alter months if not single year version
    if myExps.Date.max() -myExps.Date.min() < timedelta(days=366):    
        myExps['Year']=myExps['Date'].apply(lambda x: x.year)
        startYr=myExps['Year'].min()
        myExps['Month']=myExps['Month']+(myExps['Year']-startYr)*12
        # set starting month to one
        myExps['Month']=myExps['Month']- myExps['Month'].min() + 1
    fig, ax = plt.subplots(figsize=(15,7))
    myExps.groupby(['Month','Unit']).sum()['Amount'].unstack().plot(ax=ax)
    return

def splitSummarize(Aptexp, **kwargs):
    ''' Split summarize accounts by property.. passing apt exp google sheet
    handles split for unit (such as 24/26)
    args:
        Aptexp -  apt expenses google sheet w/ minimal prior processing
    kwargs:
        'splitTaxSubcat': bool -- split into tax subcategories (repairs, supplies, )
    
    '''
    
    expgroups={'ARS':['24A','26','24','26A'],
                'MAG':['MAG'],
                'POT':['POT','44','44A'],
                'ALL':['ALL'],
                '28':['28']
                }
    taxcols=['Amount','Repairs','Improvement', 'Supplies', 'Other', 'Home repair']
    # split and summarize expenses by unit
    Aptexp=Aptexp[pd.notnull(Aptexp['Unit'])]
    Aptexp['Unit']=Aptexp['Unit'].astype(str)
    splits=Aptexp[Aptexp['Unit'].str.contains('/')].copy()
    splits2=splits.copy()

    for col in taxcols:
        splits[col]=splits[col]/2
        splits2[col]=splits[col]/2
    splits['Unit']=splits['Unit'].str.split('/').str[0]
    splits2['Unit']=splits['Unit'].str.split('/').str[1]
    # remove split values
    myExps=Aptexp[~Aptexp.index.isin(splits.index)].copy()
    myExps=myExps.append(splits, ignore_index=True)
    myExps=myExps.append(splits2, ignore_index=True)    
    # Calculate totals by property
    sumList=[]
    for prop, units in expgroups.items():
        thisProp={'Prop':prop, 'Total':myExps[myExps['Unit'].isin(units)]['Amount'].sum()}
        if kwargs.get('splitTaxSubcat', True):
            for col in [i for i in taxcols if i!='Amount']:
                thisProp[col]=myExps[myExps['Unit'].isin(units)][col].sum()
        sumList.append(thisProp)
    props=pd.DataFrame(sumList)
    grouped=myExps.groupby('Unit')
    units=[]
    for un, gr in grouped:
        thisUnit={'Unit':un, 'Total':gr.Amount.sum()}
        if kwargs.get('splitTaxSubcat', True):
            for col in [i for i in taxcols if i!='Amount']:
                thisUnit[col]=gr[col].sum()
        units.append(thisUnit)
    units=pd.DataFrame(units)
    # reorder column order to preference
    mycols=['Prop','Total','Repairs','Improvement', 'Supplies', 'Other', 'Home repair']
    mycols2=['Unit','Total','Repairs','Improvement', 'Supplies', 'Other', 'Home repair']
    mycols=[i for i in mycols if i in props.columns]
    props=props[mycols]
    mycols2=[i for i in mycols2 if i in units.columns]
    units=units[mycols2]
    return props, units
#%% Apartment expenses tax scripts

def sumByUnits(Aptexp, units, cols):
    ''' Summarize expenses by groups of units ... 
    
    args:
        Aptexp - loaded expenses (repair/improve) from annual xls file
        units -  dict w/ name and list of units in given unit group
    '''
    summlist=[]
    for groupName in list(units.keys()):
        summdict={}
        thisUnits=units.get(groupName,[])
        summdict['group']=groupName
        thisExp=Aptexp[Aptexp['Unit'].isin(thisUnits)]
        for col in cols:
            summdict[col]=thisExp[col].sum()
        summlist.append(summdict)
    summs=pd.DataFrame(summlist)
    return summs
        
    
def loadexpenses(year, CCfiles):
    ''' Load CC bills & apt expenses for given year
    CCfiles -dict w/ num key and path
    '''
    Aptexp=pd.read_excel('C:\\Users\\tkc\\Documents\\Fin\\taxes\\apt_expenses'+str(year)+'.xlsx', skiprows=1)
    Aptexp=Aptexp.iloc[:,0:12]
    mycols=['Date','Acct','Vendor','Comments','Amount','Repair','Improve','Supplies',
            'Other','Home','Unit','Receipt']
    Aptexp.columns=mycols
    Aptexp=Aptexp.dropna(subset=['Acct'])  
    Aptexp.Acct=Aptexp.Acct.astype(str) # accts as string for comparison
    # now load credit card bill Excel files
    mycols=['Date','Vendor','Amount','Category','Subtotals','Comments','Included']
    CCbill=pd.DataFrame(columns=mycols)
    start=datetime.strptime('1/1/'+str(year), '%m/%d/%Y')  
    end=datetime.strptime('12/31/'+str(year), '%m/%d/%Y')  
    
    for key, val in CCfiles.items():
        try:
            thisCC=pd.read_excel(val)
        except:
            print("can't load file", val)
            continue
        thisCC=thisCC.iloc[:,0:7]
        thisCC.columns=mycols
        # filter to those containing APT
        thisCC=thisCC[pd.notnull(thisCC['Category'])]
        thisCC['Category']=thisCC['Category'].apply(lambda x:makeStr(x))            
        try:
            thisCC['Date']=thisCC['Date'].apply(lambda x:makeDt(x))
        except:
            print('Problem w/ type conversion for', val)
            continue
        thisCC=thisCC[ thisCC['Category'].str.contains('APT', case=False) ]
        # apply yearly time filter
        thisCC=thisCC[(thisCC['Date'] > start) & (thisCC['Date'] <= end)]
        thisCC['Acct']=key
        CCbill=CCbill.append(thisCC, ignore_index=True)
    return Aptexp, CCbill

def makeStr(val):
    '''
    Convert val to string (useful before str.contains filter)
    '''
    try:
        return str(val)
    except:
        return ''
    
def makeDt(val):
    '''
    Convert val to string (useful before str.contains filter)
    '''
    if isinstance(val, datetime):
        return val
    try:
        return val.to_pydatetime()
    except:
        print('could not convert', val, 'to datetime')
        return np.nan