#!/usr/bin/env python3
"""
批量目录RAG评分系统
支持递归扫描多层级目录结构，保持输入输出目录映射，生成汇总报告
"""
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

# 创建logs目录
Path("logs").mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/batch_rag_scoring_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

# 导入项目模块
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.inference.rag_scoring_engine import RAGScoringEngine
from src.inference.vllm_client import VLLMInferenceClient
from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.utils.html_report_generator import HTMLReportGenerator
from src.utils.batch_summary_reporter import BatchSummaryReporter


class BatchRAGScoringSystem:
    """批量目录RAG评分系统"""
    
    # 支持的文档格式
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
    
    def __init__(self, 
                 vllm_base_url: str = "http://localhost:8000/v1",
                 vllm_model: str = "qwen2.5-vl-3b"):
        """
        初始化批量RAG评分系统
        
        Args:
            vllm_base_url: VLLM服务的基础URL
            vllm_model: 要使用的模型名称
        """
        self.vllm_base_url = vllm_base_url
        self.vllm_model = vllm_model
        
        # 初始化组件
        self.knowledge_base = None
        self.vllm_client = None
        self.scoring_engine = None
        self.pipeline = None
        self.html_generator = HTMLReportGenerator()
        self.summary_reporter = BatchSummaryReporter()
        
    def initialize_components(self):
        """初始化所有组件"""
        try:
            logger.info("🚀 开始初始化批量RAG评分系统组件...")
            
            # 1. 初始化知识库
            logger.info("📚 初始化RAG知识库...")
            self.knowledge_base = RAGKnowledgeBase()
            kb_stats = self.knowledge_base.get_stats()
            logger.info(f"✅ 知识库已初始化: {kb_stats['total_documents']} 个文档, {kb_stats['total_chunks']} 个文档块")
            
            if kb_stats['total_chunks'] == 0:
                logger.warning("⚠️  知识库为空，建议先运行 quick_reindex.py 添加文档")
            
            # 2. 初始化VLLM客户端
            logger.info(f"🤖 初始化VLLM客户端 ({self.vllm_base_url})...")
            self.vllm_client = VLLMInferenceClient(
                base_url=self.vllm_base_url,
                model_name=self.vllm_model
            )
            
            # 测试VLLM连接
            test_response = self.vllm_client.text_analysis("测试连接", max_tokens=10)
            logger.info(f"✅ VLLM连接测试成功: {test_response[:50]}...")
            
            # 3. 初始化评分引擎
            logger.info("⚖️  初始化RAG评分引擎...")
            self.scoring_engine = RAGScoringEngine(
                vllm_client=self.vllm_client,
                knowledge_base=self.knowledge_base
            )
            logger.info("✅ RAG评分引擎已初始化")
            
            # 4. 初始化预处理管线
            logger.info("🔧 初始化文档预处理管线...")
            self.pipeline = PreprocessingPipeline()
            logger.info("✅ 预处理管线已初始化")
            
            logger.info("🎉 所有组件初始化完成！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 组件初始化失败: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def scan_directory(self, input_dir: str) -> List[Dict[str, Any]]:
        """
        递归扫描目录，查找所有支持的文档文件
        
        Args:
            input_dir: 输入目录路径
            
        Returns:
            文件信息列表，每个元素包含file_path和relative_path
        """
        input_path = Path(input_dir)
        
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        if not input_path.is_dir():
            raise ValueError(f"路径不是目录: {input_dir}")
        
        file_list = []
        
        # 递归查找所有支持的文档文件
        for file_path in input_path.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in self.SUPPORTED_EXTENSIONS:
                relative_path = file_path.relative_to(input_path)
                file_list.append({
                    'file_path': str(file_path),
                    'relative_path': str(relative_path),
                    'file_name': file_path.name,
                    'extension': file_path.suffix.lower()
                })
        
        # 按相对路径排序
        file_list.sort(key=lambda x: x['relative_path'])
        
        logger.info(f"📂 扫描完成，共找到 {len(file_list)} 个文档文件")
        return file_list
    
    def batch_score_directory(self, 
                             input_dir: str,
                             output_dir: str = "output/batch_rag_scoring",
                             generate_html: bool = True) -> Dict[str, Any]:
        """
        批量评分整个目录，保持目录结构
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出根目录路径
            generate_html: 是否生成HTML报告
            
        Returns:
            批量评分汇总结果
        """
        start_time = time.time()
        
        logger.info(f"📁 开始批量评分目录: {input_dir}")
        logger.info(f"📁 输出目录: {output_dir}")
        
        # 1. 扫描目录
        file_list = self.scan_directory(input_dir)
        
        if not file_list:
            logger.warning("⚠️  未找到任何支持的文档文件")
            return {
                'success': False,
                'message': '未找到任何支持的文档文件',
                'total_files': 0,
                'results': []
            }
        
        # 2. 批量处理每个文件
        results = []
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        for i, file_info in enumerate(file_list, 1):
            file_path = file_info['file_path']
            relative_path = file_info['relative_path']
            
            logger.info(f"\n{'='*80}")
            logger.info(f"📄 [{i}/{len(file_list)}] 正在处理: {relative_path}")
            logger.info(f"{'='*80}")
            
            try:
                # 评分单个文件
                result = self._score_single_file(
                    file_path=file_path,
                    relative_path=relative_path,
                    input_dir=input_path,
                    output_dir=output_path,
                    generate_html=generate_html
                )
                
                results.append({
                    'file_path': file_path,
                    'relative_path': relative_path,
                    'success': True,
                    'result': result
                })
                
                logger.info(f"✅ [{i}/{len(file_list)}] 评分完成")
                
            except Exception as e:
                logger.error(f"❌ [{i}/{len(file_list)}] 评分失败: {e}")
                import traceback
                traceback.print_exc()
                
                results.append({
                    'file_path': file_path,
                    'relative_path': relative_path,
                    'success': False,
                    'error': str(e)
                })
        
        # 3. 生成汇总报告
        logger.info("\n" + "="*80)
        logger.info("📊 生成批量评分汇总报告...")
        logger.info("="*80)
        
        summary = self.summary_reporter.generate_summary(
            batch_results=results,
            input_dir=str(input_path),
            output_dir=str(output_path)
        )
        
        # 保存汇总报告
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # JSON格式
        json_summary_path = output_path / f"batch_summary_{timestamp}.json"
        self.summary_reporter.save_json_report(summary, str(json_summary_path))
        
        # 文本格式
        text_summary_path = output_path / f"batch_summary_{timestamp}.txt"
        self.summary_reporter.save_text_report(summary, str(text_summary_path))
        
        # HTML格式
        if generate_html:
            html_summary_path = output_path / f"batch_summary_{timestamp}.html"
            self._generate_batch_summary_html(summary, str(html_summary_path))
        
        # 4. 打印总结
        total_time = time.time() - start_time
        self._print_batch_summary(summary, total_time)
        
        return summary
    
    def _score_single_file(self,
                          file_path: str,
                          relative_path: str,
                          input_dir: Path,
                          output_dir: Path,
                          generate_html: bool) -> Dict[str, Any]:
        """
        评分单个文件并保存报告
        
        Args:
            file_path: 文件绝对路径
            relative_path: 相对于输入目录的路径
            input_dir: 输入目录路径
            output_dir: 输出目录路径
            generate_html: 是否生成HTML报告
            
        Returns:
            评分结果
        """
        file_start_time = time.time()
        
        # 1. 预处理文档
        logger.info("🔄 正在预处理文档...")
        document = self.pipeline.process(file_path)
        logger.info(f"✅ 文档预处理完成: {len(document.text_content)} 个文本段落, {len(document.tables)} 个表格")
        
        # 2. 执行RAG评分
        logger.info("⚖️  开始RAG智能评分...")
        scoring_result = self.scoring_engine.score_document(document)
        
        # 添加处理时间
        processing_time = time.time() - file_start_time
        scoring_result['processing_time'] = processing_time
        
        # 3. 构建输出路径（保持目录结构）
        rel_path = Path(relative_path)
        
        # 获取不含文件名的目录部分
        if len(rel_path.parts) > 1:
            output_subdir = output_dir / Path(*rel_path.parts[:-1])
        else:
            output_subdir = output_dir
        
        output_subdir.mkdir(parents=True, exist_ok=True)
        
        # 生成报告文件名
        file_stem = Path(file_path).stem
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 4. 保存JSON报告
        json_filename = f"{file_stem}_report_{timestamp}.json"
        json_path = output_subdir / json_filename
        
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(scoring_result, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📊 JSON报告已保存: {json_path}")
        
        # 5. 生成HTML报告
        if generate_html:
            html_filename = f"{file_stem}_report_{timestamp}.html"
            html_path = output_subdir / html_filename
            
            try:
                self.html_generator.generate_html_report(scoring_result, str(html_path))
                logger.info(f"🌐 HTML报告已生成: {html_path}")
            except Exception as e:
                logger.error(f"❌ HTML报告生成失败: {e}")
        
        # 6. 打印评分摘要
        self._print_file_summary(scoring_result, relative_path)
        
        return scoring_result
    
    def _print_file_summary(self, scoring_result: Dict[str, Any], 
                           relative_path: str):
        """打印单个文件的评分摘要"""
        summary = scoring_result.get('summary', {})
        
        print(f"\n  📄 文件: {relative_path}")
        print(f"  🎯 总分: {summary.get('total_score', 0)}/{summary.get('max_total_score', 100)}")
        print(f"  📈 得分率: {summary.get('percentage', 0):.1f}%")
        print(f"  🏆 等级: {summary.get('grade', '未知')}")
        print(f"  ⏱️  耗时: {scoring_result.get('processing_time', 0):.2f} 秒")
    
    def _print_batch_summary(self, summary: Dict[str, Any], total_time: float):
        """打印批量评分总结"""
        print("\n" + "="*80)
        print("📊 批量评分完成 - 总体统计")
        print("="*80)
        
        metadata = summary['metadata']
        overall = summary['overall_stats']
        
        print(f"\n📁 输入目录: {metadata['input_directory']}")
        print(f"📁 输出目录: {metadata['output_directory']}")
        print(f"⏱️  总耗时: {total_time:.2f} 秒")
        
        print(f"\n【处理统计】")
        print(f"  总文件数: {overall['total_files']}")
        print(f"  成功处理: {overall['successful']} ✅")
        print(f"  处理失败: {overall['failed']} ❌")
        print(f"  成功率: {overall['success_rate']:.1%}")
        
        if overall['successful'] > 0:
            print(f"\n【评分统计】")
            print(f"  平均分数: {overall['average_score']:.2f}")
            print(f"  最高分数: {overall['max_score']:.2f}")
            print(f"  最低分数: {overall['min_score']:.2f}")
            print(f"  中位数: {overall.get('median_score', 0):.2f}")
        
        # 子目录统计
        if summary['subdirectory_stats']:
            print(f"\n【子目录统计】")
            for subdir, stats in summary['subdirectory_stats'].items():
                print(f"  {subdir}:")
                print(f"    文件: {stats['total_files']}, "
                      f"成功: {stats['successful']}, "
                      f"平均分: {stats['average_score']:.2f}")
        
        # 等级分布
        grade_dist = summary['grade_distribution']
        if grade_dist:
            print(f"\n【等级分布】")
            for grade, count in grade_dist.items():
                print(f"  {grade}: {count} 个")
        
        print("\n" + "="*80)
    
    def _generate_batch_summary_html(self, summary: Dict[str, Any], 
                                    output_path: str):
        """生成批量汇总的HTML报告"""
        try:
            # 使用HTMLReportGenerator的批量汇总功能
            self.html_generator.generate_batch_summary_html(summary, output_path)
            logger.info(f"🌐 HTML汇总报告已生成: {output_path}")
        except Exception as e:
            logger.error(f"❌ HTML汇总报告生成失败: {e}")


def print_usage():
    """打印使用说明"""
    print("=" * 80)
    print("批量目录RAG评分系统")
    print("=" * 80)
    print("\n用法:")
    print("  python run_batch_rag_scoring.py <input_dir> [output_dir]")
    print("\n参数:")
    print("  input_dir   - 输入目录路径（必需）")
    print("  output_dir  - 输出目录路径（可选，默认: output/batch_rag_scoring）")
    print("\n示例:")
    print("  python run_batch_rag_scoring.py /path/to/documents")
    print("  python run_batch_rag_scoring.py /path/to/documents output/my_results")
    print("\n功能:")
    print("  - 递归扫描输入目录，查找所有PDF、DOCX、DOC文件")
    print("  - 使用RAG智能评分系统对每个文档进行评分")
    print("  - 保持输入输出目录结构一致")
    print("  - 为每个文档生成JSON和HTML报告")
    print("  - 生成总体和分层级的汇总报告")
    print("\n注意:")
    print("  - 确保VLLM服务已启动 (默认: http://localhost:8000/v1)")
    print("  - 确保已建立RAG知识库 (运行 quick_reindex.py)")
    print("=" * 80)


def main():
    """主函数"""
    # 检查命令行参数
    if len(sys.argv) < 2 or sys.argv[1] in ['-h', '--help', 'help']:
        print_usage()
        return
    
    input_dir = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else "output/batch_rag_scoring"
    
    # 验证输入目录
    if not Path(input_dir).exists():
        print(f"❌ 错误: 输入目录不存在: {input_dir}")
        return
    
    if not Path(input_dir).is_dir():
        print(f"❌ 错误: 路径不是目录: {input_dir}")
        return
    
    print("\n🚀 批量目录RAG评分系统启动")
    print("=" * 80)
    
    # 创建评分系统
    system = BatchRAGScoringSystem()
    
    # 初始化组件
    if not system.initialize_components():
        print("❌ 系统初始化失败")
        return
    
    try:
        # 执行批量评分
        result = system.batch_score_directory(
            input_dir=input_dir,
            output_dir=output_dir,
            generate_html=True
        )
        
        print("\n✅ 批量评分完成！")
        
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

