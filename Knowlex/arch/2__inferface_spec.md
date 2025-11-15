# 2_interface_spec.md：接口规范（适配Weaviate，全流程可落地）
## 一、接口设计核心原则
1. **紧扣比赛评分**：所有输入/输出必须强制包含 `doc_name`（规范文件名，带后缀）、`page`（页码，1开始）、`clause_id`（条款号，格式如“3.2.1”）—— 这三个字段直接影响“语义匹配分（50%）”和“Top-1 Accuracy（20%）”，缺失将直接丢分。
2. **零歧义可复制**：所有接口均提供“代码示例+字段说明+错误案例”，避免模糊描述（如“传文档”明确为“multipart/form-data格式，仅支持.pdf/.docx/.pptx”），小白可直接复制代码落地。
3. **强容错易调试**：所有接口必须返回 `status`（success/fail）和 `message`（结果说明/错误原因），异常场景（如知识库为空、参数缺失、Weaviate连接失败）需明确提示，无需猜错。
4. **Weaviate适配约束**：接口中涉及向量库的操作，统一指向Weaviate的 `EngineeringSpecs` Class（固定名称），向量维度统一为768（匹配all-MiniLM-L6-v2模型），避免检索异常。

## 二、模块间接口（后端内部：队友A ↔ 队友B，Weaviate专属）
### 1. 数据处理模块 → Weaviate知识库模块（接口名：docs_to_weaviate）
#### 功能说明
队友A将解析后的PDF文本+元数据，传入Weaviate知识库，完成向量转换与存储（核心：元数据与向量关联，支撑后续精准检索）。

#### 输入格式（队友A输出，必须严格遵循）
类型：LangChain Document列表（需导入langchain.schema.Document），元数据字段与Weaviate的EngineeringSpecs Class完全对齐：
```python
from langchain.schema import Document

# 单个Document示例（必含字段，缺一不可）
doc_example = Document(
    page_content="地下室穿墙管应采用止水环+防水卷材包裹，止水环厚度不小于5mm，卷材宽度需覆盖穿墙管周边100mm以上。",
    metadata={
        "doc_name": "建筑防水工程标准化工艺做法.pdf",  # 必选：规范文件名（带.pdf后缀）
        "page": 8,  # 必选：页码（1开始，PyPDFLoader默认0，需+1处理）
        "clause_id": "3.2.1",  # 必选：条款号（格式严格为“x.x.x”，初赛手动标注）
        "image_path": ""  # 可选：初赛可空，决赛填图片本地路径（如"./images/pipe_01.png"）
    }
)

# 最终传入的是Document列表（支持多段文本批量入库）
input_docs = [doc_example, doc_example2, doc_example3]  # 批量传入，提升效率

