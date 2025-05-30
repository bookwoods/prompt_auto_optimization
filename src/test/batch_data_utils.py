import os
import json
import random

# 批量测试，构建请求
def batch_test_request(result_file_path, jsonl_file_path, batch_jsonl_path, model_id, max_tokens=2048):
    '''
    gpt批量测试的响应格式
    {"custom_id": "request-1", "method": "POST", "url": "/v1/chat/completions", "body": {"model": "gpt-3.5-turbo-0125", "messages": [{"role": "system", "content": "You are a helpful assistant."},{"role": "user", "content": "Hello world!"}],"max_tokens": 1000}}
    '''
    with open(jsonl_file_path, 'r', encoding='utf-8') as f:
        jsonl_data = f.readlines()
    with open(result_file_path, "r", encoding="utf-8") as f:
        test_result = json.load(f)
        custom_name = os.path.basename(result_file_path).split("_")[0]
        prompts = test_result["prompts"]
        idx = 0
        for prompt in prompts:
            for data in jsonl_data:
                data = json.loads(data)
                request_template = {"custom_id": custom_name + "_" + str(idx), "method": "POST",
                                "url": "/v1/chat/completions", "body": {"model": model_id,
                                                                        "messages": [], "max_tokens": max_tokens}}
                request_template["body"]["messages"].append({"role": "system", "content": prompt})
                request_template["body"]["messages"].append({"role": "user", "content": data["text"]})
                with open(batch_jsonl_path, "a", encoding="utf-8") as jsonl_f:
                    json_line = json.dumps(request_template, ensure_ascii=False)
                    jsonl_f.write(json_line + "\n")
                idx += 1

def sample_jsonl(input_file_path, output_file_path, sample_size=100):
    # 读取原始 JSONL 文件
    with open(input_file_path, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
    # 检查样本数量是否超过总行数
    if sample_size > len(lines):
        print(f"样本数量 {sample_size} 超过了文件中的总行数 {len(lines)}。")
        sampled_lines = lines
    else:
        # 随机采样指定数量的行
        sampled_lines = random.sample(lines, sample_size)
    # 将采样结果写入新的 JSONL 文件
    with open(output_file_path, 'w', encoding='utf-8') as outfile:
        for line in sampled_lines:
            outfile.write(line)

if __name__ == "__main__":
    data_path = "../../data/ethos.jsonl"
    sample_data_path = "ethos_sample.jsonl"
    sample_jsonl(data_path, sample_data_path)
    result_json_file = "../../result/ethos_test_result.json"
    batch_test_data = "ethos_batch_no_sample.jsonl"
    batch_test_request(result_json_file, data_path, batch_test_data, "gpt-4o-mini")

    # data_path = "../../data/liar_test.jsonl"  # "../data/liar_test.jsonl"
    # sample_data_path = "liar_sample.jsonl"
    # sample_jsonl(data_path, sample_data_path)
    # result_json_file = "../../result/liar_test_result.json"
    # batch_test_data = "liar_batch_no_sample.jsonl"
    # batch_test_request(result_json_file, data_path, batch_test_data, "gpt-4o-mini")