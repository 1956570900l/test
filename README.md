Knowlex/
├── arch/               # 架构专属工作区（设计+规范+部署指南）
│   ├── 1_arch_diagram.md  # 架构图：补充Milvus服务节点（数据层→Milvus）
│   ├── 2_interface_spec.md # 接口规范：仅调整知识库模块输入输出（适配Milvus）
│   ├── 3_milvus_deploy.md # Milvus部署指南（Docker一键启动，小白能照做）
│   └── 4_scaffold/      # 适配Milvus的脚手架代码
│       ├── backend_base.py # 后端基础：LangChain+Milvus初始化/检索
│       └── frontend_tpl/  # 前端模板不变（无需适配向量库）
├── backend/            # 核心代码（仅知识库模块适配Milvus）
│   ├── data_process/   # 数据处理（不变，仍输出带元数据的Document）
│   │   └── pdf_processor.py  # 重点：给Document加`doc_name`/`page`/`clause_id`元数据
│   ├── knowledge_base/ # 知识库（替换为Milvus，核心调整点）
│   │   ├── vector_store.py  # Milvus连接、数据写入、检索（架构给脚手架）
│   │   └── meta_store.py    # 元数据管理（与Milvus关联，不用额外数据库）
│   ├── rag/            # RAG链（不变，仍调用知识库检索结果）
│   │   └── rag_chain.py    # 用LangChain RetrievalQA，仅改检索源为Milvus
│   ├── output/         # 结果生成（不变，仍输出results.jsonl）
│   │   └── result_generator.py  
│   ├── api/            # 接口层（不变，FastAPI对接前端）
│   │   └── main.py     
│   └── utils/          # 通用工具（新增Milvus配置）
│       └── config.py   # 加Milvus连接参数（host/port/collection_name）
├── frontend/           # 前端（完全不变）
│   ├── upload.html     # 文档上传页
│   ├── query.html      # 问答展示页
│   └── export.html     # 结果导出页
├── docker-compose.yml  # 架构新增：Milvus standalone部署配置（小白一键启动）
├── requirements.txt    # ？？？暂时未知
└── README.md           #说明系统