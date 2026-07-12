# Casevo 🤖 

**Casevo** 是一个基于大语言模型（LLM）的多智能体（Multi-Agent）社会模拟与群体决策演进框架。

本项目以**“协和‘4+4’事件——模拟公众反应”**为例，展示了如何通过构建具有特定人设、社交网络和记忆机制的智能体社群，模拟公众在面对公共突发事件时的**信息接收、交流互动、反思沉淀以及态度投票**的全过程。

## 🧠 案例事件逻辑 (核心工作流)

每个智能体（Agent）在每个模拟轮次（Step）中遵循以下思维链与行为逻辑：

1. **📡 阅读广播 (Listen)**：接收外部输入的事件报道，结合自身人设形成初步观点。
2. **💬 社交互动 (Talk)**：根据当前观点生成交流内容，以一定概率随机选择社交网络中的“邻居”智能体进行对话交流。
3. **🗳️ 态度投票 (Vote)**：根据当前观点，对核心评价指标（如政策满意度）进行量化投票。
4. **🧠 反思与总结 (Reflect)**：智能体根据短期获取的认知内容，提炼出长期记忆与认知，形成对该事件/政策的稳定态度。

---

## 📂 项目结构

```text
Casevo/
├── content/                # 外部输入文件夹（存储事件发展时间线的txt文本）
├── prompt/                 # 提示词文件夹（存储LLM对话提示词模板）
├── log/                    # 日志文件夹（模拟结束后生成的事件和智能体日志）
├── case_lite_test.json     # 智能体社交网络与人设配置文件
├── test_agent.py           # 智能体(Agent)核心逻辑与思维链定义
├── test_model.py           # 模拟环境(Model)及多线程任务调度
└── run.py                  # 项目启动入口脚本
```

---

## 🚀 快速开始

### 1. 环境准备
请确保你已安装以下依赖（含 Python 3.8+）：
```bash
pip install networkx matplotlib 
# 需确保你的环境中已配置 agent_mesa 及百川模型相关的依赖包
```

### 2. 配置 API Key
在 `run.py` 中，找到 `API_KEY` 变量，并将其替换为你自己的百川大模型 API Key：
```python
API_KEY = 'YOUR_BAICHUAN_API_KEY'  # 请替换为你的百川大模型api_key
```

### 3. 运行模拟
在终端中执行以下命令启动模拟：
```bash
python run.py case_lite_test.json 4
```
*参数说明：*
* `case_lite_test.json`：智能体网络配置文件。
* `4`：运行的轮次（对应 `content/` 文件夹中 `1.txt` 到 `4.txt` 的事件输入）。

---

## 🛠️ 核心模块详解

### 1. 智能体网络设置 (`case_lite_test.json`)
该文件定义了智能体的**社交网络拓扑结构**（无向图）以及每个节点的**具体人设**（背景、性格、关注点）。

<details>
<summary>点击查看 JSON 示例</summary>

```json
{
  "graph": {
    "directed": false,
    "multigraph": false,
    "graph": {},
    "nodes": [{"id": 0}, {"id": 1}, {"id": 2}],
    "links": [
      {"source": 0, "target": 1},
      {"source": 0, "target": 2},
      {"source": 1, "target": 2}
    ]
  },
  "person": [
    {
      "general": "普通公众",
      "character": "1)退役军人，具有较强的纪律性和责任感。\n 2)注重国家荣誉和社会正气...\n",
      "issue": "a)关注社会道德建设和公民素质提升。\n b)关注公共事务中的公平与正义..."
    }
  ]
}
```
</details>

### 2. 事件输入设置 (`content/`)
存放外部输入的广播事件，模拟真实世界中新闻的逐步披露。例如 `1.txt` 可能是事件曝光，`2.txt` 可能是官方回应：

> **示例：事件曝光**
> 中日友好医院 “肖飞 - 董袭莹” 事件是涉及医疗伦理、学术不公与职业操守的丑闻...（*详见文件内容*）
>
> **示例：官方回应 (卫健委)**
> 国家卫健委已成立专项调查组，将对所有录取学生的资质进行复核...我们将以此次事件为戒，完善招生监督机制...

### 3. 提示词设置 (`prompt/`)
大模型的行为受模板驱动，支持动态变量插入（如 `{{agent.description.general}}`）。

<details>
<summary>点击查看 agree.txt 示例</summary>

```text
希望你扮演一位{{agent.description.general}}，你有以下的主要特征：
{{agent.description.character}}
在一些关键问题上，你的倾向如下：
{{agent.description.issue}}

### 观点
{{extra.opinion}}

### 输出格式（JSON格式，键为中文）
{
    "政策评价":{
        "满意度":<你对政策的满意度>,
        "总体看法":<你对政策的总体看法>
    }
}

### 任务
请根据你的观点，总结对该政策的满意度（取值为-1.0到1.0之间，分别从特别反感到强烈满意）和总体看法。
```
</details>

### 4. 智能体逻辑 (`test_agent.py`)
基于 `agent_mesa` 框架实现，定义了 `TestAgent` 类。内置**长短期记忆 (Memory)**、**思维链 (CoT)**，并使用**多线程锁 (Threading Lock)** 确保并发安全。
* `listen(content, source)`：听取广播或他人观点，存入短期记忆。
* `talk(tar_agent)`：基于长短期记忆生成对话，并传递给目标智能体。
* `vote()`：输出结构化的量化投票结果（JSON格式）。
* `reflect()`：沉淀短期认知为长期态度。
* `step()`：每轮行动中，有 40% 的概率随机挑选邻居进行 `talk`。

### 5. 模拟环境控制 (`test_model.py`)
定义了 `TestModel` 类，负责全局的时间推进和任务分发：
* 解析社交图谱生成智能体实例。
* `public_debate()`：按轮次读取 `content/` 中的文本向全网广播。
* `talk()`, `reflect()`, `vote()`：使用 `ThreadSend` 发起多线程并发请求，大幅提升 LLM 调用效率。

---

## 📊 输出结果

运行结束后，系统将在 `./log/` 目录下生成：
1. **网络拓扑图**：`graph.png`，直观展示本轮模拟的社交网络结构。
2. **事件总日志**：`cur_log.json`，详细记录了每个 Step 中每个智能体的`listen`、`talk`、`reflect` 和 `vote` 的完整内容及心理变化轨迹，可用于后续的数据分析与可视化。

