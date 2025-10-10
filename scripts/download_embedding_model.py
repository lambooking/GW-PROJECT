#!/usr/bin/env python3
"""
Embedding 模型下载工具
用于预先下载魔塔社区的中文 Embedding 模型
"""
import sys
import logging
from pathlib import Path

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def download_embedding_model(
    model_id: str = "iic/nlp_gte_sentence-embedding_chinese-base",
    local_path: str = "/home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base"
):
    """
    从魔塔社区下载 Embedding 模型
    
    Args:
        model_id: 魔塔社区模型ID
        local_path: 本地保存路径
    """
    try:
        logger.info("="*60)
        logger.info("🚀 Embedding 模型下载工具")
        logger.info("="*60)
        logger.info(f"📦 模型ID: {model_id}")
        logger.info(f"📁 保存路径: {local_path}")
        logger.info("")
        
        # 检查依赖
        logger.info("🔍 检查依赖包...")
        try:
            from modelscope import snapshot_download
            logger.info("  ✅ modelscope 已安装")
        except ImportError:
            logger.error("  ❌ modelscope 未安装")
            logger.error("  请执行: pip install modelscope")
            return False
        
        try:
            from sentence_transformers import SentenceTransformer
            logger.info("  ✅ sentence-transformers 已安装")
        except ImportError:
            logger.error("  ❌ sentence-transformers 未安装")
            logger.error("  请执行: pip install sentence-transformers")
            return False
        
        logger.info("")
        
        # 检查本地是否已存在
        local_path_obj = Path(local_path)
        if local_path_obj.exists():
            logger.warning(f"⚠️  本地路径已存在: {local_path}")
            
            # 尝试加载验证
            try:
                logger.info("🔄 验证现有模型...")
                model = SentenceTransformer(str(local_path_obj))
                test_embedding = model.encode(["测试文本"], show_progress_bar=False)
                logger.info(f"  ✅ 现有模型可用 (向量维度: {len(test_embedding[0])})")
                logger.info("")
                logger.info("✨ 无需重复下载，模型已可用")
                return True
            except Exception as e:
                logger.warning(f"  ⚠️  现有模型验证失败: {e}")
                logger.info("  📥 将重新下载模型...")
                import shutil
                shutil.rmtree(local_path_obj)
        
        # 确保父目录存在
        local_path_obj.parent.mkdir(parents=True, exist_ok=True)
        
        # 下载模型
        logger.info("📥 开始从魔塔社区下载模型...")
        logger.info("   （首次下载可能需要较长时间，请耐心等待）")
        logger.info("")
        
        model_dir = snapshot_download(
            model_id,
            cache_dir=str(local_path_obj.parent),
            revision='master'
        )
        
        logger.info(f"✅ 模型下载完成: {model_dir}")
        
        # 移动到目标位置
        if Path(model_dir) != local_path_obj:
            import shutil
            logger.info(f"📦 移动模型到: {local_path_obj}")
            if local_path_obj.exists():
                shutil.rmtree(local_path_obj)
            shutil.move(model_dir, local_path_obj)
        
        # 验证模型
        logger.info("")
        logger.info("🔍 验证下载的模型...")
        try:
            model = SentenceTransformer(str(local_path_obj))
            test_texts = ["测试文本1", "测试文本2", "这是一个中文句子"]
            test_embeddings = model.encode(test_texts, show_progress_bar=False)
            
            logger.info(f"  ✅ 模型加载成功")
            logger.info(f"  📊 向量维度: {len(test_embeddings[0])}")
            logger.info(f"  📝 测试编码: {len(test_texts)} 个文本")
            logger.info("")
            logger.info("="*60)
            logger.info("🎉 模型下载并验证成功！")
            logger.info("="*60)
            logger.info("")
            logger.info("💡 使用方法:")
            logger.info("  在代码中模型会自动从该路径加载")
            logger.info(f"  路径: {local_path_obj}")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ 模型验证失败: {e}")
            return False
            
    except Exception as e:
        logger.error(f"❌ 模型下载失败: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="从魔塔社区下载 Embedding 模型",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 使用默认配置下载
  python scripts/download_embedding_model.py
  
  # 指定模型ID和保存路径
  python scripts/download_embedding_model.py \\
    --model-id iic/nlp_gte_sentence-embedding_chinese-base \\
    --local-path /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base
  
  # 下载其他中文模型
  python scripts/download_embedding_model.py \\
    --model-id damo/nlp_corom_sentence-embedding_chinese-small \\
    --local-path /home/dataset-assist-0/models/nlp_corom_sentence-embedding_chinese-small
        """
    )
    
    parser.add_argument(
        '--model-id',
        type=str,
        default='iic/nlp_gte_sentence-embedding_chinese-base',
        help='魔塔社区模型ID (默认: iic/nlp_gte_sentence-embedding_chinese-base)'
    )
    
    parser.add_argument(
        '--local-path',
        type=str,
        default='/home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base',
        help='本地保存路径 (默认: /home/dataset-assist-0/models/nlp_gte_sentence-embedding_chinese-base)'
    )
    
    args = parser.parse_args()
    
    # 执行下载
    success = download_embedding_model(
        model_id=args.model_id,
        local_path=args.local_path
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

