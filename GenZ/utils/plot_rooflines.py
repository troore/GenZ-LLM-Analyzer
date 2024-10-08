import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from math import log

perf_roofs = [
  {"name" : "Scalar Add Peak",    "val" : 98.48},
  {"name" : "DP Vector Add Peak", "val" : 843.06},
  {"name" : "DP Vector FMA Peak", "val" : 1691.96}
]
mem_bottlenecks = [
  {"name" : "L1 Bandwidth",     "val" : 7398.95},
  {"name" : "L2 Bandwidth",     "val" : 1237.34},
  {"name" : "MCDRAM Bandwidth", "val" : 393.75},
  {"name" : "DDR Bandwidth",    "val" : 81.35}
]

datapoints = [
  # Hyper-Threading
  #{"type" : "taylor-green3D", "label" : "Flat Mode", "prop" : ["D3Q27", "AoS", 64,  192,  0], "GFLOPs" : 216.91}, # oppure 250.51
  #{"type" : "taylor-green3D", "label" : "Flat Mode", "prop" : ["D3Q27", "AoS", 128, 192,  0], "GFLOPs" : 237.53},
  {"type" : "taylor-green3D", "label" : "Flat Mode", "prop" : ["D3Q27", "AoS", 192, 192,  0], "GFLOPs" : 367.12}
]


fig = plt.figure(figsize=(10, 40));
ax = plt.subplot(1,1,1)

# Roofline window: Rect (x0, x1, y0, y1)
window_rect = [0.6, 60, 40, 4000]

def plot_log_roofline_background(perf_roofs, mem_bottlenecks):
    raise NotImplementedError()

def plot_log_roofline_points(points):
    raise NotImplementedError()

def plot_log_rooflines(perf_roofs, mem_bottlenecks, points):
    plot_log_roofline_background(perf_roofs, mem_bottlenecks)
    plot_log_roofline_points(points=points)

    plt.savefig('roofline.png')


# test
plot_log_rooflines(perf_roofs=perf_roofs, 
                   mem_bottlenecks=mem_bottlenecks)
