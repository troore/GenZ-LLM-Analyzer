# Import necessary libraries
import streamlit as st
import streamlit.components.v1 as components
import numpy as np
import plotly.graph_objects as go
import plotly.express as px
import warnings
from GenZ import decode_moddeling, prefill_moddeling, get_configs
import pandas as pd
from tqdm import tqdm

from Systems.system_configs import system_configs

st.set_page_config(
    page_title="System Comparisons",
    page_icon="🔬",

    layout="wide",
    initial_sidebar_state="expanded",
    menu_items={
        'Get Help': 'https://github.com/abhibambhaniya/GenZ-LLM-Analyzer/issues',
        'Report a bug': "https://github.com/abhibambhaniya/GenZ-LLM-Analyzer/issues",
        'About': "https://github.com/abhibambhaniya/GenZ-LLM-Analyzer/blob/main/README.md"
    }
)

st.sidebar.title("System comparisons")
st.sidebar.subheader("1. Select the LLM Model")
st.sidebar.subheader("2. Select the use-case")
st.sidebar.subheader("3. Make a list of various HW Systems to compare")

st.sidebar.info(
    "This app is maintained by Abhimanyu Bambhaniya. ")

st.title("Compare various System Performance")
# Define the function to generate the demand curve
def generate_system_comparision(graph_type, system_list,
                        model, quantization, batch_size,
                        input_tokens, output_tokens, beam_size,
                        ):
    warnings.filterwarnings("ignore")

    data = []
    mem_size_data = []
    for system in system_list:
        try:
            prefill_outputs = prefill_moddeling(model = model, batch_size = batch_size,
                                    input_tokens = input_tokens, output_tokens = output_tokens, FLAT = True,
                                    system_name = system, system_eff = system['eff'],
                                    bits=quantization,
                                    tensor_parallel = system['nodes'], debug=False)
            decode_outputs = decode_moddeling(model = model, batch_size = batch_size, Bb = beam_size ,
                                    input_tokens = input_tokens, output_tokens = output_tokens, FLAT = True,
                                    system_name = system, system_eff=system['eff'],
                                    bits=quantization,
                                    tensor_parallel = system['nodes'], debug=False)
            data.append([system['name'],  prefill_outputs['Latency'],  decode_outputs['Latency'], prefill_outputs['Latency'] + decode_outputs['Latency']*output_tokens, decode_outputs['Throughput']] + prefill_outputs['Runtime_breakdown'] + decode_outputs['Runtime_breakdown'])
        except:
            # ValueError
            decode_outputs, decode_summary_table = decode_moddeling(model = model, batch_size = batch_size, Bb = beam_size ,
                            input_tokens = input_tokens, output_tokens = output_tokens, FLAT = True,
                            system_name = system, system_eff=system['eff'],
                            bits=quantization,
                            tensor_parallel = system['nodes'], debug=False, model_profilling=True)
            total_memory = int(system.get('Memory_size'))*1024  ## per device memory
            memory_req =  decode_summary_table['Model Weights (MB)'].values[0] + decode_summary_table['KV Cache (MB)'].values[0]

            mem_size_data.append([system['name'], total_memory, batch_size, beam_size, input_tokens, output_tokens, np.ceil(memory_req/total_memory)])

    data_df = pd.DataFrame(data, columns = ['System', 'TTFT(ms)', 'TPOT(ms)', 'E2E Latency(ms)','Decode Tokens/s', 'Prefill GEMM Time', 'Prefill Attn Time', 'Prefill Communication Time', 'Decode GEMM Time', 'Decode Attn Time', 'Decode Communication Time'])
    chip_req_df = pd.DataFrame(mem_size_data, columns = ['System', 'Current Memory','Batch', 'Beam size', 'Input Tokens', 'Output Tokens', 'Min. Chips Required'])
    # 1. TTFT vs Decode Throughput
    # 2. TTFT
    # 3. Decode Throughput
    # 4. Total Time

    if graph_type == 'First Token Latency vs. Output Generation Throughput':
        fig = px.scatter(data_df, x="Decode Tokens/s", y="TTFT(ms)", color="System",
                    # labels={"Batch": "Batch", "Tokens/s": "Tokens/s", "Model": "Model"},
                    width=1200, height=600)
        # Update layout to add quadrant colors
        fig.update_layout(
            shapes=[
                # Quadrant 1 (Top-right)
                dict(
                    type='rect',
                    x0=0.5, x1=1,
                    y0=0, y1=0.5,
                    fillcolor='rgba(0, 255, 0, 0.3)',  # Red with transparency
                    line=dict(color='rgba(255, 255, 255, 0)'),
                    xref='paper', yref='paper'
                ),
                # Quadrant 3 (Bottom-left)
                dict(
                    type='rect',
                    x0=0, x1=0.5,
                    y0=0.5, y1=1,
                    fillcolor='rgba(255, 0, 0, 0.3)',  # Blue with transparency
                    line=dict(color='rgba(255, 255, 255, 0)'),
                    xref='paper', yref='paper'
                ),
            ]
        )
        fig.update_traces(marker=dict(size=20))

    elif graph_type == 'First Token Latency':
        fig = px.bar(data_df, x="System", y="TTFT(ms)")
    elif graph_type == 'Output Generation Throughput':
        fig = px.bar(data_df, x="System", y="Decode Tokens/s")
    elif graph_type == 'Total Response Time':
        fig = px.bar(data_df, x="System", y="E2E Latency(ms)")

    # Customize axis labels
    fig.update_xaxes(title_font=dict(size=24))
    fig.update_yaxes(title_font=dict(size=24))

    # Customize tick labels
    fig.update_xaxes(tickfont=dict(size=24))
    fig.update_yaxes(tickfont=dict(size=24))
    fig.update_yaxes(matches=None)

    # # Customize facet labels
    fig.update_layout(
        font_size=24,
        legend = dict(font = dict(family = "Courier", size = 24)),
        legend_title = dict(font = dict(family = "Courier", size = 24))
        )


    if len(mem_size_data) == 0 :
        return fig
    else:
        return fig, chip_req_df


def ChangeButtonColour(widget_label, font_color, background_color='transparent'):
    htmlstr = f"""
        <script>
            var elements = window.parent.document.querySelectorAll('button');
            for (var i = 0; i < elements.length; ++i) {{
                if (elements[i].innerText == '{widget_label}') {{
                    elements[i].style.color ='{font_color}';
                    elements[i].style.background = '{background_color}'
                }}
            }}
        </script>
        """
    components.html(f"{htmlstr}", height=0, width=0)

def main():
    st.header("Model")
    col1, col2 = st.columns([3,2])
    with col1:
        if 'models' not in st.session_state:
            st.switch_page("Home.py")
        selected_models = st.selectbox("Models:", st.session_state.models)
    with col2:
        st.markdown("""
            <style>
                .stSelectBox [data-baseweb=select] span{
                    max-width: 225px;
                    font-size: 1rem;
                }
            </style>
            """, unsafe_allow_html=True)
        quantization = st.selectbox("Quantization:", ['fp8', 'bf16', 'int8', 'int4', 'int2', 'fp32'])


    st.header("Use case")
    col1, col2, col3, col4, col5 = st.columns([3,1,2,1,1])
    with col1:
        use_case = st.selectbox("Usecases:", ['Ques-Ans', 'Text Summarization', 'Chatbots', 'Code Gen.', 'Custom'])
        if 'Ques-Ans' == use_case:
            used_beam_size = 4
            used_input_tokens = 1000
            used_output_tokens = 200
        elif 'Text Summarization' == use_case:
            used_beam_size = 4
            used_input_tokens = 15000
            used_output_tokens = 1000
        elif 'Chatbots' == use_case:
            used_beam_size = 2
            used_input_tokens = 2048
            used_output_tokens = 128
        elif 'Code Gen.' == use_case:
            used_beam_size = 4
            used_input_tokens = 20000
            used_output_tokens = 50
    with col2:
        batch_size = st.number_input("Batch Size:", value=8, step=1,min_value=1)
    with col3:
        beam_size = st.slider("No. of Parallel Beams:", min_value=1, max_value=16, value=used_beam_size)
    with col4:
        input_tokens = st.number_input("Input Tokens:", value=used_input_tokens)
    with col5:
        output_tokens = st.number_input("Output Tokens:", value=used_output_tokens)

    # with col3:
    st.header("HW System")
    if 'systems' not in st.session_state:
        st.switch_page("Home.py")

    col1, col2, col3, col4, col5, col6, col7, col8 = st.columns([1,1,1,1,1,1,1,1])
    with col1:
        selected_system = st.selectbox("System:", st.session_state.systems)
        if selected_system == 'Custom':
            system_name = st.text_input("System Name:")
    with col2:
        nodes = st.number_input("# Nodes:", value=2, step=1)
    with col3:
        system_efficiency = st.slider("System Efficiency:", min_value=0.0, max_value=1.0, value=0.80, step=0.01)
    if selected_system in system_configs:
        current_system_config = system_configs[selected_system]
        system_name = selected_system
        used_flops = current_system_config.get('Flops', '')
        used_mem_bw = current_system_config.get('Memory_BW', '')
        used_mem_cap = current_system_config.get('Memory_size', '')
        used_icn_bw = current_system_config.get('ICN', '')
    else:
        used_flops = 312
        used_mem_bw = 1600
        used_mem_cap = 40
        used_icn_bw = 150
    with col4:
        flops = st.number_input("FLOPS(T):", value=used_flops)
    with col5:
        mem_bw = st.number_input("MEM BW(TB/s):", value=used_mem_bw)
    with col6:
        mem_cap = st.number_input("Mem Capacity (GBs):", value=used_mem_cap)
    with col7:
        icn_bw = st.number_input("ICN BW(GB/s):", value=used_icn_bw)
    # Initialize the list in session state if it doesn't exist
    if 'system_list' not in st.session_state:
        st.session_state.system_list = [
            {'name':'A100_80GB_GPU',
            'Flops': system_configs['A100_80GB_GPU'].get('Flops', ''),
            'Memory_BW': system_configs['A100_80GB_GPU'].get('Memory_BW', ''),
            'Memory_size': system_configs['A100_80GB_GPU'].get('Memory_size', ''),
            'ICN': system_configs['A100_80GB_GPU'].get('ICN', '') , 'nodes':1, 'eff':0.8, 'real_values':True},
            {'name':'H100_GPU', 'Flops': system_configs['H100_GPU'].get('Flops', ''),
            'Memory_BW': system_configs['H100_GPU'].get('Memory_BW', ''),
            'Memory_size': system_configs['H100_GPU'].get('Memory_size', ''),
            'ICN': system_configs['H100_GPU'].get('ICN', '') , 'nodes':1, 'eff':0.8, 'real_values':True},
            {'name':'TPUv5e', 'Flops': system_configs['TPUv5e'].get('Flops', ''),
            'Memory_BW': system_configs['TPUv5e'].get('Memory_BW', ''),
            'Memory_size': system_configs['TPUv5e'].get('Memory_size', ''),
            'ICN': system_configs['TPUv5e'].get('ICN', '') , 'nodes':1, 'eff':0.8, 'real_values':True},
            {'name':'MI300X', 'Flops': system_configs['MI300X'].get('Flops', ''),
            'Memory_BW': system_configs['MI300X'].get('Memory_BW', ''),
            'Memory_size': system_configs['MI300X'].get('Memory_size', ''),
            'ICN': system_configs['MI300X'].get('ICN', '') , 'nodes':1, 'eff':0.8, 'real_values':True},
            {'name':'Gaudi3', 'Flops': system_configs['Gaudi3'].get('Flops', ''),
            'Memory_BW': system_configs['Gaudi3'].get('Memory_BW', ''),
            'Memory_size': system_configs['Gaudi3'].get('Memory_size', ''),
            'ICN': system_configs['Gaudi3'].get('ICN', '') , 'nodes':1, 'eff':0.8, 'real_values':True},
        ]
    with col8:
        if st.button("➕",key='add_item'):
            new_item = {'name':system_name, 'Flops': flops, 'Memory_BW': mem_bw, 'Memory_size': mem_cap, 'ICN': icn_bw , 'nodes':nodes, 'eff':system_efficiency, 'real_values':True}
            st.session_state.system_list.append(new_item)
            st.success(f"Added: {nodes} x {system_name}")
    st.subheader("Current Items:")
    for i, item in enumerate(st.session_state.system_list):
        col1, col2 = st.columns([3, 1])
        col1.write(f"{i+1}. {item['nodes']} x {item['name']} @ {item['eff']} efficiency : FLOPS: {item['Flops']} TOPS, Memory BW: {item['Memory_BW']} GB/s, Memory Size: {item['Memory_size']} GB, Interconnect BW: {item['ICN']} GB/s")
        if col2.button("➖", key=f"remove_{i}"):
            st.session_state.system_list.pop(i)
            st.rerun()
    ChangeButtonColour('➕', '#FF009C', '#00FF63') # button txt to find, colour to assign
    ChangeButtonColour('➖', '#00FFEF', '#FF0010') # button txt to find, colour to assign

    st.header("Output Metrics")

    graph_type = st.selectbox("Comparision Type:", [
        'First Token Latency vs. Output Generation Throughput',
        'First Token Latency',
        'Output Generation Throughput',
        'Total Response Time',
        ])


    # Create Plotly bar chart
    if st.session_state.system_list:
        outputs = generate_system_comparision(
            graph_type = graph_type,
            system_list = st.session_state.system_list,
            model=selected_models,
            quantization = quantization,
            batch_size=batch_size,
            input_tokens = input_tokens,
            output_tokens = output_tokens,
            beam_size = beam_size
            )
        if isinstance(outputs, tuple):
            st.plotly_chart(outputs[0])
            st.write("Number of nodes is insufficient for these systems, please increase the nodes to fit the model")
            st.dataframe(outputs[1])
        else:
            st.plotly_chart(outputs)

    # Display some calculated metrics
    # st.subheader("Calculated Metrics")
    # st.write(f"Effective System Performance: {flops}, {mem_bw}")

if __name__ == "__main__":
    main()
