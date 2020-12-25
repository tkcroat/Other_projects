# -*- coding: utf-8 -*-
"""
Created on Tue Apr  7 10:25:14 2020

Read/write and process google sheets through standard API

Google API developer ... setting up Sheets API
credentials -- OAuth or service account key (associated w/ process not individual)

# 12/25/2020 working creds via quickstart
https://developers.google.com/sheets/api/quickstart/python

https://console.cloud.google.com/apis/credentials -- Google Cloud console also shows new project

1) create a project or use existing project from console.developers.google.com/apis/ 
ensure correct project is chosen (this one is named pygheets-connection created 12/12/2020)
2) use enable APIs and services to enable google drive and google sheets for this project
3) Select credentials tab and click "Create Credentials" button --> create and name a service 
account (can access kcroat google sheets but not those of other users... other option is oauth)
4) choose manage service account and from list of said accts, choose actions -> create key
and save this json --> loads from file name with 
  service_account.Credentials.from_service_account_file(credFile)
5) ERROR... although auth works it gives invalid oauth scope... 
12/12/2020
something about making an token and setting scopes (read/write/delete??)


https://developers.google.com/apps-script/concepts/scopes
# use from pygsheets specific instructions
https://pygsheets.readthedocs.io/en/stable/authorization.html


https://pygsheets.readthedocs.io/en/stable/authorization.html
service account can have max 10 associated keys 

OAuth..  necessary credential for altering google sheets

Scope of Oauth2 should be:  https://www.googleapis.com/auth/spreadsheets (read and write
access to user files);  lesser and greater scopes also exist;

Separate APIs for google drive and google sheets
                                                                          

@author: Kevin

"""

import pandas as pd
import pygsheets as pyg
import numpy as np
from datetime import datetime
import os

from google_auth_oauthlib.flow import InstalledAppFlow # for credentials
# from urllib2 import Request # for credentials refresh
from requests import Request
import pickle # pickle of creds

# path to credentials file (must be outside of git repo)
homeDir="C:\\Users\\kcroat\\KC_Code"
credFile="google_drive_credentials.json"
# creating token from scopes and existing creds 
SCOPES = ['https://www.googleapis.com/auth/spreadsheets',
          'https://www.googleapis.com/auth/spreadsheets.readonly']

def getGoogleCreds():
    ''' Load and process credentials.json (generated by Google API)
    Enables creation of google Service object to access online google sheets
    run of flow.run_local_server(port=0) pops up browser wherein kcroat needs 
    to grant access of quickstart app to google sheets and drive (based on scopes)
    you may have to go through the unsafe proceed anyway warning
    then you reach "The authentication flow has completed. You may close this window."
    
    '''
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    tokenFile=homeDir+'\\google_token.pickle'
    if os.path.exists(tokenFile):
        with open(tokenFile, 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
            ''' NOTE ..not sure refresh of creds will work using requests.Requent
            was originally from urllib2
            '''
        else:
            flow = InstalledAppFlow.from_client_secrets_file('{}/{}'.format(homeDir, credFile), SCOPES)
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open(tokenFile, 'wb') as token:
            pickle.dump(creds, token)
    return creds

_GCREDS=getGoogleCreds()

# can't remember how this presumably oauth json file was created... 
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
    myPygSheet, df = readGsheet(sheetID, creds=_GCREDS, **kwargs) # call generic reader
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

def readGsheet(sheetID, creds=_GCREDS, **kwargs):
    ''' Read google sheets online and return as dataframe
    and as pygsheet
    args:
        sheetID - google sheet ID
        creds - google oauth2 credentials object (loaded from file)
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