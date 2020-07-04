# -*- coding: utf-8 -*-
"""
Created on Tue Dec 19 16:00:00 2017

@author: tkc
"""
# googlefinance.client doesn't seem to work

import urllib
import re
import pandas as pd
import numpy as np
from datetime import timedelta
from datetime import datetime
from openpyxl import load_workbook # writing to Excel
import time
from lxml import html

from lxml import etree # for config.xml reader 
from io import StringIO, BytesIO

def readMyPay(fname):
    '''
    Read values out of mypay html file
    '''    
    changes={'FEGLI OPTNL':'Fegli Optional','FEGLI':'Fegli Life',
             'FEHB':'Fehb Medical','TSP SAVINGS':'Tsp','TSP MATCHING':'Tsp Match'}
    # old version that used to work ... 
    # website change CNTRL-S doesn't work
    # using chrome CNTRL+SHIFT+I inspector -> save -> read attempt hits encoding errors 
    with open(fname,'r') as file:
        content = file.read()
    etree = html.fromstring(content)

    with open(fname,'rb') as file:
        content = file.read()
    BytesIO(content)

    parser=etree.HTMLParser()
    
    myStr = StringIO(fname)
    tree = etree.HTMLparser(fname)
    tree=etree.html(fname)
    tree = etree.parse(fname)
    # retrieve other pay columns and append
    myElems=[]
    for code in ['GROSS PAY','TAXABLE WAGES','NONTAXABLE WAGES']:
        for elem in etree.iter(tag='tr'):
            if code in elem.text_content():
                for el in elem.iter(tag='td'):
                    val=el.text_content()
                    if 'TSP DATA' in val:
                        continue
                    elif len(val.strip())>0 and len(val.strip())<50:
                        myElems.append(val.replace('\n','').strip())    
    # Get FEGLI sections (but labels, vals, YTDvals all in single column)
    for elem in etree.iter(tag='tr'):
        if 'FEGLI' in elem.text_content():
            for el in elem.iter(tag='td'):
                val=el.text_content()
                if len(val.strip())>0 and len(val.strip())<50:
                    myElems.append(val)
    # Replace 2nd instance of FERS
    dupl=[i for i, n in enumerate(myElems) if n == 'RETIRE, FERS'][1]
    myElems[dupl]='FERS MATCH'
    # drop aeic ... it's screwing up net pay grab
    myElems=[i for i in myElems if i!='AEIC'] 
    # Parse out floats 
    floatpos=[]
    for i, val in enumerate(myElems):
        if '.' in val:
            floatpos.append(i)
    floats=[] # first element will be labelled one (ignore codes)
    for key, group in it.groupby(enumerate(floatpos), lambda i: i[0]- i[1]): 
        group = list(map(itemgetter(1), group))
        floats.append(group)
            
    labelpos=[i for i in range(0,len(myElems)) if i not in floatpos]   
    
    starts=[] # first element will be labelled one (ignore codes)
    for key, group in it.groupby(enumerate(labelpos), lambda i: i[0]- i[1]): 
        group = list(map(itemgetter(1), group))
        starts.append(group[0])
    # parse/separate column names from vals from YTD vals into list of dicts
    vallist=[]
    indlist=[]
    for i, sval in enumerate(starts):
        valdict={}
        if myElems[sval] in changes: # Do name changes for values here
            indlist.append(changes.get(myElems[sval]))
        else: # switch to title case
            indlist.append(myElems[sval].title())
        # valdict['Type']=myElems[sval]
        try:
            valdict['Value']=myElems[floats[i][0]]
            valdict['YTD']=myElems[floats[i][1]]
            vallist.append(valdict)
        except:
            print('Problem with', myElems[sval] )
    # retrieve other pay columns and append
    myElems=[]
    for code in ['GROSS PAY','TAXABLE WAGES','NONTAXABLE WAGES']:
        for elem in etree.iter(tag='tr'):
            if code in elem.text_content():
                for el in elem.iter(tag='td'):
                    val=el.text_content()
                    if len(val.strip())>0 and len(val.strip())<50:
                        myElems.append(val.replace('\n','').strip())
    valdict={} # Adds regular pay
    indlist.append(myElems[0].title())
    #valdict['Type']=myElems[0]
    valdict['Value']=myElems[2] # first # is # hours 
    valdict['YTD']=myElems[2]
    vallist.append(valdict)
    # Add rows for calculated quantities or header rows (ie. deductions)
    for val in ['PRETAX','AFTERTAX','SUMMARY', 'Tax Total','Tsp Roth','Tsp Total','Tsp Percent']:
        indlist.append(val)
        vallist.append({ 'Value':'', 'YTD':''}) # not yet calculated
    # Create dataframe for vals (incl blank separator rows)
    vals=pd.DataFrame(vallist, index=indlist)
    # drop duplicates (e.g. employer medicare, etc. )
    vals=vals[~vals.index.duplicated(keep='first')]
    
    def convertFloat(val):
        # Strings replaced with float (after comman remove... missing or erroneous
        # becomes np.nan (lambda function)
        try:
            return float(val.replace(',',''))
        except:
            return np.nan
        
    # Replace type vals if in changes dict (replaced above )
    vals['Value']=vals['Value'].apply(lambda x:convertFloat(x) )
    vals['YTD']=vals['YTD'].apply(lambda x:convertFloat(x) )    
    
    # Calculate tax, tsp totals, tsp perc, taxable pay 
    taxcols=[i for i in list(vals.index) if 'Tax' in i]
    taxcols.extend(['Oasdi','Medicare'])
    currtax=vals[vals.index.isin(taxcols)]['Value'].sum()
    YTDtax=vals[vals.index.isin(taxcols)]['YTD'].sum()
    vals=vals.set_value('Tax Total', 'Value', currtax)
    vals=vals.set_value('Tax Total', 'YTD', YTDtax)
    # Calc tsp total
    tspcols=[i for i in list(vals.index) if 'Tsp' in i]
    currtsp=vals[vals.index.isin(tspcols)]['Value'].sum()
    YTDtsp=vals[vals.index.isin(tspcols)]['YTD'].sum()
    vals=vals.set_value('Tsp Total', 'Value', currtsp)
    vals=vals.set_value('Tsp Total', 'YTD', YTDtsp)
    # Calc tsp percentage
    tspper=100*(vals.loc['Tsp']['Value']/vals.loc['Gross Pay']['Value'])
    vals=vals.set_value('Tsp Percent', 'Value', tspper)
    # Now clean up and reorder for salary info
    droprows=[i for i in vals.index if '%' in i]
    for r in droprows:
        vals=vals.drop(r, axis=0)
    roworder=['Gross Pay', 'Oasdi','Medicare','Tax, Federal','Tax, State',
        'Tax, Local',  'PRETAX','Fehb Medical','Dental','Retire, Fers','Tsp', 'Tsp Roth',
        'Tsp Basic', 'Tsp Match', 'Tsp Total', 'Tsp Percent', 'AFTERTAX','Fegli Life', 
        'Fegli Optional', 'Fers Match', 'SUMMARY','Taxable Wages', 'Tax Deferred Wages', 
        'Nontaxable Wages','Tax Total', 'Deductions', 'Net Pay']
    vals=vals.reindex([roworder])    
    return vals

def processBuys(tspfiles, tsp):
    # add records of tsp purchase (csv download on day of purchase)
    mycols=tsp.columns
    for tfile in tspfiles:
        # read out each buy as dict
        buy=readTspFile(tfile) 
        tsp=tsp.append(buy, ignore_index=True)
    tsp=tsp.sort_values(['Date'])
    tsp=tsp.loc[:, mycols]
    return tsp

def updateTsp(tsp):
    '''
    Find missing # of shares and total purchase amount for new TSP transactions
    '''
    # determine # of chase for this purchase 
    purcols= [i for i in tsp.columns if 'purchase' in i]
    tsp['Delta']=tsp['Date']-tsp['Date'].shift(1) # day difference between previous entry
    for index, row in tsp.iterrows():
        if str(row.Total)=='nan':
            print(row.Delta,' for index', index)
            if row.Delta > timedelta(days=13) and row.Delta < timedelta(days=15):
                for col in purcols:
                    bcol=col[0]+' balance'
                    newval=tsp.loc[index][bcol] - tsp.loc[index-1][bcol]
                    tsp=tsp.set_value(index, col, newval)
    # sum individual sub-purchases to find grand total $ amt
    for index, row in tsp.iterrows():
        if str(row.Total)=='nan':
            total=0.0
            for col in purcols:
                fund=col[0]
                total+=row[col]*row[fund+' price']
            tsp=tsp.set_value(index,'Total', round(total,2) )
    del tsp['Delta']
    return tsp
            
def readTspFile(fname):
    '''
    Read single downloaded TSP file to dict row
    '''
    with open(fname,'r') as myfile:
        vals=myfile.readlines(2)
    # get date from file name
    myDate=vals[0].split(',')[2].replace('"','')
    mycols=['Fund','Shares','Price', 'Balance', 'Dist','Alloc']
    df=pd.read_csv(fname, header=2, names=mycols)
    df=df[df['Balance']>0]
    df=df[df['Fund'].str.contains('Fund')]
    buy={} # single dict for this purchase file
    buy['Date']=myDate
    buy['Date']=pd.to_datetime(buy['Date'], format='%m/%d/%Y')
    for index, row in df.iterrows():
        fund=row.Fund[0]
        buy[fund+' price']=row.Price
        # shares is total share balance (not purchased this period)
        # balance is current dollar value
        buy[fund+' balance']=row.Shares
    return buy

def writetoxls(df, sheetname, xlsfile):
    ''' Generic write of given df to specified tab of given xls file '''
    # convert timestamps to string so that they open nicely in Excel
    if "Date" in df.columns:
        df['Date']=df['Date'].apply(lambda x:pd.to_datetime(x).strftime("%m/%d/%Y"))        
    book=load_workbook(xlsfile)
    writer=pd.ExcelWriter(xlsfile, engine='openpyxl', datetime_format='mm/dd/yy', date_format='mm/dd/yy')
    writer.book=book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    df.to_excel(writer,sheet_name=sheetname,index=False) # this overwrites existing file
    writer.save() # saves xls file with all modified data
    return

#  row=finproj.iloc[0]
#  intrinio or alpha vantage 
# quandl https://www.quandl.com/api/v3/datasets/EOD/AAPL.csv?api_key=YOURAPIKEY

def lookup_quotes_alpha(finproj):
    ''' URL lookup of symbols from alpha vantage
    '''
    API_KEY='CSYV8EMI7A90EHKB'
    base_url='https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&apikey='+API_KEY+'&symbol='
    thisdate=datetime.date.strftime(datetime.now(), "%m/%d/%Y")
    for index, row in finproj.iterrows():
        with urllib.request.urlopen(base_url + row.Symbol) as url:
            content = url.read()
        content=content.decode("utf-8")
        match = re.search('class=pr>\d+.\d+', content)
        quote=np.nan
        if match:
            quote = match.group(0)
            quote=float(quote.split('>')[1].split("'")[0])
        else:
            # handle custom case for QQQQ
            match=re.search(r'"id":"700146"', content)
            if match:
                content=content[match.start():]
                match=re.search(r'ETF', content) # find following ETF
                if match:
                    content=content[match.start():]
                    match=re.search(r'\d+.\d+', content) 
                    if match:
                        quote=float(match.group(0))
                    else:
                        print('No quote for ', row.Symbol)
        finproj=finproj.set_value(index,'Price', quote)
        finproj=finproj.set_value(index,'Last_update', thisdate)
    return finproj

def lookup_quotes_cnbc(quotes):
    '''
    Lookup quotes from cnbc 
    '''
    base_url='https://www.cnbc.com/quotes/?symbol='
    thisdate=datetime.now().strftime('%m/%d/%Y')
    for index, row in quotes.iterrows():
        # TESTING index=1 row=quotes.loc[index]
        if ' Fund' in row.Symbol:
            continue
        try:
            with urllib.request.urlopen(base_url + row.Symbol) as url:
                content = url.read()
            content=content.decode("utf-8")
        except:
            print('No quote found for {}'.format(row.Symbol))
            continue
        startpos=content.find('"last":')+8
        match=re.match(r'\d+.\d+', content[startpos:startpos+10])        
        if match:
            thisval=float(match.group(0))
            quotes=quotes.set_value(index, 'Price',thisval)
            quotes=quotes.set_value(index, 'Last_update', thisdate)
            print('Updated ', row.Symbol)
        else:
            print(row.Symbol, ' not updated ', )
        time.sleep(0.1)
    return quotes

def updateGsheetQuotes(pyGsheet, quotes):
    ''' After stock quote web scrape, update gsheet w/ new values
    args: 
        pyGsheet - gsheets connection to quotes worksheet within fin_projection sheet
        quote - dataframe w/ new values
    '''    
    pyGsheet.update_col(2,  quotes.Price.tolist(), row_offset=1) # 1 is first col for gsheets
    pyGsheet.update_col(3,  quotes.Last_update.tolist(), row_offset=1)
    return 

def lookup_TSP(quotes):
    '''
    No TSP ticker at alphavantage... pull from tsp website
    '''
    base_url='https://www.tsp.gov/InvestmentFunds/FundPerformance/index.html'
    with urllib.request.urlopen(base_url) as url:
        content = url.read()
    content=content.decode("utf-8")
    start=content.find("oddRow") # pretty close to start of numbers/table
    content=content[start:]
    end=content.find("evenRow")
    content=content[:end]
    vals=re.findall(r'(\d+.\d{4})', content)
    if len(vals)!=10:
        print("Couldn't find first row of 10 share prices")
        return quotes
    thisdate=datetime.now().strftime('%m/%d/%Y')
    tsp=quotes[quotes['Symbol'].str.contains(' Fund')]
    vals=[float(f) for f in vals[5:]]
    tspprice={}
    tspprice['G'], tspprice['F'], tspprice['C'], tspprice['S'], tspprice['I']=vals
    for index, row in tsp.iterrows():
        quotes=quotes.set_value(index, 'Price',tspprice.get(row.Symbol[0], np.nan))
        quotes=quotes.set_value(index, 'Last_update', thisdate)
    return quotes

''' TESTING
symbol='CRSP'
base_url = 'http://finance.google.com/finance?q='
with urllib.request.urlopen(base_url + symbol) as url:
    content = url.read()
content=content.decode("utf-8")

match = re.search('ETF', content)
matches=re.findall(r'ETF*chr', content)
matches=re.findall(r'"id":"700146"', content)
match.group(0)
content[0:200]
'''

    