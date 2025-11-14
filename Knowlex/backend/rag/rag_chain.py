# rag/rag_chain.py

from langchain.chains import RetrievalQA
from langchain_openai import ChatOpenAI
# 导入我们新的 vector_store 模块
from backend import vector_store 

def get_rag_chain():
    """
    创建 RAG 链, 检索源改为 Milvus
    """
    
    # 1. 获取 LangChain 的 Milvus 存储实例
    milvus_store = vector_store.get_langchain_milvus_store()
    
    # 2. 创建 Milvus 检索器 (Retriever)
    retriever = milvus_store.as_retriever(
        search_type="similarity", # 纯向量搜索
        search_kwargs={"k": 5}    # 召回 5 个
    )
    
    # 3. 创建 RetrievalQA 链 (架构师点名要的)
    rag_chain = RetrievalQA.from_chain_type(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        chain_type="stuff", # "stuff" 是最基础的 RAG
        retriever=retriever,
        return_source_documents=True # 方便前端展示来源
    )
    
    print("RAG 链 (Milvus 源) 创建成功。")
    return rag_chain

# 在文件末尾立即创建实例，方便 api/main.py 导入
rag_chain = get_rag_chain()
