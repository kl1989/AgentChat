from langchain.tools import tool
from agentchat.core.models.manager import ModelManager
from langchain.agents import create_agent
from langchain_community.utilities import SQLDatabase #连接和操作关系型数据库的核心类
from langchain_community.agent_toolkits import SQLDatabaseToolkit
import urllib.parse
from agentchat.settings import app_settings


@tool(parse_docstring=True)
def erp_data(query: str):
    """
    根据用户输入的问题，从数据库中获取对应的单证相关的数据信息

    Args:
        query (str): 用户提供的搜索关键词。

    Returns:
        str: 与该问题相关的数据信息
    """
    return _get_erp_data(query)

#根据用户输入的问题，构建mysql 的查询语句，并执行查询，将查询结果返回
def _get_erp_data(query: str):
    """ 查询与该问题相关的数据 """

    try:
        # 从配置文件获取本地数据库连接字符串（走配置,但是存在@符号，需要URL编码）
        # db_uri = app_settings.erpsql['endpoint']
        # 连接数据库
        # db = SQLDatabase.from_uri(db_uri)
        # 获取LLM模型
        # llm = ModelManager.get_tool_invocation_model()        
        # Step 1: 获取数据库表结构信息
        # schema_info = db.get_table_info()

        # mysql_user = 'root'
        # mysql_password = 'root'
        # mysql_host = '127.0.0.1'
        # mysql_port = '3307'
        # mysql_db = 'agentchat'

        mysql_user = 'root'
        mysql_password = 'Gmys@123'
        mysql_host = '10.128.10.6'
        mysql_port = '3306'
        mysql_db = 'gmyserp'

        # 对MySQL密码进行URL编码，处理特殊字符
        try:
            encoded_password = urllib.parse.quote_plus(mysql_password)
            # 构建数据库连接字符串
            db_uri = f"mysql+pymysql://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_db}"
            # 连接数据库
            # db = SQLDatabase.from_uri(db_uri)
            # 连接数据库，只查询指定的多个表
            db = SQLDatabase.from_uri(
                db_uri,
                include_tables=['export','export_goods','ag_agcust','ag_agcust_buyer','ag_agcust_seller','ag_agcust_seller_goods'],  # 只查询export和export_goods表
            )
        except Exception as db_error:
            return f"数据库连接出错: {str(db_error)}\n错误类型: {type(db_error).__name__}"
        
        # 获取LLM模型
        llm = ModelManager.get_tool_invocation_model()
        # Step 1: 获取数据库表结构信息
        schema_info = db.get_table_info()
        # Step 2: 构建SQL查询语句的提示模板
        sql_prompt = f"""
        你是一个数据库专家，请根据以下数据库表结构和用户问题，生成一个准确的MySQL查询语句。
        只返回SQL查询语句，不要包含任何解释或其他内容。

        重要要求:
        1. 为了避免返回过多数据，确保在SQL语句末尾添加LIMIT子句，限制查询最新的结果不超过5条
        2. 只查询必要的字段，避免查询所有字段
        3. 确保SQL语句语法正确，能够直接在MySQL中执行
        4. 禁止使用任何危险的SQL操作，如删除、更新或插入操作
        
        数据库表结构:
        {schema_info}
        
        用户问题: {query}
        """
        
        # Step 3: 调用LLM生成SQL查询语句
        sql_result = llm.invoke(sql_prompt)
        # Step 4:提取SQL查询语句
        try:
            import re
            sql_match = re.search(r'SELECT.*?(?:;|$)', sql_result.content, re.DOTALL | re.IGNORECASE)
            if not sql_match:
                return f"无法生成有效的SQL查询: {sql_result.content}"
            
            generated_sql = sql_match.group(0).strip()
        except Exception as extract_error:
            return f"提取SQL语句出错: {str(extract_error)}\n错误类型: {type(extract_error).__name__}\nLLM返回内容: {sql_result}"
        
        # Step 5: 执行SQL查询
        try:
            query_result = db.run(generated_sql)
            return f"{query_result}"
        except Exception as sql_error:
            # 提供更详细的错误信息，包括SQL语句和完整错误
            return f"执行SQL查询时出错: {str(sql_error)}\n生成的SQL: {generated_sql}\n错误类型: {type(sql_error).__name__}"

    except Exception as e:
        return f"Error occurred while querying ERP data: {str(e)}\n错误类型: {type(e).__name__}"
