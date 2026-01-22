# DeepSeek API 集成文档

## 概述

DeepSeek API 是 Radiant 项目的核心 AI 引擎，负责：
- 对话生成
- 知识总结
- Idea 可行性评估
- 审稿人画像生成
- 审稿意见生成
- 论文修改建议生成

本文档详细说明 DeepSeek API 的集成方式、提示词设计、多模型协作等。

---

## 1. DeepSeek API 基础

### 1.1 API 信息

**官方文档**: https://platform.deepseek.com/docs

**API 端点**: `https://api.deepseek.com/v1`

**支持的模型**:
- `deepseek-chat`: 通用对话模型
- `deepseek-coder`: 代码专用模型（可选）

**兼容性**: DeepSeek API 与 OpenAI API 完全兼容，可使用 OpenAI SDK。

---

### 1.2 认证

使用 API Key 进行认证：

**请求头**:
```
Authorization: Bearer {API_KEY}
```

**环境变量配置**:
```bash
DEEPSEEK_API_KEY=sk-xxxxxxxxxxxxx
```

---

### 1.3 计费

**定价** (以实际为准):
- Input: $0.27 / 1M tokens
- Output: $1.10 / 1M tokens

**成本控制**:
- 使用缓存减少重复调用
- 限制上下文长度
- 使用流式输出提升用户体验

---

## 2. Python SDK 集成

### 2.1 安装

```bash
pip install openai
```

---

### 2.2 基础调用示例

```python
from openai import OpenAI

client = OpenAI(
    api_key="your-deepseek-api-key",
    base_url="https://api.deepseek.com/v1"
)

response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Hello!"}
    ],
    max_tokens=1024,
    temperature=0.7
)

print(response.choices[0].message.content)
```

---

### 2.3 流式输出

```python
response = client.chat.completions.create(
    model="deepseek-chat",
    messages=[...],
    stream=True
)

for chunk in response:
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="", flush=True)
```

---

## 3. LLM 服务封装

### 3.1 服务类设计 (`api/llm_service.py`)

```python
import os
from typing import List, Dict, Optional, Iterator
from openai import OpenAI
import hashlib
import json
from redis import Redis

class LLMService:
    def __init__(self):
        self.client = OpenAI(
            api_key=os.getenv("DEEPSEEK_API_KEY"),
            base_url="https://api.deepseek.com/v1"
        )
        self.redis_client = Redis.from_url(os.getenv("REDIS_URL"))
        self.cache_ttl = 7 * 24 * 3600  # 7 天
        self.model = "deepseek-chat"

    def _get_cache_key(self, messages: List[Dict]) -> str:
        """生成缓存键"""
        content = json.dumps(messages, sort_keys=True)
        return f"llm_cache:{hashlib.md5(content.encode()).hexdigest()}"

    def _get_from_cache(self, cache_key: str) -> Optional[str]:
        """从缓存获取"""
        cached = self.redis_client.get(cache_key)
        if cached:
            return cached.decode('utf-8')
        return None

    def _save_to_cache(self, cache_key: str, content: str):
        """保存到缓存"""
        self.redis_client.setex(cache_key, self.cache_ttl, content)

    def chat(
        self,
        messages: List[Dict],
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False,
        use_cache: bool = True
    ) -> str | Iterator:
        """
        通用对话接口

        Args:
            messages: 消息列表
            temperature: 温度参数（0-2），越高越随机
            max_tokens: 最大生成 token 数
            stream: 是否流式输出
            use_cache: 是否使用缓存
        """
        # 检查缓存
        if use_cache and not stream:
            cache_key = self._get_cache_key(messages)
            cached_response = self._get_from_cache(cache_key)
            if cached_response:
                return cached_response

        # 调用 API
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            stream=stream
        )

        if stream:
            return self._stream_response(response)
        else:
            content = response.choices[0].message.content
            # 保存到缓存
            if use_cache:
                self._save_to_cache(cache_key, content)
            return content

    def _stream_response(self, response) -> Iterator[str]:
        """处理流式响应"""
        full_content = ""
        for chunk in response:
            if chunk.choices[0].delta.content:
                content = chunk.choices[0].delta.content
                full_content += content
                yield content

        # 流式输出完成后也缓存
        # (可选，需要在调用处收集完整内容)

    def generate_summary(
        self,
        papers: List[Dict],
        query: str
    ) -> str:
        """
        生成研究方向总结

        Args:
            papers: 论文列表
            query: 研究方向查询
        """
        paper_summaries = "\n\n".join([
            f"**{p['title']}** ({p['year']})\n"
            f"作者: {', '.join(p.get('authors', []))}\n"
            f"摘要: {p.get('abstract', 'N/A')[:200]}..."
            for p in papers[:20]  # 限制数量
        ])

        messages = [
            {
                "role": "system",
                "content": "你是一位学术研究专家，擅长总结和分析学术论文。"
            },
            {
                "role": "user",
                "content": f"""我正在调研「{query}」这个研究方向。

以下是相关的论文：

{paper_summaries}

请你：
1. 总结这个研究方向的核心内容
2. 列出主要的研究者和机构
3. 指出近期的研究趋势
4. 给出进一步学习的建议

请用简洁、结构化的方式回答。"""
            }
        ]

        return self.chat(messages, temperature=0.5)

    def evaluate_idea(
        self,
        idea: str,
        related_papers: List[Dict]
    ) -> Dict:
        """
        评估 Idea 可行性

        Args:
            idea: Idea 描述
            related_papers: 相关论文

        Returns:
            {
                "understanding": "...",
                "feasibility_score": 0.8,
                "pros": [...],
                "cons": [...],
                "suggestions": [...]
            }
        """
        papers_text = "\n".join([
            f"- {p['title']} ({p['year']}): {p.get('abstract', '')[:150]}..."
            for p in related_papers[:10]
        ])

        messages = [
            {
                "role": "system",
                "content": "你是一位资深的科研顾问，擅长评估研究想法的可行性。"
            },
            {
                "role": "user",
                "content": f"""我有一个研究想法：

「{idea}」

以下是相关的已有研究：

{papers_text}

请你：
1. 用简短的话复述你对这个想法的理解
2. 评估这个想法的可行性（0-1 分）
3. 列出这个想法的优点（创新性、实用性等）
4. 列出潜在的挑战或缺点
5. 给出改进建议

请以 JSON 格式返回，格式如下：
{{
  "understanding": "...",
  "feasibility_score": 0.8,
  "pros": ["...", "..."],
  "cons": ["...", "..."],
  "suggestions": ["...", "..."]
}}"""
            }
        ]

        response = self.chat(messages, temperature=0.3)
        # 解析 JSON
        try:
            # 提取 JSON（可能包含在 markdown 代码块中）
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except:
            # 降级处理
            return {
                "understanding": response,
                "feasibility_score": 0.5,
                "pros": [],
                "cons": [],
                "suggestions": []
            }

    def generate_reviewer_profile(
        self,
        reviewer_name: str,
        papers: List[Dict]
    ) -> str:
        """
        生成审稿人画像

        Args:
            reviewer_name: 审稿人姓名
            papers: 审稿人发表的论文
        """
        papers_text = "\n".join([
            f"- {p['title']} ({p['year']})\n  摘要: {p.get('abstract', '')[:150]}..."
            for p in papers[:10]
        ])

        messages = [
            {
                "role": "system",
                "content": "你是一位学术研究专家，擅长分析研究者的研究风格和偏好。"
            },
            {
                "role": "user",
                "content": f"""请为研究者「{reviewer_name}」生成一个审稿人画像。

以下是 TA 发表的代表性论文：

{papers_text}

请分析：
1. TA 的主要研究方向和兴趣
2. TA 的研究风格（理论/实验/工程导向）
3. TA 可能看重的论文特质（创新性、严谨性、实用性等）
4. TA 可能的审稿倾向（严格/宽松）

请用 2-3 段文字简洁描述。"""
            }
        ]

        return self.chat(messages, temperature=0.5)

    def generate_review(
        self,
        paper_content: str,
        reviewer_profile: str,
        reviewer_name: str
    ) -> Dict:
        """
        生成审稿意见

        Args:
            paper_content: 论文内容
            reviewer_profile: 审稿人画像
            reviewer_name: 审稿人姓名

        Returns:
            {
                "strengths": [...],
                "weaknesses": [...],
                "suggestions": [...],
                "overall_score": 7
            }
        """
        # 截断论文内容（避免超过上下文限制）
        paper_content = paper_content[:8000]

        messages = [
            {
                "role": "system",
                "content": f"""你是审稿人「{reviewer_name}」。

{reviewer_profile}

请基于你的研究背景和风格，对以下论文进行评审。"""
            },
            {
                "role": "user",
                "content": f"""论文内容：

{paper_content}

请提供详细的审稿意见，包括：
1. 优点（Strengths）：列出 3-5 个
2. 缺点（Weaknesses）：列出 3-5 个
3. 改进建议（Suggestions）：列出 3-5 个
4. 总体评分（Overall Score）：1-10 分

请以 JSON 格式返回：
{{
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": ["...", "..."],
  "overall_score": 7
}}"""
            }
        ]

        response = self.chat(messages, temperature=0.4)

        # 解析 JSON
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except:
            return {
                "strengths": [],
                "weaknesses": [],
                "suggestions": [],
                "overall_score": 5
            }

    def generate_paper_suggestions(
        self,
        paper_content: str,
        reviews: List[Dict]
    ) -> List[Dict]:
        """
        生成论文修改建议

        Args:
            paper_content: 论文内容
            reviews: 审稿意见列表

        Returns:
            [
                {
                    "section": "Introduction",
                    "original": "...",
                    "suggestion": "...",
                    "reason": "..."
                },
                ...
            ]
        """
        reviews_text = "\n\n".join([
            f"**审稿人 {i+1} 的意见：**\n"
            f"缺点：{', '.join(r.get('weaknesses', []))}\n"
            f"建议：{', '.join(r.get('suggestions', []))}"
            for i, r in enumerate(reviews)
        ])

        paper_content = paper_content[:8000]

        messages = [
            {
                "role": "system",
                "content": "你是一位经验丰富的论文写作专家，擅长根据审稿意见提供具体的修改建议。"
            },
            {
                "role": "user",
                "content": f"""论文内容：

{paper_content}

---

审稿意见：

{reviews_text}

---

请根据审稿意见，为论文提供具体的修改建议。

对于每个建议，请指出：
1. 涉及的章节（如 Introduction, Method, Experiment 等）
2. 原文内容（简短引用）
3. 修改建议（具体文字）
4. 修改原因（对应哪条审稿意见）

请以 JSON 格式返回：
[
  {{
    "section": "Introduction",
    "original": "...",
    "suggestion": "...",
    "reason": "..."
  }},
  ...
]

请提供 5-10 条建议。"""
            }
        ]

        response = self.chat(messages, temperature=0.3, max_tokens=3000)

        # 解析 JSON
        try:
            if "```json" in response:
                response = response.split("```json")[1].split("```")[0]
            elif "```" in response:
                response = response.split("```")[1].split("```")[0]

            return json.loads(response.strip())
        except:
            return []

    def extract_references(self, text: str) -> List[Dict]:
        """
        从回复中提取文献引用

        Args:
            text: AI 回复的文本

        Returns:
            [{"type": "paper", "title": "...", "id": "..."}]
        """
        # 使用简单的规则或正则提取
        # 更高级的实现可以使用 NER 模型
        # 这里简化处理
        return []
```

---

## 4. 提示词工程

### 4.1 提示词设计原则

1. **明确角色定位**: 使用 system message 定义 AI 的角色
2. **提供充足上下文**: 包含必要的背景信息
3. **结构化输出**: 要求 JSON 格式便于解析
4. **Few-shot 学习**: 提供示例（如需要）
5. **控制温度参数**:
   - 创意任务（总结、建议）: 0.7-0.9
   - 分析任务（评估、审稿）: 0.3-0.5
   - 结构化输出: 0.1-0.3

---

### 4.2 提示词模板库 (`api/prompts.py`)

```python
class PromptTemplates:
    SUMMARIZE_RESEARCH = """我正在调研「{query}」这个研究方向。

以下是相关的论文：

{papers}

请你：
1. 总结这个研究方向的核心内容
2. 列出主要的研究者和机构
3. 指出近期的研究趋势
4. 给出进一步学习的建议"""

    EVALUATE_IDEA = """我有一个研究想法：

「{idea}」

以下是相关的已有研究：

{related_papers}

请评估这个想法的可行性，并以 JSON 格式返回：
{{
  "understanding": "...",
  "feasibility_score": 0.8,
  "pros": ["...", "..."],
  "cons": ["...", "..."],
  "suggestions": ["...", "..."]
}}"""

    REVIEWER_PROFILE = """请为研究者「{name}」生成一个审稿人画像。

以下是 TA 发表的代表性论文：

{papers}

请分析：
1. TA 的主要研究方向和兴趣
2. TA 的研究风格
3. TA 可能看重的论文特质
4. TA 可能的审稿倾向"""

    GENERATE_REVIEW = """论文内容：

{paper_content}

请提供详细的审稿意见（JSON 格式）：
{{
  "strengths": ["...", "..."],
  "weaknesses": ["...", "..."],
  "suggestions": ["...", "..."],
  "overall_score": 7
}}"""
```

---

## 5. 多模型协作

### 5.1 场景：复杂任务分解

对于复杂任务（如论文打磨），可以使用多个 LLM 调用协作：

**流程**:
1. **模型 A**: 生成审稿人列表
2. **模型 B**: 为每个审稿人生成画像
3. **模型 C**: 基于画像生成审稿意见
4. **模型 D**: 基于审稿意见生成修改建议

**实现**:
```python
async def polish_paper_workflow(paper_content: str):
    llm = LLMService()

    # 步骤 1: 推荐审稿人
    reviewers = await get_reviewers_from_graph(paper_content)

    # 步骤 2: 生成画像（并发）
    profiles = await asyncio.gather(*[
        llm.generate_reviewer_profile(r['name'], r['papers'])
        for r in reviewers
    ])

    # 步骤 3: 生成审稿意见（并发）
    reviews = await asyncio.gather(*[
        llm.generate_review(paper_content, profile, r['name'])
        for r, profile in zip(reviewers, profiles)
    ])

    # 步骤 4: 生成修改建议
    suggestions = await llm.generate_paper_suggestions(paper_content, reviews)

    return {
        "reviewers": reviewers,
        "reviews": reviews,
        "suggestions": suggestions
    }
```

---

### 5.2 场景：多模型投票

对于关键决策（如可行性评估），可以使用多次调用取平均：

```python
def evaluate_idea_with_voting(idea: str, related_papers: List[Dict]) -> Dict:
    llm = LLMService()

    results = []
    for i in range(3):  # 3 次投票
        result = llm.evaluate_idea(idea, related_papers)
        results.append(result)

    # 平均评分
    avg_score = sum(r['feasibility_score'] for r in results) / len(results)

    # 合并优缺点
    all_pros = [p for r in results for p in r['pros']]
    all_cons = [c for r in results for c in r['cons']]

    return {
        "feasibility_score": avg_score,
        "pros": list(set(all_pros)),
        "cons": list(set(all_cons)),
        "suggestions": results[0]['suggestions']
    }
```

---

## 6. 成本优化

### 6.1 缓存策略

- **缓存相同问题的回答**: 使用 Redis 缓存
- **缓存键**: 基于 messages 的 MD5 哈希
- **TTL**: 7 天

---

### 6.2 上下文压缩

- 限制论文内容长度（8000 字符）
- 只包含摘要而非全文
- 使用摘要算法预处理

---

### 6.3 智能重试

```python
import time
from openai import OpenAIError

def chat_with_retry(llm: LLMService, messages: List[Dict], max_retries: int = 3):
    for attempt in range(max_retries):
        try:
            return llm.chat(messages)
        except OpenAIError as e:
            if attempt == max_retries - 1:
                raise
            time.sleep(2 ** attempt)  # 指数退避
```

---

## 7. 流式输出实现

### 7.1 FastAPI 端点

```python
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from typing import AsyncIterator

app = FastAPI()

async def stream_chat(message: str) -> AsyncIterator[str]:
    llm = LLMService()
    messages = [
        {"role": "user", "content": message}
    ]

    for chunk in llm.chat(messages, stream=True):
        yield f"data: {chunk}\n\n"

@app.get("/api/v1/chat/stream")
async def chat_stream(message: str):
    return StreamingResponse(
        stream_chat(message),
        media_type="text/event-stream"
    )
```

---

### 7.2 前端接收（JavaScript）

```javascript
const eventSource = new EventSource(`/api/v1/chat/stream?message=${query}`);

eventSource.onmessage = (event) => {
  const chunk = event.data;
  // 追加到界面
  document.getElementById('response').innerText += chunk;
};

eventSource.onerror = () => {
  eventSource.close();
};
```

---

## 8. 错误处理

### 8.1 常见错误

- **401 Unauthorized**: API Key 无效
- **429 Too Many Requests**: 请求频率超限
- **500 Internal Server Error**: API 服务故障
- **Timeout**: 请求超时

---

### 8.2 错误处理策略

```python
from openai import OpenAIError, RateLimitError, APIConnectionError

try:
    response = llm.chat(messages)
except RateLimitError:
    # 频率限制，等待后重试
    time.sleep(60)
    response = llm.chat(messages)
except APIConnectionError:
    # 网络错误，重试
    response = llm.chat(messages)
except OpenAIError as e:
    # 其他错误，降级处理
    logger.error(f"LLM error: {e}")
    response = "抱歉，AI 服务暂时不可用。"
```

---

## 9. 监控与日志

### 9.1 记录 API 调用

```python
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class LLMService:
    def chat(self, messages, **kwargs):
        start_time = datetime.now()

        try:
            response = self.client.chat.completions.create(...)

            # 记录成功调用
            logger.info(
                f"LLM call success | "
                f"tokens: {response.usage.total_tokens} | "
                f"time: {(datetime.now() - start_time).total_seconds()}s"
            )

            # 记录到数据库（用于成本分析）
            self._log_api_usage(
                user_id=kwargs.get('user_id'),
                tokens=response.usage.total_tokens,
                cost=self._calculate_cost(response.usage)
            )

            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM call failed: {e}")
            raise

    def _calculate_cost(self, usage):
        input_cost = usage.prompt_tokens / 1_000_000 * 0.27
        output_cost = usage.completion_tokens / 1_000_000 * 1.10
        return input_cost + output_cost
```

---

## 10. 测试

### 10.1 单元测试

```python
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def llm_service():
    return LLMService()

def test_generate_summary(llm_service):
    papers = [
        {
            "title": "Attention Is All You Need",
            "year": 2017,
            "authors": ["Vaswani et al."],
            "abstract": "..."
        }
    ]

    summary = llm_service.generate_summary(papers, "Transformer")

    assert len(summary) > 0
    assert "Transformer" in summary or "Attention" in summary

@patch('openai.OpenAI')
def test_chat_with_cache(mock_openai, llm_service):
    messages = [{"role": "user", "content": "Hello"}]

    # 第一次调用
    result1 = llm_service.chat(messages, use_cache=True)

    # 第二次调用（应该从缓存获取）
    result2 = llm_service.chat(messages, use_cache=True)

    assert result1 == result2
    # API 只应该被调用一次
    assert mock_openai.call_count == 1
```

---

## 11. 项目文件结构

```
api/
├── llm_service.py          # LLM 服务封装
├── prompts.py              # 提示词模板
├── workflows.py            # 多模型协作工作流
├── utils.py                # 工具函数（文本处理等）
├── tests/                  # 测试
│   ├── test_llm_service.py
│   └── test_workflows.py
├── examples/               # 示例代码
│   ├── basic_chat.py
│   ├── streaming.py
│   └── paper_polish.py
├── docs/                   # 文档
│   ├── prompt_engineering.md
│   └── cost_optimization.md
└── API_REQUIREMENTS.md     # 本文件
```

---

## 12. 最佳实践

### 12.1 提示词版本控制
- 将提示词存储在独立文件或数据库
- 使用版本号管理提示词变更
- A/B 测试不同提示词效果

### 12.2 上下文管理
- 使用对话历史但限制长度（最近 10 条消息）
- 超过限制时使用摘要算法压缩历史

### 12.3 安全性
- 过滤用户输入，防止提示词注入
- 不在提示词中泄露敏感信息
- API Key 使用环境变量，不硬编码

---

## 13. 待实现功能清单

### Phase 1（基础集成）
- [ ] LLMService 基础类
- [ ] 基本对话接口
- [ ] 缓存机制

### Phase 2（核心功能）
- [ ] 研究方向总结
- [ ] Idea 可行性评估
- [ ] 审稿人画像生成
- [ ] 审稿意见生成

### Phase 3（高级功能）
- [ ] 流式输出
- [ ] 多模型协作工作流
- [ ] 提示词版本管理

### Phase 4（优化）
- [ ] 成本监控
- [ ] 性能优化
- [ ] 错误处理完善
