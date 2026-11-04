"""模型接入层：DeepSeek（OpenAI 兼容协议）。

为什么用 OpenAI 兼容协议：同一份代码，换一行 base_url 就能切到
GLM / Qwen / 任意兼容服务，读者不会被锁死在某一家模型上。
"""

import os

from openai import OpenAI

# DeepSeek 的 OpenAI 兼容端点；想换模型只改这里
BASE_URL = "https://api.deepseek.com"
MODEL_NAME = "deepseek-chat"


def make_client() -> OpenAI:
    """创建模型客户端。

    Raises:
        RuntimeError: 未设置 DEEPSEEK_API_KEY 时，给读者一个可读的提示，
            而不是让 openai 库在深处抛一个难懂的 KeyError。
    """
    api_key = os.environ.get("DEEPSEEK_API_KEY")
    if api_key is None:
        raise RuntimeError(
            "环境变量 DEEPSEEK_API_KEY 未设置："
            "请复制 .env.example 为 .env，填入你的 Key（获取方式见 README）"
        )
    return OpenAI(api_key=api_key, base_url=BASE_URL)
