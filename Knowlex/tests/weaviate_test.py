import weaviate
import numpy as np
import os
from tqdm import tqdm  # 用于显示进度条，需提前安装：pip install tqdm

# -------------------------- 配置参数（请根据实际情况修改） --------------------------
VECTOR_FILE_PATH = r"D:\your_vectors.npy"  # 本地.npy向量文件路径（1GB左右）
WEAVIATE_URL = "http://localhost:8080"     # Weaviate服务地址（默认本地）
COLLECTION_NAME = "MyVectorDB"             # 集合名称（与之前创建的保持一致）
VECTOR_DIM = 128                           # 向量维度（需与你的向量实际维度一致）
BATCH_SIZE = 1000                          # 每批导入数量（可根据内存调整，建议500-2000）
RESUME_FROM = 0                            # 断点续传：从第N条开始（0表示从头开始）
# ----------------------------------------------------------------------------------

def main():
    # 1. 连接Weaviate
    try:
        client = weaviate.Client(WEAVIATE_URL)
        print("成功连接到Weaviate")
    except Exception as e:
        print(f"连接Weaviate失败，请检查服务是否启动：{e}")
        return

    # 2. 检查并创建集合（确保向量维度匹配）
    if not client.schema.exists(COLLECTION_NAME):
        print(f"创建集合 {COLLECTION_NAME}（维度：{VECTOR_DIM}）...")
        schema = {
            "class": COLLECTION_NAME,
            "vectorizer": "none",  # 手动传入向量
            "properties": [
                {"name": "vector_id", "dataType": ["int"]},  # 向量唯一ID（用于追踪）
                {"name": "source_file", "dataType": ["string"]}  # 来源文件（可自定义其他元数据）
            ]
        }
        client.schema.create_class(schema)
    else:
        print(f"集合 {COLLECTION_NAME} 已存在，直接导入数据")

    # 3. 加载.npy向量文件（使用memmap避免一次性加载1GB数据到内存）
    try:
        # 用memmap模式打开大文件，仅读取需要的批次数据到内存
        vectors_memmap = np.memmap(
            VECTOR_FILE_PATH,
            dtype=np.float32,  # 假设向量是float32格式（根据实际情况修改）
            mode='r',
            shape=(-1, VECTOR_DIM)  # 自动推断样本数，固定维度
        )
        total_count = len(vectors_memmap)
        print(f"成功加载向量文件，共 {total_count} 条向量（维度：{VECTOR_DIM}）")
    except Exception as e:
        print(f"加载向量文件失败：{e}")
        return

    # 4. 分批导入向量
    print(f"开始导入（从第 {RESUME_FROM} 条开始，每批 {BATCH_SIZE} 条）...")
    for start in tqdm(range(RESUME_FROM, total_count, BATCH_SIZE), desc="导入进度"):
        end = min(start + BATCH_SIZE, total_count)
        batch_vectors = vectors_memmap[start:end]  # 读取当前批次向量（仅加载到内存）

        # 准备当前批次的ID和元数据
        batch_ids = [f"vec_{i}" for i in range(start, end)]  # 唯一ID（格式：vec_0, vec_1...）
        batch_metadatas = [
            {"vector_id": i, "source_file": os.path.basename(VECTOR_FILE_PATH)}
            for i in range(start, end)
        ]

        # 批量插入到Weaviate
        with client.batch(batch_size=BATCH_SIZE) as batch:
            for vec, vec_id, metadata in zip(batch_vectors, batch_ids, batch_metadatas):
                batch.add_data_object(
                    data_object=metadata,
                    vector=vec.tolist(),  # 转换为列表（Weaviate要求）
                    class_name=COLLECTION_NAME,
                    uuid=vec_id  # 用自定义ID，方便后续追踪
                )

        # 每批导入后打印进度
        print(f"已导入 {end}/{total_count} 条向量")

    print("所有向量导入完成！")

if __name__ == "__main__":
    main()