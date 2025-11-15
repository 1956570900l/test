from pymilvus import (
    connections, 
    utility,
    Collection, 
    FieldSchema, 
    CollectionSchema, 
    DataType
)
import numpy as np
import random

class MilvusVectorDB:
    """Milvus向量数据库实用类"""
    
    def __init__(self, host="localhost", port="19530"):
        self.host = host
        self.port = port
        self.collection = None
        self.connected = False
        
    def connect(self):
        """连接Milvus数据库"""
        try:
            connections.connect(
                alias="default", 
                host=self.host, 
                port=self.port,
                timeout=10
            )
            self.connected = True
            print(f"✅ 成功连接到Milvus: {self.host}:{self.port}")
            return True
        except Exception as e:
            print(f"❌ 连接失败: {e}")
            return False
    
    def create_collection(self, collection_name, vector_dim=768):
        """创建向量集合"""
        if not self.connected:
            print("❌ 请先连接数据库")
            return False
            
        # 如果集合已存在，删除重建
        if utility.has_collection(collection_name):
            utility.drop_collection(collection_name)
            print(f"🗑️ 删除已存在的集合: {collection_name}")
        
        # 定义字段
        fields = [
            FieldSchema(name="id", dtype=DataType.INT64, is_primary=True, auto_id=True),
            FieldSchema(name="vector", dtype=DataType.FLOAT_VECTOR, dim=vector_dim),
            FieldSchema(name="content", dtype=DataType.VARCHAR, max_length=1000),
            FieldSchema(name="category", dtype=DataType.VARCHAR, max_length=100)
        ]
        
        # 创建集合
        schema = CollectionSchema(fields, f"向量数据库集合: {collection_name}")
        self.collection = Collection(name=collection_name, schema=schema)
        print(f"✅ 创建集合: {collection_name}, 向量维度: {vector_dim}")
        return True
    
    def insert_data(self, vectors, contents, categories):
        """插入向量数据"""
        if not self.collection:
            print("❌ 请先创建集合")
            return False
        
        # 插入数据
        data = [vectors, contents, categories]
        insert_result = self.collection.insert(data)
        self.collection.flush()
        print(f"✅ 插入 {len(insert_result.primary_keys)} 条数据")
        return True
    
    def create_hnsw_index(self):
        """创建HNSW索引"""
        if not self.collection:
            print("❌ 请先创建集合")
            return False
            
        index_params = {
            "index_type": "HNSW",
            "metric_type": "L2",
            "params": {
                "M": 16,
                "efConstruction": 200
            }
        }
        
        self.collection.create_index(field_name="vector", index_params=index_params)
        print("✅ HNSW索引创建成功")
        return True
    
    def search_similar(self, query_vector, top_k=5):
        """相似向量搜索"""
        if not self.collection:
            print("❌ 请先创建集合")
            return None
        
        # 加载集合到内存
        self.collection.load()
        
        # 搜索参数
        search_params = {
            "metric_type": "L2", 
            "params": {"ef": 50}
        }
        
        # 执行搜索
        results = self.collection.search(
            data=query_vector,
            anns_field="vector",
            param=search_params,
            limit=top_k,
            output_fields=["content", "category"]
        )
        
        return results
    
    def get_collection_info(self):
        """获取集合信息"""
        if not self.collection:
            return "无活跃集合"
        
        info = f"集合名称: {self.collection.name}\n"
        info += f"实体数量: {self.collection.num_entities}\n"
        
        try:
            index_info = self.collection.index()
            info += f"索引类型: {index_info.params['index_type']}\n"
            info += f"度量方式: {index_info.params['metric_type']}"
        except:
            info += "索引状态: 未创建"
            
        return info

def generate_sample_data(num_samples=1000, vector_dim=768):
    """生成示例数据"""
    # 生成随机向量
    vectors = np.random.rand(num_samples, vector_dim).astype(np.float32)
    
    # 示例文本内容
    sample_contents = [
        "机器学习算法研究",
        "深度学习模型应用", 
        "自然语言处理技术",
        "计算机视觉项目",
        "数据分析与可视化",
        "人工智能发展趋势",
        "神经网络优化方法",
        "大数据处理技术",
        "云计算平台架构",
        "物联网应用开发"
    ]
    
    categories = ["AI", "ML", "NLP", "CV", "Data", "Cloud", "IoT"]
    
    contents = []
    category_list = []
    
    for i in range(num_samples):
        content = f"{random.choice(sample_contents)} - 示例{i}"
        contents.append(content)
        category_list.append(random.choice(categories))
    
    return vectors, contents, category_list

def main():
    """主函数演示"""
    print("🚀 Milvus向量数据库演示")
    print("=" * 50)
    
    # 创建向量数据库实例
    vector_db = MilvusVectorDB(host="localhost", port="19530")
    
    # 连接数据库
    if not vector_db.connect():
        print("💡 请确保Milvus服务已启动")
        print("启动命令: milvus-server --data ./milvus_data")
        return
    
    # 创建集合
    collection_name = "ai_documents"
    vector_db.create_collection(collection_name, vector_dim=768)
    
    # 生成示例数据
    print("📊 生成示例数据...")
    vectors, contents, categories = generate_sample_data(num_samples=1000)
    
    # 插入数据
    vector_db.insert_data(vectors, contents, categories)
    
    # 创建HNSW索引
    vector_db.create_hnsw_index()
    
    # 显示集合信息
    print("\n📋 集合信息:")
    print(vector_db.get_collection_info())
    
    # 执行相似性搜索
    print("\n🔍 执行相似性搜索...")
    query_vector = np.random.rand(1, 768).astype(np.float32)
    results = vector_db.search_similar(query_vector, top_k=3)
    
    if results:
        print("\n搜索结果:")
        for i, hit in enumerate(results[0]):
            content = hit.entity.get('content', 'N/A')
            category = hit.entity.get('category', 'N/A')
            print(f"{i+1}. 相似度: {1-hit.distance:.4f}, 分类: {category}")
            print(f"   内容: {content}")
    
    print("\n🎉 向量数据库演示完成!")

if __name__ == "__main__":
    main()
