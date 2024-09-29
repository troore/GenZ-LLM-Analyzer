import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from math import log
from GenZ.unit import Unit

unit = Unit()

def plot_roofline_background(system, max_x, unit):
    op_intensity = system.flops/system.offchip_mem_bw
    flops = unit.raw_to_unit(system.flops, type='C')
    max_x = max(max_x, op_intensity*2.5)
    turning_points = [[0, 0], [op_intensity, flops], [max_x, flops]]
    turning_points = np.array(turning_points)
    print(turning_points)
    print(turning_points[:,0])
    print(turning_points[:,1])
    plt.plot(turning_points[:,0], turning_points[:,1], c='grey')

    op_intensity = system.flops/system.onchip_mem_bw
    flops = unit.raw_to_unit(system.flops, type='C')
    turning_points = [[0, 0], [op_intensity, flops], [max_x, flops]]
    turning_points = np.array(turning_points)
    plt.plot(turning_points[:,0], turning_points[:,1], '--', c='grey')

    plt.xlabel('Op Intensity (FLOPs/Byte)')
    plt.ylabel(f'{unit.unit_compute.upper()}')

def plot_log_roofline_background(system, max_x, unit):
    op_intensity = system.flops/system.offchip_mem_bw
    flops = unit.raw_to_unit(system.flops, type='C')
    max_x = max(max_x, op_intensity*2.5)
    offchip_mem_bw = unit.raw_to_unit(system.offchip_mem_bw, type='BW') / 1024.0  # change to 'T' to be consistent with flops
    print("TFLOPS: {}".format(flops))
    print("MEM BW: {}".format(offchip_mem_bw))
    # turning_points = [[0, 0], [op_intensity, flops], [max_x, flops]]
    turning_points = [[0, log(offchip_mem_bw, 10)], 
                      [log(op_intensity, 10), log(flops ,10)], 
                      [log(max_x, 10), log(flops, 10)]]
    turning_points = np.array(turning_points)
    print(turning_points)
    print(turning_points[:,0])
    print(turning_points[:,1])
    plt.plot(turning_points[:,0], turning_points[:,1], c='grey')

    plt.xlabel('Op Intensity (FLOPs/Byte)')
    plt.ylabel(f'{unit.unit_compute.upper()}')


def dot_roofline(df, system, unit):
    max_x = max(df['Op Intensity'])
    plot_roofline_background(system, max_x, unit)
    print("Number of points: {}".format(len(df)))
    for i in range(len(df)):
        op_intensity = df.loc[i, 'Op Intensity']
        thrpt = df.loc[i, 'Throughput (Tflops)']
        plt.scatter(op_intensity, thrpt)

    plt.savefig('roofline.png')

def dot_log_roofline(df, system, unit):
    max_x = max(df['Op Intensity'])
    plot_log_roofline_background(system, max_x, unit)
    print("Number of points: {}".format(len(df)))
    for i in range(len(df)):
        op_intensity = df.loc[i, 'Op Intensity']
        thrpt = df.loc[i, 'Throughput (Tflops)']
        print(op_intensity)
        print(thrpt)
        plt.scatter(log(op_intensity, 10), log(thrpt, 10))

    plt.savefig('roofline.png')

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