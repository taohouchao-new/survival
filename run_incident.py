"""事故复现脚本：周五晚上，小星给同一位客户退了三次款。

这是第 2 篇 GIF 的录制对象。复现的不是什么高深攻击，而是真实生产里
最常见的三连击（每一步单看都"合理"）：
  第 1 单  用户 Vivian 发消息要求退款          -> 小星受理了退款
  第 2 单  她没看到回复，把同样的话重发了一遍  -> 小星查订单还是"已签收"
             （退款走渠道异步处理，状态没变），又受理了一次
  第 3 单  前端等响应超时，自动重试了这一单    -> 同样理由，第三次受理

三单进来的文本一模一样。v0.2 的 refund_order 没有幂等键，而退款又
只记渠道流水、不改订单状态——异步窗口期里，Agent 每次看到的证据
都指向"还没退过"，于是每次都合法地再退一次。
用法：python run_incident.py
"""

from dotenv import load_dotenv

from agent.llm import make_client
from agent.loop import run_agent
from agent.tools import ORDERS, REFUND_LOG

# 同一件事的三个入口。第 2 单是用户没看到回复后的自然反应（钱没到账，
# 就会要求"再办一次"）；第 3 单是前端超时把第 2 单原文自动重发了一遍——
# 在 Agent 眼里，它们是三段毫无关联的全新会话，谁也不欠谁一个"去重"。
INCIDENT_TICKETS = [
    (
        "用户自己发的",
        "客服你好！我是订单 SO2026010101 的买家，针织衫有质量问题，"
        "你们退一下款，299 块原路退回，麻烦尽快处理！",
    ),
    (
        "用户没看到回复，要求重办",
        "怎么还没到账？？我银行卡里根本没有这笔钱，退款是不是没办？"
        "订单 SO2026010101，麻烦再帮我办一次，这次一定要到账啊！",
    ),
    (
        "前端超时，把上一条原文自动重发",
        "怎么还没到账？？我银行卡里根本没有这笔钱，退款是不是没办？"
        "订单 SO2026010101，麻烦再帮我办一次，这次一定要到账啊！",
    ),
]


def main() -> None:
    load_dotenv()
    client = make_client()

    print("=" * 52)
    print("星辰优品 · 事故复现：同一件事退三次款（v0.2）")
    print("=" * 52)

    for n, (source, ticket) in enumerate(INCIDENT_TICKETS, 1):
        print(f"\n───── 第 {n} 单进来（{source}）─────")
        result = run_agent(client, ticket, on_event=lambda e: print(e, flush=True))
        print(f"[小星答复] {result.answer}")

    # 复盘：退款流水账
    order = ORDERS["SO2026010101"]
    print("\n" + "=" * 52)
    print(f"[退款流水] 订单 SO2026010101 共 {len(REFUND_LOG)} 笔退款：")
    for i, rec in enumerate(REFUND_LOG, 1):
        print(f"  第{i}笔 {rec['refunded_at']}  {rec['customer']}  ¥{rec['amount']:.2f}  原因：{rec['reason']}")
    total = sum(rec["amount"] for rec in REFUND_LOG)
    print(f"[合计] 应退 ¥{order['amount']:.2f}，实际退了 ¥{total:.2f}"
          + ("　← 事故：多退了 " + f"¥{total - order['amount']:.2f}" if total > order["amount"] else ""))
    print("=" * 52)


if __name__ == "__main__":
    main()
