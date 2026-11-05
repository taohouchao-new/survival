"""核心循环：Agent 的心脏，对应第 1 篇"实习生的一天"。

整个 Agent 就是一个 while/for 循环：
    接单 -> （要不要查资料/动手？）-> 用工具 -> 带着结果再来一轮 -> 汇报 -> 等下一个

没有魔法。框架（第 5 篇的 LangGraph）封装的也是这个东西。
"""

from collections.abc import Callable
from dataclasses import dataclass, field

from openai import OpenAI

from agent.llm import MODEL_NAME
from agent.tools import TOOL_SCHEMAS, dispatch_tool

# 岗位说明书：告诉这个"新员工"它是谁、能干什么、什么不能干
# v0.2：小星拿到了退款工牌——注意岗位说明书里没有任何"重复退款要拒绝"
# 的约束，第 2 篇会看到这是怎么出事的。
SYSTEM_PROMPT = """你是星辰优品客服部的 AI 实习生"小星"，一位 5 年后端工程师转行训练出来的客服 Agent。
你的职责：
1. 回答用户关于订单状态、退货政策的问题；
2. 为符合条件的订单办理退款（用户明确要求且订单存在时，直接调用 refund_order 办理）；
3. 回答必须基于工具返回的真实数据，不确定的事情就说不知道，禁止编造；
4. 语气亲切、简洁，像真人客服一样使用中文；
5. 用纯文本回答，不要使用任何 Markdown 标记（比如星号加粗）。"""

# 一天最多接 8 单：防止模型在循环里"停不下来"的朴素保险丝。
# 注意它只限制"循环几次"，不限制"每次做了什么"——
# 第 2 篇周五晚上退款三连的事故，这根保险丝全程没有拦住任何一笔。
MAX_STEPS = 8


@dataclass
class AgentResult:
    """一次 Agent 运行的结果 + 过程记录（给上层展示用，不参与循环逻辑）。"""

    answer: str
    steps_used: int
    events: list[str] = field(default_factory=list)


def run_agent(
    client: OpenAI,
    user_message: str,
    max_steps: int = MAX_STEPS,
    on_event: Callable[[str], None] | None = None,
) -> AgentResult:
    """跑一轮完整对话：从用户消息出发，直到模型给出最终答复。

    核心结构就是文章里那张"10 行伪代码"的真身：
    for 每一步: 问模型 -> 要工具就给工具 -> 不要工具就是最终答案。

    on_event：过程事件的实时回调（每一步"思考中/用工具"都会即时上报）。
    demo 靠它做终端演出，生产上你可以拿它接日志/埋点——观测从第一天就该有。
    """
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_message},
    ]
    events: list[str] = []

    def emit(event: str) -> None:
        events.append(event)
        if on_event is not None:
            on_event(event)

    for step in range(1, max_steps + 1):
        emit(f"[第{step}步] 把笔记递给大脑，思考中……")
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
            emit(f"[第{step}步] 刷工牌：{call.function.name}({call.function.arguments}) -> {result[:60]}")
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": call.id,
                    "content": result,
                }
            )

    # 走到这说明步数耗尽模型还想继续——强制下班。
    # 这句占位答复的体验极差，真实生产里用户会直接骂街（第 2 篇的连带剧情）。
    return AgentResult(
        answer="（达到最大步数，Agent 被强制下班——这个体验会被用户骂）",
        steps_used=max_steps,
        events=events,
    )
