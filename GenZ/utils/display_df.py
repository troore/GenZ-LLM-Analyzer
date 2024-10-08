import pandas as pd
import numpy as np

def color_bound_type(value):
    if value == 'M':
        color = 'red'
    elif value == 'C':
        color = 'green'
    else:
        return
    return 'color: %s' % color

def highlight_max_cycles(s):
    '''
    highlight the maximum in a Series green.
    '''
    is_max = s == s.max()
    return ['background-color: green' if v else '' for v in is_max]

def display_df(df):
    ## Adding % of total time for each operation
    total_cycles = np.sum(df['Cycles'])
    for i in range(len(df)):
        df.loc[i, '% of total time'] = 100*df.loc[i,'Cycles']/total_cycles

    ## reducing display precision
    pd.set_option("display.precision", 2)

    ## Reordering columns
    first_cols = ['Op Type','Dimension','Op Intensity','Num ops (MFLOP)','Input_a (MB)','Input_w (MB)','Output (MB)','Total Data (MB)',f'Compute time ({unit.unit_time})',f'Memory time ({unit.unit_time})','Bound','C/M ratio','Cycles', '% of total time','Throughput (Tflops)',f'Compute cycle',f'Memory cycle']
    last_cols = [col for col in df.columns if col not in first_cols]
    df = df.loc[:,first_cols+last_cols]

    ## Applying colors and gradients to colmns
    df = df.style.background_gradient(cmap='Blues',axis=0,subset=["Cycles","Total Data (MB)"])\
        .background_gradient(cmap='Spectral_r',axis=1,subset=['Input_a (MB)','Input_w (MB)','Output (MB)'])\
        .background_gradient(cmap='Oranges',axis=0,subset=["Op Intensity"])\
        .map(color_bound_type, subset=['Bound'])\
        .apply(highlight_max_cycles,axis=1,subset=pd.IndexSlice[:, [f'Compute time ({unit.unit_time})',f'Memory time ({unit.unit_time})']])
    

    pd.set_option('display.float_format', '{:.5f}'.format) 
    display(df)
    return df