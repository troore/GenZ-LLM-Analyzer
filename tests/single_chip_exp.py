from GenZ import decode_moddeling, prefill_moddeling
from GenZ.analye_model import *
from GenZ.utils.plot_bars import *

import itertools

# system
system_list = ['H100_GPU', 'SPR_CPU', 'SPR_HBM3e', 'SPR_3D']
# system_list = ['H100_GPU', 'SPR_HBM3e']
# model
model_list = ['llama_7b', 'llama_13b', 'llama_33b']
# model_list = ['llama_7b']

# configs
batch_size_list = [96, 64, 8]  # saturate memory
input_tokens = 128
output_tokens = 1024

tpot_results = [[None] * len(model_list) for _ in range(len(system_list))]

def ttft():
    raise NotImplementedError()

def tpot():
    i = 0
    for model, system in itertools.product(model_list, system_list):
        print("{}, {}".format(model, system))
        row, col = divmod(i, len(system_list))
        result = decode_moddeling(model=model,
                                  batch_size=batch_size_list[row],
                                  Bb=1,
                                  input_tokens=input_tokens,
                                  output_tokens=output_tokens,
                                  model_profilling=False,
                                  system_name=system,
                                  bits='bf16',
                                  tensor_parallel=1,
                                  pipeline_parallel=1, 
                                  debug=False, 
                                  time_breakdown=True)
        
        print(result['Latency'])
        tpot_results[col][row] = result['Latency']

        i = i + 1

    print(tpot_results)
    plot_grouped_bars("Decode - Time Per Output Token (TPOT)",
                      "Model",
                      "Latency (ms)", 
                      model_list, 
                      system_list, 
                      tpot_results, 
                      "tpot")

if __name__ == "__main__":
    tpot()