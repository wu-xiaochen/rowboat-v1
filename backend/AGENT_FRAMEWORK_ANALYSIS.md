# Rowboat 多 Agent 框架深度分析

## 一、原项目 Rowboat 使用的框架

### 1.1 框架概述

原项目 Rowboat 使用的是 **OpenAI Agent SDK**，有两个版本：
- **JavaScript/TypeScript版本**：`@openai/agents` (v0.0.15)
- **Python版本**：`openai-agents` (最新版本)

**重要发现**：OpenAI Agent SDK **原生支持 Python**，有完整的 Python SDK。

**官方文档**：https://openai.github.io/openai-agents-python/quickstart/

### 1.2 Python版本核心特性

#### 1.2.1 Agent（智能体）

```python
from agents import Agent

agent = Agent(
    name="Math Tutor",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
    handoff_description="Specialist agent for math questions",  # 可选
    model_config={...},  # 可选
)
```

**特点**：
- ✅ 简单的Agent定义
- ✅ 支持instructions（指令）
- ✅ 支持handoff_description（移交描述）
- ✅ 支持model_config（模型配置）

#### 1.2.2 Handoff（移交）

```python
from agents import Agent

# 创建多个agents
history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries.",
)

math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You provide help with math problems.",
)

# 定义handoff
triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_tutor_agent, math_tutor_agent]  # 定义handoff选项
)
```

**特点**：
- ✅ 原生支持handoff
- ✅ 简单的handoff定义
- ✅ 自动路由到合适的agent
- ✅ 支持handoff_description用于路由决策

#### 1.2.3 Runner（运行器）

```python
from agents import Runner

# 运行agent
async def main():
    result = await Runner.run(triage_agent, "What is the capital of France?")
    print(result.final_output)
    
    # 流式运行
    async for event in Runner.stream(triage_agent, "What is the capital of France?"):
        print(event)
```

**特点**：
- ✅ 简单的运行接口
- ✅ 支持异步运行
- ✅ 支持流式响应
- ✅ 支持上下文管理

#### 1.2.4 Guardrails（护栏）

```python
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from agents.exceptions import InputGuardrailTripwireTriggered
from pydantic import BaseModel

class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,
)

async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )

# 添加guardrail到agent
triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_tutor_agent, math_tutor_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=homework_guardrail),
    ],
)
```

**特点**：
- ✅ 支持输入guardrail
- ✅ 支持输出guardrail
- ✅ 支持自定义验证逻辑
- ✅ 支持结构化输出验证

#### 1.2.5 Tools（工具）

```python
from agents import Agent, Tool

# 创建工具
def search_tool(query: str) -> str:
    """Search for information"""
    return f"Search results for: {query}"

tool = Tool(
    name="search",
    description="Search for information",
    function=search_tool,
)

# 将工具添加到agent
agent = Agent(
    name="Research Agent",
    instructions="You are a research assistant.",
    tools=[tool],
)
```

**特点**：
- ✅ 支持工具定义
- ✅ 支持工具调用
- ✅ 支持异步工具
- ✅ 支持工具上下文

#### 1.2.6 Streaming（流式响应）

```python
from agents import Runner

# 流式运行
async for event in Runner.stream(agent, input_data):
    if event.type == "agent_start":
        print(f"Agent {event.agent_name} started")
    elif event.type == "agent_output":
        print(f"Output: {event.output}")
    elif event.type == "handoff":
        print(f"Handoff to {event.target_agent}")
    elif event.type == "agent_complete":
        print(f"Agent {event.agent_name} completed")
```

**特点**：
- ✅ 支持流式响应
- ✅ 支持事件流
- ✅ 支持handoff事件
- ✅ 支持工具调用事件

#### 1.2.7 Context Management（上下文管理）

```python
from agents import Runner

# 使用上下文
result = await Runner.run(
    agent,
    input_data,
    context={
        "user_id": "123",
        "session_id": "abc",
        "custom_data": {...},
    }
)
```

**特点**：
- ✅ 支持上下文传递
- ✅ 支持会话管理
- ✅ 支持自定义上下文数据

#### 1.2.8 Tracing（跟踪）

```python
# 自动跟踪到OpenAI Dashboard
# 可以在OpenAI Dashboard中查看traces
```

**特点**：
- ✅ 自动跟踪
- ✅ 集成OpenAI Dashboard
- ✅ 支持trace查看
- ✅ 支持性能分析

### 1.3 工作流程

```
1. 创建Agents
   ↓
2. 定义Handoffs
   ↓
3. 添加Tools（可选）
   ↓
4. 添加Guardrails（可选）
   ↓
5. 运行Agent（Runner.run或Runner.stream）
   ↓
6. 处理事件流（流式响应）
   ↓
7. 返回结果
```

### 1.4 优势

1. **原生Python支持**：OpenAI Agent SDK原生支持Python
2. **官方支持**：由OpenAI官方维护，持续更新
3. **功能完善**：支持handoff、guardrails、tools、streaming等
4. **简单易用**：API设计简单，易于使用
5. **流式响应**：完善的流式响应支持
6. **跟踪和可观察性**：集成OpenAI Dashboard，支持trace查看
7. **文档完善**：官方文档完善，示例丰富

### 1.5 与原项目Rowboat的兼容性

原项目Rowboat使用的是JavaScript/TypeScript版本的OpenAI Agent SDK，但核心概念和功能与Python版本一致：

1. **Agent定义**：概念一致，API类似
2. **Handoff机制**：概念一致，实现方式类似
3. **Pipeline支持**：Python版本可能通过handoff序列实现
4. **工具集成**：都支持工具集成
5. **流式响应**：都支持流式响应

---

## 二、CrewAI 框架分析（对比参考）

### 2.1 框架概述

CrewAI是一个成熟的Python多Agent协作框架，专门设计用于复杂的多Agent协作场景。

### 2.2 核心特性

#### 2.2.1 Agent（代理）

```python
from crewai import Agent

researcher = Agent(
    role='研究员',
    goal='收集并分析指定主题的信息',
    backstory='你是一位经验丰富的研究员，擅长收集和分析信息。',
    tools=[search_tool, rag_tool],
    verbose=True,
    allow_delegation=True,
)
```

#### 2.2.2 Task（任务）

```python
from crewai import Task

research_task = Task(
    description='研究并总结最新的人工智能发展趋势',
    agent=researcher,
    expected_output='一份详细的研究报告',
)
```

#### 2.2.3 Crew（团队）

```python
from crewai import Crew

crew = Crew(
    agents=[researcher, writer, reviewer],
    tasks=[research_task, writing_task, review_task],
    verbose=True,
    process="sequential",
)
```

### 2.3 优势

1. **成熟框架**：框架成熟，文档完善，社区活跃
2. **任务导向**：任务导向的设计，适合复杂的多Agent协作
3. **生态系统**：丰富的生态系统和工具集成

### 2.4 劣势（针对本项目）

1. **Handoff支持**：没有原生支持的handoff功能，需要自己实现
2. **Pipeline支持**：Pipeline支持可能不如OpenAI Agent SDK强大
3. **流式响应**：流式响应支持可能不如OpenAI Agent SDK完善
4. **官方支持**：不是OpenAI官方框架，可能与OpenAI生态系统集成不够紧密

---

## 三、对比分析

### 3.1 功能对比

| 功能 | OpenAI Agent SDK Python | CrewAI |
|------|------------------------|--------|
| **Agent Handoff** | ✅ 原生支持 | ❌ 需要自己实现 |
| **Pipeline** | ✅ 支持（通过handoff序列） | ⚠️ 部分支持（通过sequential process） |
| **工具集成** | ✅ 良好支持 | ✅ 良好支持 |
| **RAG 集成** | ✅ 支持（通过工具） | ✅ 支持 |
| **流式响应** | ✅ 完善支持 | ⚠️ 部分支持 |
| **Guardrails** | ✅ 原生支持 | ❌ 需要自己实现 |
| **上下文管理** | ✅ 支持 | ⚠️ 部分支持 |
| **跟踪和可观察性** | ✅ 集成OpenAI Dashboard | ⚠️ 需要自己实现 |
| **Python 支持** | ✅ 原生支持 | ✅ 原生支持 |
| **官方支持** | ✅ OpenAI官方 | ❌ 第三方框架 |
| **文档和社区** | ✅ 官方文档完善 | ✅ 社区活跃 |

### 3.2 适用场景对比

#### OpenAI Agent SDK Python 适合：

1. **原生handoff支持**：需要复杂的agent handoff场景
2. **Pipeline执行**：需要严格的顺序执行和多步骤流程
3. **实时响应**：需要流式响应和实时交互
4. **OpenAI生态系统**：需要与OpenAI生态系统紧密集成
5. **Guardrails验证**：需要输入输出验证
6. **跟踪和可观察性**：需要完善的跟踪和可观察性

#### CrewAI 适合：

1. **任务导向的协作**：需要明确的任务分配和协调
2. **团队协作**：需要团队协作和任务协调
3. **成熟的生态系统**：需要丰富的工具和集成
4. **学习和开发**：需要完善的文档和社区支持

### 3.3 迁移难度对比

#### 从原项目Rowboat（JavaScript版本）迁移到OpenAI Agent SDK Python：

- **难度**：⭐⭐（较低）
- **原因**：
  - 核心概念一致
  - API设计类似
  - 功能对应关系明确
  - 只需适配Python语法

#### 从原项目Rowboat迁移到CrewAI：

- **难度**：⭐⭐⭐⭐（较高）
- **原因**：
  - 需要重新设计agent交互模式
  - 需要实现handoff功能
  - 需要重新实现pipeline逻辑
  - 需要重新实现控制权管理

---

## 四、推荐方案

### 4.1 针对Rowboat项目的建议

#### 方案：使用OpenAI Agent SDK Python版本（强烈推荐）

**理由**：
1. ✅ **原生Python支持**：OpenAI Agent SDK原生支持Python
2. ✅ **官方支持**：由OpenAI官方维护，持续更新
3. ✅ **功能完善**：支持handoff、guardrails、tools、streaming等
4. ✅ **兼容性好**：与原项目Rowboat的JavaScript版本核心概念一致
5. ✅ **迁移简单**：迁移难度较低，只需适配Python语法
6. ✅ **流式响应**：完善的流式响应支持
7. ✅ **跟踪和可观察性**：集成OpenAI Dashboard，支持trace查看
8. ✅ **文档完善**：官方文档完善，示例丰富

**实施思路**：
1. 使用OpenAI Agent SDK Python版本创建agents
2. 使用handoff机制实现agent间交互
3. 使用handoff序列实现pipeline执行
4. 使用guardrails实现输入输出验证
5. 使用Runner.stream实现流式响应
6. 使用context实现上下文管理

**优势**：
- 保持与原项目Rowboat的兼容性
- 利用OpenAI官方框架的优势
- 迁移难度较低
- 功能完善，易于维护

**劣势**：
- 相对较新的框架，可能需要适应新的API
- 文档可能不如CrewAI丰富（但官方文档已经很完善）

### 4.2 实施步骤

1. **阶段一：基础实现**
   - 安装OpenAI Agent SDK Python版本
   - 实现单个agent创建
   - 实现工具集成（RAG、Composio等）
   - 实现流式响应

2. **阶段二：Handoff实现**
   - 实现agent handoff逻辑
   - 实现控制权管理
   - 实现agent调用栈管理

3. **阶段三：Pipeline实现**
   - 实现pipeline执行逻辑（通过handoff序列）
   - 实现pipeline状态管理
   - 实现pipeline数据传递

4. **阶段四：Guardrails实现**
   - 实现输入guardrails
   - 实现输出guardrails
   - 实现自定义验证逻辑

5. **阶段五：优化和测试**
   - 优化性能
   - 完善错误处理
   - 完善测试覆盖
   - 完善文档

### 4.3 注意事项

1. **保持兼容性**：确保与前端API兼容
2. **性能优化**：注意性能优化，避免阻塞
3. **错误处理**：完善错误处理，确保稳定性
4. **测试覆盖**：完善测试覆盖，确保质量
5. **文档完善**：完善文档，便于维护
6. **跟踪和可观察性**：利用OpenAI Dashboard进行跟踪和可观察性

---

## 五、具体实现建议

### 5.1 使用OpenAI Agent SDK Python版本

#### 5.1.1 Agent创建

```python
from agents import Agent
from app.models.schemas import WorkflowAgent, WorkflowTool

def create_agent(agent_config: WorkflowAgent, tools: list) -> Agent:
    """创建Agent"""
    return Agent(
        name=agent_config.name,
        instructions=agent_config.instructions,
        handoff_description=agent_config.description,
        tools=tools,
        model_config={
            "model": agent_config.model,
            "temperature": 0.7,
        },
    )
```

#### 5.1.2 Handoff实现

```python
from agents import Agent

# 创建多个agents
agents = {}
for agent_config in workflow.agents:
    agent = create_agent(agent_config, tools)
    agents[agent_config.name] = agent

# 定义handoffs
for agent_config in workflow.agents:
    agent = agents[agent_config.name]
    # 找到可以handoff的agents
    handoff_agents = [
        agents[name] for name in get_handoff_agent_names(agent_config, workflow)
    ]
    agent.handoffs = handoff_agents
```

#### 5.1.3 Pipeline实现

```python
from agents import Agent, Runner

# Pipeline通过handoff序列实现
async def execute_pipeline(pipeline: WorkflowPipeline, agents: dict, input_data: str):
    """执行Pipeline"""
    # 从第一个agent开始
    current_agent = agents[pipeline.agents[0]]
    context = {"pipeline_data": {}}
    
    # 依次执行每个agent
    for agent_name in pipeline.agents:
        agent = agents[agent_name]
        result = await Runner.run(agent, input_data, context=context)
        context["pipeline_data"][agent_name] = result.final_output
        input_data = result.final_output
    
    return context["pipeline_data"]
```

#### 5.1.4 流式响应实现

```python
from agents import Runner

async def stream_agent_response(agent: Agent, input_data: str, context: dict):
    """流式响应"""
    async for event in Runner.stream(agent, input_data, context=context):
        if event.type == "agent_output":
            yield {
                "type": "message",
                "data": {
                    "role": "assistant",
                    "content": event.output,
                    "agent_name": agent.name,
                },
            }
        elif event.type == "handoff":
            yield {
                "type": "handoff",
                "data": {
                    "from_agent": event.from_agent,
                    "to_agent": event.to_agent,
                },
            }
        elif event.type == "tool_call":
            yield {
                "type": "tool_call",
                "data": {
                    "tool_name": event.tool_name,
                    "tool_args": event.tool_args,
                },
            }
```

#### 5.1.5 Guardrails实现

```python
from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from pydantic import BaseModel

class ValidationOutput(BaseModel):
    is_valid: bool
    reasoning: str

guardrail_agent = Agent(
    name="Validation Agent",
    instructions="Validate the input data.",
    output_type=ValidationOutput,
)

async def input_guardrail(ctx, agent, input_data):
    """输入Guardrail"""
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(ValidationOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_valid,
    )

# 添加guardrail到agent
agent.input_guardrails = [
    InputGuardrail(guardrail_function=input_guardrail),
]
```

### 5.2 工具集成

#### 5.2.1 RAG工具

```python
from agents import Tool
from app.services.rag.rag_service import get_rag_service

async def rag_search_tool(query: str) -> str:
    """RAG搜索工具"""
    rag_service = get_rag_service()
    results = await rag_service.search(
        project_id=project_id,
        query=query,
        source_ids=source_ids,
        k=3,
    )
    return json.dumps([r.model_dump() for r in results], ensure_ascii=False)

rag_tool = Tool(
    name="rag_search",
    description="Search for relevant documents using RAG",
    function=rag_search_tool,
)
```

#### 5.2.2 Composio工具

```python
from agents import Tool
from app.services.composio.composio_service import get_composio_service

async def composio_tool(tool_name: str, **kwargs) -> str:
    """Composio工具"""
    composio_service = get_composio_service()
    # 调用Composio工具
    result = await composio_service.execute_tool(tool_name, **kwargs)
    return json.dumps(result, ensure_ascii=False)

composio_tool = Tool(
    name="composio_tool",
    description="Execute Composio tool",
    function=composio_tool,
)
```

---

## 六、总结

### 6.1 原项目框架特点

- **OpenAI Agent SDK**：原生支持handoff和pipeline，灵活性高
- **JavaScript/TypeScript版本**：原项目使用JS/TS版本
- **Python版本**：OpenAI Agent SDK原生支持Python

### 6.2 迁移建议

- **推荐方案**：使用OpenAI Agent SDK Python版本
- **理由**：原生Python支持，官方维护，功能完善，兼容性好，迁移简单
- **实施步骤**：分阶段实施，逐步完善

### 6.3 后续工作

1. 安装OpenAI Agent SDK Python版本
2. 实现agent创建和handoff逻辑
3. 实现pipeline执行逻辑
4. 实现guardrails验证
5. 实现流式响应
6. 完善测试和文档

---

**文档版本**：v2.0  
**创建日期**：2025-01-27  
**最后更新**：2025-01-27  
**重要更新**：确认OpenAI Agent SDK原生支持Python，推荐使用Python版本
