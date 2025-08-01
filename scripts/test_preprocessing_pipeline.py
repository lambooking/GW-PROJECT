#!/usr/bin/env python3
"""
测试预处理管道 - 演示完整的数据预处理流程
"""

import sys
import os
import json
from pathlib import Path

# 添加项目根目录到Python路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_processing.preprocessing_pipeline import PreprocessingPipeline

def test_preprocessing_pipeline():
    """测试完整的预处理管道"""
    
    print("=" * 80)
    print("自动化竞赛文档分析与评分系统 - 数据预处理管道测试")
    print("=" * 80)
    
    # 初始化预处理管道
    pipeline = PreprocessingPipeline(enable_enhanced_ocr=True)
    
    # 测试文件
    test_files = [
        "data/raw/场景1(1).pdf",
        "data/raw/场景2(1).docx"
    ]
    
    # 检查文件是否存在
    existing_files = []
    for file_path in test_files:
        if os.path.exists(file_path):
            existing_files.append(file_path)
            print(f"✓ 找到测试文件: {file_path}")
        else:
            print(f"✗ 未找到测试文件: {file_path}")
    
    if not existing_files:
        print("\n❌ 没有找到可测试的文件，请确保示例文件存在。")
        return
    
    print(f"\n📋 将测试 {len(existing_files)} 个文件")
    print("-" * 60)
    
    # 测试单个文档处理
    for i, file_path in enumerate(existing_files, 1):
        print(f"\n🔄 测试 {i}/{len(existing_files)}: {Path(file_path).name}")
        print("-" * 40)
        
        try:
            # 处理文档
            result = pipeline.process_document(file_path, include_ocr=True)
            
            if result.get('status') == 'success':
                print("✅ 处理成功!")
                
                # 显示基本信息
                file_info = result.get('file_info', {})
                classification = result.get('classification', {})
                document_profile = result.get('document_profile', {})
                performance_metrics = result.get('performance_metrics', {})
                
                print(f"📄 文件类型: {file_info.get('file_type')}")
                print(f"📑 总页数: {file_info.get('total_pages')}")
                print(f"🎯 场景分类: {classification.get('scenario_name')} (置信度: {classification.get('confidence', 0):.2%})")
                
                # 显示内容统计
                content_stats = document_profile.get('content_statistics', {})
                print(f"📊 内容统计:")
                print(f"   - 文本段落: {content_stats.get('text_sections', 0)}")
                print(f"   - 表格数量: {content_stats.get('tables', 0)}")
                print(f"   - 图片数量: {content_stats.get('images', 0)}")
                
                # 显示实体统计
                entity_stats = document_profile.get('entity_statistics', {})
                print(f"🏷️ 实体统计:")
                print(f"   - 日期: {entity_stats.get('dates', 0)}")
                print(f"   - 人员: {entity_stats.get('personnel', 0)}")
                print(f"   - 技术参数: {entity_stats.get('technical_parameters', 0)}")
                print(f"   - 地理位置: {entity_stats.get('locations', 0)}")
                print(f"   - 标准: {entity_stats.get('standards', 0)}")
                print(f"   - 组织机构: {entity_stats.get('organizations', 0)}")
                
                # 显示质量评估
                quality_assessment = result.get('quality_assessment', {})
                print(f"🎖️ 质量评估:")
                print(f"   - 总体质量分数: {quality_assessment.get('overall_quality_score', 0):.2f}")
                print(f"   - 质量等级: {quality_assessment.get('quality_grade', 'N/A')}")
                
                # 显示性能指标
                print(f"⏱️ 性能指标:")
                print(f"   - 文档解析: {performance_metrics.get('step1_parsing', 0):.2f}秒")
                print(f"   - 结构化提取: {performance_metrics.get('step2_extraction', 0):.2f}秒")
                print(f"   - 多模态融合: {performance_metrics.get('step3_fusion', 0):.2f}秒")
                print(f"   - 实体提取: {performance_metrics.get('step4_entities', 0):.2f}秒")
                print(f"   - OCR处理: {performance_metrics.get('step5_ocr', 0):.2f}秒")
                print(f"   - 总处理时间: {performance_metrics.get('total_time', 0):.2f}秒")
                
                # 显示关键实体示例
                analysis_ready_data = result.get('analysis_ready_data', {})
                key_entities = analysis_ready_data.get('key_entities', {})
                
                if key_entities.get('dates'):
                    print(f"📅 发现的关键日期:")
                    for date_entity in key_entities['dates'][:3]:  # 只显示前3个
                        print(f"   - {date_entity.get('value')} ({date_entity.get('semantic_type', 'unknown')})")
                
                if key_entities.get('personnel'):
                    print(f"👥 发现的人员信息:")
                    for person in key_entities['personnel'][:3]:  # 只显示前3个
                        name = person.get('name', 'Unknown')
                        title = person.get('job_title', 'Unknown')
                        print(f"   - {name} ({title})")
                
                if key_entities.get('technical_parameters'):
                    print(f"🔧 发现的技术参数:")
                    for param in key_entities['technical_parameters'][:3]:  # 只显示前3个
                        param_type = param.get('parameter_type', 'unknown')
                        value = param.get('normalized_value', 0)
                        unit = param.get('standard_unit', '')
                        print(f"   - {param_type}: {value} {unit}")
                
                # 保存详细结果
                output_file = f"output/preprocessing_result_{Path(file_path).stem}.json"
                os.makedirs("output", exist_ok=True)
                
                # 创建可序列化的结果（移除二进制数据）
                serializable_result = json.loads(json.dumps(result, default=str))
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(serializable_result, f, ensure_ascii=False, indent=2)
                
                print(f"💾 详细结果已保存到: {output_file}")
                
            else:
                print(f"❌ 处理失败: {result.get('error', 'Unknown error')}")
                
        except Exception as e:
            print(f"❌ 处理异常: {str(e)}")
            import traceback
            traceback.print_exc()
    
    # 测试批量处理
    if len(existing_files) > 1:
        print(f"\n🔄 测试批量处理功能")
        print("-" * 40)
        
        try:
            batch_result = pipeline.process_document_batch(existing_files, include_ocr=False)
            
            batch_summary = batch_result.get('batch_summary', {})
            print(f"📊 批量处理结果:")
            print(f"   - 总文件数: {batch_summary.get('total_files', 0)}")
            print(f"   - 成功处理: {batch_summary.get('successful_files', 0)}")
            print(f"   - 处理失败: {batch_summary.get('failed_files', 0)}")
            print(f"   - 成功率: {batch_summary.get('success_rate', 0):.1f}%")
            print(f"   - 总处理时间: {batch_summary.get('total_processing_time', 0):.2f}秒")
            print(f"   - 平均每文件: {batch_summary.get('average_time_per_file', 0):.2f}秒")
            
            # 保存批量结果
            batch_output_file = "output/batch_preprocessing_result.json"
            with open(batch_output_file, 'w', encoding='utf-8') as f:
                json.dump(json.loads(json.dumps(batch_result, default=str)), f, ensure_ascii=False, indent=2)
            
            print(f"💾 批量结果已保存到: {batch_output_file}")
            
        except Exception as e:
            print(f"❌ 批量处理异常: {str(e)}")

def analyze_preprocessing_performance():
    """分析预处理性能"""
    print("\n" + "=" * 80)
    print("预处理性能分析")
    print("=" * 80)
    
    # 查找输出文件
    output_dir = Path("output")
    if not output_dir.exists():
        print("❌ 未找到输出目录，请先运行预处理测试")
        return
    
    result_files = list(output_dir.glob("preprocessing_result_*.json"))
    
    if not result_files:
        print("❌ 未找到预处理结果文件")
        return
    
    print(f"📊 分析 {len(result_files)} 个处理结果")
    
    total_processing_times = []
    quality_scores = []
    
    for result_file in result_files:
        try:
            with open(result_file, 'r', encoding='utf-8') as f:
                result = json.load(f)
            
            # 收集性能数据
            performance_metrics = result.get('performance_metrics', {})
            total_time = performance_metrics.get('total_time', 0)
            total_processing_times.append(total_time)
            
            # 收集质量数据
            quality_assessment = result.get('quality_assessment', {})
            quality_score = quality_assessment.get('overall_quality_score', 0)
            quality_scores.append(quality_score)
            
            print(f"📄 {result_file.stem}:")
            print(f"   - 处理时间: {total_time:.2f}秒")
            print(f"   - 质量分数: {quality_score:.2f}")
            
        except Exception as e:
            print(f"❌ 读取文件 {result_file} 失败: {e}")
    
    if total_processing_times:
        avg_time = sum(total_processing_times) / len(total_processing_times)
        max_time = max(total_processing_times)
        min_time = min(total_processing_times)
        
        print(f"\n⏱️ 处理时间统计:")
        print(f"   - 平均时间: {avg_time:.2f}秒")
        print(f"   - 最长时间: {max_time:.2f}秒")
        print(f"   - 最短时间: {min_time:.2f}秒")
        
        # 检查是否满足120秒要求
        if max_time <= 120:
            print(f"   ✅ 所有文档都在120秒内处理完成")
        else:
            print(f"   ⚠️ 有文档超过120秒处理时间限制")
    
    if quality_scores:
        avg_quality = sum(quality_scores) / len(quality_scores)
        max_quality = max(quality_scores)
        min_quality = min(quality_scores)
        
        print(f"\n🎯 质量评估统计:")
        print(f"   - 平均质量: {avg_quality:.2f}")
        print(f"   - 最高质量: {max_quality:.2f}")
        print(f"   - 最低质量: {min_quality:.2f}")

def main():
    """主函数"""
    print("🚀 启动预处理管道测试...")
    
    try:
        # 测试预处理管道
        test_preprocessing_pipeline()
        
        # 分析性能
        analyze_preprocessing_performance()
        
        print("\n" + "=" * 80)
        print("✅ 预处理管道测试完成!")
        print("=" * 80)
        
        print("\n📋 后续步骤建议:")
        print("1. 检查输出目录中的详细结果文件")
        print("2. 根据质量评估结果优化预处理参数")
        print("3. 如果处理时间超过120秒，考虑性能优化")
        print("4. 基于提取的实体数据设计AI分析模块")
        
    except KeyboardInterrupt:
        print("\n⏹️ 用户中断测试")
    except Exception as e:
        print(f"\n❌ 测试过程中发生错误: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()