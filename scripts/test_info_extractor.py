"""
测试脚本，用于验证LLMInfoExtractor能否成功从文档中提取信息。
"""
import logging
import sys
from pathlib import Path

# 将src目录添加到Python路径，以便能够导入我们的模块
# 这是一种常见的在测试脚本中解决模块导入问题的方法
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.inference.vllm_client import VLLMInferenceClient
from src.inference.info_extractor import LLMInfoExtractor

logger = logging.getLogger(__name__)


def main():
    """
    主测试函数，执行完整的“预处理 -> 信息提取”流程。
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    # --- 步骤 1: 运行预处理流水线 ---
    logger.info("步骤 1: 正在运行预处理流水线...")
    test_file = Path(__file__).parent.parent / "data" / "raw" / "场景1(1).pdf"
    if not test_file.exists():
        logger.error(f"测试文件未找到: {test_file}")
        return

    try:
        pipeline = PreprocessingPipeline()
        standardized_doc = pipeline.process(str(test_file))
        logger.info(f"预处理完成。提取到 {len(standardized_doc.text_content)} 个文本段落。")
    except Exception as e:
        logger.error(f"预处理阶段失败: {e}", exc_info=True)
        return

    # --- 步骤 2: 初始化VLLM客户端和提取器 ---
    logger.info("步骤 2: 正在初始化VLLM客户端和信息提取器...")
    try:
        # 假设VLLM服务在本地8000端口运行
        vllm_client = VLLMInferenceClient(base_url="http://localhost:8000/v1")
        info_extractor = LLMInfoExtractor(vllm_client)
    except Exception as e:
        logger.error(f"客户端或提取器初始化失败: {e}", exc_info=True)
        return

    # --- 步骤 3: 执行信息提取 ---
    logger.info("步骤 3: 正在从文档中提取元数据...")
    try:
        extracted_info = info_extractor.extract_all_info(standardized_doc)
        
        # --- 步骤 4: 打印结果 ---
        logger.info("🎉🎉🎉 信息提取成功！🎉🎉🎉")
        import json
        pretty_json = json.dumps(extracted_info, indent=2, ensure_ascii=False)
        print(pretty_json)

    except Exception as e:
        logger.error(f"信息提取阶段失败。请检查VLLM服务是否正在运行并且模型 'qwen-vl-7b' 已加载。", exc_info=True)


if __name__ == "__main__":
    main()
