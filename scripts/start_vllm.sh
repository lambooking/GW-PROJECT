#!/bin/bash
# start_vllm.sh
# 该脚本用于启动VLLM OpenAI兼容的API服务。

# 设置环境变量
export CUDA_VISIBLE_DEVICES=0
export VLLM_ATTENTION_BACKEND=FLASHINFER

# 启动VLLM服务
# --model: 指定要加载的模型，这里是Qwen-VL-Chat-7B。
# --served-model-name: 对外暴露的模型名称。
# --host: 监听的IP地址，0.0.0.0表示允许外部访问。
# --port: 服务端口。
# --max-model-len: 模型支持的最大上下文长度。
# --tensor-parallel-size: GPU张量并行的大小，单卡设为1。
# --gpu-memory-utilization: GPU显存使用率。
# --max-num-seqs: 服务器可以并行处理的最大序列数。
# --trust-remote-code: 允许执行来自Hugging Face Hub的自定义模型代码。
# --enforce-eager: 强制使用Eager模式，有时可以解决兼容性问题。

echo "正在启动VLLM服务..."

python -m vllm.entrypoints.openai.api_server \
    --model /home/wyr/AgiBot-World-Project/agi_iros/models/Qwen2.5-VL-7B-Instruct  \
    --served-model-name qwen2.5-vl-3b \
    --host 0.0.0.0 \
    --port 8000 \
    --max-model-len 8192 \
    --tensor-parallel-size 1 \
    --gpu-memory-utilization 0.9 \
    --max-num-seqs 4 \
    --trust-remote-code \
    --enable-log-requests \
    --enforce-eager

# huggingface-cli download              
#    openai/gpt-oss-20b           
#    --local-dir                           
#    ./models/Qwen2.5-VL-7B-Instruct 