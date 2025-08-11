#!/usr/bin/env python3
"""
RAG智能评分系统 - 改进版
基于原版本进行轻量级优化，保留性能优势
"""

import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path

# 创建logs目录
Path("logs").mkdir(exist_ok=True)

# 配置日志 - 简化版
logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s: %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(f'logs/rag_scoring_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log')
    ]
)

logger = logging.getLogger(__name__)

# Ensure project root is on sys.path when running from scripts/ subdirectories
try:
    project_root = Path(__file__).resolve().parents[2]
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
except Exception:
    # Best-effort; imports below may still work when executed from repo root
    pass

# 延迟导入项目模块，避免在仅查看帮助时触发重依赖

class ImprovedRAGScoringSystem:
    """改进的RAG评分系统 - 保持原有性能"""
    
    def __init__(self, vllm_base_url: str = "http://localhost:8000/v1", 
                 vllm_model: str = "qwen2.5-vl-3b"):
        """快速初始化 - 延迟加载组件"""
        self.vllm_base_url = vllm_base_url
        self.vllm_model = vllm_model
        
        # 创建输出目录
        self.output_dir = Path("output/rag_scoring_reports")
        self.html_output_dir = Path("output/rag_scoring_reports/html")
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.html_output_dir.mkdir(parents=True, exist_ok=True)
        
        # 延迟初始化 - 只在需要时创建
        self._knowledge_base = None
        self._vllm_client = None
        self._scoring_engine = None
        self._pipeline = None
        self._html_generator = None
    
    @property
    def knowledge_base(self):
        """延迟初始化知识库"""
        if self._knowledge_base is None:
            logger.info("📚 初始化知识库...")
            from src.inference.rag_knowledge_base import RAGKnowledgeBase
            self._knowledge_base = RAGKnowledgeBase()
            logger.info("✅ 知识库就绪")
        return self._knowledge_base
    
    @property
    def vllm_client(self):
        """延迟初始化VLLM客户端"""
        if self._vllm_client is None:
            logger.info("🤖 连接VLLM服务...")
            from src.inference.vllm_client import VLLMInferenceClient
            self._vllm_client = VLLMInferenceClient(
                base_url=self.vllm_base_url,
                model_name=self.vllm_model
            )
            logger.info("✅ VLLM已连接")
        return self._vllm_client
    
    @property
    def scoring_engine(self):
        """延迟初始化评分引擎"""
        if self._scoring_engine is None:
            logger.info("⚖️  初始化评分引擎...")
            from src.inference.rag_scoring_engine import RAGScoringEngine
            self._scoring_engine = RAGScoringEngine(
                vllm_client=self.vllm_client,
                knowledge_base=self.knowledge_base
            )
            logger.info("✅ 评分引擎就绪")
        return self._scoring_engine
    
    @property
    def pipeline(self):
        """延迟初始化预处理管线"""
        if self._pipeline is None:
            logger.info("🔧 初始化预处理管线...")
            from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
            self._pipeline = PreprocessingPipeline()
            logger.info("✅ 预处理管线就绪")
        return self._pipeline
    
    @property
    def html_generator(self):
        """延迟初始化HTML生成器"""
        if self._html_generator is None:
            from src.utils.html_report_generator import HTMLReportGenerator
            self._html_generator = HTMLReportGenerator()
        return self._html_generator
    
    def quick_test(self):
        """快速测试 - 最小化检查"""
        try:
            logger.info("🧪 快速系统测试...")
            
            # 1. 测试VLLM连接
            response = self.vllm_client.text_analysis("测试", max_tokens=5)
            logger.info(f"✅ VLLM测试通过: {str(response)[:30]}...")
            
            # 2. 检查知识库
            stats = self.knowledge_base.get_stats()
            logger.info(f"✅ 知识库状态: {stats['total_chunks']} 块文档")
            
            print("🎉 系统测试通过！")
            return True
            
        except Exception as e:
            logger.error(f"❌ 测试失败: {e}")
            return False
    
    def score_document(self, file_path: str):
        """评分文档 - 保持原有逻辑"""
        try:
            logger.info(f"📄 评分: {file_path}")
            
            if not Path(file_path).exists():
                raise FileNotFoundError(f"文件不存在: {file_path}")
            
            # 预处理
            document = self.pipeline.process(file_path)
            logger.info(f"✅ 预处理完成")
            
            # 评分
            scoring_result = self.scoring_engine.score_document(document)
            
            # 保存报告（JSON + HTML）
            from src.utils.report_utils import save_scoring_report
            paths = save_scoring_report(
                scoring_result=scoring_result,
                file_stem=Path(file_path).stem,
                output_dir=str(self.output_dir),
                separate_html_dir=True,
            )
            if paths.get("html_path"):
                logger.info(f"📊 报告已保存: {paths['html_path']}")
            else:
                logger.info(f"📋 JSON报告已保存: {paths['json_path']} (HTML生成失败或已跳过)")
            
            # 打印摘要
            self._print_summary(scoring_result)
            
            return scoring_result
            
        except Exception as e:
            logger.error(f"❌ 评分失败: {e}")
            raise
    
    def batch_score(self, directory: str):
        """批量评分"""
        dir_path = Path(directory)
        pdf_files = list(dir_path.glob("*.pdf"))
        
        logger.info(f"📚 批量评分: {len(pdf_files)} 个文件")
        
        results = []
        for i, file_path in enumerate(pdf_files, 1):
            try:
                logger.info(f"[{i}/{len(pdf_files)}] {file_path.name}")
                result = self.score_document(str(file_path))
                results.append({"file": str(file_path), "success": True})
            except Exception as e:
                logger.error(f"[{i}/{len(pdf_files)}] 失败: {e}")
                results.append({"file": str(file_path), "success": False, "error": str(e)})
        
        success_count = len([r for r in results if r["success"]])
        logger.info(f"🎯 批量完成: {success_count}/{len(pdf_files)} 成功")
        
        return results
    
    def _print_summary(self, scoring_result: dict):
        """打印评分摘要 - 简化版"""
        print("\\n" + "="*50)
        print("📊 评分结果")
        print("="*50)
        
        try:
            doc_info = scoring_result["document_info"]
            summary = scoring_result["summary"]
            
            print(f"📄 文件: {doc_info['file_name']}")
            print(f"🎯 总分: {summary['total_score']}/{summary['max_total_score']}")
            print(f"📈 得分率: {summary['percentage']:.1f}%")
            print(f"⭐ 等级: {summary['grade']}")
            
            # 显示前3个评分项
            detailed = scoring_result["detailed_scores"]
            print(f"\\n📋 主要评分:")
            for i, (key, details) in enumerate(list(detailed.items())[:3]):
                print(f"  {details['name']}: {details['score']}/{details['max_score']}")
                
        except Exception as e:
            logger.warning(f"摘要显示错误: {e}")
        
        print("="*50)


def main():
    """主函数 - 保持原有命令行接口"""
    
    if len(sys.argv) < 2:
        print("🚀 RAG智能评分系统 - 改进版")
        print("="*40)
        print("用法:")
        print("  python run_rag_scoring_improved.py test")
        print("  python run_rag_scoring_improved.py score <file>")
        print("  python run_rag_scoring_improved.py batch <directory>")
        print("\\n💡 保持原有性能，优化用户体验")
        return
    
    command = sys.argv[1]
    
    # 创建系统实例 - 快速启动
    system = ImprovedRAGScoringSystem()
    
    try:
        if command == "test":
            system.quick_test()
            
        elif command == "score":
            if len(sys.argv) < 3:
                print("❌ 请指定文件路径")
                return
            system.score_document(sys.argv[2])
            
        elif command == "batch":
            if len(sys.argv) < 3:
                print("❌ 请指定目录路径")
                return
            system.batch_score(sys.argv[2])
            
        else:
            print(f"❌ 未知命令: {command}")
            
    except KeyboardInterrupt:
        print("\\n⚠️  用户中断")
    except Exception as e:
        print(f"❌ 执行失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()