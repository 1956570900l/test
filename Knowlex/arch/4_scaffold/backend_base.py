# arch/4_scaffold/backend_base.py（架构编写，后端直接导入）
from langchain.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import Milvus
from langchain.embeddings import HuggingFaceEmbeddings
from langchain.chains import RetrievalQA
from langchain.llms import OpenAI
from pymilvus import connections, Collection, FieldSchema, CollectionSchema, DataType
from backend.utils.config import MILVUS_CONFIG  # 架构在config.py里定义的参数

# 1. Milvus连接与集合创建（首次运行自动创建，避免小白手动建表）
def init_milvus():
    # 1.1 连接Milvus服务
    connections.connect(
        alias="default",
        host=MILVUS_CONFIG["host"],  # 本地部署填"localhost"
        port=MILVUS_CONFIG["port"]   # 填"19530"
    )
    
    # 1.2 定义集合Schema（必须明确字段，Milvus要求）
    fields = [
        # 主键字段（自增ID）
        FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        # 向量字段（all-MiniLM输出768维向量）
        FieldSchema(name="embedding", dtype=DataType.FLOAT_VECTOR, dim=768),
        # 元数据字段（比赛必须的：规范名、页码、条款号、文本内容）
        FieldSchema(name="doc_name", dtype=DataType.VARCHAR, max_length=255),
        FieldSchema(name="page", dtype=DataType.INT32),
        FieldSchema(name="clause_id", dtype=DataType.VARCHAR, max_length=50),
        FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=2000)
    ]
    schema = CollectionSchema(fields=fields, description="工程规范知识库")
    
    # 1.3 创建/获取集合（集合名从config.py读取，避免硬编码）
    collection = Collection(
        name=MILVUS_CONFIG["collection_name"],  # 比如"engineering_specs"
        schema=schema,
        using="default"
    )
    
    # 1.4 创建索引（提升检索速度，小白不用懂原理）
    index_params = {
        "index_type": "IVF_FLAT",  # 轻量索引，适合小样本场景
        "metric_type": "L2",       # 向量相似度计算方式
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="embedding", index_params=index_params)
    collection.load()  # 加载集合到内存（检索前必须）
    
    # 1.5 初始化LangChain的Milvus向量库（对接LangChain生态）
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    return Milvus(
        embedding_function=embeddings,
        collection_name=MILVUS_CONFIG["collection_name"],
        connection_args={"host": MILVUS_CONFIG["host"], "port": MILVUS_CONFIG["port"]}
    )

# 2. PDF处理函数（不变，重点确保元数据正确）
def load_pdf(file_path):
    loader = PyPDFLoader(file_path)
    docs = loader.load()
    # 后端需补充：给每个Document的metadata加关键信息（比赛核心）
    for doc in docs:
        doc.metadata["doc_name"] = file_path.split("/")[-1]  # 提取规范文件名
        doc.metadata["page"] = doc.metadata["page"] + 1  # PyPDFLoader页码从0开始，转成1开始
        doc.metadata["clause_id"] = ""  # 后端先手动标注，后期再自动提取（如用正则）
    # 文本分割（保持500字/段，适合检索）
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=500, chunk_overlap=50)
    return text_splitter.split_documents(docs)

# 3. RAG链（不变，仅检索源换成Milvus）
def build_rag_chain(vector_db):
    return RetrievalQA.from_chain_type(
        llm=OpenAI(api_key=MILVUS_CONFIG["openai_key"]),  # 或换开源模型（如Phi-2）
        chain_type="stuff",
        retriever=vector_db.as_retriever(search_kwargs={"k": 3}),  # 对应比赛Top-3
        return_source_documents=True  # 必须返回源文档，才能提取条款号/页码
    )