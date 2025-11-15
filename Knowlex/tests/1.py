import time
from pymilvus import connections, utility

def connect_milvus_lite(retries=3):
    """可靠的 Milvus Lite 连接函数"""
    for i in range(retries):
        try:
            # 尝试连接
            connections.connect(alias="default", host="127.0.0.1", port=19530)
            
            # 验证连接
            version = utility.get_server_version()
            print(f"✅ 成功连接到 Milvus Lite，版本: {version}")
            return True
            
        except Exception as e:
            print(f"尝试 {i+1}/{retries} 失败: {e}")
            if i < retries - 1:
                print("等待 5 秒后重试...")
                time.sleep(5)
    
    print("❌ 所有连接尝试均失败，请检查服务状态")
    return False

# 使用连接函数
if connect_milvus_lite():
    # 这里放置你的业务代码
    print("可以继续执行数据操作...")