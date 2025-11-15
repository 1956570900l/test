# 3_chroma_deploy.md：Chroma向量库部署指南（初赛专用，Windows适配）
## 一、为什么初赛选Chroma？
1. **零依赖部署**：无需Docker、数据库，纯Python库安装，一行命令搞定，适合快速开发；
2. **数据本地化**：向量数据直接存在项目目录内，压缩后可随代码一起共享，队友无需重复入库；
3. **适配接口规范**：支持`doc_name`/`page`/`clause_id`等元数据存储，与`2_interface_spec.md`完全兼容；
4. **性能足够初赛**：处理1000-2000条工程规范条款（约50MB数据）时，查询延迟<100ms，满足需求。

## 二、环境准备（Windows必做，3步完成）
### 1. 确认Python版本
Chroma要求Python 3.8-3.11，打开PowerShell执行：
```powershell
python --version  3.12
```