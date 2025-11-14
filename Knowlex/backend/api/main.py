# api/main.py
# (V4 - 决赛 RAG 最终版)

from fastapi import FastAPI
from contextlib import asynccontextmanager
import uuid

# --- 导入大模型 ---
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser

# 导入你的配置
from utils import config 
# 导入你的数据和向量库模块
from backend.knowledge_base import vector_store 
from backend.data_process import pdf_processor
# 导入我们为初赛构建的“纯检索管线”
from rag.rag_chain import run_retrieval_pipeline 

# --- 数据导入 (不变) ---
# (这部分代码和 V3 版完全一样)
def run_ingestion():
    print("--- 1. 检查并初始化 Milvus (图文) ---")
    client = vector_store.initialize_milvus()
    
    count = client.query(config.TEXT_COLLECTION_NAME, "pk != ''", limit=1)
    if count:
        print("Milvus 中已有数据，跳过入库。")
        return client

    print("--- 2. 开始图文数据处理 (pdf_processor) ---")
    text_docs, image_infos = pdf_processor.process_all_pdfs() 
    
    if text_docs:
        print("--- 3. 开始 文本数据 入库 (vector_store) ---")
        vector_store.add_text_documents(client, text_docs)
    
    if image_infos:
        print("--- 4. 开始 图片数据 入库 (vector_store) ---")
        vector_store.add_image_documents(client, image_infos)
    
    print("--- 数据入库完成 ---")
    return client

# --- 决赛 RAG 链 (新增) ---
def get_final_rag_chain():
    """
    (决赛用)
    构建一个 RAG 链, 它接收“检索结果”并“生成答案”
    """
    # (确保你的 config.py 里有 OPENAI_API_KEY)
    # (确保你的 requirements.txt 里有 langchain-openai)
    llm = ChatOpenAI(model=config.LLM_MODEL_NAME) 
    
    # 决赛的 Prompt
    prompt_template = """
    你是一个专业的中国工程规范问答助手。
    请根据下面提供的上下文信息，简洁、专业地回答问题。
    
    规则：
    1. 严格根据上下文回答，不要编造信息。
    2. 如果上下文中没有答案，请明确回答 "根据所提供的资料，我无法回答该问题。"
    3. 优先引用“条款”内容。
    
    --- 检索到的条款上下文 ---
    {clauses_context}
    ---------------------------
    
    问题: {query}
    
    答案:
    """
    prompt = ChatPromptTemplate.from_template(prompt_template)
    
    chain = prompt | llm | StrOutputParser()
    
    return chain

# --- 初始化所有模型 ---
final_rag_chain = get_final_rag_chain()

# --- FastAPI 启动事件 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时, 自动完成数据入库
    app.state.milvus_client = run_ingestion()
    yield
    print("关闭应用...")

app = FastAPI(lifespan=lifespan)

# --- API 接口 (决赛版) ---
@app.post("/api/query")
async def query_endpoint(request: dict):
    """
    (决赛版)
    接收前端查询, 运行完整的 RAG 流程
    """
    query_text = request.get("query")
    if not query_text:
        return {"error": "Query text is missing."}

    # 1. 运行初赛的“纯检索管线”(R)
    # 这会返回 Top-3 条款 和 关联的图片
    retrieval_dict = run_retrieval_pipeline(query_text)
    
    # 2. 准备 LLM (G) 的上下文
    clauses_context = "\n---\n".join(
        f"[来源: {c['doc_name']}, 第 {c['page']} 页]\n{c['content']}" 
        for c in retrieval_dict['clauses']
    )
    
    # 3. 运行决赛的“RAG链”
    generated_answer = final_rag_chain.invoke({
        "clauses_context": clauses_context,
        "query": query_text
    })
    
    # 4. 返回一个包含“生成式答案”和“来源”的最终结果
    return {
        "id": str(uuid.uuid4()),
        "generated_answer": generated_answer, # LLM 生成的答案
        "sources": retrieval_dict # 原始来源 (包含clauses和images)
    }

@app.get("/")
def read_root():
    return {"message": "Knowlex RAG API  正在运行..."}