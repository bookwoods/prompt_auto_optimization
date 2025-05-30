import json
import re
import csv
import pandas as pd
from sklearn.metrics import accuracy_score, f1_score

def recognize_result(sample, batch_input, batch_output, csv_path):
    '''
    :param
    sample:取label
    batch_input:取system输入和user输入
    batch_output:取assistant输出
    :return:
    '''
    # 取 label
    with open(sample, 'r', encoding='utf-8') as infile:
        lines = infile.readlines()
    labels = [json.loads(line.strip())["label"] for line in lines]

    # 取输入
    prompts = []
    questions = []
    with open(batch_input, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f):
            data = json.loads(line.strip())
            prompts.append(data["body"]["messages"][0]["content"])
            questions.append(data["body"]["messages"][1]["content"])

    # 取输出
    answers = []
    with open(batch_output, 'r', encoding='utf-8') as f:
        for line_number, line in enumerate(f):
            data = json.loads(line.strip())
            answer = data["response"]["body"]["choices"][0]["message"]["content"]
            try:
                answer = extract_answer_tags(answer)
                answers.append(answer)
            except:
                answers.append(answer)

    # 分割数据为每轮 100 条
    chunk_size = 461  # ethos 461  liar 998
    prompts_chunks = [prompts[i:i + chunk_size] for i in range(0, len(prompts), chunk_size)]
    questions_chunks = [questions[i:i + chunk_size] for i in range(0, len(questions), chunk_size)]
    answers_chunks = [answers[i:i + chunk_size] for i in range(0, len(answers), chunk_size)]

    # 构建表头
    csv_header = ["question", "label"]
    for i in range(len(prompts_chunks)):
        csv_header.append(f"prompt_iter_{i}")
        csv_header.append(f"answer_iter_{i}")

    # 构建数据行
    csv_rows = []
    for idx in range(chunk_size):
        row = [questions_chunks[0][idx], labels[idx]]
        for i in range(len(prompts_chunks)):
            row.append(prompts_chunks[i][idx])
            row.append(answers_chunks[i][idx])
        csv_rows.append(row)

    # 写入 CSV 文件
    with open(csv_path, 'w', newline='', encoding='utf-8') as file:
        writer = csv.writer(file)
        writer.writerow(csv_header)  # 写入表头
        writer.writerows(csv_rows)   # 写入数据行

def extract_answer_tags(text):
    pattern = r"<answer>(.*?)</answer>"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip()


def evaluate_predictions_from_csv(csv_path):
    """
    读取CSV并计算每个 answer_iter 的准确率和 F1 分数。
    自动跳过非数字（0/1）预测值的行。
    """
    df = pd.read_csv(csv_path)

    # 强制转换 label 为 int 类型
    df['label'] = pd.to_numeric(df['label'], errors='coerce')

    results = []

    for i in range(5):
        col = f'answer_iter_{i}'

        if col not in df.columns:
            print(f"列 {col} 不存在，跳过")
            continue

        # 尝试将该列转换为整数，错误的会变成 NaN
        df[col] = pd.to_numeric(df[col], errors='coerce')

        # 删除该列中任一值为 NaN 的行（说明不是合法数字）
        filtered = df[['label', col]].dropna()

        # 确保标签都是 0 或 1
        filtered = filtered[(filtered['label'].isin([0, 1])) & (filtered[col].isin([0, 1]))]

        if filtered.empty:
            print(f"{col} 没有有效数据，跳过")
            continue

        y_true = filtered['label'].astype(int)
        y_pred = filtered[col].astype(int)

        acc = accuracy_score(y_true, y_pred)
        f1 = f1_score(y_true, y_pred)

        results.append({
            'iter': col,
            'accuracy': acc,
            'f1_score': f1
        })
    print(results)

    return pd.DataFrame(results)

if __name__ == "__main__":
    # sample = "../../data/ethos.jsonl"
    # batch_input = "ethos_batch_no_sample.jsonl"
    # batch_output = "ethos_batch_no_sample_result.jsonl"
    # csv_path = "ethos_result.csv"

    sample = "../../data/liar_test.jsonl"
    batch_input = "liar_batch_no_sample.jsonl"
    batch_output = "liar_batch_no_sample_result.jsonl"
    csv_path = "liar_no_sample_result.csv"

    recognize_result(sample, batch_input, batch_output, csv_path)
    accuracies = evaluate_predictions_from_csv(csv_path)



