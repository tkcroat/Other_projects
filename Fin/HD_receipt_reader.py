# -*- coding: utf-8 -*-
"""
Created on Fri Apr 15 09:23:30 2016

@author: tkc
"""
#%%
import os, glob, sys, re # already run with functions 
import pandas as pd
from lxml import html
import numpy as np
import datetime
from openpyxl import load_workbook # writing to Excel

# from Ipython.Debugger import Tracer
# import csv, fileinput

#%%
os.chdir('C:\\Users\\tkc\\Documents\\Fin\\taxes\\HD_receipts')

# Load prior receipt and item logs (append to previous)
HDreceiptlog=pd.read_excel('C:\\Users\\tkc\Documents\\Fin\\taxes\\Receipts\\HD_receipts_log.xlsx', sheetname='HD')
HDitemlog=pd.read_excel('C:\\Users\\tkc\Documents\\Fin\\taxes\\Receipts\\HD_receipts_log.xlsx', sheetname='Items')

# Find new receipts
os.chdir('C:\Temp\HD')
os.chdir('C:\\Users\\tkc\\Documents\\Fin\\taxes\\HD_receipts')
filelist=glob.glob('*.eml') # list of new HD eml receipts
filelist=glob.glob('*.eml')+glob.glob('*.txt')

HDreceiptlog, HDitemlog = batchHDreader(filelist,HDreceiptlog, HDitemlog)

writetoxls(HDreceiptlog,'HD','C:\\Users\\tkc\Documents\\Fin\\taxes\\Receipts\\HD_receipts_log.xlsx')
writetoxls(HDitemlog,'Items','C:\\Users\\tkc\Documents\\Fin\\taxes\\Receipts\\HD_receipts_log.xlsx')

HDreceiptlog['Date']=pd.to_datetime(HDreceiptlog['Date'], format='%d%b%Y:%H:%M')
HDreceiptlog.iloc[0]['Date'].to_pydatetime()
datetime.datetime.date(HDreceiptlog.iloc[0]['Date'])
datetime.datetime.date(HDreceiptlog['Date'])
# check for matching date and amount
pd.to_datetime(HDreceiptlog['Date'], errors='coerce')

#%% Save updated file
HDreceiptlog.to_csv('HDreceiptlog.csv',index=False)
HDitemlog.to_csv('HDitemlog.csv',index=False)
#%% 
def batchHDreader(filelist, HDreceiptlog, HDitemlog):
    ''' Pass list of eml files, extract all receipt info and store in separate tabs of Excel HD receipt logfile '''
    for i, filename in enumerate(filelist):
        with open(filename, 'r') as file:
            wholefile = file.read()
        # initialize both temporary dictionaries for temp storage & transfer to dataframes (new instance for each receipt)
        mycols=HDreceiptlog.columns.tolist()
        # mycols=['Date','Acct','Vendor','Comment','Total','Repair amt','Improvement','Supplies','Other','Home Repair','Unit','Receipt']
        # HDreceiptrow=pd.DataFrame(index=np.arange(0,1), columns=mycols)
        HDrec=pd.Series()
        # HDreceipt={'Date':'','Acct':'','Vendor':'Home Depot','Comment':'','Total':'','Repair amt':'','Improvement':'','Supplies':'','Other':'','Home Repair':'','Unit':'','Receipt':'Y'}
        # useful text block starts just before CASHIER and ends near AUTH CODE        
        if '.eml' in filename:
            longstring=wholefile.split('FEED FOR RECEIPT')[1]
            longstring=longstring.split('RETURN POLICY')[0]
            longstring=longstring.replace('=','')
            longstring=longstring.replace('\n','')
        elif '.txt' in filename:
            longstring=wholefile
            cleanstring=longstring.split('SUBTOTAL')[0]
        # Find subtotal (only used for tax rate calc)
        try:
            tempstr=longstring.split('SUBTOTAL')[1]
            tempstr=tempstr.split('SALES')[0]
            match=re.search(r'(\d+\.\d{2})', tempstr)
            subtotal=float(match.group(0))
        except:
            print('problem finding subtotal for ', filename)
        #find tax
        try:
            tempstr=longstring.split('SALES TAX')[1]
            tempstr=tempstr.split('TOTAL')[0]
            match=re.search(r'(\d+\.\d{2})', tempstr)
            tax=float(match.group(0))
            taxrate=tax/subtotal
        except:
            print('Error finding sales tax for ', filename)
            # backup method of reading from wholefile
        #find total
        try:
            tempstr=longstring.split('USD$')[1]
            tempstr=tempstr.split('AUTH')[0]
            match=re.search(r'(\d+\.\d{2})', tempstr)
            total=float(match.group(0))    
            HDrec=HDrec.set_value('Total',total)
        except:
            print('Error finding total for ', filename)
        
        # this might fail for cash purchases
        #find job name (sometimes absent)
        try:
            tempstr=longstring.split('JOB NAME: ')[1]
            tempstr=tempstr.split('3011')[0]
            match=re.match(r'(\w+)', tempstr)
            HDrec=HDrec.set_value('Unit',match.group(0))
        except:
            print('Error finding job name for ', filename)
        # Just copy date from filename (easier than
        try:
            test=filename.split('_')[0]
            thisdate=datetime.datetime.strptime(test, "%d%b%y")
            thisdate=datetime.datetime.strftime(thisdate,'%m/%d/%y')
            # tempstring=longstring.split('3011')[1]
            # match=re.search(r'(\d+)/(\d+)/(\d+)',longstring)
            # thisdate=datetime.datetime.strptime(match.group(0), "%m/%d/%y")
            HDrec=HDrec.set_value('Date', thisdate)
        except:
            print('Error finding date for ', filename)
        # find CC if used
        try:
            tempstr=longstring.split('XXXXXXXXXXXX')[1]
            tempstr=tempstr.split(' ')[0]
            match=re.search(r'\d{4}',tempstr)
            HDrec=HDrec.set_value('Acct', int(match.group(0)))
        except:
            print('Error finding credit card # for ', filename)
            HDrec=HDrec.set_value('Acct', 'cash') # presumably cash but could be store credit

        '''the above works in a more foolproof way, but use xpath method to extract 
        clean text for item descriptions
        # now parse items list and add to df
        # pattern finds all 12 digit numbers incl some hyphen patterns
        # sometimes erroneous HD items numbers have hyphens in 5 and 9 ... 0000-123-124
        '''
        # if text, cleanstring already assigned above (special cleaning needed for EML)
        if '.eml' in filename: 
            HDtree=html.fromstring(wholefile)
            HDtree=html.fromstring(longstring)  
            HDtable=HDtree.xpath('//table') # oddly returns list with single HTML element
            HDtable=HDtable[0] # gets table 
            lines=HDtable.xpath('//span/text()') # list of text elements within data table of importance
            newlines=[] # turn into a list of strings
            for i,line in enumerate(lines):
                text=str(line)
                newlines.append(text)
                cleanstring=''.join(newlines) # html- stripped receipt string
                cleanstring=cleanstring.split('SUBTOTAL')[0] # truncate to avoid phantom items
        # TODO solve problem if hmtl cleaner screws up ... 12 digit HD item numbers can disappear
        # work from truncated clean string over receipt data area from now on
        pattern=re.compile(r'(\d{12})|(\d{4}-\d{3}-\d{3})|(\d{4}-\d{3}-\d{3})')
        matches=re.finditer(pattern,cleanstring)
        # matches=re.finditer(r'\d{12}',itemstr) # finds all 12digit HD item codes
        HDbreaks=[]
        HDitemnums=[]
        for m in matches:
            HDbreaks.append(m.start())
            HDitemnums.append(str(m.group(0))) # add item # as string to keep leading zeros
        dim=len(HDbreaks) # breaks between items strings set by finding HD 12 digit number
        # Create df of correct length (one row per item)
        mycols2=['Date','HD#','Cat','Item','Quantity','Unit cost','Subtotal','Tax','Item total']
        HDitemrow=pd.DataFrame(index=np.arange(0,dim), columns=mycols2)
        HDbreaks.append(len(cleanstring))
        # get single items as list of strings
    
        # Structure of HD item listings within receipt
        # structure is 12digit HD code - item_class - <A> - $1.00 - item_description or
        # 12digit HD code - item_class - <A> item_description - 2@2.50  5.00 
          
        # item category between HD# and <A>
        HDitems=[] # HDitems list must match HDbreaks
        for i in range(0,len(HDbreaks)-1):
            HDitems.append(cleanstring[HDbreaks[i]:HDbreaks[i+1]])
        # find item categories (after number before &lt;A&gt )
        HDcats=[]
        for i in range(0,len(HDbreaks)-1):
            match=re.search(pattern,HDitems[i])
            tempstr=HDitems[i][match.end():].lstrip()
            tempstr=tempstr.split('<A>')[0]
            HDcats.append(tempstr)
        HDdescr=[] # item description
        HDunitcost=[]
        HDprices=[] # list of single price or list of two
        HDquant=[] # item quantity

        for i in range(0,dim): # finding description, quantity for each item, unit price and total prices
            try:
                pricelist=re.findall(r'(\d+\.\d{2})', HDitems[i])
                if len(pricelist)==1: # single item
                    # description after price
                    match=re.search(r'(\d+\.\d{2})', HDitems[i])
                    tempstr=HDitems[i][match.end():].strip()
                    HDdescr.append(tempstr)            
                    HDquant.append(1) # single item
                    HDunitcost.append(pricelist[0])# unit price
                    HDprices.append(pricelist[0]) # subtotal price
                elif len(pricelist)==2:
                    # find last number which is quantity
                    tempstr=HDitems[i].split('<A>')[1]
                    tempstr=tempstr.split('@')[0]
                    templist=re.findall(r'\d+',tempstr)
                    HDquant.append(templist[-1]) # last number is quantity
                    tempstr=tempstr[:len(tempstr)-2].strip()
                    HDdescr.append(tempstr) 
                    HDunitcost.append(pricelist[0])# unit price
                    HDprices.append(pricelist[1]) # subtotal price
                elif len(pricelist)>2:
                    print(len(pricelist), 'prices found ... suspected missed item for ', filename)
                    match=re.search(r'(\d+\.\d{2})', HDitems[i])
                    tempstr=HDitems[i][match.end():].strip()
                    HDdescr.append(tempstr)            
                    HDquant.append(1) # single item
                    HDunitcost.append(pricelist[0])# unit price
                    HDprices.append(pricelist[0]) # subtotal price
            except: # fails for a single item... just add as blanks and zeros and maybe fix manually
                HDdescr.append('')            
                HDquant.append(0) # single item
                HDunitcost.append(0)# unit price
                HDprices.append(0) # subtotal price
                print("Couldn't find description/quantity/prices for item", i, 'of ', filename)
                           
        # now write all lists to the dataframe
        HDrec=HDrec.set_value('Vendor', 'Home Depot')
        HDrec=HDrec.set_value('Receipt', 'Y')
        HDrec=HDrec.set_value('Filename', filename)
        for i in range(0,dim):
            try:
                HDitemrow=HDitemrow.set_value(i,'Date',thisdate) # same date as determined above
            except:
                pass
            HDitemrow=HDitemrow.set_value(i,'HD#',HDitemnums[i])
            HDitemrow=HDitemrow.set_value(i,'Cat',HDcats[i])
            try:
                HDitemrow=HDitemrow.set_value(i,'Item',HDdescr[i])
            except:
                print('Problem with description for item in', filename)
            try:
                HDitemrow=HDitemrow.set_value(i,'Quantity',HDquant[i])
            except:
                print('Problem with quantity for item in', filename)
            try:
                HDitemrow=HDitemrow.set_value(i,'Unit cost',HDunitcost[i])
            except:
                print('Problem with unit cost for item in', filename)
            try:
                HDitemrow=HDitemrow.set_value(i,'Subtotal', HDprices[i])
            except:
                print('Problem with subtotal for item in', filename)
            try:
                tax=float(HDprices[i])*taxrate
                ittotal=tax+float(HDprices[i])
                HDitemrow=HDitemrow.set_value(i,'Tax', round(tax,2))
                HDitemrow=HDitemrow.set_value(i,'Item total', round(ittotal,2))
            except:
                print('Problem with tax calcs for item in', filename)
        HDitemrow=HDitemrow.sort_values(['Item total'], ascending=False) #     
        # at end of loop, concat new entries with main log
        
        HDitemlog=pd.concat([HDitemlog, HDitemrow], ignore_index=True)
        HDitemlog=HDitemlog[mycols2] # back in original order 
        HDreceiptlog=HDreceiptlog.append(HDrec, ignore_index=True)        
        HDreceiptlog=HDreceiptlog[mycols] # back in original order 
        # END OF FILE LOOP  (row dfs recreated but log )
    return HDreceiptlog, HDitemlog # return with new entries

def writetoxls(df, sheetname, xlsfile):
    ''' Generic write of given df to specified tab of given xls file '''
    book=load_workbook(xlsfile)
    writer=pd.ExcelWriter(xlsfile, engine='openpyxl', datetime_format='mm/dd/yyyy')
    writer.book=book
    writer.sheets = dict((ws.title, ws) for ws in book.worksheets)
    df.to_excel(writer,sheet_name=sheetname,index=False) # this overwrites existing file
    writer.save() # saves xls file with all modified data
    return

#%%
'''
        # now find <A or A> between item class
        pattern=re.compile(r'(<A)| (A>)')
        pos2=re.search(pattern,thisitem)
        itemclass=thisitem[match.end():pos2.start()]
        
        # find dollar amounts (very likely only one or two instances) 
        match=re.findall(r'(\d+\.\d+)', thisitem)
        if '@' not in thisitem and len(match)==1: # single item
            HDitems=HDitems.set_value(i,'Quantity',1)
            HDitems=HDitems.set_value(i,'Unit cost',float(match[0]))
            HDitems=HDitems.set_value(i,'Subtotal',float(match[0]))
        elif len(match)==2: # multiple items ( quantity@unitprice then subtotal )
            HDitems=HDitems.set_value(i,'Unit cost',float(match[0]))
            HDitems=HDitems.set_value(i,'Subtotal',float(match[1]))
            # Need to find quantity just left of match[0]
            match=re.finditer(r'@',thisitem)
            poslist=[]
            for m in match:
                poslist.append(m.start())
            
            match.start()
            for m in match:
                tempstring=thisitem[m.start()-3:m.start()]

    
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
    HDitemLog.loc[i]=pd.Series(HDitem) # convert dict to series and add as next line to dataframe
'''    
    
'''    #%%  Append all to common receipts output file... maybe easier with CSV?
C:\Users\tkc\Documents\Fin\taxes\Receipts\HD_receipts_log.xlsx
'''