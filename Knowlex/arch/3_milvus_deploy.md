# docker-compose.yml（架构编写，团队直接运行docker-compose up -d）
version: '3.8'
services:
  milvus-standalone:
    image: milvusdb/milvus:v2.3.5  # 稳定版本，适配pymilvus
    container_name: milvus-standalone
    restart: always
    environment:
      - MILVUS_ROOT_PATH=/var/lib/milvus
    volumes:
      - ./milvus_data:/var/lib/milvus
    ports:
      - "19530:19530"  # Milvus服务端口（后端连接用）
      - "9091:9091"    # 健康检查端口（不用管）
    networks:
      - milvus-network

networks:
  milvus-network:
    driver: bridge