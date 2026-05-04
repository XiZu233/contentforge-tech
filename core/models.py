"""
统一模型客户端：支持多厂商LLM API接入与自动降级

支持的Provider：
- kimi: 月之暗面 Kimi (OpenAI-compatible)
- gemini: Google Gemini (OpenAI-compatible)
- openai: OpenAI GPT
- local: 本地 Ollama 模型 (OpenAI-compatible)

使用方式：
    client = UnifiedLLMClient(["kimi", "gemini", "openai"])
    response = client.chat(messages=[{"role": "user", "content": "..."}])
"""

import os
from dataclasses import dataclass
from typing import Optional, List, Dict, Any, Iterator


@dataclass
class ProviderConfig:
    """模型厂商配置"""
    name: str
    api_key_env: str
    base_url_env: str
    default_model: str
    description: str
    format: str = "openai"


# 内置厂商配置
PROVIDERS: Dict[str, ProviderConfig] = {
    "kimi": ProviderConfig(
        name="Kimi",
        api_key_env="KIMI_API_KEY",
        base_url_env="KIMI_BASE_URL",
        default_model="moonshot-v1-8k",
        description="月之暗面 Kimi",
    ),
    "gemini": ProviderConfig(
        name="Gemini",
        api_key_env="GEMINI_API_KEY",
        base_url_env="GEMINI_BASE_URL",
        default_model="gemini-2.5-flash",
        description="Google Gemini",
    ),
    "openai": ProviderConfig(
        name="OpenAI",
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        default_model="gpt-4o-mini",
        description="OpenAI GPT",
    ),
    "local": ProviderConfig(
        name="Local",
        api_key_env="LOCAL_API_KEY",
        base_url_env="LOCAL_BASE_URL",
        default_model="qwen2.5:14b",
        description="本地 Ollama 模型",
    ),
}

# 默认降级链（从用户 .env 读取可覆盖）
DEFAULT_FALLBACK_CHAIN = ["kimi", "gemini", "openai", "local"]


class UnifiedLLMClient:
    """
    统一LLM客户端

    支持多厂商接入、自动降级、统一接口调用。
    """

    def __init__(self, providers: Optional[List[str]] = None):
        """
        Args:
            providers: 优先级列表，如 ["kimi", "gemini", "openai"]
                       为None时从环境变量 MODEL_PRIORITY 读取，否则使用默认链
        """
        if providers is None:
            priority_env = os.getenv("MODEL_PRIORITY", "")
            if priority_env:
                self.providers = [p.strip() for p in priority_env.split(",") if p.strip()]
            else:
                self.providers = DEFAULT_FALLBACK_CHAIN.copy()
        else:
            self.providers = providers

        # 缓存已创建的客户端
        self._clients: Dict[str, Any] = {}
        self._current_provider: Optional[str] = None

    def _get_provider_config(self, provider: str) -> ProviderConfig:
        """获取厂商配置"""
        if provider not in PROVIDERS:
            raise ValueError(f"不支持的模型厂商: {provider}。可用: {list(PROVIDERS.keys())}")
        return PROVIDERS[provider]

    def _create_client(self, provider: str):
        """创建底层客户端"""
        if provider in self._clients:
            return self._clients[provider]

        config = self._get_provider_config(provider)

        if config.format == "openai":
            try:
                from openai import OpenAI
            except ImportError:
                raise ImportError("请安装 openai 库: pip install openai")

            api_key = os.getenv(config.api_key_env)
            base_url = os.getenv(config.base_url_env)

            if not api_key and provider != "local":
                raise ValueError(f"{config.api_key_env} 未设置")

            # 本地 Ollama 通常不需要 key，或 key 可为空
            if provider == "local":
                api_key = api_key or "ollama"
                base_url = base_url or "http://localhost:11434/v1"

            # Kimi / Gemini / OpenAI 的默认 base_url
            if not base_url:
                if provider == "kimi":
                    base_url = "https://api.moonshot.cn/v1"
                elif provider == "gemini":
                    base_url = "https://generativelanguage.googleapis.com/v1beta/openai/"
                elif provider == "openai":
                    base_url = "https://api.openai.com/v1"

            client = OpenAI(api_key=api_key, base_url=base_url)
            self._clients[provider] = client
            return client
        else:
            raise ValueError(f"不支持的 API 格式: {config.format}")

    def is_available(self, provider: str) -> bool:
        """检查指定厂商是否可用（API key 已配置）"""
        try:
            config = self._get_provider_config(provider)
        except ValueError:
            return False

        if provider == "local":
            # 本地模型检查端口是否可访问
            base_url = os.getenv(config.base_url_env, "http://localhost:11434/v1")
            return self._check_local_server(base_url)

        return bool(os.getenv(config.api_key_env))

    def _check_local_server(self, base_url: str) -> bool:
        """检查本地 Ollama 服务是否运行"""
        try:
            import urllib.request
            import json
            # 尝试访问 Ollama 的 tags 接口
            url = base_url.replace("/v1", "") + "/api/tags"
            req = urllib.request.Request(url, method="GET")
            with urllib.request.urlopen(req, timeout=2) as resp:
                return resp.status == 200
        except Exception:
            return False

    def get_available_providers(self) -> List[str]:
        """获取当前可用的厂商列表"""
        return [p for p in self.providers if self.is_available(p)]

    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        model: Optional[str] = None,
        **kwargs,
    ) -> str:
        """
        统一 chat 接口，自动按优先级链降级

        Args:
            messages: OpenAI 格式的消息列表
            temperature: 温度
            max_tokens: 最大token数
            model: 覆盖默认模型名
            **kwargs: 其他参数（如 response_format）

        Returns:
            模型生成的文本内容

        Raises:
            RuntimeError: 所有厂商均调用失败
        """
        errors = []

        for provider in self.providers:
            try:
                if not self.is_available(provider):
                    errors.append(f"{provider}: 未配置或不可用")
                    continue

                config = self._get_provider_config(provider)
                client = self._create_client(provider)
                model_name = model or config.default_model

                response = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    **kwargs,
                )

                self._current_provider = provider
                return response.choices[0].message.content

            except Exception as e:
                errors.append(f"{provider}: {e}")
                continue

        # 所有厂商均失败
        error_msg = "所有模型厂商均调用失败:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)

    def chat_stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 4000,
        model: Optional[str] = None,
        **kwargs,
    ) -> Iterator[str]:
        """
        流式 chat 接口，自动降级

        Yields:
            每个 token 的文本片段
        """
        errors = []

        for provider in self.providers:
            try:
                if not self.is_available(provider):
                    errors.append(f"{provider}: 未配置或不可用")
                    continue

                config = self._get_provider_config(provider)
                client = self._create_client(provider)
                model_name = model or config.default_model

                stream = client.chat.completions.create(
                    model=model_name,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    stream=True,
                    **kwargs,
                )

                self._current_provider = provider
                for chunk in stream:
                    if chunk.choices and chunk.choices[0].delta.content:
                        yield chunk.choices[0].delta.content
                return

            except Exception as e:
                errors.append(f"{provider}: {e}")
                continue

        error_msg = "所有模型厂商均调用失败:\n" + "\n".join(f"  - {e}" for e in errors)
        raise RuntimeError(error_msg)

    @property
    def current_provider(self) -> Optional[str]:
        """最后一次成功调用的厂商"""
        return self._current_provider

    @property
    def current_provider_name(self) -> Optional[str]:
        """最后一次成功调用的厂商显示名称"""
        if self._current_provider:
            return PROVIDERS.get(self._current_provider, ProviderConfig(name="Unknown")).name
        return None


def get_default_client() -> UnifiedLLMClient:
    """获取默认客户端（使用环境变量配置的优先级链）"""
    return UnifiedLLMClient()
