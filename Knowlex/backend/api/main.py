# api/main.py

from fastapi import FastAPI
from contextlib import asynccontextmanager
from backend.Knowledge_base import vector_store # 导入你的模块
from backend.data_process_base import pdf_processor
from rag.rag_chain import rag_chain # 导入已创建的 RAG 链实例
from utils import config
import os

# --- 数据导入逻辑 ---
def run_ingestion():
    """
    (2号任务) 数据导入流程
    """
    print("--- 1. 检查并初始化 Milvus ---")
    client = vector_store.get_milvus_client()
    vector_store.initialize_milvus()
    
    # 检查是否已有数据，避免重复入库
    count = client.query(config.TEXT_COLLECTION_NAME, "pk != ''", limit=1)
    if count:
        print("Milvus 中已有数据，跳过入库。")
        return

    print("--- 2. 开始数据处理与入库 ---")
    # (假设你的 PDF 都在 'data/' 目录下)
    all_documents = pdf_processor.process_all_pdfs("./data") 
    
    if all_documents:
        # 3. 调用 vector_store 的写入功能
        vector_store.add_documents_to_milvus(client, all_documents)
    
    print("--- 数据入库完成 ---")


# --- FastAPI 启动事件 ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    # --- 在 FastAPI 启动时执行 ---
    run_ingestion()
    yield
    # --- 在 FastAPI 关闭时执行 ---
    print("关闭应用...")

app = FastAPI(lifespan=lifespan)

# --- API 接口 (给3号前端调用) ---
@app.post("/api/query") # 路径与架构图一致
async def query_endpoint(request: dict):
    """
    接收前端查询并返回 RAG 结果
    """
    query_text = request.get("query")
    if not query_text:
        return {"error": "Query text is missing."}

    # rag_chain 内部已经配置好了 Milvus
    result = rag_chain.invoke({"query": query_text}) 
    
    # 返回前端需要的结果
    return {
        "answer": result.get("result"),
        "sources": result.get("source_documents")
    }

@app.get("/")
def read_root():
    return {"message": "Knowlex RAG API is running."}