#!/usr/bin/env python3
"""
测试RAG知识库系统
"""
import json
import logging
from pathlib import Path
from src.inference.rag_knowledge_base import RAGKnowledgeBase

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s'
)

logger = logging.getLogger(__name__)

def test_rag_system():
    """测试RAG系统的各项功能"""
    
    print("🧪 开始RAG系统功能测试")
    print("=" * 50)
    
    try:
        # 1. 初始化RAG知识库
        print("🎯 阶段1: 初始化RAG知识库")
        print("-" * 50)
        knowledge_base = RAGKnowledgeBase()
        print("✅ 知识库初始化成功")
        
        # 2. 检查知识库状态
        print("\n📊 阶段2: 检查知识库状态")
        print("-" * 50)
        stats = knowledge_base.get_stats()
        print(f"📋 知识库统计信息:")
        print(f"   - 文档数量: {stats['total_documents']}")
        print(f"   - 文档列表: {stats['documents']}")
        print(f"   - 总块数: {stats['total_chunks']}")
        print(f"   - 存储类型: {stats['storage_type']}")
        print(f"   - 嵌入模型: {stats['embedding_model']}")
        
        if stats['total_chunks'] == 0:
            print("⚠️  知识库为空，请先运行 quick_reindex.py 来添加文档")
            return
        
        # 3. 测试基础搜索功能
        print("\n🔍 阶段3: 测试基础搜索功能")
        print("-" * 50)
        
        test_queries = [
            "范围",
            "职责分工和管理",
            "作业内容和操作步骤",
            "安全要求",
            "技术参数"
        ]
        
        for i, query in enumerate(test_queries, 1):
            print(f"🔎 搜索{i}: {query}")
            results = knowledge_base.search(query, top_k=5, min_score=0.2)
            print(f"   📋 找到 {len(results)} 个相关片段")
            
            if results:
                # 显示最相关的结果
                top_result = results[0]
                content_preview = top_result['content'][:100].replace('\n', ' ') + "..." if len(top_result['content']) > 100 else top_result['content']
                print(f"   🎯 最相关内容: {content_preview}")
                print(f"   📍 来源: 第{top_result['page_number']}页, 相关性: {top_result['score']:.3f}")
            else:
                print("   ⚠️  未找到相关内容")
            print()
        
        # 4. 测试上下文生成功能
        print("🎯 阶段4: 测试上下文生成功能")
        print("-" * 50)
        
        test_question = "文档的职责分工是什么？"
        print(f"📝 测试问题: {test_question}")
        
        context = knowledge_base.get_context_for_question(test_question, max_context_length=1000)
        print(f"📄 生成的上下文长度: {len(context)} 字符")
        
        if context:
            context_preview = context[:200].replace('\n', ' ') + "..." if len(context) > 200 else context
            print(f"📖 上下文预览: {context_preview}")
        else:
            print("⚠️  未生成有效上下文")
        
        print("\n✅ RAG系统测试完成")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ 测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

def test_scoring_simulation():
    """模拟评分场景测试"""
    print("\n🎯 模拟评分场景测试")
    print("-" * 50)
    
    try:
        knowledge_base = RAGKnowledgeBase()
        
        # 模拟各个评分项的搜索查询
        scoring_criteria = {
            "结构完整性": [
                "文档章节结构 目录 标题 编号",
                "范围 职责 作业内容 相关文件 记录文件",
                "文档组织结构 章节层次"
            ],
            "内容完整性": [
                "作业内容 操作步骤 具体要求",
                "职责分工 责任划分",
                "工作流程 操作指导 实施方法"
            ],
            "技术准确性": [
                "技术参数 规格指标 标准数据",
                "技术规范 设计要求 技术标准",
                "工程技术 施工要求 质量标准"
            ],
            "安全合规性": [
                "安全要求 风险控制 应急处置",
                "防护措施 安全隐患 风险识别",
                "应急预案 安全管理 防范措施"
            ]
        }
        
        for criterion_name, queries in scoring_criteria.items():
            print(f"\n📋 评分项: {criterion_name}")
            
            all_results = []
            for query in queries:
                results = knowledge_base.search(query, top_k=3, min_score=0.2)
                all_results.extend(results)
            
            # 去重并排序
            unique_results = []
            seen_contents = set()
            for result in all_results:
                if result['content'] not in seen_contents:
                    unique_results.append(result)
                    seen_contents.add(result['content'])
            
            unique_results.sort(key=lambda x: x['score'], reverse=True)
            
            print(f"   🔍 检索到 {len(unique_results)} 个唯一相关片段")
            
            if unique_results:
                top_result = unique_results[0]
                content_preview = top_result['content'][:150].replace('\n', ' ') + "..."
                print(f"   🎯 最相关内容: {content_preview}")
                print(f"   📊 相关性分数: {top_result['score']:.3f}")
            else:
                print("   ⚠️  未找到相关内容")
        
        print("\n✅ 评分模拟测试完成")
        
    except Exception as e:
        print(f"❌ 评分模拟测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag_system()
    test_scoring_simulation()