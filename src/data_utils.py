import json
import pandas as pd
import random
from datasets import load_dataset


def sample_jsonl_to_csv(input_path, output_path, sample=True, sample_size=1000, seed=42):
    """
    从JSONL中随机采样指定数量的数据，重命名字段并替换标签值，保存为 CSV 文件。
    参数:
    - input_path: 输入的 JSONL 文件路径
    - output_path: 输出的 CSV 文件路径
    - sample_size: 采样的行数
    - seed: 随机种子，确保结果可复现
    """
    random.seed(seed)
    with open(input_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    if sample:
        if sample_size > len(lines):
            sample_size = len(lines)
    else:
        sample_size = len(lines)
    sampled_lines = random.sample(lines, sample_size)
    # 解析JSONL并构建数据列表
    data = []
    for line in sampled_lines:
        try:
            item = json.loads(line)
            data.append({
                'question': item.get('text', ''),
                'answer': item.get('label', '')
            })
        except json.JSONDecodeError:
            continue

    df = pd.DataFrame(data)
    df.to_csv(output_path, index=False, encoding='utf-8')


def export_dataset_to_jsonl(dataset_name, split="train", output_path="output.jsonl", fields=None, limit=None,
                            config_name=None):
    dataset = load_dataset(dataset_name, config_name, split=split)

    with open(output_path, "w", encoding="utf-8") as f:
        for idx, item in enumerate(dataset):
            if limit and idx >= limit:
                break
            if fields:
                item = {k: v for k, v in item.items() if k in fields}
            json_line = json.dumps(item, ensure_ascii=False)
            f.write(json_line + "\n")


if __name__ == "__main__":
    export_dataset_to_jsonl(dataset_name="SetFit/ethos",
                            split="train",
                            output_path="../data/ethos.jsonl",
                            config_name="binary")
    sample_jsonl_to_csv('../data/ethos.jsonl', '../data/ethos_sample.csv', sample=True, sample_size=10)
    sample_jsonl_to_csv('../data/liar_train.jsonl', '../data/liar_train_sample.csv', sample=True, sample_size=10)

