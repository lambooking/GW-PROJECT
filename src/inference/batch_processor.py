"""
批量处理器
"""

import os
import asyncio
import concurrent.futures
from pathlib import Path
from typing import List, Dict, Any, Callable, Optional
import logging
from datetime import datetime
import json

from .audit_engine import AuditEngine
from .report_generator import ReportGenerator
from ..common.utils import ensure_dir, format_file_size, get_file_size

logger = logging.getLogger(__name__)


class BatchProcessor:
    """批量文档处理器"""
    
    def __init__(self, config_path: str = "config/config.yaml", max_workers: int = 4):
        self.audit_engine = AuditEngine(config_path)
        self.report_generator = ReportGenerator()
        self.max_workers = max_workers
        
    def process_directory(
        self, 
        input_dir: str, 
        output_dir: str = "output/batch_results",
        file_pattern: str = "*.{docx,pdf,doc}",
        document_type: str = "auto"
    ) -> Dict[str, Any]:
        """
        处理目录中的所有文档
        
        Args:
            input_dir: 输入目录路径
            output_dir: 输出目录路径
            file_pattern: 文件匹配模式
            document_type: 文档类型 ('auto', 'instruction_book', 'risk_management')
            
        Returns:
            处理结果汇总
        """
        input_path = Path(input_dir)
        if not input_path.exists():
            raise FileNotFoundError(f"输入目录不存在: {input_dir}")
        
        # 查找所有支持的文档文件
        file_paths = self._find_document_files(input_path, file_pattern)
        
        if not file_paths:
            logger.warning(f"在目录 {input_dir} 中未找到支持的文档文件")
            return {
                'total_files': 0,
                'processed_files': 0,
                'results': [],
                'summary': {}
            }
        
        logger.info(f"找到 {len(file_paths)} 个文档文件，开始批量处理")
        
        # 批量处理
        results = self.process_files(file_paths, document_type)
        
        # 生成报告
        ensure_dir(output_dir)
        report_path = self._generate_batch_report(results, output_dir)
        
        # 保存详细结果
        results_file = Path(output_dir) / f"batch_results_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        self._save_results_json(results, results_file)
        
        # 计算汇总信息
        summary = self.audit_engine.get_audit_statistics(results)
        
        batch_result = {
            'input_directory': str(input_path),
            'output_directory': output_dir,
            'total_files': len(file_paths),
            'processed_files': len(results),
            'results': results,
            'summary': summary,
            'report_path': report_path,
            'results_file': str(results_file),
            'processing_time': sum(r.get('processing_time', 0) for r in results)
        }
        
        logger.info(f"批量处理完成，共处理 {len(results)} 个文件")
        return batch_result
    
    def process_files(
        self, 
        file_paths: List[str], 
        document_type: str = "auto",
        progress_callback: Optional[Callable[[int, int], None]] = None
    ) -> List[Dict[str, Any]]:
        """
        处理文件列表
        
        Args:
            file_paths: 文件路径列表
            document_type: 文档类型
            progress_callback: 进度回调函数
            
        Returns:
            处理结果列表
        """
        results = []
        
        # 如果使用多线程处理
        if self.max_workers > 1 and len(file_paths) > 1:
            results = self._process_files_parallel(file_paths, document_type, progress_callback)
        else:
            results = self._process_files_sequential(file_paths, document_type, progress_callback)
        
        return results
    
    def _process_files_sequential(
        self, 
        file_paths: List[str], 
        document_type: str,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Dict[str, Any]]:
        """顺序处理文件"""
        results = []
        
        for i, file_path in enumerate(file_paths):
            try:
                logger.info(f"处理文件 ({i+1}/{len(file_paths)}): {file_path}")
                
                # 检测文档类型
                if document_type == 'auto':
                    detected_type = self.audit_engine._detect_document_type(file_path)
                else:
                    detected_type = document_type
                
                # 进行审核
                if detected_type == 'instruction_book':
                    result = self.audit_engine.audit_instruction_book(file_path)
                elif detected_type == 'risk_management':
                    result = self.audit_engine.audit_risk_management(file_path)
                else:
                    result = {
                        'overall_score': 0.0,
                        'error': f"未知文档类型: {detected_type}",
                        'file_path': file_path,
                        'document_type': detected_type
                    }
                
                results.append(result)
                
                # 调用进度回调
                if progress_callback:
                    progress_callback(i + 1, len(file_paths))
                    
            except Exception as e:
                logger.error(f"处理文件 {file_path} 时出错: {e}")
                results.append({
                    'overall_score': 0.0,
                    'error': str(e),
                    'file_path': file_path,
                    'document_type': 'unknown'
                })
        
        return results
    
    def _process_files_parallel(
        self, 
        file_paths: List[str], 
        document_type: str,
        progress_callback: Optional[Callable[[int, int], None]]
    ) -> List[Dict[str, Any]]:
        """并行处理文件"""
        results = []
        completed_count = 0
        
        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 提交所有任务
            future_to_path = {}
            for file_path in file_paths:
                future = executor.submit(self._process_single_file, file_path, document_type)
                future_to_path[future] = file_path
            
            # 收集结果
            for future in concurrent.futures.as_completed(future_to_path):
                file_path = future_to_path[future]
                try:
                    result = future.result()
                    results.append(result)
                    completed_count += 1
                    
                    logger.info(f"完成处理 ({completed_count}/{len(file_paths)}): {file_path}")
                    
                    # 调用进度回调
                    if progress_callback:
                        progress_callback(completed_count, len(file_paths))
                        
                except Exception as e:
                    logger.error(f"处理文件 {file_path} 时出错: {e}")
                    results.append({
                        'overall_score': 0.0,
                        'error': str(e),
                        'file_path': file_path,
                        'document_type': 'unknown'
                    })
                    completed_count += 1
        
        # 按原始顺序排序结果
        path_to_result = {r['file_path']: r for r in results}
        ordered_results = [path_to_result[path] for path in file_paths if path in path_to_result]
        
        return ordered_results
    
    def _process_single_file(self, file_path: str, document_type: str) -> Dict[str, Any]:
        """处理单个文件"""
        try:
            # 检测文档类型
            if document_type == 'auto':
                detected_type = self.audit_engine._detect_document_type(file_path)
            else:
                detected_type = document_type
            
            # 进行审核
            if detected_type == 'instruction_book':
                return self.audit_engine.audit_instruction_book(file_path)
            elif detected_type == 'risk_management':
                return self.audit_engine.audit_risk_management(file_path)
            else:
                return {
                    'overall_score': 0.0,
                    'error': f"未知文档类型: {detected_type}",
                    'file_path': file_path,
                    'document_type': detected_type
                }
                
        except Exception as e:
            return {
                'overall_score': 0.0,
                'error': str(e),
                'file_path': file_path,
                'document_type': 'unknown'
            }
    
    def _find_document_files(self, directory: Path, pattern: str) -> List[str]:
        """查找目录中的文档文件"""
        supported_extensions = ['.docx', '.pdf', '.doc']
        file_paths = []
        
        for file_path in directory.rglob('*'):
            if file_path.is_file() and file_path.suffix.lower() in supported_extensions:
                file_paths.append(str(file_path))
        
        return sorted(file_paths)
    
    def _generate_batch_report(self, results: List[Dict[str, Any]], output_dir: str) -> str:
        """生成批量处理报告"""
        try:
            report_path = self.report_generator.generate_batch_report(results, output_dir)
            return report_path
        except Exception as e:
            logger.error(f"生成批量报告失败: {e}")
            return ""
    
    def _save_results_json(self, results: List[Dict[str, Any]], output_file: Path):
        """保存结果为JSON文件"""
        try:
            # 准备JSON序列化的数据
            json_data = {
                'generated_at': datetime.now().isoformat(),
                'total_results': len(results),
                'results': results
            }
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(json_data, f, ensure_ascii=False, indent=2)
            
            logger.info(f"详细结果已保存到: {output_file}")
            
        except Exception as e:
            logger.error(f"保存JSON结果失败: {e}")
    
    def generate_summary_report(self, results: List[Dict[str, Any]], output_path: str = None) -> str:
        """生成汇总报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = f"output/reports/summary_report_{timestamp}.txt"
        
        ensure_dir(Path(output_path).parent)
        
        # 计算统计信息
        stats = self.audit_engine.get_audit_statistics(results)
        
        # 生成报告内容
        report_lines = [
            "=" * 50,
            "批量审核汇总报告",
            "=" * 50,
            f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "基本统计:",
            f"  总文件数: {stats.get('total_files', 0)}",
            f"  成功审核: {stats.get('successful_audits', 0)}",
            f"  失败审核: {stats.get('failed_audits', 0)}",
            f"  成功率: {stats.get('success_rate', 0):.1%}",
            "",
            "分数统计:",
            f"  平均分数: {stats.get('average_score', 0):.2f}",
            f"  优秀 (>=90分): {stats.get('score_distribution', {}).get('excellent', 0)} 个",
            f"  良好 (80-90分): {stats.get('score_distribution', {}).get('good', 0)} 个",
            f"  合格 (70-80分): {stats.get('score_distribution', {}).get('fair', 0)} 个",
            f"  不合格 (<70分): {stats.get('score_distribution', {}).get('poor', 0)} 个",
            "",
            "文档类型:",
            f"  作业指导书: {stats.get('document_types', {}).get('instruction_books', 0)} 个",
            f"  风险管控方案: {stats.get('document_types', {}).get('risk_managements', 0)} 个",
            "",
            "处理效率:",
            f"  平均处理时间: {stats.get('average_processing_time', 0):.2f} 秒",
            f"  快速处理 (<=30秒): {stats.get('efficiency_stats', {}).get('fast', 0)} 个",
            f"  正常处理 (30-60秒): {stats.get('efficiency_stats', {}).get('normal', 0)} 个",
            f"  慢速处理 (>60秒): {stats.get('efficiency_stats', {}).get('slow', 0)} 个",
            "",
            "=" * 50
        ]
        
        # 写入文件
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(report_lines))
        
        logger.info(f"汇总报告已生成: {output_path}")
        return output_path 