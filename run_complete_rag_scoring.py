#!/usr/bin/env python3
"""
完整的RAG评分系统测试脚本
连接VLLM服务进行文档智能评分
"""
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 创建logs目录
Path("logs").mkdir(exist_ok=True)

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(name)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/rag_scoring_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

# 导入项目模块
from src.inference.rag_knowledge_base import RAGKnowledgeBase
from src.inference.rag_scoring_engine import RAGScoringEngine
from src.inference.vllm_client import VLLMInferenceClient
from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.utils.html_report_generator import HTMLReportGenerator
from src.annotation.manager import AnnotationManager

class RAGScoringSystem:
    """完整的RAG评分系统"""
    
    def __init__(self, vllm_base_url: str = "http://localhost:8000/v1", 
                 vllm_model: str = "qwen2.5-vl-3b"):
        """
        初始化RAG评分系统
        
        Args:
            vllm_base_url: VLLM服务的基础URL
            vllm_model: 要使用的模型名称
        """
        self.vllm_base_url = vllm_base_url
        self.vllm_model = vllm_model
        
        # 创建输出目录
        self.output_dir = Path("output/rag_scoring_reports")
        self.html_output_dir = Path("output/rag_scoring_reports/html")
        self.annotated_output_dir = Path("output/annotated_documents")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.html_output_dir.mkdir(parents=True, exist_ok=True)
        self.annotated_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 初始化组件
        self.knowledge_base = None
        self.vllm_client = None
        self.scoring_engine = None
        self.pipeline = None
        self.html_generator = HTMLReportGenerator()
        self.annotation_manager = AnnotationManager()
        
    def initialize_components(self):
        """初始化所有组件"""
        try:
            logger.info("🚀 开始初始化RAG评分系统组件...")
            
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
    
    def test_vllm_connection(self):
        """测试VLLM服务连接"""
        try:
            logger.info("🧪 测试VLLM服务连接...")
            
            test_prompt = """
请对以下作业指导书内容进行简要评估：

内容：管道处及时掌握险情动态，分析、预测灾害发展趋势，随时根据险情变化提出应急防范的对策、措施建议。

请给出简短评价（1-2句话）。
"""
            
            start_time = time.time()
            response = self.vllm_client.text_analysis(test_prompt, max_tokens=100)
            elapsed_time = time.time() - start_time
            
            logger.info(f"✅ VLLM连接正常，响应时间: {elapsed_time:.2f}秒")
            logger.info(f"📝 测试响应: {response}")
            return True
            
        except Exception as e:
            logger.error(f"❌ VLLM连接测试失败: {e}")
            return False
    
    def score_document_from_file(self, file_path: str) -> dict:
        """
        对指定文件进行完整的RAG评分
        
        Args:
            file_path: 要评分的文档路径
            
        Returns:
            评分结果字典
        """
        try:
            logger.info(f"📄 开始评分文档: {file_path}")
            
            # 1. 检查文件是否存在
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 2. 预处理文档
            logger.info("🔄 正在预处理文档...")
            document = self.pipeline.process(file_path)
            logger.info(f"✅ 文档预处理完成: {len(document.text_content)} 个文本段落, {len(document.tables)} 个表格")
            
            # 3. 执行RAG评分
            logger.info("⚖️  开始RAG智能评分...")
            scoring_result = self.scoring_engine.score_document(document)
            
            # 4. 保存评分报告
            report_filename = f"rag_scoring_report_{Path(file_path).stem}_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
            report_path = self.output_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(scoring_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 JSON评分报告已保存: {report_path}")
            
            # 5. 生成HTML报告
            try:
                html_filename = report_filename.replace('.json', '.html')
                html_path = self.html_output_dir / html_filename
                self.html_generator.generate_html_report(scoring_result, str(html_path))
                logger.info(f"🌐 HTML评分报告已生成: {html_path}")
            except Exception as e:
                logger.error(f"❌ HTML报告生成失败: {e}")
            
            # 6. 生成批注版文档
            try:
                logger.info("📝 正在生成批注版文档...")
                annotated_file = self.generate_annotated_document(
                    file_path, 
                    scoring_result
                )
                logger.info(f"✅ 批注版文档已生成: {annotated_file}")
                scoring_result['annotated_document_path'] = str(annotated_file)
            except Exception as e:
                logger.error(f"❌ 批注文档生成失败: {e}")
                import traceback
                traceback.print_exc()
            
            # 7. 打印评分摘要
            self._print_scoring_summary(scoring_result)
            
            return scoring_result
            
        except Exception as e:
            logger.error(f"❌ 文档评分失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def score_existing_document(self, document_name: str = None) -> dict:
        """
        对已在知识库中的文档进行评分
        
        Args:
            document_name: 文档名称，如果为None则对第一个文档评分
            
        Returns:
            评分结果字典
        """
        try:
            kb_stats = self.knowledge_base.get_stats()
            if kb_stats['total_documents'] == 0:
                raise ValueError("知识库中没有文档，请先添加文档或使用 score_document_from_file 方法")
            
            # 选择要评分的文档
            if document_name is None:
                document_name = kb_stats['documents'][0]
                logger.info(f"📄 使用知识库中的第一个文档: {document_name}")
            else:
                if document_name not in kb_stats['documents']:
                    raise ValueError(f"文档 '{document_name}' 不在知识库中。可用文档: {kb_stats['documents']}")
            
            # 从知识库创建一个模拟的StandardizedDocument
            from src.data_processing.schemas import StandardizedDocument, DocumentInfo
            
            doc_info = DocumentInfo(
                scene_type="scenario_one",
                scene_name="作业指导书",
                file_name=document_name,
                total_pages=12,
                processing_timestamp=datetime.now(),
                classification_confidence=0.8
            )
            
            document = StandardizedDocument(
                document_info=doc_info,
                text_content=[],  # 空的，因为内容已在知识库中
                tables=[],
                images=[]
            )
            
            logger.info(f"⚖️  开始对知识库文档 '{document_name}' 进行RAG评分...")
            scoring_result = self.scoring_engine.score_document(document)
            
            # 保存评分报告
            report_filename = f"rag_scoring_report_{document_name.replace('.', '_')}_{datetime.now().strftime('%Y-%m-%dT%H-%M-%S')}.json"
            report_path = self.output_dir / report_filename
            
            with open(report_path, 'w', encoding='utf-8') as f:
                json.dump(scoring_result, f, indent=2, ensure_ascii=False)
            
            logger.info(f"📊 JSON评分报告已保存: {report_path}")
            
            # 生成HTML报告
            try:
                html_filename = report_filename.replace('.json', '.html')
                html_path = self.html_output_dir / html_filename
                self.html_generator.generate_html_report(scoring_result, str(html_path))
                logger.info(f"🌐 HTML评分报告已生成: {html_path}")
            except Exception as e:
                logger.error(f"❌ HTML报告生成失败: {e}")
            
            # 打印评分摘要
            self._print_scoring_summary(scoring_result)
            
            return scoring_result
            
        except Exception as e:
            logger.error(f"❌ 文档评分失败: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def generate_annotated_document(
        self,
        original_file_path: str,
        scoring_result: dict
    ) -> Path:
        """
        生成批注版文档
        
        Args:
            original_file_path: 原始文档路径
            scoring_result: 评分结果
            
        Returns:
            批注版文档路径
        """
        original_file = Path(original_file_path)
        
        # 生成输出路径
        output_file = self.annotated_output_dir / f"{original_file.stem}_批注版{original_file.suffix}"
        
        # 调用批注管理器
        annotated_file = self.annotation_manager.annotate_document(
            original_file=original_file_path,
            scoring_result=scoring_result,
            output_path=output_file
        )
        
        # 同时生成批注报告文本文件
        try:
            if scoring_result.get('annotations'):
                from src.annotation.schemas import Annotation
                # 转换为Annotation对象
                annotations = [
                    Annotation(**ann) if isinstance(ann, dict) else ann
                    for ann in scoring_result['annotations']
                ]
                
                report_file = self.annotated_output_dir / f"{original_file.stem}_批注报告.txt"
                self.annotation_manager.generate_annotation_report(
                    annotations,
                    report_file
                )
                logger.info(f"📄 批注报告已生成: {report_file}")
        except Exception as e:
            logger.warning(f"生成批注报告失败: {e}")
        
        return annotated_file
    
    def _print_scoring_summary(self, scoring_result: dict):
        """打印评分摘要"""
        print("\n" + "="*60)
        print("📊 RAG智能评分报告摘要")
        print("="*60)
        
        doc_info = scoring_result["document_info"]
        summary = scoring_result["summary"]
        
        print(f"📄 文档信息:")
        print(f"   - 文件名: {doc_info['file_name']}")
        print(f"   - 场景类型: {doc_info['scene_name']}")
        print(f"   - 总页数: {doc_info['total_pages']}")
        
        print(f"\n🎯 总体评分:")
        print(f"   - 总分: {summary['total_score']}/{summary['max_total_score']}")
        print(f"   - 得分率: {summary['percentage']:.1f}%")
        print(f"   - 等级: {summary['grade']}")
        
        # 打印批注统计
        if 'annotation_count' in scoring_result:
            print(f"\n📝 批注统计:")
            print(f"   - 批注总数: {scoring_result['annotation_count']} 条")
            if 'annotated_document_path' in scoring_result:
                print(f"   - 批注文档: {scoring_result['annotated_document_path']}")
        
        print(f"\n📋 各项评分:")
        detailed_scores = scoring_result["detailed_scores"]
        score_breakdown = scoring_result["score_breakdown"]
        
        for criterion_key, details in detailed_scores.items():
            breakdown = score_breakdown[criterion_key]
            print(f"   {details['name']}: {details['score']}/{details['max_score']} "
                  f"(权重: {breakdown['weight']:.1%}, 加权分: {breakdown['weighted_score']:.1f})")
        
        print(f"\n📈 评分详情:")
        for criterion_key, details in detailed_scores.items():
            print(f"\n   【{details['name']}】")
            print(f"     分数: {details['score']}/{details['max_score']}")
            print(f"     评估重点: {details.get('evaluation_focus', '综合评估')}")
            
            # 截取reasoning前200字符显示
            reasoning = details.get('reasoning', '无详细说明')
            if len(reasoning) > 200:
                reasoning = reasoning[:200] + "..."
            print(f"     评分理由: {reasoning}")
        
        print("\n" + "="*60)
    
    def batch_score_documents(self, file_paths: list) -> list:
        """
        批量评分多个文档
        
        Args:
            file_paths: 文档路径列表
            
        Returns:
            评分结果列表
        """
        results = []
        
        logger.info(f"📚 开始批量评分 {len(file_paths)} 个文档...")
        
        for i, file_path in enumerate(file_paths, 1):
            try:
                logger.info(f"📄 [{i}/{len(file_paths)}] 正在评分: {file_path}")
                result = self.score_document_from_file(file_path)
                results.append({
                    "file_path": file_path,
                    "success": True,
                    "result": result
                })
                logger.info(f"✅ [{i}/{len(file_paths)}] 评分完成")
                
            except Exception as e:
                logger.error(f"❌ [{i}/{len(file_paths)}] 评分失败: {e}")
                results.append({
                    "file_path": file_path,
                    "success": False,
                    "error": str(e)
                })
        
        # 保存批量评分汇总
        batch_summary = {
            "batch_timestamp": datetime.now().isoformat(),
            "total_files": len(file_paths),
            "successful": len([r for r in results if r["success"]]),
            "failed": len([r for r in results if not r["success"]]),
            "results": results
        }
        
        summary_path = self.output_dir / f"batch_scoring_summary_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(summary_path, 'w', encoding='utf-8') as f:
            json.dump(batch_summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"📋 批量评分汇总已保存: {summary_path}")
        logger.info(f"🎯 批量评分完成: {batch_summary['successful']}/{batch_summary['total_files']} 成功")
        
        return results

def main():
    """主函数"""
    print("🚀 RAG智能评分系统启动")
    print("="*50)
    
    # 检查命令行参数
    if len(sys.argv) < 2:
        print("用法:")
        print("  python run_complete_rag_scoring.py <command> [options]")
        print("")
        print("命令:")
        print("  test              - 测试系统连接")
        print("  score <file>      - 评分指定文件")
        print("  score-kb [name]   - 评分知识库中的文档")
        print("  batch <dir>       - 批量评分目录中的PDF文件")
        print("  html-convert      - 将现有JSON报告转换为HTML格式")
        print("")
        print("示例:")
        print("  python run_complete_rag_scoring.py test")
        print("  python run_complete_rag_scoring.py score data/raw/场景1\\(1\\).pdf")
        print("  python run_complete_rag_scoring.py score-kb")
        print("  python run_complete_rag_scoring.py batch data/raw/")
        print("  python run_complete_rag_scoring.py html-convert")
        return
    
    # 特殊处理：如果第一个参数是文件路径，默认为score命令
    if len(sys.argv) == 2 and (sys.argv[1].endswith('.pdf') or '/' in sys.argv[1]):
        command = "score"
        file_path = sys.argv[1]
    else:
        command = sys.argv[1]
    
    # 创建评分系统
    system = RAGScoringSystem()
    
    # 初始化组件
    if not system.initialize_components():
        print("❌ 系统初始化失败")
        return
    
    try:
        if command == "test":
            # 测试连接
            print("\n🧪 执行系统测试...")
            success = system.test_vllm_connection()
            if success:
                print("✅ 系统测试通过")
            else:
                print("❌ 系统测试失败")
                
        elif command == "score":
            # 评分单个文件
            if 'file_path' not in locals():
                if len(sys.argv) < 3:
                    print("❌ 请指定要评分的文件路径")
                    return
                file_path = sys.argv[2]
            
            print(f"\n📄 评分文件: {file_path}")
            system.score_document_from_file(file_path)
            
        elif command == "score-kb":
            # 评分知识库中的文档
            document_name = sys.argv[2] if len(sys.argv) > 2 else None
            print(f"\n📚 评分知识库文档: {document_name or '(第一个文档)'}")
            system.score_existing_document(document_name)
            
        elif command == "batch":
            # 批量评分
            if len(sys.argv) < 3:
                print("❌ 请指定要批量评分的目录路径")
                return
            
            dir_path = Path(sys.argv[2])
            if not dir_path.exists():
                print(f"❌ 目录不存在: {dir_path}")
                return
            
            pdf_files = list(dir_path.glob("*.pdf"))
            if not pdf_files:
                print(f"❌ 目录中没有找到PDF文件: {dir_path}")
                return
            
            print(f"\n📚 批量评分目录: {dir_path}")
            print(f"找到 {len(pdf_files)} 个PDF文件")
            system.batch_score_documents([str(f) for f in pdf_files])
            
        elif command == "html-convert":
            # 批量转换JSON报告为HTML
            json_reports_dir = "output/rag_scoring_reports"
            html_output_dir = "output/rag_scoring_reports/html"
            
            if not Path(json_reports_dir).exists():
                print(f"❌ JSON报告目录不存在: {json_reports_dir}")
                return
            
            print(f"\n🌐 批量转换JSON报告为HTML格式...")
            print(f"源目录: {json_reports_dir}")
            print(f"输出目录: {html_output_dir}")
            
            # 不需要初始化完整系统，只使用HTML生成器
            html_generator = HTMLReportGenerator()
            generated_files = html_generator.batch_convert_reports(json_reports_dir, html_output_dir)
            
            if generated_files:
                print(f"✅ 成功转换 {len(generated_files)} 个HTML报告:")
                for file_path in generated_files:
                    print(f"   📄 {file_path}")
            else:
                print("⚠️  没有找到需要转换的JSON报告文件")
            
        else:
            print(f"❌ 未知命令: {command}")
            
    except KeyboardInterrupt:
        print("\n⚠️  用户中断操作")
    except Exception as e:
        print(f"\n❌ 执行过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()