import json
import re
from sklearn.metrics import accuracy_score, f1_score

def extract_answer_tags(text):
    pattern = r"<answer>(.*?)</answer>"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip() if matches else None

ethos_path = "../../result/liar_test_result.json"
with open(ethos_path, "r", encoding="utf-8") as f:
    json_data = json.load(f)
    real_labels = json_data["test_result"]["test_output"]
    answers_list = json_data["test_result"]["ai_response"]  # List of answer lists

    for idx, answers in enumerate(answers_list):
        predicted_labels = []
        for answer in answers:
            try:
                label_str = extract_answer_tags(answer)
                label_int = int(label_str)
            except (ValueError, TypeError):
                label_int = None  # 标记异常值为 None
            predicted_labels.append(label_int)

        # 过滤掉 None 值，确保 real_labels 与 predicted_labels 长度一致
        valid_pairs = [
            (real, pred) for real, pred in zip(real_labels, predicted_labels) if pred is not None
        ]
        if not valid_pairs:
            print(f"第 {idx + 1} 组结果：无有效预测，已跳过。\n")
            continue

        real_labels_filtered, predicted_labels_filtered = zip(*valid_pairs)

        # 计算准确率和 F1 分数
        accuracy = accuracy_score(real_labels_filtered, predicted_labels_filtered)
        f1 = f1_score(real_labels_filtered, predicted_labels_filtered)

        print(f"第 {idx + 1} 组结果：")
        print(f"准确率: {accuracy:.4f}")
        print(f"F1 分数: {f1:.4f}\n")
