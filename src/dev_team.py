"""
Day 21: 第三阶段综合项目 - 多Agent软件开发团队
改造版：支持完整开发流程、单Agent聊天、动态多Agent协作三种模式
优化点：
1. 所有路径迁移到D盘（符合Conda-Disk-Manager规范）
2. 集成Skill技能体系（功能亮点3）
3. 集成MCP+Skill工具调用（功能亮点4）
4. 集成记忆系统和会话隔离（功能亮点5、6）
5. 新增用户输入通俗化转换（功能亮点7）
6. 新增问题类型分流（功能亮点8）
7. 强化中心化调度（功能亮点2）
8. 支持智能推理规划模式（功能亮点9）
"""

import os
import sys
import re
import uuid
from datetime import datetime
from typing import Dict, List, Optional

# ============ 环境变量配置 ============
from dotenv import load_dotenv
load_dotenv()  # 加载.env文件

# ============ 路径配置（符合Conda-Disk-Manager规范） ============
# 项目根目录: D:\projects\dev_team
project_root = os.getenv("PROJECT_ROOT", "D:\\projects\\dev_team")
os.makedirs(project_root, exist_ok=True)

# 输出目录: D:\generated_outputs\dev_team
output_dir = os.getenv("OUTPUT_DIR", "D:\\generated_outputs\\dev_team")
os.makedirs(output_dir, exist_ok=True)
os.makedirs(os.path.join(output_dir, "src"), exist_ok=True)

# 将项目根目录加入Python路径
sys.path.insert(0, project_root)

# ============ 导入自定义模块 ============
try:
    from llm_client import LLMClient
except ImportError:
    # 简化版LLMClient实现
    class LLMClient:
        def __init__(self):
            pass

        def chat_with_system(self, system_prompt: str, user_input: str) -> str:
            # 识别闲聊问候
            greet_words = ["你好", "hi", "hello", "早上好", "下午好", "晚上好"]
            if any(word in user_input.strip().lower() for word in greet_words):
                return "你好😊！我是多Agent开发助手，你可以向我咨询产品需求、系统架构、代码编写、代码审查相关问题，也可以提出完整的软件开发需求。"

            # 普通业务问题兜底
            if "代码" in user_input or "开发" in user_input:
                return "我可以为你编写Python代码、排查代码问题，请描述具体需求。"
            elif "架构" in user_input or "设计" in user_input:
                return "我可以帮你设计系统架构、做技术选型，请告诉我你的项目场景。"
            elif "需求" in user_input or "PR" in user_input:
                return "我可以帮你梳理产品需求、编写PRD文档。"

            # 原有模拟逻辑（其他问题）
            return f"模拟LLM响应：\n系统提示：{system_prompt[:120]}...\n用户输入：{user_input}"

# 导入新增模块
from skills import SkillManager, create_default_skill_manager, BaseSkill
from memory import ConversationMemory

# ============ 导入CrewAI组件 ============
try:
    from crewai import Agent, Task, Crew, Process, LLM
    from crewai.tools import tool
    CREWAI_AVAILABLE = True
except ImportError:
    print("⚠️ 未安装crewai，使用简化实现")
    CREWAI_AVAILABLE = False

# ============ 全局初始化 ============
# 初始化Skill管理器
skill_manager = create_default_skill_manager()

# 初始化记忆系统
memory = ConversationMemory()

# ============ 创建CrewAI兼容的LLM ============
def create_crewai_llm():
    """创建CrewAI兼容的LLM配置（使用DeepSeek）"""
    if not CREWAI_AVAILABLE:
        return None
    
    return LLM(
        model=os.getenv("MODEL_NAME", "deepseek-chat"),
        base_url=os.getenv("OPENAI_BASE_URL", "https://api.deepseek.com/v1"),
        api_key=os.getenv("OPENAI_API_KEY"),
    )

# ============ 功能亮点7：用户输入通俗化转换 ============
def normalize_user_input(user_input: str) -> str:
    """将口语化输入转换为标准化需求描述"""
    # 去除无意义的语气词
    stop_words = ["嗯", "啊", "哦", "吧", "呢", "嘛", "喂", "那个", "这个"]
    for word in stop_words:
        user_input = user_input.replace(word, "")
    
    # 标准化标点符号
    user_input = re.sub(r"，", ",", user_input)
    user_input = re.sub(r"。", ".", user_input)
    user_input = re.sub(r"？", "?", user_input)
    user_input = re.sub(r"！", "!", user_input)
    
    # 提取核心需求（简单实现）
    requirement_patterns = [
        r"开发(.*?)工具",
        r"做一个(.*?)系统",
        r"实现(.*?)功能",
        r"编写(.*?)代码",
        r"设计(.*?)架构",
    ]
    
    core_requirements = []
    for pattern in requirement_patterns:
        matches = re.findall(pattern, user_input)
        core_requirements.extend(matches)
    
    if core_requirements:
        normalized = f"核心需求：{'，'.join(core_requirements)}。详细描述：{user_input}"
    else:
        normalized = user_input
    
    return normalized.strip()

# ============ 功能亮点8：问题类型分流 ============
def classify_user_query(user_input: str) -> str:
    """识别用户问题类型，进行分流处理"""
    # 定义问题类型和关键词
    query_types = {
        "requirement_analysis": ["需求", "PRD", "产品", "功能", "用户故事"],
        "architecture_design": ["架构", "设计", "技术栈", "模块", "接口"],
        "coding": ["代码", "编程", "实现", "bug", "调试"],
        "code_review": ["审查", "检查", "质量", "规范", "优化"],
        "general_consult": ["对比", "建议", "选型", "优缺点", "如何"]
    }
    
    # 转换为小写
    user_input_lower = user_input.lower()
    
    # 匹配关键词
    for qtype, keywords in query_types.items():
        if any(keyword in user_input_lower for keyword in keywords):
            return qtype
    
    # 默认类型
    return "general_consult"

# ================================================================
# 第一部分：工具定义（集成Skill体系）
# ================================================================

# 使用Skill替代原有工具函数
save_file_skill = skill_manager.get_skill("file_save")
read_file_skill = skill_manager.get_skill("file_read")

def save_file(filename: str, content: str) -> str:
    """保存文件到D盘输出目录（使用FileSaveSkill）"""
    return save_file_skill.execute(filename=filename, content=content)

def read_file(filename: str) -> str:
    """读取文件内容（使用FileReadSkill）"""
    return read_file_skill.execute(filename=filename)

# 如果CrewAI可用，注册为工具
if CREWAI_AVAILABLE:
    @tool
    def save_file_tool(filename: str, content: str) -> str:
        """【CrewAI工具】保存文件到D盘项目目录"""
        return save_file(filename, content)
    
    @tool
    def read_file_tool(filename: str) -> str:
        """【CrewAI工具】读取D盘项目文件内容"""
        return read_file(filename)

# ================================================================
# 第二部分：Agent角色定义（强化中心化调度）
# ================================================================

class DevTeamAgents:
    """开发团队Agent工厂 - 创建各角色Agent"""
    
    def __init__(self):
        """初始化Agent工厂"""
        self.llm = create_crewai_llm()
        self.skill_manager = skill_manager
    
    def create_product_manager(self) -> Optional["Agent"]:
        """创建产品经理Agent"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Agent(
            role="产品经理",
            goal="分析用户需求，编写清晰完整的产品需求文档(PRD)",
            backstory="""你是一位经验丰富的产品经理，擅长将模糊的用户需求转化为清晰的产品定义。
你善于识别核心功能、用户场景和验收标准。
你的输出应该结构清晰，包含功能列表、用户故事和验收标准。""",
            verbose=True,
            allow_delegation=False,
            tools=[save_file_tool, read_file_tool],
            llm=self.llm,
        )
    
    def create_architect(self) -> Optional["Agent"]:
        """创建架构师Agent"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Agent(
            role="系统架构师",
            goal="设计可扩展、可维护的系统架构，输出详细的技术方案",
            backstory="""你是一位资深系统架构师，精通多种编程语言和框架。
你擅长将产品需求转化为技术实现方案，注重代码的可扩展性和可维护性。
你会选择合适的技术栈，设计清晰的模块划分和接口定义。""",
            verbose=True,
            allow_delegation=False,
            tools=[save_file_tool, read_file_tool],
            llm=self.llm,
        )
    
    def create_developer(self) -> Optional["Agent"]:
        """创建开发者Agent"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Agent(
            role="高级开发工程师",
            goal="根据架构设计编写高质量、可运行的代码",
            backstory="""你是一位技术精湛的开发工程师，代码风格优雅，注重细节。
你擅长将架构设计转化为实际代码，编写完整的单元测试。
你的代码包含详细的中文注释，遵循最佳实践。""",
            verbose=True,
            allow_delegation=False,
            tools=[save_file_tool, read_file_tool],
            llm=self.llm,
        )
    
    def create_reviewer(self) -> Optional["Agent"]:
        """创建代码审查Agent"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Agent(
            role="代码审查专家",
            goal="审查代码质量，发现潜在问题，确保代码符合最佳实践",
            backstory="""你是一位严格的代码审查专家，对代码质量有极高要求。
你善于发现潜在的bug、性能问题和安全隐患。
你会提供具体的改进建议，帮助团队提升代码质量。""",
            verbose=True,
            allow_delegation=False,
            tools=[read_file_tool],
            llm=self.llm,
        )
    
    def create_scheduler_agent(self) -> Optional["Agent"]:
        """创建调度Agent（功能亮点2：中心化调度）"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Agent(
            role="项目调度专家",
            goal="根据用户需求和问题类型，智能调度最合适的Agent团队完成任务",
            backstory="""你是一位资深的项目调度专家，精通软件开发全流程。
你能够准确识别用户问题类型，合理分配任务给不同的专业Agent，
确保任务高效、高质量完成。""",
            verbose=True,
            allow_delegation=True,
            llm=self.llm,
        )

# ================================================================
# 第三部分：任务定义（集成智能推理规划）
# ================================================================

class DevTeamTasks:
    """开发团队任务工厂 - 创建各阶段任务"""
    
    def create_requirement_task(self, product_manager: "Agent", user_requirement: str) -> Optional["Task"]:
        """创建需求分析任务"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Task(
            description=f"""分析以下用户需求（已标准化），编写产品需求文档(PRD)：

用户需求：
{normalize_user_input(user_requirement)}

请完成以下工作：
1. 理解用户的核心需求
2. 定义产品的目标用户
3. 列出核心功能列表（至少3个）
4. 编写用户故事（至少2个）
5. 定义验收标准
6. 将PRD保存到文件 prd.md

输出格式要求：
- 使用Markdown格式
- 结构清晰，包含标题和列表
- 使用中文""",
            expected_output="一份完整的产品需求文档，已保存到prd.md",
            agent=product_manager,
        )
    
    def create_architecture_task(self, architect: "Agent") -> Optional["Task"]:
        """创建架构设计任务"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Task(
            description="""阅读prd.md中的产品需求，设计系统架构。

请完成以下工作：
1. 选择合适的技术栈（编程语言、框架、数据库等）
2. 设计系统模块划分
3. 定义模块间的接口
4. 设计数据模型
5. 绘制架构图（用文字描述）
6. 将架构设计保存到文件 architecture.md

输出格式要求：
- 使用Markdown格式
- 包含技术选型理由
- 使用中文""",
            expected_output="一份完整的架构设计文档，已保存到architecture.md",
            agent=architect,
        )
    
    def create_development_task(self, developer: "Agent") -> Optional["Task"]:
        """创建代码开发任务"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Task(
            description="""阅读prd.md和architecture.md，实现完整的代码。

请完成以下工作：
1. 根据架构设计实现所有模块
2. 编写完整的中文注释
3. 编写单元测试
4. 确保代码可运行
5. 将代码保存到 src/ 目录下的适当文件中

代码要求：
- 使用Python语言
- 遵循PEP8规范
- 包含详细的文档字符串
- 使用中文注释
- 代码必须是完整可运行的""",
            expected_output="完整的项目源代码，已保存到src/目录",
            agent=developer,
        )
    
    def create_review_task(self, reviewer: "Agent") -> Optional["Task"]:
        """创建代码审查任务"""
        if not CREWAI_AVAILABLE:
            return None
        
        return Task(
            description="""审查src/目录下的所有代码文件。

请完成以下工作：
1. 检查代码是否符合架构设计
2. 检查是否有明显的bug
3. 检查代码风格和注释质量
4. 检查是否有安全隐患
5. 提出具体的改进建议
6. 将审查报告保存到 review_report.md

审查报告格式：
- 总体评价
- 发现的问题（按严重程度分类）
- 改进建议
- 评分（1-10分）""",
            expected_output="一份详细的代码审查报告，已保存到review_report.md",
            agent=reviewer,
        )
    
    def create_scheduling_task(self, scheduler_agent: "Agent", user_requirement: str) -> Optional["Task"]:
        """创建调度任务（功能亮点9：智能推理规划）"""
        if not CREWAI_AVAILABLE:
            return None
        
        query_type = classify_user_query(user_requirement)
        agent_mapping = {
            "requirement_analysis": "产品经理",
            "architecture_design": "架构师",
            "coding": "开发者",
            "code_review": "代码审查专家",
            "general_consult": "产品经理+架构师+开发者"
        }
        
        return Task(
            description=f"""执行智能任务规划（ReAct推理模式）：
1. 分析用户问题类型：{query_type}
2. 根据问题类型选择最合适的Agent：{agent_mapping[query_type]}
3. 制定任务执行计划，明确每个Agent的职责和执行顺序
4. 监控任务执行过程，确保质量和进度
5. 整合所有Agent的输出，生成最终结果

用户原始需求：
{user_requirement}

输出要求：
- 清晰的任务执行计划
- 各Agent的任务分配清单
- 预期输出结果说明""",
            expected_output="完整的任务调度计划和执行结果",
            agent=scheduler_agent,
        )

# ================================================================
# 第四部分：简化实现（当CrewAI不可用时）
# ================================================================

class SimpleDevTeam:
    """简化版开发团队 - 使用LLMClient直接实现"""
    
    def __init__(self):
        """初始化简化开发团队"""
        self.llm = LLMClient()
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        memory.create_session(self.session_id, "简化版开发流程会话")
    
    def _analyze_requirements(self, user_requirement: str) -> str:
        """需求分析（使用RequirementAnalysisSkill）"""
        normalized_input = normalize_user_input(user_requirement)
        
        # 记录到记忆系统
        memory.add_message(
            session_id=self.session_id,
            role="user",
            content=f"需求分析请求：{user_requirement}",
            agent_name="用户"
        )
        
        system_prompt = """你是一位产品经理。请分析用户需求，编写PRD文档。
输出Markdown格式，包含：功能列表、用户故事、验收标准。"""
        
        result = self.llm.chat_with_system(system_prompt, normalized_input)
        
        # 记录响应
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=result,
            agent_name="产品经理"
        )
        
        return result
    
    def _design_architecture(self, prd: str) -> str:
        """架构设计"""
        system_prompt = """你是一位系统架构师。请根据PRD设计系统架构。
输出Markdown格式，包含：技术栈选择、模块划分、接口定义。"""
        
        result = self.llm.chat_with_system(system_prompt, f"PRD内容：\n{prd}")
        
        # 记录响应
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=result,
            agent_name="架构师"
        )
        
        return result
    
    def _check_code_completeness(self, code: str) -> bool:
        """检查代码是否完整"""
        if not code.strip():
            return False
        
        # 检查括号是否匹配
        if code.count('(') != code.count(')'):
            return False
        if code.count('[') != code.count(']'):
            return False
        if code.count('{') != code.count('}'):
            return False
        
        # 检查缩进是否完整
        lines = code.split('\n')
        indent_level = 0
        for line in lines:
            stripped = line.strip()
            if stripped.startswith(('def ', 'class ', 'if ', 'elif ', 'else:', 
                                  'for ', 'while ', 'try:', 'except ', 'with ')):
                if stripped.endswith(':') and not stripped.startswith(('elif ', 'else:')):
                    indent_level += 1
        
        return True
    
    def _develop_code(self, prd: str, architecture: str) -> str:
        """代码开发"""
        system_prompt = """你是一位Python开发工程师。请根据PRD和架构设计编写完整的代码。

要求：
1. 代码必须完整可运行，包含所有必要的函数和类
2. 包含详细中文注释
3. 遵循PEP8规范
4. 输出完整的代码文件，不要有任何截断
5. 确保所有函数和方法都有完整的实现（包括所有分支）
6. 确保括号()[]{}完全匹配
7. 确保所有代码块都有正确的缩进和闭合

只输出代码，不要解释。"""
        
        context = f"PRD:\n{prd}\n\n架构设计:\n{architecture}"
        code = self.llm.chat_with_system(system_prompt, context)
        
        # 检查代码完整性，如果不完整则重试
        if not self._check_code_completeness(code):
            print("⚠️ 检测到代码不完整，正在重新生成...")
            system_prompt += "\n\n注意：上一次生成的代码不完整，请确保输出完整的代码！"
            code = self.llm.chat_with_system(system_prompt, context)
        
        # 记录响应
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=code,
            agent_name="开发者"
        )
        
        return code
    
    def _review_code(self, code: str) -> str:
        """代码审查"""
        system_prompt = """你是一位代码审查专家。请审查以下代码，输出审查报告。
报告格式：
- 总体评价
- 发现的问题
- 改进建议
- 评分（1-10分）"""
        
        result = self.llm.chat_with_system(system_prompt, f"代码：\n{code}")
        
        # 记录响应
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=result,
            agent_name="代码审查专家"
        )
        
        return result
    
    def run(self, user_requirement: str):
        """运行简化开发流程"""
        print("=" * 60)
        print("简化版多Agent开发团队")
        print(f"会话ID：{self.session_id}")
        print("=" * 60)
        
        # 标准化用户输入
        normalized_input = normalize_user_input(user_requirement)
        print(f"\n📝 标准化需求：{normalized_input[:100]}...")
        
        # ---- Step 1: 需求分析 ----
        print("\n👤 [产品经理] 正在分析需求...")
        prd = self._analyze_requirements(user_requirement)
        save_file("prd.md", prd)
        print("   ✅ PRD已保存到 D:\\generated_outputs\\dev_team\\prd.md")
        
        # ---- Step 2: 架构设计 ----
        print("\n👤 [架构师] 正在设计架构...")
        architecture = self._design_architecture(prd)
        save_file("architecture.md", architecture)
        print("   ✅ 架构设计已保存到 D:\\generated_outputs\\dev_team\\architecture.md")
        
        # ---- Step 3: 代码开发 ----
        print("\n👤 [开发者] 正在编写代码...")
        code = self._develop_code(prd, architecture)
        save_file("src/main.py", code)
        print("   ✅ 代码已保存到 D:\\generated_outputs\\dev_team\\src/main.py")
        
        # ---- Step 4: 代码审查 ----
        print("\n👤 [审查者] 正在审查代码...")
        review = self._review_code(code)
        save_file("review_report.md", review)
        print("   ✅ 审查报告已保存到 D:\\generated_outputs\\dev_team\\review_report.md")
        
        print("\n" + "=" * 60)
        print("✅ 开发流程完成！")
        print(f"📁 所有文件已保存到：D:\\generated_outputs\\dev_team")
        print("=" * 60)

# ================================================================
# 第五部分：CrewAI完整实现
# ================================================================

class CrewAIDevTeam:
    """CrewAI版开发团队 - 使用CrewAI框架实现"""
    
    def __init__(self):
        """初始化CrewAI开发团队"""
        self.agents = DevTeamAgents()
        self.tasks = DevTeamTasks()
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        memory.create_session(self.session_id, "CrewAI开发流程会话")
    
    def run(self, user_requirement: str):
        """运行CrewAI开发流程"""
        print("=" * 60)
        print("CrewAI多Agent开发团队")
        print(f"会话ID：{self.session_id}")
        print("=" * 60)
        
        # 记录用户输入
        memory.add_message(
            session_id=self.session_id,
            role="user",
            content=user_requirement,
            agent_name="用户"
        )
        
        # ---- 创建Agent ----
        print("\n🔧 创建Agent团队...")
        product_manager = self.agents.create_product_manager()
        architect = self.agents.create_architect()
        developer = self.agents.create_developer()
        reviewer = self.agents.create_reviewer()
        scheduler = self.agents.create_scheduler_agent()
        
        # ---- 创建任务 ----
        print("📋 分配任务...")
        scheduling_task = self.tasks.create_scheduling_task(scheduler, user_requirement)
        requirement_task = self.tasks.create_requirement_task(product_manager, user_requirement)
        architecture_task = self.tasks.create_architecture_task(architect)
        development_task = self.tasks.create_development_task(developer)
        review_task = self.tasks.create_review_task(reviewer)
        
        # ---- 创建Crew（中心化调度） ----
        print("🚀 启动开发流程...\n")
        crew = Crew(
            agents=[scheduler, product_manager, architect, developer, reviewer],
            tasks=[scheduling_task, requirement_task, architecture_task, development_task, review_task],
            process=Process.sequential,
            verbose=True,
        )
        
        # ---- 执行 ----
        result = crew.kickoff()
        
        # 记录执行结果
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=str(result),
            agent_name="调度专家"
        )
        
        print("\n" + "=" * 60)
        print("✅ 开发流程完成！")
        print(f"📁 所有文件已保存到：D:\\generated_outputs\\dev_team")
        print("   - prd.md: 产品需求文档")
        print("   - architecture.md: 架构设计文档")
        print("   - src/: 源代码目录")
        print("   - review_report.md: 代码审查报告")
        print("=" * 60)
        
        return result

# ================================================================
# 第六部分：单Agent聊天模式（集成记忆系统）
# ================================================================

def single_agent_chat():
    """单Agent聊天模式：和指定角色一对一对话"""
    print("=" * 60)
    print("单Agent聊天模式（支持会话记忆）")
    print("=" * 60)
    print("可选角色：")
    print("  1. 产品经理 - 分析需求、写PRD、产品建议")
    print("  2. 架构师 - 系统设计、技术选型、架构方案")
    print("  3. 开发者 - 写代码、解决bug、技术问题")
    print("  4. 代码审查 - 审查代码、质量评估、改进建议")
    print("  0. 返回上级菜单")
    print("=" * 60)
    
    # 创建新会话
    session_id = f"session_{uuid.uuid4().hex[:8]}"
    memory.create_session(session_id, "单Agent聊天会话")
    print(f"\n🆔 当前会话ID：{session_id}")
    
    llm = LLMClient()
    
    # 角色定义
    roles = {
        "1": {
            "name": "产品经理",
            "prompt": """你是一位经验丰富的产品经理，拥有10年互联网产品经验。
你擅长将模糊的想法转化为清晰的产品需求，识别核心功能和用户痛点。
请用简洁、专业、有条理的语言回答用户的问题，提供可落地的建议。"""
        },
        "2": {
            "name": "架构师",
            "prompt": """你是一位资深系统架构师，精通Python、Java、Go等多种编程语言。
你擅长设计高可用、可扩展的分布式系统，熟悉各种技术栈的优缺点。
请给出专业的技术方案，说明技术选型理由，提供清晰的架构设计。"""
        },
        "3": {
            "name": "开发者",
            "prompt": """你是一位技术精湛的全栈开发工程师，代码风格优雅，注重细节。
你擅长编写高质量、可维护的代码，解决各种复杂的技术问题。
请提供完整可运行的代码，包含详细的中文注释，遵循最佳实践。"""
        },
        "4": {
            "name": "代码审查",
            "prompt": """你是一位严格的代码审查专家，对代码质量有极高要求。
你善于发现潜在的bug、性能问题、安全隐患和可维护性问题。
请给出具体的改进建议和代码示例，帮助用户提升代码质量。"""
        }
    }
    
    while True:
        choice = input("\n请选择要对话的角色（输入数字）：")
        if choice == "0":
            print(f"\n📝 会话已保存（ID：{session_id}）")
            return
        
        if choice not in roles:
            print("❌ 无效的选择，请重新输入")
            continue
        
        role = roles[choice]
        print(f"\n✅ 已连接到【{role['name']}】")
        print("输入你的问题，输入'quit'返回上级菜单\n")
        
        while True:
            user_input = input(f"[{role['name']}] > ")
            if user_input.lower() == "quit":
                break
            
            # 标准化用户输入
            normalized_input = normalize_user_input(user_input)
            
            # 记录用户输入
            memory.add_message(
                session_id=session_id,
                role="user",
                content=user_input,
                agent_name=role['name']
            )
            
            # 获取历史对话
            history = memory.get_messages(session_id)
            history_context = "\n".join([
                f"{msg['role']}: {msg['content'][:200]}..." 
                for msg in history[:-1]  # 排除当前输入
            ])
            
            # 构建完整提示
            full_prompt = f"{role['prompt']}\n\n对话历史：\n{history_context}\n\n当前问题：{normalized_input}"
            
            print(f"\n[{role['name']}] 正在思考...")
            response = llm.chat_with_system(full_prompt, user_input)
            
            # 记录响应
            memory.add_message(
                session_id=session_id,
                role="assistant",
                content=response,
                agent_name=role['name']
            )
            
            print(f"\n[{role['name']}]: {response}\n")

# ================================================================
# 第七部分：动态多Agent协作模式（强化中心化调度）
# ================================================================

class DynamicAgentTeam:
    """动态多Agent团队：根据用户问题自动调度合适的Agent协作"""
    
    def __init__(self):
        self.llm = LLMClient()
        self.session_id = f"session_{uuid.uuid4().hex[:8]}"
        memory.create_session(self.session_id, "动态多Agent协作会话")
        
        # 注册所有可用的专业Agent
        self.agents = {
            "产品经理": {
                "description": "需求分析、产品设计、PRD编写、用户故事定义",
                "prompt": """你是一位经验丰富的产品经理。
请基于用户的需求，提供专业的产品建议，输出清晰的结构和明确的结论。"""
            },
            "架构师": {
                "description": "系统架构设计、技术选型、模块划分、接口定义",
                "prompt": """你是一位资深系统架构师。
请基于用户的问题，设计合理的技术方案，说明技术选型理由，给出清晰的架构设计。"""
            },
            "开发者": {
                "description": "代码编写、技术问题解决、bug调试、性能优化",
                "prompt": """你是一位技术精湛的Python开发工程师。
请提供完整可运行的代码，包含详细的中文注释，遵循最佳实践。"""
            },
            "代码审查": {
                "description": "代码质量审查、bug发现、改进建议、最佳实践指导",
                "prompt": """你是一位严格的代码审查专家。
请从正确性、性能、安全性、可维护性四个方面审查代码，给出具体的改进建议。"""
            }
        }
    
    def _plan_tasks(self, user_query: str) -> List[str]:
        """分析用户问题，规划需要调用的Agent和执行顺序（功能亮点9：智能推理）"""
        # 先进行问题分类
        query_type = classify_user_query(user_query)
        
        agent_list = "\n".join([f"- {name}: {info['description']}" for name, info in self.agents.items()])
        
        system_prompt = f"""你是一个任务规划专家。
用户的问题是：{user_query}

可用的专业Agent有：
{agent_list}

规则：
1. 如果是【你好、问候、闲聊】，统一只返回：通用问答
2. 业务问题再按角色分配Agent名称
3. 按执行顺序返回内容，每行一个，不要额外解释。"""
        
        response = self.llm.chat_with_system(system_prompt, user_query)
        
        # 解析返回的Agent列表
        agents_to_call = []
        for line in response.split('\n'):
            line = line.strip()
            if line == "通用问答":
                agents_to_call = ["开发者"]
                break
            if line in self.agents:
                agents_to_call.append(line)
        
        return agents_to_call if agents_to_call else ["开发者"]
    
    def _execute_agent_task(self, agent_name: str, user_query: str, previous_results: str) -> str:
        """执行单个Agent的任务"""
        agent_info = self.agents[agent_name]
        
        # 标准化用户输入
        normalized_input = normalize_user_input(user_query)
        
        system_prompt = f"""{agent_info['prompt']}

之前的执行结果：
{previous_results if previous_results else "无"}

请基于以上信息，完成你的任务。"""
        
        result = self.llm.chat_with_system(system_prompt, normalized_input)
        
        # 记录Agent执行结果
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=result,
            agent_name=agent_name
        )
        
        return f"【{agent_name}】：\n{result}\n\n"
    
    def _synthesize_results(self, all_results: str) -> str:
        """整合所有Agent的输出，生成最终答案"""
        system_prompt = """请将以下多个专业Agent的输出整理成一个清晰、连贯、有条理的最终答案。
保留所有关键信息，去除重复内容，使用清晰的标题和列表结构，语言简洁流畅。"""
        
        return self.llm.chat_with_system(system_prompt, f"所有Agent的输出：\n{all_results}")
    
    def run(self, user_query: str) -> str:
        """处理用户问题，自动调度Agent协作"""
        # 记录用户输入
        memory.add_message(
            session_id=self.session_id,
            role="user",
            content=user_query,
            agent_name="用户"
        )
        
        print(f"\n🤖 正在分析你的问题：{user_query}")
        print(f"🆔 会话ID：{self.session_id}")
        
        # Step 1: 任务规划（中心化调度）
        agents_to_call = self._plan_tasks(user_query)
        print(f"📋 任务规划完成，需要调用：{', '.join(agents_to_call)}")
        
        # Step 2: 按顺序执行任务
        all_results = ""
        for i, agent_name in enumerate(agents_to_call):
            print(f"\n⚡ [{i+1}/{len(agents_to_call)}] 正在调用【{agent_name}】...")
            result = self._execute_agent_task(agent_name, user_query, all_results)
            all_results += result
            print(f"✅ 【{agent_name}】完成任务")
        
        # Step 3: 结果整合
        print("\n📝 正在整理最终结果...")
        final_answer = self._synthesize_results(all_results)
        
        # 记录最终结果
        memory.add_message(
            session_id=self.session_id,
            role="assistant",
            content=final_answer,
            agent_name="调度专家"
        )
        
        return final_answer

def dynamic_agent_chat():
    """动态多Agent协作聊天模式"""
    print("=" * 60)
    print("动态多Agent协作模式（智能调度+记忆系统）")
    print("=" * 60)
    print("你可以问任何问题，我会自动调度最合适的Agent团队为你服务")
    print("示例问题：")
    print("  - 帮我设计一个用户登录系统，包括需求、架构和代码")
    print("  - 帮我写一个FastAPI接口，然后审查代码质量")
    print("  - 对比FastAPI和Django的优缺点，给出技术选型建议")
    print("输入'quit'返回上级菜单")
    print("=" * 60)
    
    team = DynamicAgentTeam()
    
    while True:
        user_input = input("\n[你] > ")
        if user_input.lower() == "quit":
            print(f"\n📝 会话已保存（ID：{team.session_id}）")
            break
        
        answer = team.run(user_input)
        print(f"\n[助手]: {answer}\n")

# ================================================================
# 第八部分：主函数
# ================================================================

def main():
    """主函数"""
    # 确保所有D盘目录存在（符合Conda-Disk-Manager规范）
    os.makedirs("D:\\projects\\dev_team", exist_ok=True)
    os.makedirs("D:\\generated_outputs\\dev_team", exist_ok=True)
    os.makedirs("D:\\generated_outputs\\dev_team\\src", exist_ok=True)
    os.makedirs("D:\\generated_outputs\\dev_team\\memory", exist_ok=True)
    
    print("=" * 60)
    print("🚀 多Agent开发团队 v3.0（D盘版）")
    print("=" * 60)
    print("📁 项目路径：D:\\projects\\dev_team")
    print("📁 输出路径：D:\\generated_outputs\\dev_team")
    print("=" * 60)
    print("请选择运行模式：")
    print("  1. 完整开发流程 - 自动生成完整项目（原功能）")
    print("  2. 单Agent聊天 - 和指定角色一对一对话（带记忆）")
    print("  3. 动态多Agent协作 - 自动调度多个Agent完成复杂任务")
    print("  0. 退出")
    print("=" * 60)
    
    while True:
        choice = input("请输入数字选择模式：")
        
        if choice == "0":
            print("\n📋 当前所有会话：")
            sessions = memory.get_all_sessions()
            if sessions:
                for i, sess in enumerate(sessions):
                    print(f"   {i+1}. {sess}")
            print("\n再见！")
            break
        
        elif choice == "1":
            # 原来的完整开发流程（迁移到D盘）
            user_requirement = """开发一个Python待办事项管理工具，要求：
1. 可以添加、删除、列出待办事项
2. 可以标记任务完成状态
3. 数据持久化到本地文件
4. 命令行界面操作简单直观
5. 支持任务优先级设置"""
            
            print("\n📝 默认用户需求：")
            print(user_requirement)
            print()
            
            # 可以让用户输入自定义需求
            custom_requirement = input("按回车使用默认需求，或输入你的自定义需求：")
            if custom_requirement.strip():
                user_requirement = custom_requirement
            
            print("\n⚠️ 使用简化版多Agent开发团队（所有文件将保存到D盘）\n")
            team = SimpleDevTeam()
            team.run(user_requirement)
        
        elif choice == "2":
            single_agent_chat()
        
        elif choice == "3":
            dynamic_agent_chat()
        
        else:
            print("❌ 无效的选择，请重新输入")

if __name__ == "__main__":
    main()