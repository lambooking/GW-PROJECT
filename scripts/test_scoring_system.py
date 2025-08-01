"""
测试脚本，用于验证完整的文档处理和评分流程。
"""
import json
import logging
import sys
from pathlib import Path

# 将src目录添加到Python路径
sys.path.append(str(Path(__file__).parent.parent))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline
from src.inference.vllm_client import VLLMInferenceClient
from src.inference.info_extractor import LLMInfoExtractor
from src.inference.scoring_engine import SimpleScoringEngine

logger = logging.getLogger(__name__)

def main():
    """
    主测试函数，执行完整的"预处理 → 信息提取 → 评分"流程。
    """
    # 配置日志
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(name)s - %(message)s')

    print("=" * 60)
    print("🚀 开始完整的文档智能审核流程测试")
    print("=" * 60)

    # --- 步骤 1: 运行预处理流水线 ---
    logger.info("步骤 1: 正在运行预处理流水线...")
    test_file = Path(__file__).parent.parent / "data" / "raw" / "场景1(1).pdf"
    if not test_file.exists():
        logger.error(f"测试文件未找到: {test_file}")
        return

    try:
        pipeline = PreprocessingPipeline()
        standardized_doc = pipeline.process(str(test_file))
        logger.info(f"✅ 预处理完成。提取到 {len(standardized_doc.text_content)} 个文本段落，{len(standardized_doc.tables)} 个表格。")
    except Exception as e:
        logger.error(f"❌ 预处理阶段失败: {e}", exc_info=True)
        return

    # --- 步骤 2: 初始化所有组件 ---
    logger.info("步骤 2: 正在初始化VLLM客户端、信息提取器和评分引擎...")
    try:
        vllm_client = VLLMInferenceClient(base_url="http://localhost:8000/v1")
        info_extractor = LLMInfoExtractor(vllm_client)
        scoring_engine = SimpleScoringEngine(vllm_client)
        logger.info("✅ 所有组件初始化成功。")
    except Exception as e:
        logger.error(f"❌ 组件初始化失败: {e}", exc_info=True)
        return

    # --- 步骤 3: 执行信息提取 ---
    logger.info("步骤 3: 正在从文档中提取结构化信息...")
    try:
        extracted_info = info_extractor.extract_all_info(standardized_doc)
        logger.info("✅ 信息提取成功。")
        
        print("\n" + "=" * 40)
        print("📄 提取的文档信息:")
        print("=" * 40)
        print(json.dumps(extracted_info, indent=2, ensure_ascii=False))
        
    except Exception as e:
        logger.error(f"❌ 信息提取失败: {e}", exc_info=True)
        return

    # --- 步骤 4: 执行智能评分 ---
    logger.info("步骤 4: 正在进行智能评分...")
    try:
        scoring_result = scoring_engine.score_document(standardized_doc, extracted_info)
        logger.info("✅ 智能评分完成。")
        
        print("\n" + "=" * 40)
        print("🎯 智能评分结果:")
        print("=" * 40)
        print(json.dumps(scoring_result, indent=2, ensure_ascii=False))
        
        # 打印简化的结果摘要
        print("\n" + "=" * 40)
        print("📊 评分摘要:")
        print("=" * 40)
        total_score = scoring_result.get("total_score", 0)
        grade = scoring_result.get("grade", "未知")
        print(f"总分: {total_score}/100")
        print(f"等级: {grade}")
        
        detailed_scores = scoring_result.get("detailed_scores", {})
        if detailed_scores:
            print("\n各项评分:")
            for key, value in detailed_scores.items():
                if isinstance(value, dict) and "score" in value:
                    print(f"  - {key}: {value['score']} 分")
        
    except Exception as e:
        logger.error(f"❌ 智能评分失败: {e}", exc_info=True)
        return

    print("\n" + "=" * 60)
    print("🎉 完整流程测试成功完成！")
    print("=" * 60)

if __name__ == "__main__":
    main()