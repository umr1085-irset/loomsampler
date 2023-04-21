#---------------------------------------------------------------------
# Loom sampling script
# Performance issues from Loompy / HDF5
# See https://linnarssonlab.org/loompy/apiwalkthrough/index.html#shape-indexing-and-slicing
#---------------------------------------------------------------------
import argparse

def is_valid_attrs_list(loom_path,attrs):
    '''
    Return a list of valid column attributes for given loom file
    '''
    df = loompy.connect(loom_path,'r') # open connection
    valid = df.ca.keys() # get column attributes
    df.close() # close connection
    res = [] # empty list to return
    for x in attrs: # for each attribute
        if x in valid: # check if valid
            res.append(x) # append
        else:
            print(f'{x} not present in metadata. Will not be used') # warn user
    return res # return valid list

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Sample your loom files!')
    parser.add_argument('-f','--input', help='Input loom file', required=True)
    parser.add_argument('-o','--output', help='Output loom file. Optional, default will use input file and change the .loom extension to .light.loom', required=False)
    parser.add_argument('-s','--sample', help='Number of items to sample. Optional, default is 20000', required=False)
    parser.add_argument('-t','--threshold', help='Threshold value for sampling. Optional, default is 25000', required=False)
    parser.add_argument('-m','--minimum', help='Minimum number of items per combination. Optional, default is 10', required=False)
    parser.add_argument('-v','--vars', help='Variables to preserve representativity. Must be separated by | and. If not specifed, items will be randomly sampled', required=False)

    args = vars(parser.parse_args())
    print(args)
    
    # imports
    import numpy as np
    import loompy

    NUM_SAMPLING = 20000 # target number of items to sample
    NUM_THRESHOLD = 25000 # threshold to launch sampling
    BARE_MINIMUM = 10 # minimum number of items per combination. If below, all items are kept
    VARS = [] # list of column attributes to combine for representativity
    
    # check input file
    if args['input'].lower().endswith('.loom'):
        INPUT_FILE = args['input']        
    else:
        raise Exception('Input file is not a loom file')
    
    # check output file. If none, will use input file and change the .loom extension to .light.loom
    if args['output'] is None:
        OUTPUT_FILE = INPUT_FILE.replace('.loom', '.light.loom')
    else:
        if args['output'].lower().endswith('.loom'):
            OUTPUT_FILE = args['output']        
        else:
            raise Exception('Output file is not a loom file')
            
    # check sampling value
    if args['sample'] is not None:
        try:
            NUM_SAMPLING = int(args['sample'])
        except:
            raise Exception('Sampling value must be an integer')
    
    # check threshold value
    if args['threshold'] is not None:
        try:
            NUM_THRESHOLD = int(args['threshold'])
        except:
            raise Exception('Threshold value must be an integer')
    
    # check minimum value
    if args['minimum'] is not None:
        try:
            BARE_MINIMUM = int(args['minimum'])
        except:
            raise Exception('Minimum value must be an integer')
            
    # check cluster variable
    if args['vars'] is not None:
        VARS = is_valid_attrs_list(INPUT_FILE, args['vars'].split('|'))

    # check sampling and threshold values
    if NUM_SAMPLING>NUM_THRESHOLD:
        raise Exception('Threshold value must be greater than sampling value')
    
    #-------------#
    # Main script #
    #-------------#
    
    df = loompy.connect(INPUT_FILE) # open loompy connection
    num_items_loom = df.shape[1] # get number of items in loom file

    # check if loom needs to be sampled
    if num_items_loom<=NUM_THRESHOLD:
        exit()    
    else:
        perc_to_sample = NUM_SAMPLING/num_items_loom
        
    # compute combinations & indices
    if VARS==[]:
        print('List of variables to use is empty. Sampling will be 100% random')
        idx = np.sort(np.random.choice(num_items_loom,NUM_SAMPLING,replace=False)) # random indices
    else:
        idx = []
        combinations = np.apply_along_axis(' '.join, 0, [df.ca[x] for x in VARS]) # combine valid attributes
        for combination in np.unique(combinations): # for each combination
            subidx, = np.where(combinations==combination) # get indices of items matching current combination
            num_subidx = len(subidx) # get number of matching items
            if num_subidx <= BARE_MINIMUM: # if number of items is under the bare minimum threshold
                idx.append(subidx) # save indices
            else: # else if number of items is above threshold
                to_sample = int(np.ceil(num_subidx*perc_to_sample)) # compute number of items to sample for combination
                if to_sample <= BARE_MINIMUM: to_sample = 10 # minimum to sample is 10
                idx.append(np.random.choice(subidx, to_sample, replace=False)) # save sampled indices
        idx = np.sort(np.concatenate(idx)) # concatenate and sort indices
    
    # data fetching
    views = [] # empty list to store data from views
    for (ix, selection, view) in df.scan(items=idx, axis=1): # scan file to get views for selected items
        views.append(view[:,:]) # get data from view and append to list
    views = np.concatenate(views,axis=1) # concatenate all data from views

    # metadata and attributes
    ca = {} # empty dictionary for column attributes
    for k in df.ca.keys(): # for each key
        ca[k] = df.ca[k][idx] # sample and assign

    ra = {} # empty dictionary for row attributes
    for k in df.ra.keys(): # for each key
        ra[k] = df.ra[k] # assign

    attrs = {} # empty dictionary for global attributes
    for k in df.attrs.keys(): # for each key
        attrs[k] = df.attrs[k] # assign
    attrs['LOOM_SPEC_VERSION'] = loompy.__version__ # correct loompy version
    
    loompy.create(OUTPUT_FILE, views, row_attrs=ra, col_attrs=ca, file_attrs=attrs) # create new loom file
    
    df.close() # close original file