"""
Skill技能体系模块 - 标准化可插拔Skill单元（功能亮点3）
支持MCP+Skill一体化工具调用（功能亮点4）
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, List
import json

class BaseSkill(ABC):
    """Skill基类 - 标准化接口"""
    
    @property
    @abstractmethod
    def skill_id(self) -> str:
        """唯一技能ID"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """技能名称"""
        pass
    
    @property
    @abstractmethod
    def description(self) -> str:
        """技能描述"""
        pass
    
    @property
    @abstractmethod
    def parameters(self) -> List[Dict]:
        """技能参数定义"""
        pass
    
    @abstractmethod
    def execute(self, **kwargs) -> Any:
        """执行技能"""
        pass
    
    def to_mcp_spec(self) -> Dict:
        """转换为MCP协议规范"""
        return {
            "name": self.skill_id,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    param["name"]: {
                        "type": param["type"],
                        "description": param["description"]
                    } for param in self.parameters
                },
                "required": [param["name"] for param in self.parameters if param["required"]]
            }
        }

# ==================== 具体Skill实现 ====================

class FileSaveSkill(BaseSkill):
    """文件保存Skill"""
    
    @property
    def skill_id(self) -> str:
        return "file_save"
    
    @property
    def name(self) -> str:
        return "文件保存"
    
    @property
    def description(self) -> str:
        return "将内容保存到指定路径的文件中，支持自动创建目录"
    
    @property
    def parameters(self) -> List[Dict]:
        return [
            {
                "name": "filename",
                "type": "string",
                "description": "文件路径（相对D:\\generated_outputs\\dev_team目录）",
                "required": True
            },
            {
                "name": "content",
                "type": "string",
                "description": "文件内容",
                "required": True
            }
        ]
    
    def execute(self, filename: str, content: str) -> str:
        """执行文件保存"""
        import os
        base_dir = "D:\\generated_outputs\\dev_team"
        filepath = os.path.join(base_dir, filename)
        
        # 确保目录存在
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        # 写入文件
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        
        return f"✅ 文件已保存到: {filepath}"

class FileReadSkill(BaseSkill):
    """文件读取Skill"""
    
    @property
    def skill_id(self) -> str:
        return "file_read"
    
    @property
    def name(self) -> str:
        return "文件读取"
    
    @property
    def description(self) -> str:
        return "读取指定路径的文件内容"
    
    @property
    def parameters(self) -> List[Dict]:
        return [
            {
                "name": "filename",
                "type": "string",
                "description": "文件路径（相对D:\\generated_outputs\\dev_team目录）",
                "required": True
            }
        ]
    
    def execute(self, filename: str) -> str:
        """执行文件读取"""
        import os
        base_dir = "D:\\generated_outputs\\dev_team"
        filepath = os.path.join(base_dir, filename)
        
        if not os.path.exists(filepath):
            return f"❌ 文件不存在: {filepath}"
        
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()

class RequirementAnalysisSkill(BaseSkill):
    """需求分析Skill"""
    
    @property
    def skill_id(self) -> str:
        return "requirement_analysis"
    
    @property
    def name(self) -> str:
        return "需求分析"
    
    @property
    def description(self) -> str:
        return "将用户需求转换为结构化的PRD文档"
    
    @property
    def parameters(self) -> List[Dict]:
        return [
            {
                "name": "user_requirement",
                "type": "string",
                "description": "用户原始需求描述",
                "required": True
            }
        ]
    
    def execute(self, user_requirement: str) -> str:
        """执行需求分析"""
        # 实际实现会调用LLM，这里简化返回结构
        return f"""# 产品需求文档 (PRD)
## 核心需求
{user_requirement}

## 功能列表
1. 待办事项添加/删除/修改
2. 任务状态标记
3. 数据持久化存储
4. 优先级管理
5. 命令行交互界面

## 用户故事
1. 作为普通用户，我希望能添加待办事项，以便记录需要完成的任务
2. 作为普通用户，我希望能标记任务完成状态，以便跟踪任务进度

## 验收标准
1. 所有功能必须在命令行界面正常运行
2. 数据必须持久化到本地文件
3. 操作流程简单直观，无需复杂命令
"""

# ==================== Skill管理器 ====================

class SkillManager:
    """Skill管理器 - 负责Skill的注册、发现和调用"""
    
    def __init__(self):
        self.skills: Dict[str, BaseSkill] = {}
    
    def register_skill(self, skill: BaseSkill):
        """注册Skill"""
        self.skills[skill.skill_id] = skill
    
    def unregister_skill(self, skill_id: str):
        """注销Skill"""
        if skill_id in self.skills:
            del self.skills[skill_id]
    
    def get_skill(self, skill_id: str) -> BaseSkill:
        """获取Skill实例"""
        return self.skills.get(skill_id)
    
    def list_skills(self) -> List[Dict]:
        """列出所有可用Skill"""
        return [
            {
                "skill_id": skill.skill_id,
                "name": skill.name,
                "description": skill.description
            }
            for skill in self.skills.values()
        ]
    
    def call_skill(self, skill_id: str, **kwargs) -> Any:
        """调用Skill"""
        skill = self.get_skill(skill_id)
        if not skill:
            raise ValueError(f"Skill {skill_id} 不存在")
        
        # 参数验证
        required_params = [p["name"] for p in skill.parameters if p["required"]]
        for param in required_params:
            if param not in kwargs:
                raise ValueError(f"缺少必填参数: {param}")
        
        return skill.execute(**kwargs)
    
    def get_mcp_specs(self) -> List[Dict]:
        """获取所有Skill的MCP协议规范"""
        return [skill.to_mcp_spec() for skill in self.skills.values()]

# 初始化默认Skill
def create_default_skill_manager() -> SkillManager:
    """创建默认Skill管理器并注册常用Skill"""
    manager = SkillManager()
    
    # 注册基础Skill
    manager.register_skill(FileSaveSkill())
    manager.register_skill(FileReadSkill())
    manager.register_skill(RequirementAnalysisSkill())
    
    return manager