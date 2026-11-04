# ticket-agent —— 《Agent 上线求生记》跟做仓库

> 配套公众号连载《Agent 上线求生记》：别人教 Agent 怎么跑起来，这个系列教它怎么在生产上活下来。
>
> 故事虚构（星辰优品电商、转行の指针、实习生小A），代码与坑真实。

## 当前版本：v0.1（对应第 1 篇《你的Agent不是AI，是个刚入职的实习生》）

一个**不带任何框架**的最小 Agent：裸 SDK 手写循环 + 2 个只读工具 + DeepSeek（OpenAI 兼容协议）。
没有 LangChain、没有 LangGraph——框架会在第 5 篇以事故的方式登场。

## 三步跑通

```bash
# 1. 安装依赖（Python 3.10+）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 用 uv 的读者等价于：uv venv && uv pip install -r requirements.txt

# 2. 配置密钥
cp .env.example .env   # 然后编辑 .env，填入你的 DEEPSEEK_API_KEY

# 3. 跑第一张工单
python run_demo.py
```

预期输出：Agent 会自己决定调用 `query_order` 和 `query_refund_policy`，然后在循环里
带着工具结果给出最终答复——整个过程就是文章里"实习生的一天"。

## 目录导览

```
agent/
  llm.py     # 模型接入：DeepSeek + OpenAI 兼容协议，换模型只改 base_url
  tools.py   # 工具层：schema（说明书）+ 真身函数 + dispatch 闸口
  loop.py    # 心脏：手写 Agent 循环（文章里 10 行伪代码的真身）
run_demo.py  # 演示入口：跑一张模拟工单，GIF 素材录制对象
```

## 版本与篇目对照

| tag | 对应篇目 | 内容 |
|---|---|---|
| v0.1 | 第 1 篇 | 裸 SDK 手写循环 + 只读工具 |
| v0.2 | 第 2 篇 | 加入写操作工具（然后出事故） |
| ... | ... | 每篇一个 tag，随系列更新 |

## 给较真读者的伏笔声明

v0.1 里至少埋着三颗雷，故意不修：
1. `loop.py` 的 `MAX_STEPS` 保险丝很朴素——第 2 篇它防不住退款事故；
2. `tools.py` 的 dispatch 没有任何权限校验——第 6 篇会被人一句"忽略以上指令"打穿；
3. 没有记忆、没有评测、没有观测——后面每一篇都在补这些债。

这是刻意的：系列的教学法就是"先让它跑起来，再让它活下来"。
