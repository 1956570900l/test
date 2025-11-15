# 3_weaviate_deploy.md：Weaviate部署指南（单机版，小白全流程落地）
## 一、部署目标
1. 快速启动Weaviate社区版（免费无授权），支撑初赛小样本知识库（10-20个规范文档，约1000-2000条条款）；
2. 数据持久化到项目目录内，删除容器不丢失数据（适配多人先后开发，避免重复入库）；
3. 适配项目技术栈（LangChain+Python），确保后端模块能正常连接、读写数据；
4. 提供问题排查方案，队友遇到部署问题可自主解决，无需依赖架构师。

## 二、前置条件（必装软件，架构师先验证，队友按步骤装）
### 1. 安装Docker（核心依赖，所有开发人员必须装）
Weaviate基于Docker运行，需先安装Docker Desktop（Windows/Mac）或Docker引擎（Linux），步骤如下：
#### （1）Windows/Mac安装
1. 下载地址：https://www.docker.com/products/docker-desktop/（官网免费下载）；
2. 安装：双击安装包，一路默认下一步（Windows需勾选“使用WSL 2而非Hyper-V”，Mac无需额外设置）；
3. 验证：安装完成后启动Docker Desktop，等待状态栏变绿（显示“Docker Desktop running”），表示启动成功。

#### （2）Linux（Ubuntu为例）安装
1. 打开终端，逐行执行以下命令（复制粘贴即可，避免手动输入错误）：
```bash
# 更新apt源
sudo apt-get update
# 安装Docker依赖
sudo apt-get install -y apt-transport-https ca-certificates curl software-properties-common
# 添加Docker官方GPG密钥
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo apt-key add -
# 添加Docker源
sudo add-apt-repository "deb [arch=amd64] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable"
# 安装Docker
sudo apt-get update && sudo apt-get install -y docker-ce docker-ce-cli containerd.io
# 启动Docker服务
sudo systemctl start docker
# 设置Docker开机自启
sudo systemctl enable docker
# 验证安装（输出Docker版本即成功）
docker --version