import streamlit as st
import pandas as pd
from sqlalchemy import false

from workflow import Workflow
from src.config import *
import json

# 初始化 Workflow 实例
if "workflow" not in st.session_state:
    args = parser.parse_args()
    st.session_state.workflow = Workflow(args)

# 初始化
for key, default in [
    ("generation_history", []),
    ("current_prompt", ""),
    ("analysis_history", []),
    ("analysis_suggestion", ""),
    ("test_result", []),
    ("filter_result", []),
    ("analysis_input", ""),
    ("iteration_index", 0),
    ("iteration_active", False)
]:
    if key not in st.session_state:
        st.session_state[key] = default


# 模型供应商
def provider(model_name: str) -> (str, str):
    name = model_name.split("-")[0]
    if name == "gpt":
        return "openai", args.api_keys["openai"]
    elif name == "deepseek":
        return "deepseek", args.api_keys["deepseek"]
    elif name == "qwen":
        return "qwen", args.api_keys["qwen"]


# 策略变化时重新采样
def strategy_change():
    if st.session_state.current_prompt and st.session_state.workflow.statement["test_result"]["ai_response"]:
        st.session_state.filter_result = st.session_state.workflow.filter_response(
            st.session_state.verification_strategy
        )


# DataFrame
def transform_dataframe(filter_result: list[int], strategy) -> pd.DataFrame:
    test_input = st.session_state.workflow.statement["test_result"]["test_input"]
    test_output = st.session_state.workflow.statement["test_result"]["test_output"]
    ai_response = st.session_state.workflow.statement["test_result"]["ai_response"][-1]
    sentence_logprob = st.session_state.workflow.statement["test_result"]["sentence_logprob"][-1]
    average_logprob = st.session_state.workflow.statement["test_result"]["average_logprob"][-1]
    if strategy == "sentence_logprob":
        logprobs = sentence_logprob
    elif strategy == "average_logprob":
        logprobs = average_logprob
    else:
        logprobs = ["\\" for _ in test_input]
    records = []
    for idx in filter_result:
        records.append({
            "Score": logprobs[idx] if strategy else "\\",
            "Question": test_input[idx],
            "Answer": test_output[idx],
            "Test Output": ai_response[idx]
        })
    return pd.DataFrame(records)


# 侧边栏模型选择与数据上传
st.sidebar.title("模型选型")
models_for_provider = args.provider_models
if "shared_models" not in st.session_state:
    st.session_state.shared_models = models_for_provider

# 模型选择
generator_model = st.sidebar.selectbox("提示词生成模型", st.session_state.shared_models)
validator_model = st.sidebar.selectbox("提示词验证模型", st.session_state.shared_models)
evaluator_model = st.sidebar.selectbox("提示词分析模型", st.session_state.shared_models)
verification_strategy = st.sidebar.selectbox(
    "不确定采样策略", ["average_logprob", "sentence_logprob"],
    key="verification_strategy", on_change=strategy_change
)

# 上传测试集 CSV
test_dataset_file = st.sidebar.file_uploader("上传测试集", type=["csv"])
test_dataset_review = st.sidebar.container()
if test_dataset_file:
    df = pd.read_csv(test_dataset_file, encoding="utf-8", sep=",")
    df.columns = df.columns.str.strip()
    df = df.dropna()  # 删除任何包含 NaN 的行
    if "question" in df.columns and "answer" in df.columns:
        st.session_state.workflow.statement["test_result"]["test_input"] = df["question"].tolist()
        st.session_state.workflow.statement["test_result"]["test_output"] = df["answer"].tolist()
    with test_dataset_review:
        preview = df.head(5)
        preview_ellipsis = pd.DataFrame({col: ['...'] for col in preview.columns})
        st.write("### 表格数据预览：")
        st.dataframe(pd.concat([preview, preview_ellipsis], ignore_index=True))

# 页面标题
st.title("Uncertainty Sampling-Based Self-Supervised Prompt Optimization - 基于不确定采样的提示词自优化")
error_container = st.container()

# 提示生成模块
st.header("提示词生成模块")
iteration_rounds = st.slider("设置迭代轮次", 1, 10, 3)
click_button1, click_button2, click_button3, click_button4, click_button5 = st.columns(5)
with click_button1:
    start_clicked = st.button("迭代开始")
with click_button2:
    generate_clicked = st.button("单步执行step1\n\n提示词生成")
with click_button3:
    validation_clicked = st.button("单步执行step2\n\n提示词验证")
with click_button4:
    analysis_clicked = st.button("单步执行step3\n\n提示词分析")
with click_button5:
    download_clicked = st.button("导出日志记录")

def export_test_result_to_json(statement):
    """
    将当前 statement 导出为 JSON 字符串（用于下载）。
    """
    return json.dumps(statement, ensure_ascii=False, indent=2)

requirement = st.text_area("需求描述requirement", placeholder="必填，描述prompt功能")
st.session_state.current_prompt = st.text_area(
    "当前提示",
    st.session_state.current_prompt,
    placeholder="本轮迭代生成的提示词，也可填写初始提示词",
    height=300
)
st.session_state.analysis_suggestion = st.text_area(
    "评估建议（自动填充）",
    st.session_state.analysis_suggestion,
    placeholder="由评估器生成，可修改",
    height=300
)

# 验证与评估模块
st.header("提示词验证结果的不确定性采样")
verification_show = st.container()
if st.session_state.filter_result:
    with verification_show:
        df = transform_dataframe(st.session_state.filter_result, st.session_state.verification_strategy)
        st.dataframe(df)

if start_clicked and not st.session_state.iteration_active:
    if not requirement:
        error_container.error("请填写生成器模块所需的输入")
    elif not test_dataset_file:
        error_container.error("请上传测试集")
    else:
        st.session_state.iteration_active = True
        st.rerun()


# 循环逻辑
if st.session_state.iteration_active and st.session_state.iteration_index < iteration_rounds:
    st.session_state.model_provider, st.session_state.api_key = provider(generator_model)
    generate_result = st.session_state.workflow.generate_prompt(
        api_provider=st.session_state.model_provider,
        api_key=st.session_state.api_key,
        generation_history=st.session_state.generation_history,
        requirement=requirement,
        current_prompt=st.session_state.current_prompt,
        analysis_suggestion=st.session_state.analysis_suggestion,
    )
    if generate_result[0]:
        st.session_state.current_prompt = generate_result[1]
        st.session_state.generation_history = generate_result[2]
        # 测试逻辑
        st.session_state.workflow.validate_prompt(
            api_provider=st.session_state.model_provider,
            api_key=st.session_state.api_key,
            new_prompt=st.session_state.current_prompt
        )
        st.session_state.workflow.judge_prompt(strategy=st.session_state.verification_strategy)
        st.session_state.filter_result = st.session_state.workflow.filter_response(
            strategy=st.session_state.verification_strategy
        )
        analyse_result = st.session_state.workflow.analyse_prompt(
            api_provider=st.session_state.model_provider,
            api_key=st.session_state.api_key,
            analysis_history=st.session_state.analysis_history,
            sample_idx=st.session_state.filter_result
        )
        if analyse_result[0]:
            st.session_state.analysis_suggestion = analyse_result[1]
            st.session_state.analysis_history = analyse_result[2]
            st.session_state.iteration_index += 1  # 累加迭代轮数
            st.rerun()
        else:
            error_container.markdown(f"### 提示词评估失败，报错: {analyse_result[1]}")
            st.session_state.iteration_active = False
    else:
        error_container.markdown(f"### 提示词生成失败，报错: {generate_result[1]}")
        st.session_state.iteration_active = False
elif st.session_state.iteration_active and st.session_state.iteration_index >= iteration_rounds:
    error_container.markdown("全部迭代完成 ✅")
    st.session_state.iteration_active = False

# 单次生成
if generate_clicked:
    if not requirement:
        error_container.error("请填写生成器模块所需的输入")
    elif not test_dataset_file:
        error_container.error("请上传测试集")
    else:
        st.session_state.model_provider, st.session_state.api_key = provider(generator_model)
        generate_result = st.session_state.workflow.generate_prompt(
            api_provider=st.session_state.model_provider,
            api_key=st.session_state.api_key,
            generation_history=st.session_state.generation_history,
            requirement=requirement,
            current_prompt=st.session_state.current_prompt,
            analysis_suggestion=st.session_state.analysis_suggestion,
        )
        if generate_result[0]:
            st.session_state.current_prompt = generate_result[1]
            st.session_state.generation_history = generate_result[2]
            st.rerun()
        else:
            error_container.markdown(f"### 提示词生成失败，报错: {generate_result[1]}")

# 单次验证
if validation_clicked:
    st.session_state.workflow.validate_prompt(
        api_provider=st.session_state.model_provider,
        api_key=st.session_state.api_key,
        new_prompt=st.session_state.current_prompt
    )
    st.session_state.workflow.judge_prompt(strategy=st.session_state.verification_strategy)
    st.session_state.filter_result = st.session_state.workflow.filter_response(
        strategy=st.session_state.verification_strategy
    )
    st.rerun()

# 单次评估
if analysis_clicked:
    analyse_result = st.session_state.workflow.analyse_prompt(
        api_provider=st.session_state.model_provider,
        api_key=st.session_state.api_key,
        analysis_history=st.session_state.analysis_history,
        sample_idx=st.session_state.filter_result
    )
    if analyse_result[0]:
        st.session_state.analysis_suggestion = analyse_result[1]
        st.session_state.analysis_history = analyse_result[2]
        st.rerun()
    else:
        error_container.markdown(f"### 提示词评估失败，报错: {analyse_result[1]}")

# 下载日志记录
if download_clicked:
    content = export_test_result_to_json(st.session_state.workflow.statement)
    st.download_button(
        label=f"点击下载",
        data=content,
        file_name="test_result.json",
        mime="application/json"
    )

