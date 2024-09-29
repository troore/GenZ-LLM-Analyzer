from GenZ import decode_moddeling, prefill_moddeling
from GenZ.analye_model import *
from GenZ.utils.plot_bars import *

import itertools
import copy

# system
system_list = ['H100_GPU', 'SPR_HBM3e', 'SPR_3D']
# system_list = ['SPR_HBM3e']

# model
model_list = ['llama_7b', 'llama_13b', 'llama_33b']
# model_list = ['llama_33b']

# configs
batch_size = 32
input_tokens = 128
output_tokens = 1024

tpot_latency = [[None] * len(model_list) for _ in range(len(system_list))]
tpot_thrpt = copy.deepcopy(tpot_latency)

def ttft():
    raise NotImplementedError()

def tpot(offload=False):
    i = 0
    for model, system in itertools.product(model_list, system_list):
        print("{}, {}".format(model, system))
        row, col = divmod(i, len(system_list))
        try:
            result = decode_moddeling(model=model,
                                      batch_size=(batch_size if offload else 1),
                                      reset_batch_size=(False if offload else True),
                                      Bb=1,
                                      input_tokens=input_tokens,
                                      output_tokens=output_tokens,
                                      model_profilling=False,
                                      system_name=system,
                                      bits='bf16',
                                      tensor_parallel=1,
                                      pipeline_parallel=1,
                                      model_offload=offload,
                                      debug=False,
                                      time_breakdown=True)
        
            print(result['Latency'])
            print(result['Throughput'])
            tpot_latency[col][row] = result['Latency']
            tpot_thrpt[col][row] = result['Throughput']
        except ValueError as ve:
            tpot_latency[col][row] = 0.0
            tpot_thrpt[col][row] = 0.0

        i=i+1

    plot_grouped_bars(title="Decode{} - Time Per Output Token (TPOT)".format("/Offload" if offload else ""),
                      xlabel="Model",
                      ylabel="Latency (ms)", 
                      categories=model_list, 
                      labels=system_list, 
                      value_groups=tpot_latency, 
                      figure_name="tpot_latency{}".format("_offload" if offload else ""))
    
    plot_grouped_bars(title="Decode{} - Throughput Per Batch".format("/Offload" if offload else ""),
                      xlabel="Model",
                      ylabel="Output Tokens/s", 
                      categories=model_list, 
                      labels=system_list, 
                      value_groups=tpot_thrpt, 
                      figure_name="tpot_thrpt{}".format("_offload" if offload else ""))

if __name__ == "__main__":
    tpot(offload=True)