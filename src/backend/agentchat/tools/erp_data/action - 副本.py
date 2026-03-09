from langchain.tools import tool
from agentchat.core.models.manager import ModelManager
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase #连接和操作关系型数据库的核心类
from langchain_community.agent_toolkits import SQLDatabaseToolkit
import urllib.parse


@tool(parse_docstring=True)
def erp_data(query: str):
    """
    根据用户输入的问题，从数据库中获取对应的数据

    Args:
        query (str): 用户提供的搜索关键词。

    Returns:
        str: 与该问题相关的数据信息
    """
    return _get_erp_data(query)

#根据用户输入的问题，构建mysql 的查询语句，并执行查询，将查询结果返回
#根据用户输入的问题，构建mysql 的查询语句，并执行查询，将查询结果返回
def _get_erp_data(query: str):
    """ 查询与该问题相关的数据 """

    # mysql_user = 'root'
    # mysql_password = 'Gmys@123'
    # mysql_host = '10.128.10.6'
    # mysql_port = '3306'
    # mysql_db = 'gmyserp'

    mysql_user = 'root'
    mysql_password = 'root'
    mysql_host = '127.0.0.1'
    mysql_port = '3307'
    mysql_db = 'agentchat'

    try:
        # 对MySQL密码进行URL编码，处理特殊字符
        encoded_password = urllib.parse.quote_plus(mysql_password)
        
        # 构建数据库连接字符串
        db_uri = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        
        # 连接数据库
        db = SQLDatabase.from_uri(db_uri)
        
        # 获取LLM模型
        llm = ModelManager.get_tool_invocation_model()
        
        # 构建SQL查询语句的提示模板
        
        # Step 1: 获取数据库表结构信息
        schema_info = db.get_table_info()
        
        # Step 2: 构建SQL查询语句的提示模板
        sql_prompt = f"""
        你是一个数据库专家，请根据以下数据库表结构和用户问题，生成一个准确的MySQL查询语句。
        只返回SQL查询语句，不要包含任何解释或其他内容。
        
        数据库表结构:
        {schema_info}
        
        用户问题: {query}
        
        SQL查询语句:
        """
        
        # Step 3: 调用LLM生成SQL查询语句
        sql_result = llm.invoke(sql_prompt)
        
        # Step 4:提取SQL查询语句
        import re
        sql_match = re.search(r'SELECT.*?(?:;|$)', sql_result.content, re.DOTALL | re.IGNORECASE)
        if not sql_match:
            return f"无法生成有效的SQL查询: {sql_result.content}"
        
        generated_sql = sql_match.group(0).strip()
        
        # Step 5: 执行SQL查询
        try:
            query_result = db.run(generated_sql)
            return f"查询结果: {query_result}"
        except Exception as sql_error:
            return f"执行SQL查询时出错: {str(sql_error)}\n生成的SQL: {generated_sql}"
        
    except Exception as e:
        return f"Error occurred while querying ERP data: {str(e)}"
