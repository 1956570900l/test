 # utils/config.py

# --- Milvus 配置 (1号 架构师) ---
MILVUS_HOST = "localhost"  # 或 "127.0.0.1"
MILVUS_PORT = "19530"      # Docker 映射的端口
MILVUS_URI = f"http://{MILVUS_HOST}:{MILVUS_PORT}"

# --- Collection (表) 配置 ---
TEXT_COLLECTION_NAME = "knowlex_texts"

# --- 嵌入模型配置 ---
# (我们用 moka-ai/m3e-base, 它是 768 维)
EMBEDDING_MODEL_NAME = "moka-ai/m3e-base"
TEXT_EMBEDDING_DIM = 768 

# --- LLM 配置 ---
LLM_MODEL_NAME = "gpt-3.5-turbo"

# --- 数据路径 ---
DATA_DIR = "./data" # 存放 PDF 的目录

# 1. 提取的图片存放路径
OUTPUT_IMAGE_PATH = "./output/images" 

# 2. Milvus 中的“图片集合”名称
IMAGE_COLLECTION_NAME = "knowlex_images"

# 3. 图片嵌入模型 (CLIP)
IMAGE_EMBEDDING_MODEL = "openai/clip-vit-base-patch32"
IMAGE_EMBEDDING_DIM = 512 # CLIP-base 模型的维度