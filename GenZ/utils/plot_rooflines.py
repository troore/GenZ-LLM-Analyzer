import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from math import log
import copy

# systems = {"Scalar": {"gflops": 98.48, "bandwidth": 81.35},
#            "Vector": {"gflops": 843.06, "bandwidth": 393.75},
#            "Matrix": {"gflops":  1691.96, "bandwidth": 1237.34}
#            }

# benchmarks = {
#   "MyBWHungryBenchmark" : 0.8,
#   "MyCPUIntensiveBenchmark" : 30
# }

# datapoints = [
#   # Hyper-Threading
#   #{"type" : "taylor-green3D", "label" : "Flat Mode", "prop" : ["D3Q27", "AoS", 64,  192,  0], "GFLOPs" : 216.91}, # oppure 250.51
#   #{"type" : "taylor-green3D", "label" : "Flat Mode", "prop" : ["D3Q27", "AoS", 128, 192,  0], "GFLOPs" : 237.53},
#   {"type" : "taylor-green3D", "label" : "Flat Mode", "prop" : ["D3Q27", "AoS", 192, 192,  0], "GFLOPs" : 367.12}
# ]

# basic figure settings
fig = plt.figure(figsize=(10, 5))
ax = plt.subplot(1,1,1)
## Roofline window
xmin, xmax, ymin, ymax = 0.04, 600, 0.4, 2000000

fig_ratio = 2
fig_dimension = 5

xlogsize = float(np.log10(xmax/xmin))
ylogsize = float(np.log10(ymax/ymin))
m = xlogsize/ylogsize

def set_size(w,h, ax=None):
  """ w, h: width, height in inches """
  if not ax: ax=plt.gca()
  l = ax.figure.subplotpars.left
  r = ax.figure.subplotpars.right
  t = ax.figure.subplotpars.top
  b = ax.figure.subplotpars.bottom
  figw = float(w)/(r-l)
  figh = float(h)/(t-b)
  ax.figure.set_size_inches(figw, figh)

def get_max_roof(perf_roofs):
  max_roof = perf_roofs[0]["val"]
  
  for roof in perf_roofs:
    if roof["val"] > max_roof:
       max_roof = roof["val"]

  return max_roof

def plot_slope(perf_roof, mem_bottleneck, slope_name=None):
  y = [0, perf_roof]
  x = [float(yy)/mem_bottleneck for yy in y]
  
  ax.loglog(x, 
            y, 
            linewidth=1.0,
            linestyle='-.',
            marker="2",
            color="grey",
            zorder=10)
  
  # Label
  xpos = xmin*(10**(xlogsize*0.04))
  ypos = xpos*mem_bottleneck
  if ypos<ymin:
    ypos = ymin*(10**(ylogsize*0.02))
    xpos = ypos/mem_bottleneck
  pos = (xpos, ypos)

    # In case of linear plotting you might need something like this: trans_angle = np.arctan(slope["val"]*m)*180/np.pi
    #trans_angle = 45*m
    # print "\t" + str(trans_angle) + "°"
  
  if slope_name is not None:
      ax.annotate(slope_name + ": " + str(mem_bottleneck) + " GB/s",
                  pos,
                  rotation=np.arctan(m/fig_ratio)*180/np.pi,
                  rotation_mode='anchor',
                  fontsize=11,
                  ha="left",
                  va='bottom',
                  color="grey")
    
def plot_roof(perf_roof, mem_bottleneck, roof_name=None):
  if roof_name is not None:
     print("roof\t\"" + roof_name + "\"\t\t" + str(perf_roof) + " GFLOP/s")

  x = [perf_roof/mem_bottleneck, xmax*10]
  ax.loglog(x, 
            [perf_roof for xx in x], 
            linewidth=1.0,
            linestyle='-.',
            marker="2",
            color="grey",
            zorder=10)

  # Label
  if roof_name is not None:
      ax.text(  # roof["val"]/max_slope*10,roof["val"]*1.1,
          xmax/(10**(xlogsize*0.01)), perf_roof*(10**(ylogsize*0.01)),
          roof_name + ": " + str(perf_roof) + " GFLOPs",
          ha="right",
          fontsize=11,
          color="grey")

def plot_log_roofline_background(systems):
    systems_copy = copy.deepcopy(systems)
    for _, config in systems_copy.items():
       config["label"] = 0

    for i, (name, config_i) in enumerate(systems_copy.items()):
      new_name = name
      if config_i["label"] == 0:
          for j, (name_j, config_j) in enumerate(systems_copy.items()):
             if i != j:
                if abs(config_i["bandwidth"] - config_j["bandwidth"]) < 1e-3:
                   config_j["label"] = 1
                   new_name = "{}/{}".format(new_name, name_j)
          plot_slope(config_i["gflops"], config_i["bandwidth"], slope_name=new_name)
      else:
          plot_slope(config_i["gflops"], config_i["bandwidth"], slope_name=None)


    # systems_copy = copy.deepcopy(systems)
    # for _, config in systems_copy.items():
    #    config["label"] = 0

    # for name, config in systems.items(): 
    #   plot_roof(config["gflops"], config["bandwidth"], roof_name=name)

    systems_copy = copy.deepcopy(systems)
    for _, config in systems_copy.items():
       config["label"] = 0

    for i, (name, config_i) in enumerate(systems_copy.items()):
      new_name = name
      if config_i["label"] == 0:
          for j, (name_j, config_j) in enumerate(systems_copy.items()):
             if i != j:
                if abs(config_i["gflops"] - config_j["gflops"]) < 1e-3:
                   config_j["label"] = 1
                   new_name = "{}/{}".format(new_name, name_j)
          plot_roof(config_i["gflops"], config_i["bandwidth"], roof_name=new_name)
      else:
          plot_roof(config_i["gflops"], config_i["bandwidth"], roof_name=None)

def plot_log_roofline_benchmarks(benchmarks):
  for benchmark in benchmarks:
      AI = benchmarks[benchmark]
      # print "benchmark\t\"" + benchmark + "\"\t\t" + str(AI) + " GFLOP/Byte"

      plt.axvline(x=AI, dashes=[10, 10, 3, 10], linewidth=0.4, color="red")

      ax.text(
        AI/1.15, ymin*1.24,
        benchmark,
        fontsize=8,
        rotation=90,
        va="bottom",
        color="red")

def plot_log_roofline_points(datapoints):
    raise NotImplementedError()

# def plot_log_rooflines(perf_roofs, mem_bottlenecks, datapoints):
def plot_log_rooflines(systems, benchmarks, datapoints=None):
    plot_log_roofline_background(systems)
    plot_log_roofline_benchmarks(benchmarks)
    if datapoints is not None:
      plot_log_roofline_points(datapoints)

    ax.grid(color="#dddddd", zorder=-1)
    ax.set_xlabel("Arithmetic Intensity [FLOP/Byte]", fontsize=15)
    ax.set_ylabel("Performance [GFLOP/s]", fontsize=15)

    # Set aspect
    ax.set_xlim(xmin, xmax)
    ax.set_ylim(ymin, ymax)

    ax.set_title("Roofline", fontsize=20)

    plt.tight_layout()
    set_size(fig_dimension*fig_ratio,fig_dimension)

    plt.savefig('roofline.png')


# # test
# plot_log_rooflines(systems=systems, 
#                    benchmarks=benchmarks,
#                    datapoints=datapoints)
