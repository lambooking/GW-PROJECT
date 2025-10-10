#!/usr/bin/env python3
"""
追踪完整的文档处理流程
从 PDF 解析 -> 结构化提取 -> 分块 -> 向量化 -> 存储
"""
import sys
import json
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def trace_document_flow(pdf_path: str):
    """追踪文档处理的完整流程"""
    
    print("="*60)
    print("  追踪文档处理完整流程")
    print("="*60)
    print(f"文档: {pdf_path}")
    print()
    
    try:
        from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
        from src.inference.rag_knowledge_base import DocumentChunker
        
        # 步骤 1: 文档预处理
        print("步骤 1: 文档预处理（PDF -> StandardizedDocument）")
        print("-"*60)
        
        pipeline = PreprocessingPipeline()
        document = pipeline.process(pdf_path)
        
        print(f"✅ 文档解析完成")
        print(f"   文件名: {document.document_info.file_name}")
        print(f"   页数: {document.document_info.total_pages}")
        print(f"   场景类型: {document.document_info.scene_type}")
        print(f"   场景名称: {document.document_info.scene_name}")
        
        # 检查提取的内容
        print(f"\n   提取的内容统计:")
        print(f"   - text_content 数量: {len(document.text_content)}")
        print(f"   - tables 数量: {len(document.tables)}")
        print(f"   - images 数量: {len(document.images)}")
        
        # 步骤 2: 检查文本内容质量
        print(f"\n步骤 2: 检查提取的文本内容质量")
        print("-"*60)
        
        if document.text_content:
            print(f"   前 10 个文本内容:")
            for i, text in enumerate(document.text_content[:10]):
                content_preview = text.content.replace('\n', ' ')[:60]
                print(f"   [{i+1}] 页{text.page_number}, 类型={text.section_type}, "
                      f"字数={text.word_count}")
                print(f"       内容: '{content_preview}...'")
            
            # 统计各种类型
            type_stats = {}
            for text in document.text_content:
                section_type = text.section_type or "unknown"
                type_stats[section_type] = type_stats.get(section_type, 0) + 1
            
            print(f"\n   文本类型统计:")
            for type_name, count in type_stats.items():
                print(f"     {type_name}: {count}")
            
            # 检查是否有关键词
            print(f"\n   检查关键内容:")
            keywords = ["范围", "职责", "作业内容", "相关文件", "记录文件"]
            for keyword in keywords:
                found = [t for t in document.text_content if keyword in t.content]
                print(f"     包含'{keyword}'的段落: {len(found)}")
                if found:
                    print(f"       示例: '{found[0].content[:50]}...'")
        else:
            print("   ❌ 没有提取到任何文本内容！")
        
        # 步骤 3: 文档分块
        print(f"\n步骤 3: 文档分块（StandardizedDocument -> Chunks）")
        print("-"*60)
        
        chunker = DocumentChunker(max_chunk_size=500, overlap_size=50)
        chunks = chunker.chunk_document(document)
        
        print(f"✅ 分块完成")
        print(f"   总块数: {len(chunks)}")
        
        # 检查 chunks 质量
        print(f"\n   Chunks 质量检查:")
        
        # 统计 chunk 类型
        chunk_type_stats = {}
        for chunk in chunks:
            chunk_type_stats[chunk.chunk_type] = chunk_type_stats.get(chunk.chunk_type, 0) + 1
        
        print(f"   Chunk 类型分布:")
        for type_name, count in chunk_type_stats.items():
            print(f"     {type_name}: {count}")
        
        # 检查前 20 个 chunks
        print(f"\n   前 20 个 chunks:")
        for i, chunk in enumerate(chunks[:20]):
            content_preview = chunk.content.replace('\n', ' ')[:60]
            print(f"   [{i+1}] 页{chunk.page_number}, 类型={chunk.chunk_type}, "
                  f"字数={chunk.word_count}")
            print(f"       ID: {chunk.chunk_id}")
            print(f"       内容: '{content_preview}...'")
        
        # 检查是否有无意义的 chunks（太短、只有数字等）
        print(f"\n   质量问题检查:")
        
        very_short = [c for c in chunks if len(c.content.strip()) < 5]
        print(f"     内容过短（<5字符）的chunks: {len(very_short)}")
        if very_short:
            print(f"       示例: {[c.content for c in very_short[:5]]}")
        
        only_numbers = [c for c in chunks if c.content.strip().isdigit()]
        print(f"     只有数字的chunks: {len(only_numbers)}")
        if only_numbers:
            print(f"       示例: {[c.content for c in only_numbers[:5]]}")
        
        only_symbols = [c for c in chunks if len(c.content.strip()) < 10 and not any(ch.isalpha() for ch in c.content)]
        print(f"     只有符号/数字的chunks: {len(only_symbols)}")
        if only_symbols:
            print(f"       示例: {[c.content for c in only_symbols[:5]]}")
        
        # 检查有意义的 chunks
        meaningful = [c for c in chunks if len(c.content.strip()) >= 10 and any(ch.isalpha() for ch in c.content)]
        print(f"     有意义的chunks（≥10字符且包含文字）: {len(meaningful)}")
        
        # 步骤 4: 查找包含关键词的 chunks
        print(f"\n步骤 4: 查找包含关键词的 chunks")
        print("-"*60)
        
        keywords = ["范围", "职责", "作业内容", "相关文件", "记录文件"]
        for keyword in keywords:
            matching_chunks = [c for c in chunks if keyword in c.content]
            print(f"\n   包含'{keyword}'的chunks: {len(matching_chunks)}")
            if matching_chunks:
                for i, chunk in enumerate(matching_chunks[:3]):
                    print(f"     [{i+1}] ID: {chunk.chunk_id}")
                    print(f"         内容: '{chunk.content[:80]}...'")
        
        # 步骤 5: 检查分块算法
        print(f"\n步骤 5: 检查分块算法逻辑")
        print("-"*60)
        
        print(f"   DocumentChunker 配置:")
        print(f"     max_chunk_size: {chunker.max_chunk_size}")
        print(f"     overlap_size: {chunker.overlap_size}")
        
        # 检查清理逻辑
        print(f"\n   内容清理测试:")
        test_content = "=== 第1页 === \n1 范围\n本作业指导书适用于..."
        cleaned = chunker._clean_content(test_content)
        print(f"     原始: '{test_content}'")
        print(f"     清理后: '{cleaned}'")
        
        # 步骤 6: 模拟向量化和存储
        print(f"\n步骤 6: 模拟向量化和查询")
        print("-"*60)
        
        from src.inference.rag_knowledge_base import EmbeddingModel
        
        embedding_model = EmbeddingModel()
        
        # 测试几个关键 chunks 的向量化
        test_chunks = []
        for keyword in ["范围", "职责"]:
            matching = [c for c in chunks if keyword in c.content]
            if matching:
                test_chunks.append(matching[0])
        
        if test_chunks:
            print(f"   测试 {len(test_chunks)} 个 chunks 的向量化:")
            chunk_texts = [c.content for c in test_chunks]
            embeddings = embedding_model.encode(chunk_texts)
            
            for i, (chunk, emb) in enumerate(zip(test_chunks, embeddings)):
                print(f"     [{i+1}] 内容: '{chunk.content[:40]}...'")
                print(f"         向量维度: {len(emb)}, 前5值: {emb[:5]}")
            
            # 测试查询相似度
            print(f"\n   测试查询向量:")
            query = "范围"
            query_emb = embedding_model.encode([query])[0]
            print(f"     查询: '{query}'")
            print(f"     向量维度: {len(query_emb)}, 前5值: {query_emb[:5]}")
            
            # 计算余弦相似度
            import numpy as np
            
            print(f"\n   计算与 chunks 的相似度:")
            for i, (chunk, chunk_emb) in enumerate(zip(test_chunks, embeddings)):
                # 余弦相似度
                similarity = np.dot(query_emb, chunk_emb) / (np.linalg.norm(query_emb) * np.linalg.norm(chunk_emb))
                print(f"     [{i+1}] '{chunk.content[:30]}...'")
                print(f"         余弦相似度: {similarity:.4f}")
        
        print(f"\n" + "="*60)
        print("✅ 流程追踪完成")
        print("="*60)
        
        # 总结问题
        print(f"\n问题诊断总结:")
        
        if len(very_short) > len(chunks) * 0.3:
            print(f"  ⚠️  警告: {len(very_short)} 个过短的chunks（占{len(very_short)/len(chunks)*100:.1f}%）")
            print(f"      建议: 在 DocumentChunker._chunk_text_content() 中过滤过短内容")
        
        if len(only_numbers) > 0:
            print(f"  ⚠️  警告: {len(only_numbers)} 个只有数字的chunks")
            print(f"      建议: 在分块前过滤掉纯数字内容")
        
        if len(only_symbols) > len(chunks) * 0.2:
            print(f"  ⚠️  警告: {len(only_symbols)} 个无意义chunks（占{len(only_symbols)/len(chunks)*100:.1f}%）")
            print(f"      建议: 加强内容清理逻辑")
        
        # 保存详细报告
        report = {
            "document_info": {
                "file_name": document.document_info.file_name,
                "total_pages": document.document_info.total_pages,
                "scene_type": document.document_info.scene_type
            },
            "text_content_count": len(document.text_content),
            "chunks_total": len(chunks),
            "chunks_very_short": len(very_short),
            "chunks_only_numbers": len(only_numbers),
            "chunks_only_symbols": len(only_symbols),
            "chunks_meaningful": len(meaningful),
            "chunk_type_stats": chunk_type_stats
        }
        
        report_path = project_root / "output" / "document_flow_report.json"
        report_path.parent.mkdir(exist_ok=True)
        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        print(f"\n详细报告已保存: {report_path}")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 流程追踪失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    if len(sys.argv) < 2:
        print("用法: python scripts/trace_document_flow.py <pdf_path>")
        print("示例: python scripts/trace_document_flow.py /home/batchcom/Desktop/提交训练集/作业指导书/YQ作业区作业指导书.pdf")
        return 1
    
    pdf_path = sys.argv[1]
    
    if not Path(pdf_path).exists():
        print(f"错误: 文件不存在: {pdf_path}")
        return 1
    
    success = trace_document_flow(pdf_path)
    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())

