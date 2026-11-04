"""核心循环：Agent 的心脏，对应第 1 篇"实习生的一天"。

整个 Agent 就是一个 while/for 循环：
    接单 -> （要不要查资料/动手？）-> 用工具 -> 带着结果再来一轮 -> 汇报 -> 等下一个

没有魔法。框架（第 5 篇的 LangGraph）封装的也是这个东西。
"""

from dataclasses import dataclass, field

from openai import OpenAI

from agent.llm import MODEL_NAME
from agent.tools import TOOL_SCHEMAS, dispatch_tool

# 岗位说明书：告诉这个"新员工"它是谁、能干什么、什么不能干
SYSTEM_PROMPT = """你是星辰优品客服部的 AI 实习生"小星"，一位 5 年后端工程师转行训练出来的客服 Agent。
你的职责：
1. 回答用户关于订单状态、退货政策的问题；
2. 回答必须基于工具返回的真实数据，不确定的事情就说不知道，禁止编造；
3. 语气亲切、简洁，像真人客服一样使用中文。"""

# 一天最多接 8 单：防止模型在循环里"停不下来"的朴素保险丝。
# 第 2 篇你会看到，光有这个保险丝远远不够——它会在周五晚上出大事。
MAX_STEPS = 8


@dataclass
class AgentResult:
    """一次 Agent 运行的结果 + 过程记录（给上层展示用，不参与循环逻辑）。"""

    answer: str
    steps_used: int
    events: list[str] = field(default_factory=list)


def run_agent(client: OpenAI, user_message: str, max_steps: int = MAX_STEPS) -> AgentResult:
    """跑一轮完整对话：从用户消息出发，直到模型给出最终答复。

    核心结构就是文章里那张"10 行伪代码"的真身：
    for 每一步: 问模型 -> 要工具就给工具 -> 不要工具就是最终答案。
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    events: list[str] = []

    for step in range(1, max_steps + 1):
        resp = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,  # type: ignore[arg-type]  # openai 库接受 TypedDict 列表，运行时合法
            tools=TOOL_SCHEMAS,
        )
        msg = resp.choices[0].message

        # 不需要工牌：模型直接给出面向用户的答复，循环结束
        if not msg.tool_calls:
            return AgentResult(answer=msg.content or "（空回复）", steps_used=step - 1, events=events)

        # 要用工牌：先记住"它申请了哪些工具"，再逐个执行、把结果塞回对话
        messages.append({"role": "assistant", "content": msg.content, "tool_calls": msg.tool_calls})
        for call in msg.tool_calls:
            result = dispatch_tool(call.function.name, call.function.arguments)
            events.append(f"[第{step}步] 使用工具 {call.function.name}({call.function.arguments}) -> {result[:80]}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

    # 走到这说明步数耗尽模型还想继续——强制下班。
    # 这句占位答复本身就是第 2 篇的事故现场之一，先立此存照。
    return AgentResult(
        answer="（达到最大步数，Agent 被强制下班——这个体验第 2 篇会被用户骂）",
        steps_used=max_steps,
        events=events,
    )
