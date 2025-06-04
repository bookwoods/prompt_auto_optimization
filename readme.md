# 《高级机器学习》课程报告

主要参考谷歌23年的**ProTeGi**与今年二月arxiv上的**SPO**实现的提示词自动优化方法，受到***伍冬睿老师**讲授主动学习课程的相关启发，决定自行尝试从头写一个框架，在提示词评估环节实现定量分析，减少LLM认知偏差，修正语义梯度以加快优化迭代

**运行前需要在./src/config.py 文件中填写gpt或deepseek的api-key**

运行main.py文件启动streamlit界面

./src/result 文件夹下，ethos_test_result.json 与 liar_test_result.json 为提示词迭代优化日志

./src/test 文件夹下，ethos-result.csv 与 liar_no_sample_result.csv 为提示词在测试集上的实验结果



### 整个优化迭代流程示例：

1.打开streamlit界面后，模型选型默认gpt-4o-mini

2.选择./data 文件夹下的ethos_sample.csv上传测试样例

3.填写需求描述description：输入为新闻，需要鉴定新闻的真假，若为真则输出1，若为假则输出0

4.迭代轮次设为1，点击迭代开始

5.等待本轮迭代完成后，点击导出日志，在页面最下方点击下载提示词优化日志



### pending清单

1.与其他提示词优化方法的对比实验

2.多模型、开放类任务的实验验证

3.已预留元提示meta prompt
