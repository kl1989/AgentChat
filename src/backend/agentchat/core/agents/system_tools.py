# 系统工具模块——by lk
from pydantic import BaseModel
from langchain_core.tools import StructuredTool
from agentchat.utils.date_utils import get_beijing_time

# 时间工具参数模型
class GetCurrentTimeArgs(BaseModel):
    pass

async def get_current_time_async():
    return get_beijing_time()

# 系统工具列表
SYSTEM_TOOLS = [
    StructuredTool(
        name="SysCurrentTime", # 工具名称
        description="Get the current Beijing time. Use this tool only when the question requires real-time information.",
        coroutine=get_current_time_async, # 异步执行函数
        args_schema=GetCurrentTimeArgs #参数模型，当前不需要参数
    ),
    # 未来可以添加更多系统工具
    # 例如：获取系统信息、环境变量等
]