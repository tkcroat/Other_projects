# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 10:25:14 2020

Read/write and process google sheets through standard API
@author: Kevin

"""

import pandas as pd
import pygsheets as pyg
import numpy as np
from datetime import datetime

import googlecreds as gc # loading google creds from KC_code path

def readProcessGsheet(sheetID, **kwargs):
    ''' Calls reader and then apply some flexible col conversion to google sheet
    returns both pandas dataframe and pyg sheet (handles write back to google drive)
    TODO: consider use of pygsheet DataRange for import (and perhaps alteration)
    args:
        tokenFile - google token
        sheetID- google sheet ID     
    kwargs:
        floats - list of cols to float convert
        dates - list of cols to date convert 
        strings - list of cols as strings
        filters - drop row if null in these cols (usually blank string)
        title - optional retrieve worksheet by title (otherwise first)... passed through
    '''
    def convFloat(val):
        try:
            return round(float(val),2)
        except:
            return np.nan
        
    def convDate(val):
        try:
            return datetime.strptime(val, '%m/%d/%Y')
        except:
            try:
                return datetime.strptime(val, '%m/%d/%y')
            except:
                try:
                    return datetime.strptime(val.split(' ')[0], '%Y-%m-%d')
                except:
                    print('Error converting', val)
                    return val
    myPygSheet, df = readGsheet(sheetID, creds=gc.creds, **kwargs) # call generic reader
    # apply '' and nan filters
    for col in kwargs.get('filters',[]):        
        df=df[df[col]!='']
        df=df[pd.notnull(df[col])]
    for col in kwargs.get('strings',[]):        
        df[col]=df[col].astype(str)
    for col in kwargs.get('dates',[]): # convert date columns
        df[col]=df[col].apply(lambda x: convDate(x))
    for col in kwargs.get('floats',[]): # convert numbers to floats
        df[col]=df[col].apply(lambda x: convFloat(x))
    return myPygSheet, df

def readGsheet(sheetID, creds=gc.creds, **kwargs):
    ''' Read google sheets online and return as dataframe
    and as pygsheet
    args:
        sheetID - google sheet ID
        creds - google oauth2 credentials loaded by gc module 
    kwargs:
        title - worksheet title (otherwise grabs first sheet)
    '''
    gc = pyg.authorize(custom_credentials=creds) # pygsheets client
    sh = gc.open_by_key(sheetID)
    if 'title' in kwargs:
        myPygSheet = sh.worksheet_by_title(kwargs.get('title',''))
    else:
        myPygSheet=sh[0] # default first sheet 
    mycols=myPygSheet.get_row(1) # gets column names
    df=pd.DataFrame(myPygSheet.get_all_records())
    mycols=[i for i in mycols if i!='']
    df=df[mycols] # reorder cols 
    return myPygSheet, df