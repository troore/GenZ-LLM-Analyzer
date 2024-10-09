from GenZ import decode_moddeling, prefill_moddeling
from GenZ.analye_model import *
from GenZ.utils.plot_bars import *
from GenZ.utils.plot_rooflines import plot_log_rooflines
from GenZ.LLM_inference import get_inference_system

import itertools
import copy

unit = Unit()

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
    benchmarks = {}
    systems = {}

    i = 0
    for model_name, system_name in itertools.product(model_list, system_list):
        print("{}, {}".format(model_name, system_name))

        system = get_inference_system(system_name=system_name,
                                      bits='bf16')
        if system_name not in systems:
            systems[system_name] = {"gflops": unit.raw_to_unit(system.flops, 'C')*1e3, 
                                    "bandwidth": unit.raw_to_unit(system.offchip_mem_bw, 'BW')}
            
        row, col = divmod(i, len(system_list))
        try:
            result = decode_moddeling(model=model_name,
                                      batch_size=(batch_size if offload else 1),
                                      reset_batch_size=(False if offload else True),
                                      Bb=1,
                                      input_tokens=input_tokens,
                                      output_tokens=output_tokens,
                                      model_profilling=False,
                                      system_name=system_name,
                                      bits='bf16',
                                      tensor_parallel=1,
                                      pipeline_parallel=1,
                                      model_offload=offload,
                                      debug=False,
                                      time_breakdown=True)
        
            tpot_latency[col][row] = result['Latency']
            tpot_thrpt[col][row] = result['Throughput']
            benchmarks["{}_{}".format(model_name, result['Batch'])] = result['AI_total']
        except ValueError as ve:
            tpot_latency[col][row] = 0.0
            tpot_thrpt[col][row] = 0.0

        i=i+1

    print(tpot_latency)

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
    
    # plot_log_rooflines(systems, benchmarks)

if __name__ == "__main__":
    tpot(offload=False)