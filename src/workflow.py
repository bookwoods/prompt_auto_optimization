import re
import random
import pandas as pd
from ai_chat import AIChat
import io


class Workflow:
    def __init__(self, args):
        self.args = args
        self.test_dataset = []  # 测试数据集
        self.prompt_template = ""  # 提示词模板
        self.generation_prompt = open("../prompt/generation_prompt_en.md", "r", encoding="utf-8").read()
        self.analysis_prompt = open("../prompt/analysis_prompt_en.md", "r", encoding="utf-8").read()
        # self.meta_prompt = open("../prompt/meta_prompt.md", "r", encoding="utf-8").read()
        self.statement = {
            "prompts": [],
            "best_prompt_idx": 0,
            "test_result": {
                "test_input": [],
                "test_output": [],
                "ai_response": [],
                "sentence_logprob": [],
                "average_logprob": [],
                "strategy_filter_idx": [],
            },
        }

    def generate_prompt(self,
                        api_provider: str,
                        api_key: str,
                        generation_history: list,
                        requirement: str,
                        meta_prompt: str = None,
                        current_prompt: str = None,
                        analysis_suggestion: str = None) -> (bool, str, list):
        """
        提示词生成器
        :param
            generation_history:生成器的历史上下文
            requirement:需求描述
            meta_prompt:元提示，可选输入
            current_prompt:当前提示，第一轮迭代为可选输入
            analysis_suggestion:评估器的分析建议，可选输入
        :return
            bool:本次会话发起是否正常
            new_prompt:新生成的prompt
            generation_history:生成器的历史上下文
        """
        input_text = ""
        if meta_prompt:
            input_text += f"## Meta Prompt：\n{meta_prompt}\n\n"
        if current_prompt:
            input_text += f"## Current Prompt：\n{current_prompt}\n\n"
        if analysis_suggestion:
            input_text += f"## Analysis Suggestion：\n{analysis_suggestion}\n\n"
        input_text += f"## Requirement description：\n{requirement}"
        generation_history.append({"role": "system", "content": self.generation_prompt})
        generation_history.append({"role": "user", "content": input_text})
        ai_chat = AIChat(api_provider=api_provider, api_key=api_key)

        for attempt in range(3):
            completion = ai_chat.chat(generation_history, logprobs=False)
            response = ai_chat.get_response(completion)
            if response["response"]:
                try:
                    new_prompt = extract_Answer_tags(response["response"])  # 如果这里失败将跳转到 except
                    generation_history.append({"role": "assistant", "content": new_prompt})
                    self.statement["prompts"].append(new_prompt)
                    return True, new_prompt, generation_history
                except Exception as e:
                    generation_history.append({"role": "assistant", "content": response["response"]})
                    generation_history.append({"role": "system", "content": self.generation_prompt})
                    generation_history.append({"role": "user", "content": input_text})
                    if attempt == 2:
                        # 第三次仍失败就退出
                        return False, f"extract_Answer_tags failed after 3 attempts: {str(e)}", generation_history
            else:
                return False, response["error_message"], generation_history


    def validate_prompt(self,
                        api_provider: str,
                        api_key: str,
                        new_prompt: str):
        """
        提示词验证器，加载测试数据集后批量测试
        :param
            new_prompt:新生成的prompt
        :return
            filter_test_output:筛选后的测试结果
        """
        all_response = []
        all_sentence_logprob = []
        all_average_logprob = []

        for qs in self.statement["test_result"]["test_input"]:
            validation_history = [
                {"role": "system", "content": new_prompt},
                {"role": "user", "content": qs}
            ]
            success = False
            for _ in range(3):
                try:
                    ai_chat = AIChat(api_provider=api_provider, api_key=api_key)
                    completion = ai_chat.chat(validation_history)
                    response = ai_chat.get_response(completion)
                    all_response.append(response["response"])
                    all_sentence_logprob.append(response["sentence_logprob"])
                    all_average_logprob.append(response["average_logprob"])
                    success = True
                    break
                except:
                    continue
            if not success:
                all_response.append("error or empty response")
                all_sentence_logprob.append(None)
                all_average_logprob.append(None)
        self.statement["test_result"]["ai_response"].append(all_response)
        self.statement["test_result"]["sentence_logprob"].append(all_sentence_logprob)
        self.statement["test_result"]["average_logprob"].append(all_average_logprob)


    def judge_prompt(self, strategy: str) -> (bool, str, list):
        """
        多数优胜策略，统计验证结果
        """
        if len(self.statement["test_result"]["ai_response"]) > 1:
            test_dataset = self.statement["test_result"]["test_output"]
            previous_prompt_output = self.statement["test_result"]["ai_response"][self.statement["best_prompt_idx"]]
            previous_output_logprob = self.statement["test_result"][strategy][self.statement["best_prompt_idx"]]
            current_prompt_output = self.statement["test_result"]["ai_response"][-1]
            current_output_logprob = self.statement["test_result"][strategy][-1]
            result_flags = []
            for idx in range(len(test_dataset)):
                # 获取 current / previous 的 answer 和 logprob
                test_answer = str(self.statement["test_result"]["test_output"][idx])
                previous_output = previous_prompt_output[idx]
                current_output = current_prompt_output[idx]
                try:
                    previous_answer = extract_answer_tags(previous_output)
                except Exception:
                    try:
                        current_answer = extract_answer_tags(current_output)
                        result_flags.append(True)
                        continue
                    except Exception:
                        result_flags.append(False)
                        continue
                try:
                    current_answer = extract_answer_tags(current_output)
                except Exception:
                    result_flags.append(False)
                    return
                previous_answer_logprob = previous_output_logprob[idx]
                current_answer_logprob = current_output_logprob[idx]
                better = False
                # 相同答案
                if current_answer == previous_answer:
                    if current_answer == test_answer:
                        better = current_answer_logprob > previous_answer_logprob
                    else:
                        better = current_answer_logprob < previous_answer_logprob
                else:
                    better = current_answer == test_answer
                result_flags.append(better)
            # 多数优胜策略
            if sum(result_flags) > len(result_flags) // 2:
                self.statement["best_prompt_idx"] = len(self.statement["prompts"])-1  # 多数样本表现更好，替换为更好的提示词

    def analyse_prompt(self,
                       api_provider: str,
                       api_key: str,
                       analysis_history: list,
                       sample_idx: list) -> (bool, str, list):
        """
        提示词评估器
        :param
            analysis_history:评估器的历史上下文
            new_prompt:新生成的prompt
            input_text:本次评估结果
        :return
            bool:本次会话发起是否正常
            analysis_suggestion:评估分析建议
            generation_history:生成器的历史上下文
        """
        previous_prompt = self.statement["prompts"][self.statement["best_prompt_idx"]]
        previous_prompt_output = self.statement["test_result"]["ai_response"][self.statement["best_prompt_idx"]]
        test_question = self.statement["test_result"]["test_input"]
        test_answer = self.statement["test_result"]["test_output"]
        input_text = f"## Current Prompt\n{previous_prompt}\n\n"
        for idx in sample_idx:
            q = test_question[idx]
            a = test_answer[idx]
            p = previous_prompt_output[idx]
            input_text += f"### Test Question\n{q}\n### True Answer\n{a}\n### Test Answer\n{p}\n\n"
        analysis_history.append({"role": "system", "content": self.analysis_prompt})
        analysis_history.append({"role": "user", "content": input_text})
        ai_chat = AIChat(api_provider=api_provider, api_key=api_key)
        completion = ai_chat.chat(analysis_history, logprobs=False)
        response = ai_chat.get_response(completion)
        if response["response"]:
            analysis_suggestion = response["response"]
            analysis_history.append({"role": "assistant", "content": analysis_suggestion})
            return True, analysis_suggestion, analysis_history
        else:
            return False, response["error_message"], analysis_history

    def filter_response(self, strategy: str = "random",  # sentence_logprob/average_logprob
                        top_k: int = 1,
                        bottom_k: int = 1,
                        middle_k: int = 1) -> list[int]:
        """
        从浮点列表中筛选 Top-K、Middle-K、Bottom-K 项，并返回其在原始列表中的索引。

        参数：
            strategy: str，可选 "sentence_logprob" 或 "average_logprob"
            top_k: int，选择得分最高的数量
            middle_k: int，选择中间段的数量
            bottom_k: int，选择得分最低的数量
        返回：
            List[int]，被选中项在原始列表中的索引
        """
        if strategy == "random":
            all_sample_list = list(range(len(self.statement["test_result"]["ai_response"][-1])))
            sampled_list = random.sample(all_sample_list, 3)
            return sampled_list
        else:
            indexed_logprob = [
                (idx, score)
                for idx, score in enumerate(self.statement["test_result"][strategy][-1])
                if score is not None
            ]

        # 排序
        sorted_responses = sorted(indexed_logprob, key=lambda x: x[1], reverse=True)
        n = len(sorted_responses)

        # 获取 Top, Middle, Bottom 采样
        top_samples = sorted_responses[:top_k]
        bottom_samples = sorted_responses[-bottom_k:]
        middle_start = max(0, n // 2 - middle_k // 2)
        middle_end = min(n, middle_start + middle_k)
        middle_samples = sorted_responses[middle_start:middle_end]

        # 合并并打乱顺序
        selected_samples = top_samples + middle_samples + bottom_samples
        random.shuffle(selected_samples)

        # 返回原始索引
        return [sample[0] for sample in selected_samples]

    def load_csv_sample(self, data, n):
        data = list(zip(data["question"], data["answer"]))
        if len(data) > n:
            return random.sample(data, n)
        return data

    def export_test_result_to_csv(self, filepath=None):
        """
        将当前 statement 的测试结果导出为 CSV 文件。
        """
        test_input = self.statement["test_result"].get("test_input", [])
        test_output = self.statement["test_result"].get("test_output", [])
        ai_responses = self.statement["test_result"].get("ai_response", [])
        sent_logprobs = self.statement["test_result"].get("sentence_logprob", [])
        avg_logprobs = self.statement["test_result"].get("average_logprob", [])

        df = pd.DataFrame({
            "Question": test_input,
            "Answer": test_output
        })

        # 每轮展开为 interaction 列
        for i, responses in enumerate(ai_responses):
            df[f"Response_Iter{i + 1}"] = responses
        for i, s_lp in enumerate(sent_logprobs):
            df[f"SentenceLogProb_Iter{i + 1}"] = s_lp
        for i, a_lp in enumerate(avg_logprobs):
            df[f"AverageLogProb_Iter{i + 1}"] = a_lp

        if filepath:
            df.to_csv(filepath, index=False, encoding="utf-8")
        else:
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False, encoding="utf-8")
            return csv_buffer.getvalue()


def extract_Answer_tags(text):
    pattern = r"<Answer>(.*?)</Answer>"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip()


def extract_answer_tags(text):
    pattern = r"<answer>(.*?)</answer>"
    matches = re.findall(pattern, text, re.DOTALL)
    return matches[0].strip()


if __name__ == '__main__':
    df = pd.read_csv("../data/test.csv", encoding="utf-8")
    df.columns = df.columns.str.strip()

    for index, row in df.iloc[1:].iterrows():
        if "question" not in row or "answer" not in row:
            continue
        question = row["question"]
        answer = row["answer"]
        print(f"第{index}行问题：{question}")
        print(f"第{index}行答案：{answer}")
