# 2_interface_spec.md：接口规范（模块间+前后端）
## 一、接口设计原则
1. 必须包含比赛评分关键信息：所有接口的输入/输出必须携带 `doc_name`（规范文件名）、`page`（页码）、`clause_id`（条款号），否则影响“Top-1 Accuracy”和“语义匹配分”。
2. 小白友好：用“示例代码+表格”明确格式，避免模糊描述（如“传文档”→ 明确“传 multipart/form-data 格式的文件列表”）。
3. 兼容性：预留扩展字段（如 `images` 字段，初赛可空，决赛填图片路径），避免后期改接口。


## 二、模块间接口（后端内部：队友A → 队友B）
### 1. 数据处理模块 → 知识库模块（接口名：send_docs_to_milvus）
#### 功能说明
队友A将解析后的 PDF 文本+元数据，传给队友B的知识库模块，用于存入 Milvus。

#### 输入格式（队友A输出，队友B接收）
类型：LangChain Document 列表（每个 Document 含 `page_content` 和 `metadata`）  
示例代码：
```python
from langchain.schema import Document

# 单个 Document 示例
doc1 = Document(
    page_content="地下室穿墙管应采用止水环+防水卷材包裹，止水环厚度不小于5mm，卷材宽度应覆盖穿墙管周边100mm以上。",
    metadata={
        "doc_name": "建筑防水工程标准化工艺做法.pdf",  # 必选：规范文件名（含后缀）
        "page": 8,  # 必选：页码（1开始，PyPDFLoader默认0开始，需+1）
        "clause_id": "3.2.1",  # 必选：条款号（比赛要求，初期手动标注）
        "image_path": ""  # 可选：图片路径（初赛可空，决赛补充）
    }
)
#输出格式（队友 B 返回给队友 A）类型：JSON（告知数据是否成功入库）
# 传给知识库模块的是 Document 列表
docs_list = [doc1, doc2, doc3]  # 多个 Document 组成列表
{
    "status": "success",  # "success" 或 "fail"
    "message": "3个Document成功存入Milvus",
    "data": {
        "total_docs": 3,  # 入库的 Document 总数
        "collection_name": "engineering_specs",  # 存入的 Milvus 集合名
        "insert_ids": [1001, 1002, 1003]  # Milvus 自动生成的主键ID（用于后续查询）
    }
}
####若 metadata 缺少 doc_name/page/clause_id：返回 status: fail，提示 “元数据不完整，缺少 xx 字段”。
####若 Milvus 连接失败：返回 status: fail，提示 “Milvus 连接超时，请检查服务是否启动”。
```

