#!/usr/bin/env python3
"""
RAG智能评分系统 - 重构版主入口文件
"""

import sys
import logging
from pathlib import Path
from typing import List, Optional

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.core import RAGScoringApplication
from src.config import ConfigManager
from src.data import DocumentParserFactory, DocumentProcessorPipeline
from src.intelligence import KnowledgeBaseManager, VLLMClient, ScoringEngineFactory


def setup_logging(log_level: str = "INFO") -> None:
    """Setup logging configuration."""
    logging.basicConfig(
        level=getattr(logging, log_level.upper()),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/rag_scoring_system.log')
        ]
    )


def create_application() -> RAGScoringApplication:
    """Create and configure the RAG scoring application."""
    # Load configuration
    config_manager = ConfigManager("config/rag_config.yaml")
    
    # Setup logging
    setup_logging(config_manager.system.log_level)
    logger = logging.getLogger(__name__)
    
    # Create application
    app = RAGScoringApplication(config_manager)
    
    try:
        # Initialize knowledge base
        kb_manager = KnowledgeBaseManager(config_manager.knowledge_base)
        app.set_knowledge_base(kb_manager)
        
        # Initialize VLLM client
        vllm_client = VLLMClient(config_manager.vllm)
        
        # Create and register scoring engine
        scoring_engine = ScoringEngineFactory.create_engine(
            engine_type="rag",
            config=config_manager._config,
            model_client=vllm_client,
            knowledge_base=kb_manager
        )
        app.register_scoring_engine("rag", scoring_engine)
        
        # Register document parsers
        for file_format in DocumentParserFactory.get_supported_formats():
            parser = DocumentParserFactory.create_parser(
                f"dummy{file_format}",
                enable_ocr=config_manager.processing.ocr_enabled,
                enable_images=config_manager.processing.image_extraction
            )
            app.register_parser(file_format, parser)
        
        # Register HTML report generator (placeholder for now)
        # TODO: Implement HTML report generator
        
        logger.info("RAG Scoring Application initialized successfully")
        return app
        
    except Exception as e:
        logger.error(f"Failed to initialize application: {e}")
        raise


def main():
    """Main entry point."""
    import argparse
    
    parser = argparse.ArgumentParser(description="RAG智能评分系统")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # Score command
    score_parser = subparsers.add_parser('score', help='评分指定文件')
    score_parser.add_argument('file', help='要评分的文件路径')
    score_parser.add_argument('--engine', default='rag', help='评分引擎类型')
    score_parser.add_argument('--output-dir', help='输出目录')
    
    # Batch score command
    batch_parser = subparsers.add_parser('batch', help='批量评分目录中的文件')
    batch_parser.add_argument('directory', help='包含文件的目录路径')
    batch_parser.add_argument('--engine', default='rag', help='评分引擎类型')
    batch_parser.add_argument('--output-dir', help='输出目录')
    
    # Knowledge base commands
    kb_parser = subparsers.add_parser('kb', help='知识库管理')
    kb_subparsers = kb_parser.add_subparsers(dest='kb_command', help='知识库操作')
    
    kb_add_parser = kb_subparsers.add_parser('add', help='添加文档到知识库')
    kb_add_parser.add_argument('file', help='要添加的文件路径')
    
    kb_list_parser = kb_subparsers.add_parser('list', help='列出知识库中的文档')
    
    kb_query_parser = kb_subparsers.add_parser('query', help='查询知识库')
    kb_query_parser.add_argument('query', help='查询字符串')
    kb_query_parser.add_argument('--top-k', type=int, default=5, help='返回结果数量')
    
    # Test command
    test_parser = subparsers.add_parser('test', help='测试系统连接')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='显示系统状态')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    try:
        app = create_application()
        
        if args.command == 'score':
            result = app.process_document_complete(
                args.file,
                output_dir=args.output_dir,
                engine_name=args.engine
            )
            print(f"✅ 评分完成: {result['scoring_result'].total_score:.1f}分")
            print(f"📄 报告已生成: {[str(p) for p in result['reports']]}")
            
        elif args.command == 'batch':
            directory = Path(args.directory)
            if not directory.exists():
                print(f"❌ 目录不存在: {directory}")
                return
            
            files = []
            for ext in ['.pdf', '.docx', '.doc']:
                files.extend(directory.glob(f"*{ext}"))
            
            print(f"📂 找到 {len(files)} 个文件")
            results = []
            
            for file_path in files:
                try:
                    result = app.process_document_complete(
                        file_path,
                        output_dir=args.output_dir,
                        engine_name=args.engine
                    )
                    results.append((file_path.name, result['scoring_result'].total_score))
                    print(f"✅ {file_path.name}: {result['scoring_result'].total_score:.1f}分")
                except Exception as e:
                    print(f"❌ {file_path.name}: {e}")
            
            print(f"\n📊 批量评分完成，处理了 {len(results)} 个文件")
            
        elif args.command == 'kb':
            if args.kb_command == 'add':
                document = app.parse_document(args.file)
                doc_id = app.add_to_knowledge_base(document)
                print(f"✅ 文档已添加到知识库: {doc_id}")
                
            elif args.kb_command == 'list':
                docs = app._knowledge_base.list_documents()
                print(f"📚 知识库包含 {len(docs)} 个文档:")
                for doc in docs:
                    print(f"  - {doc.get('file_name', 'unknown')} ({doc.get('document_id', 'no-id')})")
                    
            elif args.kb_command == 'query':
                results = app.query_knowledge_base(args.query, args.top_k)
                print(f"🔍 查询结果 (找到 {len(results)} 个相关片段):")
                for i, result in enumerate(results, 1):
                    print(f"\n{i}. 相关度: {1-result.get('distance', 0):.3f}")
                    print(f"   内容: {result['content'][:200]}...")
                    
        elif args.command == 'test':
            status = app.get_system_status()
            print("🔧 系统状态:")
            print(f"  解析器: {', '.join(status['parsers'])}")
            print(f"  评分引擎: {', '.join(status['scoring_engines'])}")
            print(f"  知识库: {'✅' if status['knowledge_base'] else '❌'}")
            print(f"  报告生成器: {', '.join(status['report_generators'])}")
            
        elif args.command == 'status':
            status = app.get_system_status()
            print("📈 系统状态详情:")
            for key, value in status.items():
                print(f"  {key}: {value}")
                
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        if '--debug' in sys.argv:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()