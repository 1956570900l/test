# import weaviate
# import numpy as np
# import os
# from tqdm import tqdm

# # -------------------------- 核心配置（团队协作必看） --------------------------
# # 1. 向量文件路径（自动适配脚本所在目录，无论在哪运行脚本都能找到文件）
# # 脚本所在目录的绝对路径（__file__是当前脚本的路径）
# script_dir = os.path.dirname(os.path.abspath(__file__))  
# # 拼接向量文件路径：脚本目录/data/weaviate.npy（项目结构约定）
# VECTOR_FILE_PATH = os.path.join(script_dir, "Knowlex","tests", "weaviate.npy")  

# # 2. Weaviate核心配置
# WEAVIATE_URL = "http://localhost:8080"  # 本地服务地址（团队成员需确保Weaviate已启动）
# COLLECTION_NAME = "MyVectorDB"          # 向量集合名称（团队必须统一，否则访问的不是同一个数据集）
# VECTOR_DIM = 128                        # 向量维度（必须与实际向量维度一致）
# BATCH_SIZE = 1000                       # 每批导入数量（根据内存调整）
# RESUME_FROM = 0                         # 断点续传起始位置
# # ----------------------------------------------------------------------------

# def main():
#     # 检查向量文件是否存在（容错处理）
#     if not os.path.exists(VECTOR_FILE_PATH):
#         print(f"❌ 错误：未找到向量文件，实际路径：{VECTOR_FILE_PATH}")
#         print(f"💡 请确认项目结构是否符合约定：")
#         print(f"项目根目录/")
#         print(f"  ├─ 你的脚本.py（当前脚本）")
#         print(f"  └─ data/")
#         print(f"       └─ weaviate.npy（测试向量文件）")
#         return

#     # 连接Weaviate服务
#     try:
#         client = weaviate.Client(WEAVIATE_URL)
#         print("✅ 成功连接到Weaviate服务")
#     except Exception as e:
#         print(f"❌ 连接Weaviate失败：{e}")
#         print(f"💡 请先启动Weaviate服务（双击weaviate.exe或cmd运行）")
#         return

#     # 检查并创建集合（COLLECTION_NAME的核心作用区）
#     if not client.schema.exists(COLLECTION_NAME):
#         print(f"📂 集合'{COLLECTION_NAME}'不存在，正在创建...")
#         # 定义集合的schema（相当于数据库表结构）
#         schema = {
#             "class": COLLECTION_NAME,  # 集合名称（必须与COLLECTION_NAME一致）
#             "vectorizer": "none",      # 手动传入向量，不使用Weaviate内置向量化
#             "properties": [            # 元数据字段定义（类似数据库表的列）
#                 {"name": "vector_id", "dataType": ["int"]},  # 向量序号（唯一标识）
#                 {"name": "source_file", "dataType": ["string"]}  # 来源文件路径
#             ]
#         }
#         client.schema.create_class(schema)
#         print(f"✅ 集合'{COLLECTION_NAME}'创建成功")
#     else:
#         print(f"📂 集合'{COLLECTION_NAME}'已存在，直接导入数据")

#     # 加载向量文件（用memmap分块读取，避免内存溢出）
#     try:
#         vectors_memmap = np.memmap(
#             VECTOR_FILE_PATH,
#             dtype=np.float32,  # 向量数据类型（需与实际一致）
#             mode='r',
#             shape=(-1, VECTOR_DIM)  # 自动适配向量数量，固定维度
#         )
#         total_count = len(vectors_memmap)
#         print(f"📊 成功加载向量文件，共 {total_count} 条向量（维度：{VECTOR_DIM}）")
#     except Exception as e:
#         print(f"❌ 加载向量文件失败：{e}")
#         print(f"💡 请检查文件是否损坏，或维度是否与VECTOR_DIM一致")
#         return

#     # 分批导入向量
#     print(f"🚀 开始导入（从第 {RESUME_FROM} 条开始，每批 {BATCH_SIZE} 条）...")
#     for start in tqdm(range(RESUME_FROM, total_count, BATCH_SIZE), desc="导入进度"):
#         end = min(start + BATCH_SIZE, total_count)
#         batch_vectors = vectors_memmap[start:end]  # 当前批次向量（仅加载到内存）
#         batch_ids = [f"vec_{i}" for i in range(start, end)]  # 唯一ID
#         batch_metadatas = [
#             {"vector_id": i, "source_file": os.path.basename(VECTOR_FILE_PATH)}
#             for i in range(start, end)
#         ]

#         # 批量插入到集合中
#         with client.batch(batch_size=BATCH_SIZE) as batch:
#             for vec, vec_id, metadata in zip(batch_vectors, batch_ids, batch_metadatas):
#                 batch.add_data_object(
#                     data_object=metadata,  # 元数据
#                     vector=vec.tolist(),   # 向量数据
#                     class_name=COLLECTION_NAME,  # 指定插入到哪个集合
#                     uuid=vec_id  # 自定义ID（方便后续查询/删除）
#                 )
#         print(f"✅ 已导入 {end}/{total_count} 条向量")

#     print("🎉 所有向量导入完成！可通过集合名'{COLLECTION_NAME}'查询数据")

# if __name__ == "__main__":
#     main()
import weaviate

# 连接到 Weaviate（端口与启动时一致，这里用6981）
client = weaviate.Client("http://localhost:6981")

# 1. 测试连接是否成功
try:
    client.is_ready()  # 检查服务状态
    print("✅ 服务连接成功")
except Exception as e:
    print(f"❌ 服务连接失败：{e}")
    exit()

# 2. 测试创建集合（表）
test_collection = "TestCollection"
if not client.schema.exists(test_collection):
    client.schema.create_class({
        "class": test_collection,
        "vectorizer": "none"  # 手动传入向量
    })
    print(f"✅ 集合 '{test_collection}' 创建成功")
else:
    print(f"ℹ️ 集合 '{test_collection}' 已存在")

# 3. 测试插入一条向量
sample_vector = [0.1] * 128  # 128维测试向量
client.data_object.create(
    data_object={"name": "test_vector"},
    vector=sample_vector,
    class_name=test_collection
)
print("✅ 向量插入成功")

# 4. 测试检索向量
results = client.query.get(
    test_collection, ["name"]
).with_near_vector({"vector": sample_vector}).with_limit(1).do()
print("检索结果：", results)
print("✅ 向量检索成功，服务完全可用")