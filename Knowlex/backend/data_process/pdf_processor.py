# backend/data_process/pdf_processor.py
# (V2 - 图文多模态版)

import os
import fitz  # PyMuPDF
from PIL import Image
import io
from typing import List, Tuple, Dict
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document
from tqdm import tqdm # (pip install tqdm) 用于显示进度条
from utils import config # 导入我们的配置

def process_all_pdfs() -> Tuple[List[Document], List[Dict]]:
    """
    加载 data/ 目录下的所有 PDF。
    - 提取文本，切块，返回 LangChain Document 列表
    - 提取图片，保存，返回图片元数据列表
    """
    data_dir = config.DATA_DIR
    output_image_dir = config.OUTPUT_IMAGE_PATH
    os.makedirs(output_image_dir, exist_ok=True) # 确保输出目录存在
    
    print(f"--- (升级版) 开始从 {data_dir} 加载 PDF (图文) ---")
    
    all_text_docs: List[Document] = [] # 存储所有文本块
    all_image_infos: List[Dict] = []  # 存储所有图片元数据
    
    if not os.path.exists(data_dir):
        print(f"错误: 目录 {data_dir} 不存在。")
        return [], []

    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, 
        chunk_overlap=100
    )

    for filename in os.listdir(data_dir):
        if not filename.endswith(".pdf"):
            continue
            
        file_path = os.path.join(data_dir, filename)
        print(f"\n正在处理: {filename}")
        
        doc = fitz.open(file_path)
        
        for page_num in tqdm(range(len(doc)), desc=f"  > 遍历 {filename}"):
            page = doc.load_page(page_num)
            
            # 1. --- 处理文本 ---
            page_text = page.get_text("text")
            if page_text:
                chunks = text_splitter.split_text(page_text)
                for chunk in chunks:
                    new_metadata = {
                        "doc_name": filename,
                        "page": page_num + 1,
                        "clause_id": "" # 占位符
                    }
                    all_text_docs.append(Document(
                        page_content=chunk,
                        metadata=new_metadata
                    ))
            
            # 2. --- 处理图片 ---
            image_list = page.get_images(full=True)
            for img_index, img in enumerate(image_list):
                xref = img[0] # 图片的引用 ID
                
                try:
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    image_ext = base_image["ext"]
                    
                    # 生成唯一的图片保存路径
                    img_filename = f"{filename}_p{page_num+1}_img{img_index}.{image_ext}"
                    img_save_path = os.path.join(output_image_dir, img_filename)
                    
                    # 保存图片到 output/images/
                    with open(img_save_path, "wb") as f:
                        f.write(image_bytes)

                    # [span_0](start_span)比赛要求：输出“对应的插图/节点图”[span_0](end_span)
                    # 我们将图片元数据存起来，用于入库
                    all_image_infos.append({
                        "image_path": img_save_path, # 关键：图片路径
                        "doc_name": filename,
                        "page": page_num + 1
                    })
                except Exception as e:
                    print(f"  > 处理图片 {xref} 失败: {e}")

        doc.close()

    print(f"--- 所有 PDF 处理完毕 ---")
    print(f"  > 共提取 {len(all_text_docs)} 个文本块")
    print(f"  > 共提取 {len(all_image_infos)} 张图片")
    
    # 返回两个列表
    return all_text_docs, all_image_infos