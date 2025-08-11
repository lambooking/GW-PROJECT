"""
CLI commands for RAG Scoring System.
"""

import sys
import json
from pathlib import Path
from typing import List, Dict, Any

import click

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from src.core import RAGScoringApplication
from src.config import ConfigManager
from src.data import DocumentParserFactory
from src.intelligence import KnowledgeBaseManager, VLLMClient, ScoringEngineFactory


def create_app(config_path: str = "config/rag_config.yaml") -> RAGScoringApplication:
    """Create configured application instance."""
    config_manager = ConfigManager(config_path)
    app = RAGScoringApplication(config_manager)
    
    # Setup knowledge base
    kb_manager = KnowledgeBaseManager(config_manager.knowledge_base)
    app.set_knowledge_base(kb_manager)
    
    # Setup VLLM client and scoring engine
    vllm_client = VLLMClient(config_manager.vllm)
    scoring_engine = ScoringEngineFactory.create_engine(
        "rag", 
        config=config_manager._config,
        model_client=vllm_client,
        knowledge_base=kb_manager
    )
    app.register_scoring_engine("rag", scoring_engine)
    
    # Register parsers
    for fmt in DocumentParserFactory.get_supported_formats():
        parser = DocumentParserFactory.create_parser(
            f"dummy{fmt}",
            enable_ocr=config_manager.processing.ocr_enabled,
            enable_images=config_manager.processing.image_extraction
        )
        app.register_parser(fmt, parser)
    
    return app


@click.group()
@click.option('--config', default="config/rag_config.yaml", help='配置文件路径')
@click.option('--verbose', '-v', is_flag=True, help='详细输出')
@click.pass_context
def cli(ctx, config, verbose):
    """RAG智能评分系统命令行工具"""
    ctx.ensure_object(dict)
    ctx.obj['config'] = config
    ctx.obj['verbose'] = verbose
    
    # Setup logging based on verbosity
    import logging
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(level=level, format='%(levelname)s: %(message)s')


@cli.command()
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--engine', default='rag', help='评分引擎')
@click.option('--output-dir', help='输出目录')
@click.option('--format', 'output_formats', multiple=True, default=['html'], help='输出格式')
@click.pass_context
def score(ctx, file_path, engine, output_dir, output_formats):
    """评分单个文档"""
    try:
        app = create_app(ctx.obj['config'])
        
        click.echo(f"📄 正在评分文档: {file_path}")
        
        result = app.process_document_complete(
            file_path,
            output_dir=output_dir,
            engine_name=engine,
            report_formats=list(output_formats)
        )
        
        scoring_result = result['scoring_result']
        click.echo(f"✅ 评分完成!")
        click.echo(f"📊 总分: {scoring_result.total_score:.1f}/{scoring_result.max_total_score}")
        click.echo(f"📈 百分比: {scoring_result.score_percentage:.1f}%")
        click.echo(f"⏱️  处理时间: {scoring_result.processing_time:.2f}秒")
        
        if result['reports']:
            click.echo(f"📄 报告文件:")
            for report_path in result['reports']:
                click.echo(f"  - {report_path}")
        
        if ctx.obj['verbose']:
            click.echo("\n📋 详细评分:")
            for item in scoring_result.score_items:
                click.echo(f"  {item.name}: {item.score:.1f}/{item.max_score}")
        
    except Exception as e:
        click.echo(f"❌ 评分失败: {e}", err=True)
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.argument('directory', type=click.Path(exists=True, file_okay=False, dir_okay=True))
@click.option('--engine', default='rag', help='评分引擎')
@click.option('--output-dir', help='输出目录')
@click.option('--pattern', default='*.pdf,*.docx,*.doc', help='文件匹配模式')
@click.option('--parallel', '-p', is_flag=True, help='并行处理')
@click.pass_context
def batch(ctx, directory, engine, output_dir, pattern, parallel):
    """批量评分目录中的文档"""
    try:
        app = create_app(ctx.obj['config'])
        directory = Path(directory)
        
        # Find files
        files = []
        patterns = pattern.split(',')
        for pat in patterns:
            files.extend(directory.glob(pat.strip()))
        
        if not files:
            click.echo(f"❌ 在 {directory} 中未找到匹配的文件")
            return
        
        click.echo(f"📂 找到 {len(files)} 个文件")
        
        results = []
        failed = []
        
        with click.progressbar(files, label='处理文件') as bar:
            for file_path in bar:
                try:
                    result = app.process_document_complete(
                        file_path,
                        output_dir=output_dir,
                        engine_name=engine
                    )
                    results.append({
                        'file': file_path.name,
                        'score': result['scoring_result'].total_score,
                        'max_score': result['scoring_result'].max_total_score,
                        'percentage': result['scoring_result'].score_percentage
                    })
                except Exception as e:
                    failed.append({'file': file_path.name, 'error': str(e)})
        
        # Summary
        click.echo(f"\n📊 批量处理完成:")
        click.echo(f"  ✅ 成功: {len(results)}")
        click.echo(f"  ❌ 失败: {len(failed)}")
        
        if results:
            avg_score = sum(r['score'] for r in results) / len(results)
            click.echo(f"  📈 平均分: {avg_score:.1f}")
            
            # Top scores
            results.sort(key=lambda x: x['score'], reverse=True)
            click.echo(f"\n🏆 前3名:")
            for i, result in enumerate(results[:3], 1):
                click.echo(f"  {i}. {result['file']}: {result['score']:.1f} ({result['percentage']:.1f}%)")
        
        if failed:
            click.echo(f"\n❌ 失败的文件:")
            for fail in failed:
                click.echo(f"  - {fail['file']}: {fail['error']}")
    
    except Exception as e:
        click.echo(f"❌ 批量处理失败: {e}", err=True)
        sys.exit(1)


@cli.group()
def kb():
    """知识库管理命令"""
    pass


@kb.command('add')
@click.argument('file_path', type=click.Path(exists=True))
@click.option('--metadata', help='元数据 (JSON格式)')
@click.pass_context
def kb_add(ctx, file_path, metadata):
    """添加文档到知识库"""
    try:
        app = create_app(ctx.obj['config'])
        
        click.echo(f"📚 正在添加文档到知识库: {file_path}")
        
        # Parse metadata if provided
        meta_dict = None
        if metadata:
            meta_dict = json.loads(metadata)
        
        # Parse and add document
        document = app.parse_document(file_path)
        doc_id = app.add_to_knowledge_base(document, meta_dict)
        
        click.echo(f"✅ 文档已添加，ID: {doc_id}")
        
    except Exception as e:
        click.echo(f"❌ 添加失败: {e}", err=True)
        sys.exit(1)


@kb.command('list')
@click.option('--format', 'output_format', default='table', type=click.Choice(['table', 'json']), help='输出格式')
@click.pass_context
def kb_list(ctx, output_format):
    """列出知识库中的文档"""
    try:
        app = create_app(ctx.obj['config'])
        
        documents = app._knowledge_base.list_documents()
        
        if not documents:
            click.echo("📚 知识库为空")
            return
        
        if output_format == 'json':
            click.echo(json.dumps(documents, indent=2, ensure_ascii=False))
        else:
            click.echo(f"📚 知识库包含 {len(documents)} 个文档:")
            for doc in documents:
                click.echo(f"  📄 {doc.get('file_name', 'unknown')}")
                click.echo(f"     ID: {doc.get('document_id', 'no-id')}")
                click.echo(f"     类型: {doc.get('scene_type', 'unknown')}")
                click.echo(f"     页数: {doc.get('total_pages', 0)}")
                click.echo(f"     添加时间: {doc.get('added_timestamp', 'unknown')}")
                click.echo()
        
    except Exception as e:
        click.echo(f"❌ 列表获取失败: {e}", err=True)
        sys.exit(1)


@kb.command('query')
@click.argument('query_text')
@click.option('--top-k', default=5, help='返回结果数量')
@click.option('--format', 'output_format', default='text', type=click.Choice(['text', 'json']), help='输出格式')
@click.pass_context
def kb_query(ctx, query_text, top_k, output_format):
    """查询知识库"""
    try:
        app = create_app(ctx.obj['config'])
        
        results = app.query_knowledge_base(query_text, top_k)
        
        if not results:
            click.echo("🔍 未找到相关结果")
            return
        
        if output_format == 'json':
            click.echo(json.dumps(results, indent=2, ensure_ascii=False))
        else:
            click.echo(f"🔍 查询 '{query_text}' 找到 {len(results)} 个结果:")
            for i, result in enumerate(results, 1):
                relevance = 1 - result.get('distance', 0)
                click.echo(f"\n{i}. 相关度: {relevance:.3f}")
                click.echo(f"   内容: {result['content'][:200]}...")
                if 'metadata' in result:
                    meta = result['metadata']
                    if 'section_name' in meta:
                        click.echo(f"   章节: {meta['section_name']}")
                    if 'page_number' in meta:
                        click.echo(f"   页码: {meta['page_number']}")
        
    except Exception as e:
        click.echo(f"❌ 查询失败: {e}", err=True)
        sys.exit(1)


@kb.command('clear')
@click.confirmation_option(prompt='确定要清空知识库吗？')
@click.pass_context
def kb_clear(ctx):
    """清空知识库"""
    try:
        app = create_app(ctx.obj['config'])
        
        if app._knowledge_base.clear():
            click.echo("✅ 知识库已清空")
        else:
            click.echo("❌ 清空失败")
            
    except Exception as e:
        click.echo(f"❌ 清空失败: {e}", err=True)
        sys.exit(1)


@cli.command()
@click.pass_context  
def test(ctx):
    """测试系统连接和功能"""
    try:
        app = create_app(ctx.obj['config'])
        
        click.echo("🧪 正在测试系统组件...")
        
        # Test system status
        status = app.get_system_status()
        
        click.echo("📊 系统状态:")
        click.echo(f"  📄 解析器: {', '.join(status['parsers'])}")
        click.echo(f"  🧠 评分引擎: {', '.join(status['scoring_engines'])}")
        click.echo(f"  📚 知识库: {'✅' if status['knowledge_base'] else '❌'}")
        click.echo(f"  📄 报告生成器: {', '.join(status['report_generators'])}")
        
        # Test VLLM connection if available
        if 'rag' in app._scoring_engines:
            engine = app._scoring_engines['rag']
            if hasattr(engine, '_model_client'):
                client = engine._model_client
                if hasattr(client, 'health_check'):
                    click.echo("\n🔗 测试VLLM连接...")
                    health = client.health_check()
                    if health['status'] == 'healthy':
                        click.echo(f"  ✅ VLLM服务正常 (响应时间: {health.get('response_time_ms', 0):.1f}ms)")
                    else:
                        click.echo(f"  ❌ VLLM服务异常: {health.get('error', 'unknown')}")
        
        # Test knowledge base
        if status['knowledge_base']:
            kb_stats = app._knowledge_base.get_statistics()
            click.echo(f"\n📚 知识库统计:")
            click.echo(f"  📄 文档数量: {kb_stats.get('total_documents', 0)}")
            if 'total_chunks' in kb_stats:
                click.echo(f"  📝 块数量: {kb_stats['total_chunks']}")
        
        click.echo("\n✅ 系统测试完成")
        
    except Exception as e:
        click.echo(f"❌ 系统测试失败: {e}", err=True)
        if ctx.obj['verbose']:
            import traceback
            traceback.print_exc()
        sys.exit(1)


@cli.command()
@click.pass_context
def status(ctx):
    """显示详细系统状态"""
    try:
        app = create_app(ctx.obj['config'])
        status = app.get_system_status()
        
        click.echo("📊 系统详细状态:")
        for key, value in status.items():
            if isinstance(value, dict):
                click.echo(f"  {key}:")
                for sub_key, sub_value in value.items():
                    click.echo(f"    {sub_key}: {sub_value}")
            elif isinstance(value, list):
                click.echo(f"  {key}: {', '.join(map(str, value))}")
            else:
                click.echo(f"  {key}: {value}")
                
    except Exception as e:
        click.echo(f"❌ 状态获取失败: {e}", err=True)
        sys.exit(1)


if __name__ == '__main__':
    cli()