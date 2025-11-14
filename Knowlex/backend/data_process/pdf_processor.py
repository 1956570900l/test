# backend/pdf_processor.py (示意代码)

from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
# ... (你的 PyPDFLoader 或其他加载器)

def process_all_pdfs(data_dir: str) -> List[Document]:
    # ... (你加载 PDF 文件的逻辑)
    
    all_docs = []
    
    # 示例：假设你正在遍历一个 PDF
    file_name = "example.pdf" 
    
    # (你的 PyPDFLoader 加载逻辑)
    # loader = PyPDFLoader(...) 
    # pages = loader.load_and_split() # 这是一个旧的方法
    
    # (推荐的逻辑)
    # loader = ... 
    # raw_pages = loader.load() # 加载原始页面
    
    text_splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    
    for page in raw_pages:
        page_content = page.page_content
        page_number = page.metadata.get("page", 0) # 从加载器获取页码
        
        # 切分
        chunks = text_splitter.split_text(page_content)
        
        for chunk in chunks:
            # --- 这是关键 ---
            # 架构师要求你在这里添加元数据
            new_metadata = {
                "doc_name": file_name, 
                "page": page_number + 1, # 页码通常从 1 开始
                "clause_id": "temp-123" # 你需要实现逻辑从 chunk 中提取条款 ID
            }
            
            all_docs.append(Document(
                page_content=chunk,
                metadata=new_metadata # 关键：传入元数据
            ))
            
    return all_docs