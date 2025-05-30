from pathlib import Path

from openai import OpenAI
from src.config import *


args = parser.parse_args()
client = OpenAI(api_key=args.api_keys["openai"])

# 批次文件上传
def upload_file(file_path):
    batch_input_file = client.files.create(
        file=open(file_path, "rb"),
        purpose="batch"
    )
    print(batch_input_file)
    file_id = batch_input_file.id
    print(f"Uploaded file ID: {file_id}")
    return file_id

# 创建批次
def create_batch(file_id, metadata):
    response = client.batches.create(
        input_file_id=file_id,
        endpoint="/v1/chat/completions",
        completion_window="24h",
        metadata={
            "description": metadata
        }
    )
    print(response.id)
    return response.id

# 检查批次状态
def check_status(batch_id, output_file_path):
    '''
    status      description
    validating	批处理开始前正在验证输入文件
    failed	    输入文件未通过验证过程
    in_progress	输入文件已成功验证，批处理当前正在运行
    finalizing	批次已完成，正在准备结果
    completed	批次已完成，结果已准备好
    expired	    该批次无法在 24 小时内完成
    cancelling	批次正在取消（可能需要 10 分钟）
    cancelled	该批次已被取消
    '''
    batch = client.batches.retrieve(batch_id)
    if batch.status == "completed":
        output_file = client.files.content(batch.output_file_id)
        with open(output_file_path, "wb") as f:
            f.write(output_file.read())
        print(f"批处理测试已完成，输出文件id为：{str(batch.output_file_id)}\n已保存文件为：{output_file_path}")
    else:
        print(f"批处理测试当前未完成，当前状态为：{batch.status}")

def cancel_batch(batch_id):
    client.batches.cancel(batch_id)

def check_batch_list():
    print(client.batches.list(limit=10))

if __name__ == "__main__":
    check_batch_list()
