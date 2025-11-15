import chroma  as chromadb

# 1. 数据存到D盘指定文件夹（D:\xxx，自动创建，无需手动建）
client = chromadb.PersistentClient(path=r"D:\xxx")  # 路径改为D盘的xxx文件夹

# 2. 关键：先判断集合是否存在，存在则获取，不存在才创建（避免重复报错）
collection_name = "my_collection"
if collection_name in client.list_collections():
    # 集合已存在，直接获取
    collection = client.get_collection(name=collection_name)
    print(f"✅ 已获取现有集合：{collection_name}")
else:
    # 集合不存在，创建新集合
    collection = client.create_collection(name=collection_name)
    print(f"✅ 已创建新集合：{collection_name}")

# 3. 插入数据（加判断：避免重复插入同一条id的数据）
data_id = "id1"
if data_id not in collection.get(ids=[data_id])["ids"]:  # 检查id是否已存在
    collection.add(
        documents=["这是测试文本，用于验证Chroma是否正常运行"],
        metadatas=[{"source": "test"}],
        ids=[data_id]
    )
    print("✅ 数据插入成功")
else:
    print("✅ 数据已存在，无需重复插入")

# 4. 查询测试
results = collection.query(
    query_texts=["测试"],
    n_results=1
)
print("查询到的文本：", results["documents"][0][0])
