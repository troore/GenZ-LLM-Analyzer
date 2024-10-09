from .utils import ModdelingOutput, get_inference_system, get_offload_system
from GenZ.unit import Unit
from GenZ.operators import *

from GenZ.operator_base import op_type_dicts
from GenZ.system import System
import pandas as pd
from GenZ.analye_model import *
import warnings
from GenZ.collective_times import *
from GenZ.utils.plot_rooflines import *
from GenZ.utils.display_df import *

unit = Unit()

def get_single_layer_all_reduce_data(system, batch_size, Bb, model_D):
    return 2*batch_size*Bb*model_D*system.get_bit_multiplier(type='M')

def get_single_stage_pipe_data(system, batch_size, Bb, model_D):
    return batch_size*Bb*model_D*system.get_bit_multiplier(type='M')

def get_num_layers_per_pipeline_stage(num_layers, pipeline_parallel):
    return ceil(num_layers / pipeline_parallel)

def decode_model_characterization_calculation(model, 
                                              system, 
                                              input_tokens, 
                                              output_tokens, 
                                              batch_size, 
                                              Bb, 
                                              FLAT, 
                                              num_layers, 
                                              model_D,
                                              tensor_parallel, 
                                              pipeline_parallel
                                              ):
    # if is_moe:
    model_decode = create_inference_moe_decode_model(input_sequence_length=input_tokens,output_gen_tokens = output_tokens , 
                                        name=model,  tensor_parallel=tensor_parallel)

    model_df = get_model_df(model_decode, system, unit, batch_size*Bb, intermediate_on_chip=FLAT , beam_merge= (Bb > 1), beam_size= Bb, model_characterstics = True)
    summary_table = get_summary_table(model_df, system,unit, model_characterstics = True)
    summary_table_cols = [f'MACs ({unit.unit_flop})', f'Total Data ({unit.unit_mem})']
    ## Drop columns not is list
    summary_table = summary_table[summary_table.columns.intersection(summary_table_cols)]

    model_weights = 0
    kv_cache = 0
    unused_weights = 0
    for i in range(len(model_df)):
        if ('Logit'  in model_df.loc[i, 'Op Type']  or 'Attend'  in model_df.loc[i, 'Op Type']):
            kv_cache += model_df.loc[i,'Input_w (MB)'] 
        else:
           if model_df.loc[i, f'Num ops ({unit.unit_flop})'] == 0:
               unused_weights += model_df.loc[i,'Input_w (MB)'] 
           model_weights += model_df.loc[i,'Input_w (MB)'] 
    num_layers_per_pipeline_stage = ceil(num_layers / pipeline_parallel)

    ## TP data volumn
    single_layer_all_reduce_data  = 2* batch_size*Bb*model_D* system.get_bit_multiplier(type='M')
    total_all_reduce_data = single_layer_all_reduce_data * num_layers_per_pipeline_stage

    ## PP volumn
    single_stage_pipe_data =  batch_size*Bb*model_D* system.get_bit_multiplier(type='M')
    total_pipe_data = single_stage_pipe_data * (pipeline_parallel-1)

    model_weights *= num_layers_per_pipeline_stage
    unused_weights *= num_layers_per_pipeline_stage
    kv_cache *= num_layers_per_pipeline_stage

    summary_table[f'MACs ({unit.unit_flop})'] = summary_table[f'MACs ({unit.unit_flop})'].apply(lambda x: x*num_layers_per_pipeline_stage)
    summary_table[f'Total Data ({unit.unit_mem})'] = summary_table[f'Total Data ({unit.unit_mem})'].apply(lambda x: x*num_layers_per_pipeline_stage)
    summary_table[f'Model Weights ({unit.unit_mem})'] = model_weights       ## In MB
    summary_table[f'Unused Weights ({unit.unit_mem})'] = unused_weights       ## In MB
    summary_table[f'KV Cache ({unit.unit_mem})'] = kv_cache                 ## In MB
    summary_table[f'AR data ({unit.unit_mem})'] = unit.raw_to_unit( total_all_reduce_data, 'M')      ## In MB
    summary_table[f'Pipe data  ({unit.unit_mem})'] = unit.raw_to_unit( total_pipe_data, 'M')         ## In MB

    return summary_table


def decode_moddeling(model = 'BERT', 
                     batch_size = 1, 
                     reset_batch_size = False, 
                     input_tokens = 4096,
                     output_tokens = 0, 
                     FLAT = True,  
                     Bb = 4 ,           ## Only for Decode
                     system_name = 'A100_40GB_GPU', 
                     system_eff = 1, 
                     bits='bf16', 
                     debug= False, 
                     model_profilling = False,  
                     tensor_parallel = 1, 
                     pipeline_parallel = 1, 
                     time_breakdown = False, 
                     return_model_df=False,
                     model_offload = False, 
                     ceff = None, 
                     meff = None):
    
    ################################################################################################## # 
    ### Model parsing
    ################################################################################################## # 

    model_config = get_configs(model, get_model_config=True)
    
    model_D = model_config.hidden_size
    F = model_config.intermediate_size 
    fi = model_config.num_ffi
    H = model_config.num_attention_heads
    Hkv = model_config.num_key_value_heads
    num_layers = model_config.num_decoder_layers
    is_moe = model_config.moe_layer_freq

    ################################################################################################## # 
    ### System Declaration
    ################################################################################################## # 
    system = get_inference_system(system_name=system_name, 
                                  bits=bits, 
                                  ceff=system_eff , 
                                  meff=system_eff)
    
    ################################################################################################## # 
    ### Model Characterization Calculation
    ################################################################################################## # 
    summary_table = decode_model_characterization_calculation(model=model,
                                                              system=system,
                                                              input_tokens=input_tokens,
                                                              output_tokens=output_tokens,
                                                              batch_size=batch_size,
                                                              Bb=Bb,
                                                              FLAT=FLAT,
                                                              num_layers=num_layers,
                                                              model_D=model_D,
                                                              tensor_parallel=tensor_parallel,
                                                              pipeline_parallel=pipeline_parallel)
    

    model_weights = summary_table[f'Model Weights ({unit.unit_mem})'].values[0]
    kv_cache = summary_table[f'KV Cache ({unit.unit_mem})'].values[0]
    total_memory_req = model_weights + kv_cache

    if reset_batch_size:
        per_chip_memory = system.get_off_chip_mem_size()   ## MB
        if per_chip_memory > model_weights:
            full_load_kv_cache = per_chip_memory - model_weights
            batch_size = int(full_load_kv_cache / (kv_cache / batch_size))

            summary_table = decode_model_characterization_calculation(model=model,
                                                                      system=system,
                                                                      input_tokens=input_tokens,
                                                                      output_tokens=output_tokens,
                                                                      batch_size=batch_size,
                                                                      Bb=Bb,
                                                                      FLAT=FLAT,
                                                                      num_layers=num_layers,
                                                                      model_D=model_D,
                                                                      tensor_parallel=tensor_parallel,
                                                                      pipeline_parallel=pipeline_parallel)
        
            model_weights = summary_table[f'Model Weights ({unit.unit_mem})'].values[0]
            kv_cache = summary_table[f'KV Cache ({unit.unit_mem})'].values[0]
            total_memory_req = model_weights + kv_cache
            
        print("Reset batch: {}".format(batch_size))

    Num_cores = pipeline_parallel * tensor_parallel

    ################################################################################# # 
    ### Offloading calculations
    ################################################################################# # 
    is_offloaded = False
    per_chip_memory = system.get_off_chip_mem_size()   ## MB
    if  per_chip_memory < total_memory_req:
        if model_offload:
            system = get_offload_system(system=system, total_memory_req = total_memory_req , debug=debug)
            warnings.warn(f"Some Parameter offloaded, effective Memory BW:{unit.raw_to_unit(system.offchip_mem_bw, type='BW')} ")
            is_offloaded = True
        elif model_profilling:
            warnings.warn(f"All params would not fit on chip. System Memory Cap:{per_chip_memory/1024} GB , Weights : {model_weights/1024} GB, KV Cache:{kv_cache/1024} ")
        else: 
            raise ValueError(f"All params would not fit on chip. System Memory Cap:{per_chip_memory/1024} GB , Weights : {model_weights/1024} GB, KV Cache:{kv_cache/1024}. \n System:{system_name}")

    ## for tensor shareding per layer.
    assert pipeline_parallel >= 1, "Pipeline parallel must be >= 1"
    assert tensor_parallel >= 1, f"Tensor parallel must be >= 1, {tensor_parallel}"

    if num_layers % pipeline_parallel != 0:
        raise ValueError(f"Number of layers:{num_layers} should be divisible by PP:{pipeline_parallel}")
    if model_profilling:
        return model_df, summary_table
    

    ################################################################################################## # 
    ### First token generation time
    ################################################################################################## # 
    model_decode = create_inference_moe_decode_model(input_sequence_length=input_tokens,output_gen_tokens = 1 , 
                                        name=model, Hkv=Hkv, tensor_parallel=tensor_parallel, beam_merge= (Bb > 1), beam_size = Bb)
    model_df = get_model_df(model_decode, system, unit, batch_size*Bb, intermediate_on_chip=FLAT, beam_merge= (Bb > 1), beam_size= Bb )
    summary_table = get_summary_table(model_df,system,unit)

    num_first_token_ops = model_df["Num ops ({})".format(unit.unit_flop)].sum()
    num_first_token_data = model_df["Total Data (MB)".format(unit.unit_flop)].sum()

    if debug:
        # display_df(model_df)
        display(summary_table)
        # dot_log_roofline(model_df, system, unit)
    decode_latency_first_token = summary_table['Latency (msec)'].values[0]   # Latency in msec


    ################################################################################################## # 
    ### Last token generation time
    ################################################################################################## # 
    model_decode = create_inference_moe_decode_model(input_sequence_length=input_tokens,output_gen_tokens = output_tokens , 
                                        name=model, Hkv=Hkv, tensor_parallel=tensor_parallel, beam_merge= (Bb > 1), beam_size = Bb)

    model_df = get_model_df(model_decode, system, unit, batch_size*Bb,  intermediate_on_chip=FLAT , beam_merge= (Bb > 1), beam_size= Bb)
    summary_table = get_summary_table(model_df,system,unit)

    # print(model_df)
    # print(model_df.loc[0].at["Num ops ({})".format(unit.unit_flop)])
    num_last_token_ops = model_df["Num ops ({})".format(unit.unit_flop)].sum()
    num_last_token_data = model_df["Total Data (MB)".format(unit.unit_flop)].sum()

    total_op_intensity = (num_first_token_ops + num_last_token_ops) / (num_first_token_data + num_last_token_data)
    # print(total_op_intensity)

    if return_model_df:
        return model_df, summary_table
    if debug:
        display_df(model_df)
        display(summary_table)
        # dot_log_roofline(model_df, system, unit)
    decode_latency_last_token = summary_table['Latency (msec)'].values[0]      # Latency in msec 

    ################################################################################################## # 
    ### Communication time
    ################################################################################################## # 
    ## TP time
    if tensor_parallel > 1:
        all_reduce_delay  = 2*get_AR_time(data = get_single_layer_all_reduce_data(system, batch_size, Bb, model_D)/2, 
                                          num_AR_nodes=tensor_parallel, 
                                          system=system)
    else:
        all_reduce_delay = 0

    ## PP time
    single_stage_pipe_delay = get_message_pass_time(data = get_single_stage_pipe_data(system, batch_size, Bb, model_D), system=system )

    ## Total Comm time
    total_communication_delay = single_stage_pipe_delay * (pipeline_parallel-1) + all_reduce_delay * num_layers


    ################################################################################################## # 
    ### Final Latency and Thrpt Calculation
    ################################################################################################## # 
    
    ## Single layer will have compute/memory time + 2 AR delay
    single_layer_time = (decode_latency_first_token+decode_latency_last_token)/2  + all_reduce_delay 
    single_pipe_stage = single_layer_time * get_num_layers_per_pipeline_stage(num_layers, pipeline_parallel)

    decode_latency =  single_pipe_stage * pipeline_parallel + single_stage_pipe_delay * (pipeline_parallel-1)
    
    if debug:
            print(f'Decode Latency:{decode_latency} {unit.unit_time}')
            print(f'single_pipe_stage:{single_pipe_stage} {unit.unit_time}; single_layer_time:{single_layer_time} {unit.unit_time}')
            print(f'Layers per pipeline stage:{(get_num_layers_per_pipeline_stage(num_layers, pipeline_parallel))}')

    thrpt = 1000 * batch_size / decode_latency        ## this is for TP
    ## 1000x because the latency is in milli seconds. thrpt is in Token/s
    if pipeline_parallel > 1:
        token_generation_interval = single_pipe_stage + single_stage_pipe_delay
        thrpt = 1000 * batch_size / token_generation_interval 

    attn_time, linear_time = 0,0
    for i in range(len(model_df)):
        if ('Logit' in model_df.loc[i, 'Op Type'] or 'Attend' in model_df.loc[i, 'Op Type']):
            attn_time +=  model_df.loc[i,'Latency (msec)']
            # print(i, model_df.loc[i, 'Op Type'])
        else:
            linear_time +=  model_df.loc[i,'Latency (msec)']
               
    linear_time *= num_layers     ## In milliseconds
    attn_time *= num_layers       ## In milliseconds
    total_time = linear_time + attn_time + total_communication_delay
    runtime_breakdown = [linear_time, attn_time, total_communication_delay]

    ################################################################################################## # 
    ### Output Generation
    ################################################################################################## # 
    ## Check for error in total time.
    Error_rate = 100*(total_time-decode_latency)/decode_latency
    if Error_rate > 50:
        warnings.warn(f"Error in latency calc. Avg Decode Latency:{decode_latency} msec , Latency based on last token : {total_time} msec, \n Attn time:{attn_time}; Linear time:{linear_time}; AR time:{all_reduce_delay * (get_num_layers_per_pipeline_stage(num_layers, pipeline_parallel))}; Pipeline Comm time:{single_stage_pipe_delay * (pipeline_parallel-1)}")

 
    if debug:
        print(f'Error = {Error_rate} in latency calc. Avg Decode Latency:{decode_latency} msec , Latency based on last token : {total_time} msec')
        print(f'Attn time:{attn_time}; Linear time:{linear_time}; AR time:{all_reduce_delay * (get_num_layers_per_pipeline_stage(num_layers, pipeline_parallel))}; Pipeline Comm time:{single_stage_pipe_delay * (pipeline_parallel-1)}')
    
    return ModdelingOutput(
                        Latency=decode_latency,
                        Throughput=thrpt,
                        AI_total=total_op_intensity,
                        Batch=batch_size,
                        Runtime_breakdown=runtime_breakdown,
                        is_offload=is_offloaded,
                )
