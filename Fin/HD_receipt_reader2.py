# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 09:23:30 2016

@author: tkc
"""
#%%
import os, pandas, glob, sys, re # already run with functions 
from lxml import html
import numpy as np

# from Ipython.Debugger import Tracer
# import csv, fileinput
if 'C:\\Users\\tkc\\Documents\\Python_Scripts' not in sys.path:
    sys.path.append('C:\\Users\\tkc\\Documents\\Python_Scripts')
os.chdir('C:\Temp\HD')
filelist=glob.glob('*.eml') # all receipt files in selected data folder

HDreceiptLog=pandas.DataFrame(columns=['Date','Acct','Vendor','Comment','Total','Repair amt','Improvement','Supplies','Other','Home Repair','Unit','Receipt'])
HDitemLog=pandas.DataFrame(columns=['Date','HD#','Item','Quantity','Unit cost','Subtotal','Tax','Item total'])
#%%
for val in enumerate(filelist):
    with open(val, 'r') as file:
        wholefile = file.read()
    # initialize both temporary dictionaries for temp storage & transfer to dataframes (new instance for each receipt)
    HDreceipt={'Date':'','Acct':'','Vendor':'Home Depot','Comment':'','Total':'','Repair amt':'','Improvement':'','Supplies':'','Other':'','Home Repair':'','Unit':'','Receipt':'Y'}
    # HDitem={'Date':'','HD#':'','Item':'','Quantity':'','Unit cost':'','Subtotal':'','Tax':'','Item total':''}
    
    # useful text block starts just before CASHIER and ends near AUTH CODE        
    longstring=wholefile.split('FEED FOR RECEIPT')[1]
    longstring=longstring.split('RETURN POLICY')[0]
'''    
    # now load table with purchase as xml object
    HDtree=html.fromstring(HDdata)  
    HDtable=HDtree.xpath('//table') # oddly returns list with single HTML element
    HDtable=HDtable[0] # gets table 
    lines=HDtable.xpath('//span/text()') # list of text elements within data table of importance
    newlines=[] # turn into a list of strings
    for i,val in enumerate(lines):
        text=str(val)
        newlines.append(text)
    longstring=''.join(newlines)  
'''    
    longstring=longstring.replace('=','')
    longstring=longstring.replace('\n','')
    itemstr=longstring.split('SUBTOTAL')[0]
    # Find subtotal (only used for tax rate calc)
    tempstr=longstring.split('SUBTOTAL')[1]
    tempstr=tempstr.split('SALES')[0]
    match=re.search(r'(\d+\.d{2})', tempstr)
    
    match=re.findall(r'(\d+\.\d+)', tempstr)
    type(match)
    subtotal=float(tempstr.strip())
    #find tax
    tempstr=longstring.split('SALES TAX')[1]
    tempstr=tempstr.split('TOTAL')[0]
    tax=float(tempstr.strip())
    taxrate=tax/subtotal
    #find total
    tempstr=longstring.split('USD$')[1]
    tempstr=tempstr.split('AUTH')[0]
    total=float(tempstr.strip())
    HDreceipt.update({'Total':total})
    
    # this might fail for cash purchases
    #find job name
    tempstring=longstring.split('JOB NAME: ')[1]
    tempstring=tempstring.split('3011')[0]
    HDreceipt.update({'Unit':tempstring}) # i.e. ARS,MAG, all property categories
    # find date    
    tempstring=longstring.split('JOB NAME: ')[1]
    match=re.search(r'(\d+)/(\d+)/(\d+)',tempstring)    
    date=match.group(0)
    HDreceipt.update({'Date':date})   
    # find CC if used
    if 'XXXXXXXXXXXX' in longstring: # find credit card acct
        tempstring=wholefile.split('XXXXXXXXXXXX')[1]
        tempstring=tempstring.split(' ')[0]
        HDreceipt.update({'Acct':tempstring})
    else:
        HDreceipt.update({'Acct':'cash'}) # presumably cash but could be credit
    # now parse items list and add to df
    matches=re.finditer(r'\d\d\d\d\d\d\d\d\d\d\d\d',itemstr) # finds all 12digit HD item codes
    breaks=[]
    for m in matches:
        breaks.append(m.start())
    dim=len(breaks)
    # create df of correct length (one row per item)
    HDitems=pandas.DataFrame(index=np.arange(0,dim), columns=['Date','HD#','Item','Quantity','Unit cost','Subtotal','Tax','Item total'])
    breaks.append(len(itemstr))

    for i in range(0,len(breaks)-1):
        thisitem=itemstr[breaks[i]:breaks[i+1]]
        match=re.search(r'\d\d\d\d\d\d\d\d\d\d\d\d',thisitem) 
        HDitems=HDitems.set_value(i,'HD#',match.group(0))
        HDitems=HDitems.set_value(i,'Date',date)
        # find dollar amounts (very likely only one or two instances) 
        match=re.findall(r'(\d+\.\d+)', thisitem)
        if '@' not in thisitem and len(match)==1: # single item
            HDitems=HDitems.set_value(i,'Quantity',1)
            HDitems=HDitems.set_value(i,'Unit cost',float(match[0]))
            HDitems=HDitems.set_value(i,'Subtotal',float(match[0]))
        elif len(match)==2:
            HDitems=HDitems.set_value(i,'Unit cost',float(match[0]))
            HDitems=HDitems.set_value(i,'Subtotal',float(match[1]))
            # need to find quantity just left of match[0]
            match=re.finditer(r'@',thisitem)
            poslist=[]
            for m in match:
                poslist.append(m.start())
            
            match.start()
            for m in match:
                tempstring=thisitem[m.start()-3:m.start()]
                        

        type(match)

            
    tempstring=wholefile.split(' TOTAL ')[1]
    mymatch=re.match(r'($\d+\.\d+)',tempstring)
    
    mymatch=re.match(r'\d+\S\d+',tempstring)
    mymatch=re.match(r'\d+','  22.22')
    tempstring=mymatch.group(0)
        HDreceipt.update({'Unit':tempstring})
    
    startindex=receiptstring.index('CASHIER')-150
    endindex=receiptstring.index('AUTH CODE')
    receiptstring=receiptstring[startindex:endindex]
    receiptstring=re.sub(' +',' ', receiptstring) # why is this used
    
    # each section starts with "black"... make list of start position indices for parsing 
    starts=[m.start() for m in re.finditer('black', receiptstring)]
    # add 5 to each list element or use m.end()??
    # first extract date and time 
    tempstring=receiptstring[starts[0]:]
    tempstring.split('M')[0]
    # FINISH DATE/TIME
    date=tempstring.split(' ')[3]
    tempstring=receiptstring[starts[2]:]  # skip cashier block
	
	# item number is 12 digits
	# item description is upper case only
	
	# Price: if multiple items @ symbol separates number and price per unit... followed by total
	#Subtotal block
	#Sales tax block
	# total block
	# credit card details
	# grand total 
     # check for job name
     
	# attribute total tax to each sub-item 
	# calculate item total (subtotal + tax for each)
	# find/copy 3 most expensive items for comments of receipt log
	
	# need to append unknown # of li
	len(HDitem)
	len(HDreceipt)
    HDitemLog.loc[i]=pandas.Series(HDitem) # convert dict to series and add as next line to dataframe
    
    
'''    #%%  Append all to common receipts output file... maybe easier with CSV?
C:\Users\tkc\Documents\Fin\taxes\Receipts\HD_receipts_log.xlsx
'''