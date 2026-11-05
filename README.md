# ticket-agent —— 《Agent 上线求生记》跟做仓库

> 配套公众号连载《Agent 上线求生记》：别人教 Agent 怎么跑起来，这个系列教它怎么在生产上活下来。
>
> 故事虚构（星辰优品电商、转行の指针、实习生小A），代码与坑真实。

## 当前版本：v0.2（对应第 2 篇《周五晚上，我的 Agent 给客户退了三次款》）

v0.1 的裸 SDK 循环之上，**小星拿到了第一个写操作工牌：退款**。
`refund_order` 是故意的朴素版——没有幂等键、不改订单状态（退款走渠道异步
处理）、dispatch 无权限校验。跑一下事故复现脚本，亲眼看看"同一件事
退三次款"是怎么发生的：

```bash
python run_incident.py
```

⚠️ 修复方案（幂等键 + 写操作人审）见第 2 篇第 4 节，完整实现随 v0.3 合入。
在学习它之前，别把这个工具接到任何真的支付系统上。

## 三步跑通

```bash
# 1. 安装依赖（Python 3.10+）
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
# 用 uv 的读者等价于：uv venv && uv pip install -r requirements.txt

# 2. 配置密钥
cp .env.example .env   # 然后编辑 .env，填入你的 DEEPSEEK_API_KEY

# 3. 跑第一张工单（v0.1 日常版）或事故复现（v0.2 事故版）
python run_demo.py       # 正常客服演示：查订单 + 查政策
python run_incident.py   # 第 2 篇事故复现：同一件事退三次款
```

预期输出：`run_demo.py` 会看到 Agent 自己决定调用 `query_order` 和
`query_refund_policy`；`run_incident.py` 会看到三单进料、退款流水账
最终打出"共 3 笔退款"——每一次受理在当时的证据下都"合理"，这正是事故的可怕之处。

## 目录导览

```
agent/
  llm.py     # 模型接入：DeepSeek + OpenAI 兼容协议，换模型只改 base_url
  tools.py   # 工具层：schema（说明书）+ 真身函数 + dispatch 闸口
  loop.py    # 心脏：手写 Agent 循环（文章里 10 行伪代码的真身）
run_demo.py  # 演示入口：跑一张模拟工单（第 1 篇 GIF 素材）
run_incident.py  # 事故复现：同一诉求退三次款（第 2 篇 GIF 素材）
```

## 版本与篇目对照

| tag | 对应篇目 | 内容 |
|---|---|---|
| v0.1 | 第 1 篇 | 裸 SDK 手写循环 + 只读工具 |
| v0.2 | 第 2 篇 | 加入写操作工具 refund_order（朴素版，事故复现） |
| ... | ... | 每篇一个 tag，随系列更新 |

## 给较真读者的伏笔声明

仓库里至少埋着几颗雷，故意不修：
1. `tools.py` 的 `refund_order` 没有幂等键、不改订单状态——这正是第 2 篇事故的主角，修复随 v0.3 合入；
2. `tools.py` 的 dispatch 没有任何权限校验——第 6 篇会被人一句"忽略以上指令"打穿；
3. `loop.py` 的 `MAX_STEPS` 保险丝只数步数不看操作——它在第 2 篇全程没拦住任何一笔退款；
4. 没有记忆、没有评测、没有观测——后面每一篇都在补这些债。

这是刻意的：系列的教学法就是"先让它跑起来，再让它活下来"。
