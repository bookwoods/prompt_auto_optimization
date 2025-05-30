import os
import torch
import argparse

current_path = os.path.dirname(os.path.realpath(__file__))
father_path = os.path.dirname(current_path)
data_path = os.path.join(father_path, 'data')
model_path = os.path.join(father_path, 'model')
test_path = os.path.join(father_path, 'test')
generation_prompt_path = os.path.join(father_path, 'prompt ')

provider_models = ["gpt-4o-mini", "gpt-4o", "gpt-4.1-mini", "gpt-4.1", "deepseek-chat", "deepseek-coder"]  # qwen系列无法返回logprob


api_keys = {
    "openai": "",
    "deepseek": "",
}
logprobs = True
top_logprobs = 2

parser = argparse.ArgumentParser()

parser.add_argument('--data_path', type=str, default=data_path)
parser.add_argument('--model_path', type=str, default=model_path)
parser.add_argument('--test_path', type=str, default=test_path)
parser.add_argument('--provider_models', type=list, default=provider_models)
parser.add_argument('--api_keys', type=dict, default=api_keys)
parser.add_argument('--logprobs', type=bool, default=logprobs)
parser.add_argument('--top_logprobs', type=int, default=top_logprobs)


args = parser.parse_args()