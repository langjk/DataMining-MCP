# gpt_api.py
# 封装 OpenAI API 请求

from openai import OpenAI

# 可配置你的API密钥和代理地址
client = OpenAI(
    api_key="sk-Q7Wvw9HQBNqo6nhaJhkQOSggekWlzYHwllH1e5YRcSvwanTY",
    base_url="https://chatapi.zjt66.top/v1"
)

# 初始化对话时载入 system prompt
with open("prompt.txt", "r", encoding="utf-8") as f:
    SYSTEM_PROMPT = f.read().strip()

def ask_gpt(messages):
    """
    封装 GPT 调用：补充 system prompt，返回 assistant 回复字符串
    参数: messages (list of dict)
    返回: assistant 回复内容（str）
    """
    full_messages = [{"role": "system", "content": SYSTEM_PROMPT}] + messages

    response = client.chat.completions.create(
        model="gpt-4o",  # 或 "gpt-4o" / "gpt-3.5-turbo"
        messages=full_messages
    )
    return response.choices[0].message.content.strip()
