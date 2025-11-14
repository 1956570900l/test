# backend/data_process/pdf_processor.py

import os
from langchain_community.document_loaders import PyPDFLoader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from  typing import List
from utils import config # 导入我们的配置

def process_all_pdfs() -> List[Document]:
    """
    加载 data/ 目录下的所有 PDF，切分并添加元数据。
    """
    data_dir = config.DATA_DIR
    print(f"--- 开始从 {data_dir} 加载 PDF ---")
    
    all_docs = [] # 存储所有处理后的 Document 块
    
    if not os.path.exists(data_dir):
        print(f"错误: 目录 {data_dir} 不存在。")
        return []

    for filename in os.listdir(data_dir):
        if filename.endswith(".pdf"):
            file_path = os.path.join(data_dir, filename)
            print(f"正在处理: {filename}")
            
            # 1. 加载 PDF
            loader = PyPDFLoader(file_path)
            raw_pages = loader.load() # 加载所有页面
            
            # 2. 初始化切分器
            text_splitter = RecursiveCharacterTextSplitter(
                chunk_size=1000, 
                chunk_overlap=100
            )

            print(f"  > 已加载 {len(raw_pages)} 页。开始切分...")
            
            # 3. 遍历页面、切分、添加元数据
            for page in raw_pages:
                page_content = page.page_content
                page_number = page.metadata.get("page", 0) # PyPDFLoader 自动提供页码
                
                chunks = text_splitter.split_text(page_content)
                
                for chunk in chunks:
                    # --- 关键：按架构要求添加元数据 ---
                    new_metadata = {
                        "doc_name": filename, 
                        "page": page_number + 1, # 页码从 1 开始
                        "clause_id": "" # 占位符，你可以实现逻辑从 chunk 中提取
                    }
                    
                    all_docs.append(Document(
                        page_content=chunk,
                        metadata=new_metadata # 传入元数据
                    ))
            
            print(f"  > {filename} 处理完毕，生成 {len(all_docs)} 个块。")

    print(f"--- 所有 PDF 处理完毕，共 {len(all_docs)} 个文档块 ---")
    return all_docs