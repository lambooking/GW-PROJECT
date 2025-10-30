"""
批量审核汇总报告生成器
支持分层级统计和多格式报告输出
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional
from collections import defaultdict

logger = logging.getLogger(__name__)


class BatchSummaryReporter:
    """批量审核汇总报告生成器"""
    
    def __init__(self):
        """初始化报告生成器"""
        pass
    
    def generate_summary(self, batch_results: List[Dict[str, Any]], 
                        input_dir: str, 
                        output_dir: str) -> Dict[str, Any]:
        """
        生成批量审核汇总统计
        
        Args:
            batch_results: 批量评分结果列表
            input_dir: 输入目录路径
            output_dir: 输出目录路径
            
        Returns:
            汇总统计数据
        """
        input_path = Path(input_dir)
        
        # 基本统计
        total_files = len(batch_results)
        successful = [r for r in batch_results if r.get('success', False)]
        failed = [r for r in batch_results if not r.get('success', False)]
        
        # 计算总体统计
        overall_stats = self._calculate_overall_stats(successful, failed)
        
        # 计算分层级统计（按子目录）
        subdirectory_stats = self._calculate_subdirectory_stats(
            batch_results, input_path
        )
        
        # 评分分布统计
        score_distribution = self._calculate_score_distribution(successful)
        
        # 等级分布统计
        grade_distribution = self._calculate_grade_distribution(successful)
        
        # 耗时分析
        timing_analysis = self._calculate_timing_analysis(successful)
        
        # 失败原因分类
        failure_analysis = self._analyze_failures(failed)
        
        # 构建完整汇总
        summary = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'input_directory': str(input_path),
                'output_directory': str(output_dir),
                'total_files': total_files,
                'successful_count': len(successful),
                'failed_count': len(failed)
            },
            'overall_stats': overall_stats,
            'subdirectory_stats': subdirectory_stats,
            'score_distribution': score_distribution,
            'grade_distribution': grade_distribution,
            'timing_analysis': timing_analysis,
            'failure_analysis': failure_analysis,
            'detailed_results': batch_results
        }
        
        return summary
    
    def _calculate_overall_stats(self, successful: List[Dict], 
                                 failed: List[Dict]) -> Dict[str, Any]:
        """计算总体统计信息"""
        total = len(successful) + len(failed)
        success_rate = len(successful) / total if total > 0 else 0
        
        if not successful:
            return {
                'total_files': total,
                'successful': 0,
                'failed': len(failed),
                'success_rate': 0.0,
                'average_score': 0.0,
                'min_score': 0.0,
                'max_score': 0.0
            }
        
        # 提取分数
        scores = []
        for result in successful:
            score_data = result.get('result', {})
            summary = score_data.get('summary', {})
            total_score = summary.get('total_score', 0)
            scores.append(total_score)
        
        return {
            'total_files': total,
            'successful': len(successful),
            'failed': len(failed),
            'success_rate': success_rate,
            'average_score': sum(scores) / len(scores) if scores else 0.0,
            'min_score': min(scores) if scores else 0.0,
            'max_score': max(scores) if scores else 0.0,
            'median_score': sorted(scores)[len(scores) // 2] if scores else 0.0
        }
    
    def _calculate_subdirectory_stats(self, batch_results: List[Dict], 
                                     input_path: Path) -> Dict[str, Dict[str, Any]]:
        """计算每个子目录的统计信息"""
        subdirectory_results = defaultdict(list)
        
        # 按子目录分组
        for result in batch_results:
            file_path = Path(result.get('file_path', ''))
            
            # 计算相对于输入目录的路径
            try:
                rel_path = file_path.relative_to(input_path)
                # 获取第一级子目录名称
                if len(rel_path.parts) > 1:
                    subdir = rel_path.parts[0]
                else:
                    subdir = "根目录"
            except ValueError:
                # 如果不在input_path下，归类为"其他"
                subdir = "其他"
            
            subdirectory_results[subdir].append(result)
        
        # 为每个子目录计算统计
        stats = {}
        for subdir, results in subdirectory_results.items():
            successful = [r for r in results if r.get('success', False)]
            failed = [r for r in results if not r.get('success', False)]
            
            scores = []
            for result in successful:
                score_data = result.get('result', {})
                summary = score_data.get('summary', {})
                total_score = summary.get('total_score', 0)
                scores.append(total_score)
            
            stats[subdir] = {
                'total_files': len(results),
                'successful': len(successful),
                'failed': len(failed),
                'success_rate': len(successful) / len(results) if results else 0.0,
                'average_score': sum(scores) / len(scores) if scores else 0.0,
                'min_score': min(scores) if scores else 0.0,
                'max_score': max(scores) if scores else 0.0
            }
        
        return dict(stats)
    
    def _calculate_score_distribution(self, successful: List[Dict]) -> Dict[str, int]:
        """计算分数段分布"""
        distribution = {
            '90-100': 0,
            '80-89': 0,
            '70-79': 0,
            '60-69': 0,
            '0-59': 0
        }
        
        for result in successful:
            score_data = result.get('result', {})
            summary = score_data.get('summary', {})
            total_score = summary.get('total_score', 0)
            
            if total_score >= 90:
                distribution['90-100'] += 1
            elif total_score >= 80:
                distribution['80-89'] += 1
            elif total_score >= 70:
                distribution['70-79'] += 1
            elif total_score >= 60:
                distribution['60-69'] += 1
            else:
                distribution['0-59'] += 1
        
        return distribution
    
    def _calculate_grade_distribution(self, successful: List[Dict]) -> Dict[str, int]:
        """计算等级分布"""
        distribution = defaultdict(int)
        
        for result in successful:
            score_data = result.get('result', {})
            summary = score_data.get('summary', {})
            grade = summary.get('grade', '未知')
            distribution[grade] += 1
        
        return dict(distribution)
    
    def _calculate_timing_analysis(self, successful: List[Dict]) -> Dict[str, Any]:
        """计算耗时分析"""
        processing_times = []
        
        for result in successful:
            score_data = result.get('result', {})
            processing_time = score_data.get('processing_time', 0)
            if processing_time > 0:
                processing_times.append(processing_time)
        
        if not processing_times:
            return {
                'total_time': 0.0,
                'average_time': 0.0,
                'min_time': 0.0,
                'max_time': 0.0,
                'fast_count': 0,
                'normal_count': 0,
                'slow_count': 0
            }
        
        fast_count = len([t for t in processing_times if t <= 30])
        normal_count = len([t for t in processing_times if 30 < t <= 60])
        slow_count = len([t for t in processing_times if t > 60])
        
        return {
            'total_time': sum(processing_times),
            'average_time': sum(processing_times) / len(processing_times),
            'min_time': min(processing_times),
            'max_time': max(processing_times),
            'fast_count': fast_count,
            'normal_count': normal_count,
            'slow_count': slow_count
        }
    
    def _analyze_failures(self, failed: List[Dict]) -> Dict[str, Any]:
        """分析失败原因"""
        if not failed:
            return {
                'total_failures': 0,
                'error_types': {},
                'failed_files': []
            }
        
        error_types = defaultdict(int)
        failed_files = []
        
        for result in failed:
            error = result.get('error', '未知错误')
            file_path = result.get('file_path', '')
            
            # 简化错误类型
            if 'FileNotFoundError' in error or '不存在' in error:
                error_type = '文件不存在'
            elif 'parsing' in error.lower() or '解析' in error:
                error_type = '文档解析失败'
            elif 'timeout' in error.lower() or '超时' in error:
                error_type = '处理超时'
            elif 'connection' in error.lower() or '连接' in error:
                error_type = '服务连接失败'
            else:
                error_type = '其他错误'
            
            error_types[error_type] += 1
            failed_files.append({
                'file_path': file_path,
                'error_type': error_type,
                'error_message': error
            })
        
        return {
            'total_failures': len(failed),
            'error_types': dict(error_types),
            'failed_files': failed_files
        }
    
    def save_json_report(self, summary: Dict[str, Any], 
                        output_path: str) -> str:
        """
        保存JSON格式的汇总报告
        
        Args:
            summary: 汇总统计数据
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(summary, f, indent=2, ensure_ascii=False)
        
        logger.info(f"✅ JSON汇总报告已保存: {output_file}")
        return str(output_file)
    
    def save_text_report(self, summary: Dict[str, Any], 
                        output_path: str) -> str:
        """
        保存文本格式的汇总报告
        
        Args:
            summary: 汇总统计数据
            output_path: 输出文件路径
            
        Returns:
            输出文件路径
        """
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)
        
        lines = []
        lines.append("=" * 80)
        lines.append("批量审核汇总报告")
        lines.append("=" * 80)
        lines.append("")
        
        # 元数据
        metadata = summary['metadata']
        lines.append(f"生成时间: {metadata['generated_at']}")
        lines.append(f"输入目录: {metadata['input_directory']}")
        lines.append(f"输出目录: {metadata['output_directory']}")
        lines.append("")
        
        # 总体统计
        overall = summary['overall_stats']
        lines.append("【总体统计】")
        lines.append(f"  总文件数: {overall['total_files']}")
        lines.append(f"  成功处理: {overall['successful']}")
        lines.append(f"  处理失败: {overall['failed']}")
        lines.append(f"  成功率: {overall['success_rate']:.1%}")
        lines.append(f"  平均分数: {overall['average_score']:.2f}")
        lines.append(f"  最高分数: {overall['max_score']:.2f}")
        lines.append(f"  最低分数: {overall['min_score']:.2f}")
        lines.append("")
        
        # 子目录统计
        if summary['subdirectory_stats']:
            lines.append("【子目录统计】")
            for subdir, stats in summary['subdirectory_stats'].items():
                lines.append(f"  {subdir}:")
                lines.append(f"    文件数: {stats['total_files']}, "
                           f"成功: {stats['successful']}, "
                           f"失败: {stats['failed']}")
                lines.append(f"    平均分: {stats['average_score']:.2f}, "
                           f"成功率: {stats['success_rate']:.1%}")
            lines.append("")
        
        # 分数分布
        lines.append("【分数段分布】")
        score_dist = summary['score_distribution']
        for range_str, count in score_dist.items():
            lines.append(f"  {range_str}分: {count} 个")
        lines.append("")
        
        # 等级分布
        lines.append("【等级分布】")
        grade_dist = summary['grade_distribution']
        for grade, count in grade_dist.items():
            lines.append(f"  {grade}: {count} 个")
        lines.append("")
        
        # 耗时分析
        timing = summary['timing_analysis']
        lines.append("【处理耗时分析】")
        lines.append(f"  总耗时: {timing['total_time']:.2f} 秒")
        lines.append(f"  平均耗时: {timing['average_time']:.2f} 秒")
        lines.append(f"  最快: {timing['min_time']:.2f} 秒")
        lines.append(f"  最慢: {timing['max_time']:.2f} 秒")
        lines.append(f"  快速处理 (<=30秒): {timing['fast_count']} 个")
        lines.append(f"  正常处理 (30-60秒): {timing['normal_count']} 个")
        lines.append(f"  慢速处理 (>60秒): {timing['slow_count']} 个")
        lines.append("")
        
        # 失败分析
        if summary['failure_analysis']['total_failures'] > 0:
            failure = summary['failure_analysis']
            lines.append("【失败分析】")
            lines.append(f"  失败总数: {failure['total_failures']}")
            lines.append("  失败类型:")
            for error_type, count in failure['error_types'].items():
                lines.append(f"    {error_type}: {count} 个")
            lines.append("")
        
        lines.append("=" * 80)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))
        
        logger.info(f"✅ 文本汇总报告已保存: {output_file}")
        return str(output_file)

