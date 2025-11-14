# backend/vector_store.py

import time
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType, MilvusClient
from langchain_community.vectorstores import Milvus
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from typing import List

# 导入你的配置
# (假设你的 config.py 在 utils/config.py)
from utils import config 

# --- 1. 嵌入模型 ---
# RAG 链和数据入库必须使用同一个模型
def get_embedding_model():
    """获取文本嵌入模型"""
    print("正在加载嵌入模型...")
    return HuggingFaceEmbeddings(
        model_name="moka-ai/m3e-base", # 示例: 768 维
        model_kwargs={'device': 'cpu'}
    )

# --- 2. Milvus 初始化 (你已经开始写的部分) ---
def initialize_milvus():
    """
    (后端启动时调用)
    检查并创建 Milvus Collection (表) 和 Schema (结构)
    """
    print("正在连接 Milvus...")
    # 使用 MilvusClient 更简单
    client = MilvusClient(uri=config.MILVUS_URI)
    
    # 1. 定义 Schema (你照片里的代码)
    # 主键
    field_pk = FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100)
    # 嵌入
    field_embedding = FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=config.TEXT_EMBEDDING_DIM)
    # 原始文本
    field_text = FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535)
    
    # --- 架构师要求的元数据 ---
    field_doc_name = FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=500)
    field_page = FieldSchema(name="page", dtype=DataType.INT64)
    # (我再加一个 clause_id，架构图里提到了)
    field_clause_id = FieldSchema(name="clause_id", dtype=DataType.VARCHAR, max_length=100, default_value="")
    
    # 2. 创建 CollectionSchema
    schema = CollectionSchema(
        fields=[field_pk, field_embedding, field_text, field_doc_name, field_page, field_clause_id],
        description="Knowlex 知识库文本"
    )
    
    # 3. 创建 Collection
    collection_name = config.TEXT_COLLECTION_NAME
    if not client.has_collection(collection_name):
        client.create_collection(
            collection_name, 
            schema, 
            consistency_level="Strong" # 强一致性
        )
        
        # 4. 为 embedding 字段创建索引
        print(f"正在为 {collection_name} 创建索引...")
        client.create_index(
            collection_name, 
            "embedding", 
            {"index_type": "IVF_FLAT", "params": {"nlist": 128}, "metric_type": "L2"}
        )
    else:
        print(f"Collection '{collection_name}' 已存在。")

    # 5. 加载 Collection 到内存
    client.load_collection(collection_name)
    print(f"Collection '{collection_name}' 加载到内存。")

# --- 3. 数据写入功能 (给 pdf_processor.py 调用) ---
def add_documents_to_milvus(client: MilvusClient, documents: List[Document]):
    """
    将 LangChain Document 列表批量插入 Milvus
    """
    if not documents:
        return

    embeddings_model = get_embedding_model()
    data = []
    
    print(f"准备插入 {len(documents)} 条数据...")
    
    # 转换数据格式
    for doc in documents:
        meta = doc.metadata
        # 检查元数据是否符合架构要求
        if "doc_name" not in meta or "page" not in meta:
            print(f"警告: 文档缺少元数据: {doc.page_content[:20]}...")
            continue
            
        data.append({
            "chunk_text": doc.page_content,
            "embedding": embeddings_model.embed_query(doc.page_content), # 实时嵌入
            "doc_name": meta.get("doc_name"),
            "page": meta.get("page"),
            "clause_id": meta.get("clause_id", "")
        })
    
    if not data:
        print("没有可插入的数据。")
        return

    print(f"正在向 Milvus 批量插入 {len(data)} 条数据...")
    client.insert(
        collection_name=config.TEXT_COLLECTION_NAME,
        data=data
    )
    print("数据插入 Milvus 成功。")
    client.flush([config.TEXT_COLLECTION_NAME]) # 确保数据可被搜索


# --- 4. 检索功能 (给 rag_chain.py 调用) ---
def get_langchain_milvus_store():
    """
    获取一个 LangChain 兼容的 Milvus 向量存储实例
    """
    embeddings = get_embedding_model()
    store = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": config.MILVUS_URI},
        collection_name=config.TEXT_COLLECTION_NAME,
        text_field="chunk_text", # 告诉 LangChain 我们的文本字段叫 'chunk_text'
        auto_id=True, # 使用 Milvus 的 auto_id
    )
    return store