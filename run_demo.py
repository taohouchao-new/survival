"""演示入口：跑一张模拟工单，看 Agent 循环的完整内脏。

这是第 1 篇 GIF 素材的录制对象——文章里"实习生的一天"终端演示就是它。
用法：python run_demo.py
"""

from dotenv import load_dotenv

from agent.llm import make_client
from agent.loop import run_agent

# 一张工单，同时考两个工具：查订单 + 查退货政策
DEMO_TICKET = "你好，我上周买的针织衫还没到，订单号 SO2026010101。另外想问下这个能无理由退货吗？"


def main() -> None:
    load_dotenv()  # 从 .env 读取 DEEPSEEK_API_KEY
    client = make_client()

    print("=" * 52)
    print("星辰优品 · 智能客服工单演示（v0.1 裸 SDK 手写循环）")
    print("=" * 52)
    print(f"\n[工单] {DEMO_TICKET}\n")

    # 实时事件回调：循环每走一步，这里立刻打印一行——
    # 终端演示（GIF）要的"过程感"就来自它
    result = run_agent(client, DEMO_TICKET, on_event=lambda e: print(e, flush=True))

    print("-" * 52)
    print(f"\n[小星的答复]\n{result.answer}\n")
    print(f"[过程] 共 {result.steps_used} 轮循环")


if __name__ == "__main__":
    main()
