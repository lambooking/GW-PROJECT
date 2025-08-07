#!/usr/bin/env python3
"""
简化的VLLM评分测试脚本
专门测试已索引文档的RAG评分功能
"""
import json
import logging
import sys
from datetime import datetime
from pathlib import Path

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.inference.rag_scoring_engine import RAGScoringEngine
from src.inference.vllm_client import VLLMInferenceClient
from src.data_processing.schemas import StandardizedDocument, DocumentInfo

def test_vllm_connection(vllm_url: str = "http://localhost:8000/v1", model: str = "qwen2.5-vl-3b"):
    """测试VLLM连接"""
    try:
        print("🤖 测试VLLM连接...")
        client = VLLMInferenceClient(base_url=vllm_url, model_name=model)
        
        response = client.text_analysis("你好，请简单介绍一下你自己。", max_tokens=50)
        print(f"✅ VLLM连接成功！")
        print(f"📝 响应示例: {response}")
        return client
        
    except Exception as e:
        print(f"❌ VLLM连接失败: {e}")
        return None

def test_rag_scoring(vllm_url: str = "http://localhost:8000/v1", model: str = "qwen2.5-vl-3b"):
    """测试RAG评分功能"""
    try:
        print("\n" + "="*60)
        print("🎯 开始RAG评分测试")
        print("="*60)
        
        # 1. 初始化组件
        print("📚 初始化知识库...")
        knowledge_base = RAGKnowledgeBase()
        kb_stats = knowledge_base.get_stats()
        print(f"   知识库状态: {kb_stats['total_documents']} 个文档, {kb_stats['total_chunks']} 个文档块")
        
        if kb_stats['total_chunks'] == 0:
            print("❌ 知识库为空，请先运行 quick_reindex.py 添加文档")
            return False
        
        print("🤖 初始化VLLM客户端...")
        vllm_client = VLLMInferenceClient(base_url=vllm_url, model_name=model)
        
        print("⚖️  初始化评分引擎...")
        scoring_engine = RAGScoringEngine(vllm_client, knowledge_base)
        
        # 2. 创建模拟文档对象
        doc_name = kb_stats['documents'][0]
        print(f"📄 准备评分文档: {doc_name}")
        
        doc_info = DocumentInfo(
            scene_type="scenario_one",
            scene_name="作业指导书",
            file_name=doc_name,
            total_pages=12,
            processing_timestamp=datetime.now(),
            classification_confidence=0.8
        )
        
        document = StandardizedDocument(
            document_info=doc_info,
            text_content=[],
            tables=[],
            images=[]
        )
        
        # 3. 执行评分
        print("🚀 开始执行RAG智能评分...")
        start_time = datetime.now()
        
        scoring_result = scoring_engine.score_document(document)
        
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()
        
        print(f"✅ 评分完成！耗时: {duration:.2f} 秒")
        
        # 4. 展示结果
        print_scoring_results(scoring_result)
        
        # 5. 保存结果
        output_dir = Path("output/rag_scoring_reports")
        output_dir.mkdir(parents=True, exist_ok=True)
        
        report_file = output_dir / f"test_scoring_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, 'w', encoding='utf-8') as f:
            json.dump(scoring_result, f, indent=2, ensure_ascii=False)
        
        print(f"📊 详细报告已保存: {report_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ RAG评分测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def print_scoring_results(result: dict):
    """打印评分结果"""
    print("\n" + "="*60)
    print("📊 评分结果汇总")
    print("="*60)
    
    summary = result["summary"]
    doc_info = result["document_info"]
    
    print(f"📄 文档: {doc_info['file_name']}")
    print(f"🎯 总分: {summary['total_score']}/{summary['max_total_score']} ({summary['percentage']:.1f}%)")
    print(f"🏆 等级: {summary['grade']}")
    
    print(f"\n📋 分项评分:")
    detailed_scores = result["detailed_scores"]
    
    for criterion_key, details in detailed_scores.items():
        print(f"\n  【{details['name']}】")
        print(f"    分数: {details['score']}/{details['max_score']}")
        print(f"    评估重点: {details.get('evaluation_focus', '综合评估')}")
        
        reasoning = details.get('reasoning', '无说明')
        if len(reasoning) > 150:
            reasoning = reasoning[:150] + "..."
        print(f"    评分理由: {reasoning}")
        
        if details.get('context_length', 0) > 0:
            print(f"    上下文长度: {details['context_length']} 字符")

def test_individual_scoring_components(vllm_url: str = "http://localhost:8000/v1", model: str = "qwen2.5-vl-3b"):
    """测试各个评分组件"""
    try:
        print("\n" + "="*60)
        print("🔬 组件功能测试")
        print("="*60)
        
        # 初始化组件
        knowledge_base = RAGKnowledgeBase()
        vllm_client = VLLMInferenceClient(base_url=vllm_url, model_name=model)
        scoring_engine = RAGScoringEngine(vllm_client, knowledge_base)
        
        # 测试各个评分项的上下文检索
        test_queries = {
            "结构完整性": ["范围 职责 作业内容", "文档结构 章节"],
            "内容完整性": ["作业内容 操作步骤", "职责分工"],
            "技术准确性": ["技术参数 标准", "工程技术"],
            "安全合规性": ["安全要求 风险控制", "应急预案"],
            "语法规范性": ["第1页", "管道 防汛"]
        }
        
        for criterion_name, queries in test_queries.items():
            print(f"\n🔍 测试 {criterion_name} 的内容检索:")
            
            # 测试检索
            context = scoring_engine._retrieve_relevant_context(queries, 500, 0.2)
            
            if context:
                print(f"  ✅ 检索到上下文: {len(context)} 字符")
                preview = context[:100].replace('\n', ' ') + "..." if len(context) > 100 else context
                print(f"  📝 内容预览: {preview}")
                
                # 测试LLM评分
                if criterion_name == "结构完整性":
                    test_prompt = f"""
请基于以下文档内容评估结构完整性，满分20分：

{context[:300]}

请给出评分和简要理由。
"""
                    try:
                        response = vllm_client.text_analysis(test_prompt, max_tokens=200)
                        print(f"  🤖 LLM响应: {response[:100]}...")
                        
                        # 测试分数解析
                        score, reasoning = scoring_engine._parse_scoring_response(response, 20)
                        print(f"  📊 解析得分: {score}/20")
                        
                    except Exception as e:
                        print(f"  ❌ LLM测试失败: {e}")
            else:
                print(f"  ⚠️  未检索到相关内容")
        
        return True
        
    except Exception as e:
        print(f"❌ 组件测试失败: {e}")
        return False

def main():
    """主函数"""
    print("🧪 VLLM RAG评分系统测试")
    print("="*50)
    
    # 解析命令行参数
    vllm_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000/v1"
    model_name = sys.argv[2] if len(sys.argv) > 2 else "qwen2.5-vl-3b"
    
    print(f"🔗 VLLM服务地址: {vllm_url}")
    print(f"🤖 模型名称: {model_name}")
    
    # 1. 测试VLLM连接
    vllm_client = test_vllm_connection(vllm_url, model_name)
    if not vllm_client:
        print("❌ 无法连接到VLLM服务，请检查服务是否启动")
        return
    
    # 2. 测试RAG评分
    print("\n" + "="*50)
    success = test_rag_scoring(vllm_url, model_name)
    
    if success:
        print("\n✅ RAG评分测试成功！")
        
        # 3. 可选：测试组件功能
        response = input("\n是否进行详细的组件功能测试？(y/N): ")
        if response.lower() in ['y', 'yes']:
            test_individual_scoring_components(vllm_url, model_name)
        
    else:
        print("\n❌ RAG评分测试失败")
        
    print("\n🎉 测试完成")

if __name__ == "__main__":
    main()