# 1_arch_diagram.md：系统架构与分工说明
## 一、架构核心目标
1. 支撑初赛：实现“文档上传→知识库构建→问题检索→生成 results.jsonl”全链路，确保符合比赛格式要求（含规范编号、条款号、原文）。
2. 预留决赛：兼容 Milvus 大规模知识库扩展，支持后续图文联合检索、工程部署（Docker 封装）。
3. 分工明确：3人团队（架构+前端+后端）无重叠，每个模块对应唯一负责人，降低协作成本。


## 二、文字版架构图（含数据流向+技术栈）
### 1. 整体链路（从用户输入到输出）

### 2. 模块拆解与数据流向（按流程顺序）
| 流程步骤 | 负责模块         | 负责人   | 核心功能                                  | 技术栈                          | 数据输入                          | 数据输出                          |
|----------|------------------|----------|-------------------------------------------|---------------------------------|-----------------------------------|-----------------------------------|
| 1        | 前端上传页       | 队友C    | 接收用户上传的比赛规范文档（PDF/Word/PPT） | HTML+CSS+Jinja2                 | 用户选择的本地文档                | 文档文件流 → 后端数据处理模块     |
| 2        | 数据处理模块     | 队友A    | 解析文档，提取“文本+元数据”（关键：条款号、页码） | LangChain PyPDFLoader/ python-docx | 前端传来的文档文件流              | LangChain Document 列表（含 doc_name/page/clause_id） |
| 3        | 知识库模块       | 队友A    | 将 Document 转向量，存入 Milvus           | Milvus + pymilvus +  sentence-transformers | 数据处理模块输出的 Document 列表  | 向量化数据（关联元数据）存入 Milvus |
| 4        | 前端问答页       | 队友C    | 接收用户输入的工程风险问题（如“地下室穿墙管渗漏”） | HTML+CSS+Jinja2                 | 用户输入的问题文本                | 问题文本 → 后端 RAG 模块          |
| 5        | RAG 检索模块     | 队友B    | 调用 Milvus 检索 Top-3 匹配条款，结合 LLM 生成答案 | LangChain RetrievalQA + OpenAI/开源LLM | 前端传来的问题文本                | 带元数据的 Top-3 结果（含 doc_name/page/clause_id/content） |
| 6        | 结果生成模块     | 队友B    | 按比赛要求生成 results.jsonl 文件          | Python jsonlines 库             | RAG 模块输出的 Top-3 结果         | 符合比赛格式的 results.jsonl      |
| 7        | 前端导出页       | 队友C    | 提供 results.jsonl 下载入口                | HTML+CSS+Jinja2                 | 后端返回的 jsonlines 文件流       | 下载文件到用户本地（用于比赛提交） |


## 三、核心模块分工表（避免推诿，明确责任）
| 角色   | 负责模块         | 具体任务清单                                  | 交付物（可验证）                          | 依赖项（需架构提供）                          |
|--------|------------------|-----------------------------------------------|-------------------------------------------|-------------------------------------------|
| 架构   | 全局协调         | 1. 编写架构文档（本文件+接口规范+Milvus部署指南）<br>2. 解决跨模块问题（如 Milvus 连接失败、接口格式不匹配）<br>3. 验证最终结果是否符合比赛要求 | 1. arch/ 下3个文档<br>2. 联调测试清单<br>3. 合格的 results.jsonl 样例 | 无（主导提供支持）                          |
| 前端（队友C） | 前端3个页面      | 1. 美化 upload.html（文档上传页）：加进度提示、格式校验（仅允许 PDF/Word/PPT）<br>2. 美化 query.html（问答页）：清晰展示 Top-3 条款（突出规范编号+条款号）<br>3. 美化 export.html（导出页）：加下载按钮、历史查询记录 | 1. 3个可访问的 HTML 页面（localhost:8000 可打开）<br>2. 页面间跳转正常（上传→问答→导出） | 1. 前后端接口规范（2_interface_spec.md）<br>2. 前端模板（arch/4_scaffold/frontend_tpl） |
| 后端（队友A） | 数据处理+知识库  | 1. 写 pdf_processor.py：提取 PDF 文本+元数据（doc_name/page/clause_id，初期手动标注条款号）<br>2. 写 vector_store.py：实现 Milvus 连接、数据写入、检索<br>3. 测试：上传 PDF 后，Milvus 能查到对应数据 | 1. 上传1个 PDF 后，输出含元数据的 Document 列表<br>2. Milvus 集合（engineering_specs）有数据<br>3. 调用检索函数能返回匹配结果 | 1. Milvus 部署指南（3_milvus_deploy.md）<br>2. 后端基础脚手架（arch/4_scaffold/backend_base.py） |
| 后端（队友B） | RAG+结果生成+API | 1. 写 rag_chain.py：用 LangChain 构建 RAG 链，返回 Top-3 结果<br>2. 写 result_generator.py：生成 results.jsonl<br>3. 写 main.py：实现 FastAPI 接口（/api/upload_docs、/api/query_single、/api/export_results） | 1. 输入问题能返回含条款号的 Top-3 结果<br>2. 导出的 results.jsonl 符合比赛格式<br>3. 3个 API 能正常调用 | 1. 模块间接口规范（2_interface_spec.md）<br>2. 队友A提供的检索函数 |


## 四、当前重点 vs 后期扩展（避免一开始做复杂功能）
| 阶段   | 模块重点（初赛必须完成）                          | 后期扩展（决赛加分）                          |
|--------|-----------------------------------|-------------------------------------------|
| 数据处理 | 仅处理 PDF，手动标注 clause_id（保证准确性） | 支持 Word/PPT 解析，自动识别 clause_id（用正则/LLM） |
| 知识库   | Milvus 单集合存储，基础索引（IVF_FLAT） | Milvus 分集合（按规范类型分类），优化索引（HNSW） |
| RAG 检索  | 文本语义检索，返回 Top-3 文本结果 | 图文联合检索（图片转向量），结果重排序（提升准确率） |
| 前端     | 基础功能（上传/问答/导出），无样式要求 | 美化界面（加工程相关主题），支持图片预览、条款高亮 |
| 工程部署 | 本地运行，无部署要求 | Docker 封装（一键启动全服务），支持 Linux 服务器部署 |