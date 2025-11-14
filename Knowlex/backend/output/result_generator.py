# output/result_generator.py

import json
from rag.rag_chain import run_retrieval_pipeline # 导入我们的核心管线
from tqdm import tqdm

# --- 你需要自己创建这个文件 ---
# 格式: 每行一个 JSON, {"id": "q1", "query": "地下室穿墙管渗漏"}
INPUT_QUESTIONS_FILE = "test_questions.jsonl" 

# --- 这是你最终要提交给评委的文件 ---
OUTPUT_RESULTS_FILE = "./output/results.jsonl" 

def main():
    print("--- 开始生成初赛提交文件 ---")
    
    questions = []
    try:
        with open(INPUT_QUESTIONS_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                questions.append(json.loads(line))
    except FileNotFoundError:
        print(f"错误: 未找到测试问题文件: {INPUT_QUESTIONS_FILE}")
        print("请先创建该文件。")
        return

    print(f"已加载 {len(questions)} 个测试问题。")
    
    # 打开输出文件 (JSON Lines 格式)
    with open(OUTPUT_RESULTS_FILE, 'w', encoding='utf-8') as f:
        for item in tqdm(questions, desc="处理问题"):
            query_id = item.get("id")
            query_text = item.get("query")
            
            if not query_id or not query_text:
                continue
                
            # 运行你的核心检索管线
            answer_dict = run_retrieval_pipeline(query_text)
            
            # [span_5](start_span)构造符合比赛要求的 JSON 行[span_5](end_span)
            output_line = {
                "id": query_id,
                "answer": answer_dict 
            }
            
            # 写入文件
            f.write(json.dumps(output_line, ensure_ascii=False) + "\n")

    print(f"--- 提交文件已生成: {OUTPUT_RESULTS_FILE} ---")

if __name__ == "__main__":
    # 确保 Milvus 正在运行
    # 确保数据已入库
    # (你需要先启动一次 api/main.py 来完成数据入库)
    
    print("正在导入 RAG 管线 ...")
    main()
