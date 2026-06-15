"""
LLM客户端封装类
目标：封装一个好用、可复用的LLM调用工具
这个类会在后续所有项目中使用！
"""
import os
import logging
from typing import Optional
from dotenv import load_dotenv
from openai import OpenAI

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S'
)
logger = logging.getLogger(__name__)


class LLMClient:
    """
    封装OpenAI API调用的客户端类
    
    功能：
    1. 自动从.env加载配置
    2. 支持普通调用和流式调用
    3. 支持带system prompt的快捷方法
    4. 自动记录日志
    5. 支持自定义参数
    """
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        model: Optional[str] = None,
        default_temperature: float = 0.7,
        default_max_tokens: int = 2000
    ):
        """
        初始化LLM客户端
        
        参数:
            api_key: API密钥（不传则从.env读取）
            base_url: API地址（不传则从.env读取）
            model: 模型名称（不传则从.env读取）
            default_temperature: 默认温度参数
            default_max_tokens: 默认最大token数
        """
        # 加载.env文件
        load_dotenv()
        
        # 读取配置（优先使用传入参数，否则从环境变量读取）
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.model = model or os.getenv("MODEL_NAME")
        self.default_temperature = default_temperature
        self.default_max_tokens = default_max_tokens
        
        # 验证配置
        if not self.api_key:
            raise ValueError("API Key未配置！请在.env文件中设置OPENAI_API_KEY")
        if not self.model:
            raise ValueError("模型名称未配置！请在.env文件中设置MODEL_NAME")
        
        # 初始化OpenAI客户端
        client_kwargs = {"api_key": self.api_key}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url
        
        self.client = OpenAI(**client_kwargs)
        
        logger.info(f"LLMClient初始化成功 | 模型: {self.model}")
    
    def chat(
        self,
        messages: list,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False
    ):
        """
        发送聊天请求
        
        参数:
            messages: 消息列表，格式 [{"role": "user", "content": "..."}]
            temperature: 温度参数（不传则使用默认值）
            max_tokens: 最大token数（不传则使用默认值）
            stream: 是否使用流式输出
        
        返回:
            普通模式: 字符串（AI的回答内容）
            流式模式: 生成器（逐块产出内容）
        """
        # 使用默认值或传入值
        temp = temperature if temperature is not None else self.default_temperature
        tokens = max_tokens if max_tokens is not None else self.default_max_tokens
        
        logger.debug(f"发送请求 | 消息数: {len(messages)} | temperature: {temp}")
        
        if stream:
            # 流式模式
            return self._stream_chat(messages, temp, tokens)
        else:
            # 普通模式
            return self._normal_chat(messages, temp, tokens)
    
    def _normal_chat(self, messages: list, temperature: float, max_tokens: int) -> str:
        """普通模式调用"""
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        content = response.choices[0].message.content
        usage = response.usage
        
        logger.info(f"请求完成 | Tokens: {usage.total_tokens} (输入:{usage.prompt_tokens} 输出:{usage.completion_tokens})")
        
        return content
    
    def _stream_chat(self, messages: list, temperature: float, max_tokens: int):
        """流式模式调用，返回生成器"""
        stream = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=True
        )
        
        for chunk in stream:
            content = chunk.choices[0].delta.content
            if content is not None:
                yield content
        
        logger.info("流式请求完成")
    
    def chat_with_system(
        self,
        system_prompt: str,
        user_message: str,
        temperature: Optional[float] = None,
        stream: bool = False
    ) -> str:
        """
        快捷方法：带system prompt的对话
        
        参数:
            system_prompt: 系统提示词（定义AI的角色和行为）
            user_message: 用户消息
            temperature: 温度参数
            stream: 是否流式输出
        
        返回:
            AI的回答内容
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message}
        ]
        return self.chat(messages, temperature=temperature, stream=stream)


# ===== 测试代码 =====
if __name__ == "__main__":
    print("=" * 50)
    print("LLMClient 功能测试")
    print("=" * 50)
    
    # 初始化客户端
    llm = LLMClient()
    
    # 测试1：普通调用
    print("\n--- 测试1：普通调用 ---")
    result = llm.chat([
        {"role": "user", "content": "用一句话介绍Python"}
    ])
    print(f"回答: {result}")
    
    # 测试2：带system prompt
    print("\n--- 测试2：带system prompt ---")
    result = llm.chat_with_system(
        system_prompt="你是一个幽默的程序员，回答要带点笑话。",
        user_message="什么是bug？"
    )
    print(f"回答: {result}")
    
    # 测试3：流式输出
    print("\n--- 测试3：流式输出 ---")
    print("AI: ", end="", flush=True)
    for chunk in llm.chat(
        messages=[{"role": "user", "content": "数到5，每个数字后面加一个emoji"}],
        stream=True
    ):
        print(chunk, end="", flush=True)
    print()
    
    # 测试4：多轮对话模拟
    print("\n--- 测试4：多轮对话 ---")
    conversation = [
        {"role": "system", "content": "你是一个Python老师。"},
        {"role": "user", "content": "什么是装饰器？"}
    ]
    answer1 = llm.chat(conversation)
    print(f"老师: {answer1}")
    
    conversation.append({"role": "assistant", "content": answer1})
    conversation.append({"role": "user", "content": "能写一个简单的例子吗？"})
    answer2 = llm.chat(conversation)
    print(f"老师: {answer2}")
    
    print("\n" + "=" * 50)
    print("所有测试通过！LLMClient 封装完成 ✅")
    print("=" * 50)