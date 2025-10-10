#!/usr/bin/env python3
"""
系统修复验证脚本
自动检查所有修复是否正确实施
"""
import sys
import subprocess
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class FixVerifier:
    """修复验证器"""
    
    def __init__(self):
        self.passed = []
        self.failed = []
        self.warnings = []
    
    def print_header(self, text):
        """打印标题"""
        print("\n" + "="*60)
        print(f"  {text}")
        print("="*60)
    
    def check_dependencies(self):
        """检查依赖包"""
        self.print_header("检查 1: Python 依赖包")
        
        required_packages = [
            'modelscope',
            'sentence_transformers',
            'chromadb',
            'python-docx'
        ]
        
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                logger.info(f"✅ {package} 已安装")
                self.passed.append(f"依赖: {package}")
            except ImportError:
                logger.error(f"❌ {package} 未安装")
                self.failed.append(f"依赖: {package}")
                logger.error(f"   安装命令: pip install {package}")
    
    def check_antiword(self):
        """检查 antiword 工具"""
        self.print_header("检查 2: antiword 工具")
        
        try:
            result = subprocess.run(
                ['which', 'antiword'],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                antiword_path = result.stdout.strip()
                logger.info(f"✅ antiword 已安装: {antiword_path}")
                
                # 验证版本
                version_result = subprocess.run(
                    ['antiword', '-v'],
                    capture_output=True,
                    text=True
                )
                logger.info(f"   版本: {version_result.stdout.strip()}")
                self.passed.append("antiword 工具")
            else:
                logger.warning("⚠️  antiword 未安装（.doc 文件支持将不可用）")
                self.warnings.append("antiword 工具")
                logger.info("   安装命令:")
                logger.info("     Ubuntu/Debian: sudo apt-get install antiword")
                logger.info("     CentOS/RHEL: sudo yum install antiword")
        except Exception as e:
            logger.error(f"❌ 检查 antiword 失败: {e}")
            self.failed.append("antiword 工具")
    
    def check_embedding_model(self):
        """检查 Embedding 模型"""
        self.print_header("检查 3: Embedding 模型")
        
        # 检查本地路径
        model_path = Path("/home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base")
        
        if model_path.exists():
            logger.info(f"✅ 模型目录存在: {model_path}")
            
            # 检查关键文件
            key_files = ['config.json', 'pytorch_model.bin', 'tokenizer_config.json']
            missing_files = []
            
            for file in key_files:
                if not (model_path / file).exists():
                    missing_files.append(file)
            
            if missing_files:
                logger.warning(f"⚠️  模型目录不完整，缺失文件: {missing_files}")
                self.warnings.append("Embedding 模型（不完整）")
            else:
                logger.info("   模型文件完整")
                self.passed.append("Embedding 模型")
        else:
            logger.warning(f"⚠️  模型目录不存在: {model_path}")
            logger.info("   运行以下命令下载:")
            logger.info("     python scripts/download_embedding_model.py")
            self.warnings.append("Embedding 模型（未下载）")
    
    def test_model_loading(self):
        """测试模型加载"""
        self.print_header("检查 4: 模型加载测试")
        
        try:
            from src.inference.rag_knowledge_base import EmbeddingModel
            
            logger.info("正在加载模型...")
            model = EmbeddingModel()
            
            logger.info("✅ 模型加载成功")
            logger.info(f"   向量维度: {model.embedding_dim}")
            
            # 测试编码
            logger.info("测试文本编码...")
            test_texts = ["测试文本1", "测试文本2"]
            embeddings = model.encode(test_texts)
            
            logger.info(f"✅ 文本编码成功")
            logger.info(f"   编码文本数: {len(embeddings)}")
            logger.info(f"   向量维度: {len(embeddings[0])}")
            
            # 验证不是随机向量
            if len(embeddings[0]) == 768:
                logger.info("✅ 向量维度正确（768维，中文模型）")
                self.passed.append("模型加载和编码")
            else:
                logger.warning(f"⚠️  向量维度异常: {len(embeddings[0])}")
                self.warnings.append("模型加载和编码")
                
        except Exception as e:
            logger.error(f"❌ 模型测试失败: {e}")
            self.failed.append("模型加载和编码")
            import traceback
            logger.debug(traceback.format_exc())
    
    def check_doc_parser(self):
        """检查 DOC 解析器"""
        self.print_header("检查 5: DOC 文件解析器")
        
        try:
            from src.data.parsers.docx_parser import DocxDocumentParser, ANTIWORD_AVAILABLE
            
            parser = DocxDocumentParser()
            
            # 检查支持的格式
            test_file_doc = Path("test.doc")
            test_file_docx = Path("test.docx")
            
            if parser.supports_format(test_file_doc):
                logger.info("✅ 支持 .doc 格式")
            else:
                logger.error("❌ 不支持 .doc 格式")
                self.failed.append("DOC 解析器（格式支持）")
            
            if parser.supports_format(test_file_docx):
                logger.info("✅ 支持 .docx 格式")
            else:
                logger.error("❌ 不支持 .docx 格式")
                self.failed.append("DOCX 解析器（格式支持）")
            
            # 检查 antiword 可用性
            if ANTIWORD_AVAILABLE:
                logger.info("✅ antiword 可用，.doc 文件可以解析")
                self.passed.append("DOC 解析器")
            else:
                logger.warning("⚠️  antiword 不可用，.doc 文件无法解析")
                logger.info("   安装 antiword 以支持 .doc 文件")
                self.warnings.append("DOC 解析器（antiword 不可用）")
                
        except Exception as e:
            logger.error(f"❌ DOC 解析器检查失败: {e}")
            self.failed.append("DOC 解析器")
    
    def check_knowledge_base(self):
        """检查知识库"""
        self.print_header("检查 6: 向量知识库")
        
        kb_path = Path("output/rag_knowledge_base/chromadb")
        
        if kb_path.exists():
            logger.info(f"✅ 知识库目录存在: {kb_path}")
            
            # 检查是否有内容
            try:
                from src.inference.rag_knowledge_base import RAGKnowledgeBase
                
                kb = RAGKnowledgeBase()
                stats = kb.get_stats()
                
                logger.info(f"   文档数: {stats['total_documents']}")
                logger.info(f"   文档块数: {stats['total_chunks']}")
                
                if stats['total_chunks'] > 0:
                    logger.info("✅ 知识库有内容")
                    self.passed.append("向量知识库")
                else:
                    logger.warning("⚠️  知识库为空")
                    logger.info("   运行以下命令索引文档:")
                    logger.info("     python quick_reindex.py")
                    self.warnings.append("向量知识库（为空）")
                    
            except Exception as e:
                logger.error(f"❌ 知识库检查失败: {e}")
                self.failed.append("向量知识库")
        else:
            logger.warning(f"⚠️  知识库目录不存在: {kb_path}")
            logger.info("   运行以下命令创建知识库:")
            logger.info("     python quick_reindex.py")
            self.warnings.append("向量知识库（不存在）")
    
    def print_summary(self):
        """打印总结"""
        self.print_header("验证总结")
        
        print(f"\n✅ 通过: {len(self.passed)}")
        for item in self.passed:
            print(f"   • {item}")
        
        if self.warnings:
            print(f"\n⚠️  警告: {len(self.warnings)}")
            for item in self.warnings:
                print(f"   • {item}")
        
        if self.failed:
            print(f"\n❌ 失败: {len(self.failed)}")
            for item in self.failed:
                print(f"   • {item}")
        
        print("\n" + "="*60)
        
        if not self.failed:
            if self.warnings:
                print("🟡 验证基本通过，但有警告需要注意")
                print("   建议解决警告项以获得最佳体验")
                return 1
            else:
                print("🎉 所有检查通过！系统已正确配置")
                return 0
        else:
            print("❌ 验证失败，请解决上述问题")
            return 2


def main():
    """主函数"""
    print("="*60)
    print("  RAG 评分系统修复验证")
    print("="*60)
    print("\n本脚本将检查所有修复是否正确实施\n")
    
    verifier = FixVerifier()
    
    try:
        verifier.check_dependencies()
        verifier.check_antiword()
        verifier.check_embedding_model()
        verifier.test_model_loading()
        verifier.check_doc_parser()
        verifier.check_knowledge_base()
        
    except KeyboardInterrupt:
        print("\n\n⚠️  用户中断验证")
        return 130
    except Exception as e:
        print(f"\n\n❌ 验证过程发生错误: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return verifier.print_summary()


if __name__ == "__main__":
    sys.exit(main())

