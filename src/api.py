"""
FastAPI后端服务模块（功能亮点10）
提供多Agent开发团队的API接口
"""
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict
import uvicorn
import uuid

from dev_team import SimpleDevTeam, DynamicAgentTeam
from memory import ConversationMemory
from skills import SkillManager, create_default_skill_manager

# 初始化FastAPI应用
app = FastAPI(title="多Agent开发团队API", version="3.0")

# 全局实例
memory = ConversationMemory()
skill_manager = create_default_skill_manager()

# 数据模型
class UserRequest(BaseModel):
    """用户请求模型"""
    user_input: str
    session_id: Optional[str] = None

class AgentResponse(BaseModel):
    """Agent响应模型"""
    session_id: str
    response: str
    agents_involved: List[str]
    timestamp: str

# API路由
@app.get("/")
async def root():
    """根路由"""
    return {
        "title": "多Agent开发团队API",
        "version": "3.0",
        "endpoints": [
            "/api/sessions - 获取所有会话",
            "/api/chat/single/{agent_type} - 单Agent聊天",
            "/api/chat/dynamic - 动态多Agent协作",
            "/api/develop - 完整开发流程",
            "/api/skills - 获取所有可用Skill",
            "/api/memory/{session_id} - 获取会话记忆"
        ]
    }

@app.get("/api/sessions")
async def get_sessions():
    """获取所有会话ID"""
    sessions = memory.get_all_sessions()
    return {"sessions": sessions}

@app.get("/api/memory/{session_id}")
async def get_session_memory(session_id: str):
    """获取指定会话的记忆"""
    if not memory.get_session(session_id):
        raise HTTPException(status_code=404, detail="会话不存在")
    
    messages = memory.get_messages(session_id)
    return {
        "session_id": session_id,
        "messages": messages
    }

@app.post("/api/chat/dynamic", response_model=AgentResponse)
async def dynamic_chat(request: UserRequest):
    """动态多Agent协作聊天"""
    # 生成会话ID
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    # 运行动态Agent团队
    team = DynamicAgentTeam()
    team.session_id = session_id
    
    # 执行任务
    response = team.run(request.user_input)
    
    return {
        "session_id": session_id,
        "response": response,
        "agents_involved": ["产品经理", "架构师", "开发者", "代码审查专家"],
        "timestamp": str(memory.get_session(session_id)["last_active"])
    }

@app.post("/api/chat/single/{agent_type}")
async def single_chat(agent_type: str, request: UserRequest):
    """单Agent聊天"""
    agent_types = {
        "pm": "产品经理",
        "architect": "架构师",
        "developer": "开发者",
        "reviewer": "代码审查专家"
    }
    
    if agent_type not in agent_types:
        raise HTTPException(status_code=400, detail="无效的Agent类型")
    
    # 生成会话ID
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    # 简化版单Agent响应
    from llm_client import LLMClient
    llm = LLMClient()
    
    prompts = {
        "pm": """你是一位经验丰富的产品经理，擅长分析用户需求和编写PRD。""",
        "architect": """你是一位资深系统架构师，擅长设计系统架构和技术选型。""",
        "developer": """你是一位技术精湛的开发工程师，擅长编写高质量代码。""",
        "reviewer": """你是一位严格的代码审查专家，擅长发现代码问题并给出改进建议。"""
    }
    
    response = llm.chat_with_system(prompts[agent_type], request.user_input)
    
    # 记录到记忆系统
    if not memory.get_session(session_id):
        memory.create_session(session_id, f"单Agent聊天-{agent_types[agent_type]}")
    
    memory.add_message(
        session_id=session_id,
        role="user",
        content=request.user_input,
        agent_name=agent_types[agent_type]
    )
    
    memory.add_message(
        session_id=session_id,
        role="assistant",
        content=response,
        agent_name=agent_types[agent_type]
    )
    
    return {
        "session_id": session_id,
        "agent_type": agent_types[agent_type],
        "response": response,
        "timestamp": str(memory.get_session(session_id)["last_active"])
    }

@app.post("/api/develop")
async def develop_project(request: UserRequest):
    """完整开发流程"""
    # 生成会话ID
    session_id = request.session_id or f"session_{uuid.uuid4().hex[:8]}"
    
    # 运行简化版开发团队
    team = SimpleDevTeam()
    team.session_id = session_id
    team.run(request.user_input)
    
    return {
        "session_id": session_id,
        "status": "completed",
        "output_dir": "D:\\generated_outputs\\dev_team",
        "files": [
            "prd.md",
            "architecture.md",
            "src/main.py",
            "review_report.md"
        ],
        "timestamp": str(memory.get_session(session_id)["last_active"])
    }

@app.get("/api/skills")
async def get_skills():
    """获取所有可用Skill"""
    skills = skill_manager.list_skills()
    mcp_specs = skill_manager.get_mcp_specs()
    
    return {
        "skills": skills,
        "mcp_specifications": mcp_specs
    }

# 启动服务器
def run_api():
    """启动FastAPI服务器"""
    uvicorn.run(
        "api:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )

if __name__ == "__main__":
    run_api()