# backend/knowledge_base/vector_store.py
# (V2 - 图文多模态版)

from pymilvus import MilvusClient, FieldSchema, CollectionSchema, DataType
from langchain_community.vectorstores import Milvus
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_core.documents import Document
from typing import List, Dict
from PIL import Image
import torch
from transformers import CLIPProcessor, CLIPModel

# 导入你的配置
from utils import config 

# --- 1. 嵌入模型加载 ---

def get_text_embedding_model():
    """获取文本嵌入模型 (m3e-base)"""
    print("正在加载 文本嵌入模型...")
    return HuggingFaceEmbeddings(
        model_name=config.EMBEDDING_MODEL_NAME, 
        model_kwargs={'device': 'cpu'} # 嵌入计算用 CPU
    )

def get_image_embedding_models():
    """获取图片嵌入模型 (CLIP)"""
    print("正在加载 图片嵌入模型 (CLIP)...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    model = CLIPModel.from_pretrained(config.IMAGE_EMBEDDING_MODEL).to(device)
    processor = CLIPProcessor.from_pretrained(config.IMAGE_EMBEDDING_MODEL)
    return model, processor, device

# --- 2. Milvus 初始化 (升级版) ---
def initialize_milvus():
    """
    (后端启动时调用)
    检查并创建 两个 Milvus 集合 (文本 + 图片)
    """
    print("正在连接 Milvus...")
    client = MilvusClient(uri=config.MILVUS_URI)
    
    # 1. 定义 Schema - 文本
    text_schema = CollectionSchema([
        FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=config.TEXT_EMBEDDING_DIM),
        FieldSchema(name="chunk_text", dtype=DataType.VARCHAR, max_length=65535),
        FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="page", dtype=DataType.INT64),
        FieldSchema(name="clause_id", dtype=DataType.VARCHAR, max_length=100, default_value=""),
    ], description="知识库 文本块")
    
    # 2. 定义 Schema - 图片
    image_schema = CollectionSchema([
        FieldSchema(name="pk", dtype=DataType.VARCHAR, is_primary=True, auto_id=True, max_length=100),
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=config.IMAGE_EMBEDDING_DIM),
        FieldSchema(name="image_path", dtype=DataType.VARCHAR, max_length=1000), # 存储图片路径
        FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=500),
        FieldSchema(name="page", dtype=DataType.INT64),
    ], description="知识库 图片")

    # 3. 创建 文本集合
    collection_name_text = config.TEXT_COLLECTION_NAME
    if not client.has_collection(collection_name_text):
        client.create_collection(collection_name_text, text_schema, consistency_level="Strong")
        client.create_index(collection_name_text, "embedding", 
                            {"index_type": "IVF_FLAT", "params": {"nlist": 128}, "metric_type": "L2"})
        print(f"创建 文本集合: {collection_name_text}")
    
    # 4. 创建 图片集合
    collection_name_image = config.IMAGE_COLLECTION_NAME
    if not client.has_collection(collection_name_image):
        client.create_collection(collection_name_image, image_schema, consistency_level="Strong")
        client.create_index(collection_name_image, "embedding", 
                            {"index_type": "IVF_FLAT", "params": {"nlist": 128}, "metric_type": "L2"})
        print(f"创建 图片集合: {collection_name_image}")

    # 5. 加载集合到内存
    client.load_collection(collection_name_text)
    client.load_collection(collection_name_image)
    print(f"Milvus 集合 '{collection_name_text}' 和 '{collection_name_image}' 加载到内存。")
    return client

# --- 3. 数据写入功能 (升级版) ---

def add_text_documents(client: MilvusClient, text_docs: List[Document]):
    """将 LangChain 文本块 批量插入 Milvus"""
    if not text_docs:
        print("没有 文本块 需要插入。")
        return
    
    embeddings_model = get_text_embedding_model()
    data = []
    print(f"准备插入 {len(text_docs)} 条 文本块...")
    
    for doc in text_docs:
        meta = doc.metadata
        data.append({
            "chunk_text": doc.page_content,
            "embedding": embeddings_model.embed_query(doc.page_content),
            "doc_name": meta.get("doc_name"),
            "page": meta.get("page"),
            "clause_id": meta.get("clause_id", "")
        })
    
    client.insert(collection_name=config.TEXT_COLLECTION_NAME, data=data)
    print(f"{len(data)} 条 文本块 插入 Milvus 成功。")
    client.flush([config.TEXT_COLLECTION_NAME])

def add_image_documents(client: MilvusClient, image_infos: List[Dict]):
    """将 图片元数据 批量插入 Milvus"""
    if not image_infos:
        print("没有 图片 需要插入。")
        return

    model, processor, device = get_image_embedding_models()
    data = []
    print(f"准备插入 {len(image_infos)} 张 图片...")

    for info in image_infos:
        try:
            # 1. 打开图片
            img = Image.open(info['image_path']).convert("RGB")
            
            # 2. 用 CLIP 编码
            inputs = processor(images=img, return_tensors="pt", padding=True).to(device)
            with torch.no_grad():
                image_features = model.get_image_features(**inputs)
            
            embedding = image_features[0].cpu().numpy().tolist() # 获取向量
            
            # 3. 准备数据
            data.append({
                "image_path": info['image_path'],
                "embedding": embedding,
                "doc_name": info.get("doc_name"),
                "page": info.get("page")
            })
        except Exception as e:
            print(f"警告: 处理图片 {info['image_path']} 失败: {e}")

    if not data:
        print("没有图片数据被成功处理。")
        return

    client.insert(collection_name=config.IMAGE_COLLECTION_NAME, data=data)
    print(f"{len(data)} 张 图片 插入 Milvus 成功。")
    client.flush([config.IMAGE_COLLECTION_NAME])


# --- 4. 检索功能 (为 RAG 链准备) ---

def get_text_retriever():
    """获取 文本检索器 (LangChain)"""
    embeddings = get_text_embedding_model()
    store = Milvus(
        embedding_function=embeddings,
        connection_args={"uri": config.MILVUS_URI},
        collection_name=config.TEXT_COLLECTION_NAME,
        text_field="chunk_text",
        auto_id=True,
    )
    return store.as_retriever(search_kwargs={"k": 10}) # 召回10个，后续 rerank

