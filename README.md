# 多Agent软件开发团队

基于 CrewAI 的多智能体协作系统，支持完整开发流程、单Agent对话、动态多Agent协作三种运行模式。

## 功能特性

| 模式 | 说明 |
|------|------|
| **完整开发流程** | 需求分析 → 架构设计 → 代码实现 → 代码审查，自动生成完整项目 |
| **单Agent聊天** | 与产品经理/架构师/开发者/审查员一对一对话，支持会话记忆 |
| **动态多Agent协作** | 根据问题类型自动调度最合适的Agent团队协作 |

### 核心亮点
- **Skill技能体系** - 标准化可插拔工具单元，支持 MCP 协议
- **记忆系统** - SQLite 持久化会话历史，支持会话 ID 隔离
- **用户输入标准化** - 口语化需求自动转结构化描述
- **问题类型分流** - 关键词识别自动路由到对应专家
- **中心化调度** - 智能任务规划与 Agent 编排
- **FastAPI 服务** - 提供 RESTful API 接口

## 目录结构

```
dev_team/
├── src/
│   ├── dev_team.py      # 主程序：三种运行模式入口
│   ├── memory.py        # 记忆系统（SQLite持久化+会话隔离）
│   ├── skills.py        # Skill体系（文件读写、需求分析等）
│   ├── api.py           # FastAPI后端服务
│   └── llm_client.py    # LLM客户端封装
├── .env                 # 环境变量（需自行配置API Key）
├── requirements.txt     # 依赖包
└── README.md
```

## 快速开始

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 配置环境变量
复制 `.env` 并填入真实 Key：
```env
# DeepSeek Chat模型
OPENAI_API_KEY=sk-xxx
OPENAI_BASE_URL=https://api.deepseek.com/v1
MODEL_NAME=deepseek-chat

# SiliconFlow Embedding（可选）
SILICONFLOW_API_KEY=sk-xxx
SILICONFLOW_BASE_URL=https://api.siliconflow.cn/v1

# 路径配置（默认D盘）
PROJECT_ROOT=D:\projects\dev_team
OUTPUT_DIR=D:\generated_outputs\dev_team
```

### 3. 运行

**CLI 交互模式**
```bash
python src/dev_team.py
```

**启动 API 服务**
```bash
python src/api.py
# 访问 http://localhost:8000/docs 查看 Swagger 文档
```

## 使用示例

### CLI 模式
```
请选择运行模式：
  1. 完整开发流程 - 自动生成完整项目
  2. 单Agent聊天 - 和指定角色一对一对话
  3. 动态多Agent协作 - 自动调度多个Agent完成复杂任务
```

### API 调用

**动态多Agent协作**
```bash
curl -X POST http://localhost:8000/api/chat/dynamic \
  -H "Content-Type: application/json" \
  -d '{"user_input": "设计一个用户登录系统，包含需求、架构和代码"}'
```

**单Agent聊天**
```bash
curl -X POST http://localhost:8000/api/chat/single/developer \
  -H "Content-Type: application/json" \
  -d '{"user_input": "帮我写一个FastAPI中间件"}'
```

**完整开发流程**
```bash
curl -X POST http://localhost:8000/api/develop \
  -H "Content-Type: application/json" \
  -d '{"user_input": "开发一个待办事项管理工具"}'
```

## 输出产物

所有生成文件保存至 `OUTPUT_DIR`（默认 `D:\generated_outputs\dev_team`）：
```
generated_outputs/dev_team/
├── prd.md              # 产品需求文档
├── architecture.md     # 架构设计文档
├── src/main.py         # 生成的项目代码
├── review_report.md    # 代码审查报告
└── memory/             # 会话记忆数据库
```

## 依赖说明

核心依赖：
- `crewai>=0.28.8` - 多Agent编排框架
- `langchain>=0.1.10` - LLM应用开发框架
- `fastapi>=0.109.0` - Web API框架
- `uvicorn>=0.27.0` - ASGI服务器
- `python-dotenv>=1.0.0` - 环境变量管理

完整列表见 `requirements.txt`。

## 许可证

MIT License