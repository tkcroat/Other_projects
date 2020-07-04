# -*- coding: utf-8 -*-
"""
Created on Mon May 11 22:54:13 2020

@author: Kevin
"""

import os
import pandas as pd

subdirs, total =get_subdirs_size()
test=pd.DataFrame(subdirs)

fig, ax = plt.subplots(figsize=(15, 8))
ax.barh(dff['name'], dff['value'])

#%%
def get_subdirs_size(start_path = '.'):
    ''' From cwd Split into top level subdirs and calculate size of each
    similar to du -d 1 . (first level down summaries)
    args:
        start_path - top level dir for disk space sub-characterization
    returns:
        total_size - val (bytes)
        subdirs_size -dict w/ size split into top leve and subdirs
    '''
    total_size = 0
    # first grab top level domains
    subdirs=[]
    subdirs_size={} # Only top level subdirectories
    subdirs_size['.']=0
    for dirpath, dirnames, filenames in os.walk(start_path):
        if '\\' not in dirpath.replace('.\\',''):
            subdirs.append(dirpath.replace('.\\',''))
            subdirs_size[dirpath.replace('.\\','')]=0
    # first list opt 
    for dirpath, dirnames, filenames in os.walk(start_path):
        try:
            mysubdir=dirpath.split('\\')[1]
        except:
            mysubdir='.' # top level
        for f in filenames:
            fp = os.path.join(dirpath, f)
            # skip if it is symbolic link
            if not os.path.islink(fp):
                # add to total size and to top level subdir size
                subdirs_size[mysubdir]=subdirs_size.get(mysubdir) + os.path.getsize(fp)
                total_size += os.path.getsize(fp)
    return subdirs_size, total_size 
