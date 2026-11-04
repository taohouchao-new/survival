"""工具层：把 Python 函数变成模型能"点名使用"的工牌。

对应第 1 篇比喻：Tools = 新员工的工牌权限。
每个工具由两部分组成：
  1. TOOL_SCHEMAS 里的"说明书"——告诉模型这个工具是干嘛的、要什么参数
  2. 真身函数       ——模型点名后由我们的代码执行，模型自己碰不到数据库

v0.1 只有只读工具（查询类）。写操作工具（比如退款）第 2 篇才会上线——
不是因为写不出来，是因为写操作会闯祸，那正是第 2 篇的故事。
"""

import json

# 假订单库：教学用内存数据，第 2 篇之后会逐步换成"像样"的存储
ORDERS: dict[str, dict] = {
    "SO2026010101": {
        "customer": "Vivian",
        "item": "羊毛针织衫",
        "amount": 299.0,
        "status": "已签收",
        "created_at": "2026-10-30 20:15",
    },
    "SO2026102803": {
        "customer": "小A",
        "item": "机械键盘",
        "amount": 549.0,
        "status": "运输中",
        "created_at": "2026-11-02 09:41",
    },
    "SO2026110207": {
        "customer": "老张",
        "item": "人体工学椅",
        "amount": 1299.0,
        "status": "已发货",
        "created_at": "2026-11-03 14:07",
    },
}

REFUND_POLICY = """星辰优品退货政策（2026 修订版）：
1. 支持 7 天无理由退货（自签收次日起算），商品需保持吊牌完好、不影响二次销售；
2. 质量问题 15 天内可退可换，运费由平台承担；
3. 定制类商品、贴身衣物、食品不支持无理由退货；
4. 退款在审核通过后 3 个工作日内原路退回。"""


def query_order(order_id: str) -> str:
    """按订单号查询订单状态。查不到时返回明确的"未找到"文本，
    让模型能据此回复用户，而不是拿到一个报错干瞪眼。"""
    order = ORDERS.get(order_id)
    if order is None:
        return f"未找到订单 {order_id}，请确认订单号是否正确（当前库里有：{list(ORDERS)})"
    return json.dumps(order, ensure_ascii=False)


def query_refund_policy() -> str:
    """查询退货政策原文。第 3 篇会看到：光有政策文本，Agent 依然可能胡说八道。"""
    return REFUND_POLICY


# —— 模型能看到的"工具说明书"（OpenAI function calling 格式）——
TOOL_SCHEMAS = [
    {
        "type": "function",
        "function": {
            "name": "query_order",
            "description": "按订单号查询星辰优品的订单状态、商品、金额等信息",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "订单号，形如 SO2026010101",
                    }
                },
                "required": ["order_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "query_refund_policy",
            "description": "查询星辰优品的退货政策原文（7天无理由、质量问题15天等）",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]

# 工具名 -> 真身函数 的路由表
_TOOL_IMPLS = {
    "query_order": query_order,
    "query_refund_policy": query_refund_policy,
}


def dispatch_tool(name: str, arguments_json: str) -> str:
    """执行模型点名的工具，返回结果文本。

    模型只交回"工具名 + JSON 字符串"，真正动手的是这里——
    这层 dispatch 就是新员工和工牌之间的闸口。第 6 篇（提示注入）会
    回到这里加权限校验，现在它还很天真。
    """
    impl = _TOOL_IMPLS.get(name)
    if impl is None:
        # 未知工具：返回错误文本而不是抛异常，让模型有机会向用户说明情况
        return f"错误：不存在名为 {name} 的工具"
    try:
        args = json.loads(arguments_json or "{}")
    except json.JSONDecodeError:
        return f"错误：工具参数不是合法 JSON：{arguments_json!r}"
    return impl(**args)
