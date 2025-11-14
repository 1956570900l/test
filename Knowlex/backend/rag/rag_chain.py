# rag/rag_chain.py
# (V2 - 竞赛版: 纯检索 + Rerank)

from typing import Dict, List
from FlagEmbedding import FlagReranker
from pymilvus import MilvusClient

# 导入你的配置
from utils import config 
# 导入你的 vector_store 模块
from backend.knowledge_base import vector_store 

# --- 1. 初始化模型 (只需一次) ---

print("正在加载 Reranker 模型 (用于 Top-k 排序)...")
# (这个模型将极大提升你的 Top-1, Top-3 准确率)
reranker_model = FlagReranker(
    'BAAI/bge-reranker-large', # SOTA Reranker
    use_fp16=True # 如果你有 GPU，速度更快
)

print("正在加载 文本检索器 (用于初步召回)...")
# 这是 Milvus 的 LangChain 检索器，用于“粗召回”
text_retriever = vector_store.get_text_retriever()

print("正在连接 Milvus Client (用于图片检索)...")
# 这是 Milvus 的原生 SDK 客户端，用于“精确查询”
milvus_client = MilvusClient(uri=config.MILVUS_URI)


# --- 2. 核心检索管线 ---

def run_retrieval_pipeline(query: str) -> Dict:
    """
    运行完整的“图文联合检索”管线
    这完全符合竞赛要求
    """
    
    # === 步骤 1: 文本粗召回 (Retrieve) ===
    # 从 Milvus 中召回 10 个（我们在 vector_store.py 中设置的）相关的文本块
    retrieved_docs = text_retriever.get_relevant_documents(query)
    
    # === 步骤 2: 文本精排 (Rerank) ===
    # 这是刷 Top-1 和 Top-3 分数的核心
    
    # 1. 准备 [query, doc] 对
    sentence_pairs = [[query, doc.page_content] for doc in retrieved_docs]
    
    # 2. Reranker 打分
    scores = reranker_model.compute_score(sentence_pairs)
    
    # 3. 组合、排序，并选出 Top 3
    scored_docs = sorted(zip(scores, retrieved_docs), key=lambda x: x[0], reverse=True)
    [span_0](start_span)top_3_text_chunks = scored_docs[:3] # 这对应 Top-3 Recall[span_0](end_span)
    
    # === 步骤 3: 格式化 `clauses` (匹配提交要求) ===
    clauses_output = []
    # (用于下一步搜图)
    page_references = set() 
    
    for score, doc in top_3_text_chunks:
        meta = doc.metadata
        clauses_output.append({
            "content": doc.page_content,
            "doc_name": meta.get("doc_name"),
            "page": meta.get("page"),
            [span_1](start_span)"clause_id": meta.get("clause_id", ""), # 这对应 Top-1 Accuracy[span_1](end_span)
            "rerank_score": score
        })
        # 记录这些文本块所在的 (文件名, 页码)
        page_references.add((meta.get("doc_name"), meta.get("page")))

    # === 步骤 4: 图片关联检索 (图文联合) ===
    # [span_2](start_span)比赛要求：检索“对应的插图/节点图”[span_2](end_span)
    images_output = []
    if page_references:
        # 构造 Milvus 筛选表达式
        # 例如: (doc_name == 'A.pdf' AND page == 5) OR (doc_name == 'B.pdf' AND page == 10)
        filter_expr = " or ".join(
            f"(doc_name == '{name}' AND page == {page})" for name, page in page_references if name
        )
        
        try:
            # 在“图片集合”中查询
            image_results = milvus_client.query(
                collection_name=config.IMAGE_COLLECTION_NAME,
                filter=filter_expr,
                output_fields=["image_path", "doc_name", "page"],
                limit=10 # 最多返回 10 张关联图片
            )
            
            for res in image_results:
                images_output.append({
                    "image_path": res["image_path"],
                    "doc_name": res["doc_name"],
                    "page": res["page"]
                })
        except Exception as e:
            print(f"图片检索失败: {e}")

    # === 步骤 5: 返回最终结果 (匹配提交要求) ===
    # [span_3](start_span)这就是你提交的 results.jsonl 中 "answer" 字段的内容[span_3](end_span)
    return {
        "clauses": clauses_output,
        "images": images_output
    }