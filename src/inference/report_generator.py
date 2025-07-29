"""
审核报告生成器
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any
from jinja2 import Template
import pandas as pd

logger = logging.getLogger(__name__)


class ReportGenerator:
    """审核报告生成器"""
    
    def __init__(self):
        self.report_template = self._get_report_template()
        
    def generate_single_report(self, audit_results: Dict[str, Any], output_path: str = None) -> str:
        """生成单个文档的审核报告"""
        if output_path is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = Path(audit_results.get('file_path', 'document')).stem
            output_path = f"output/reports/{file_name}_audit_report_{timestamp}.html"
        
        # 准备报告数据
        report_data = self._prepare_report_data(audit_results)
        
        # 生成HTML报告
        html_content = self.report_template.render(**report_data)
        
        # 保存报告
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        logger.info(f"审核报告已生成: {output_path}")
        return output_path
    
    def generate_batch_report(self, batch_results: List[Dict[str, Any]], output_dir: str = None) -> str:
        """生成批量审核报告"""
        if output_dir is None:
            output_dir = "output/reports"
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = f"{output_dir}/batch_audit_report_{timestamp}.html"
        
        # 统计数据
        total_files = len(batch_results)
        avg_score = sum(result.get('overall_score', 0) for result in batch_results) / total_files if total_files > 0 else 0
        
        # 按文档类型分组统计
        instruction_books = [r for r in batch_results if r.get('document_type') == 'instruction_book']
        risk_management = [r for r in batch_results if r.get('document_type') == 'risk_management']
        
        batch_data = {
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'total_files': total_files,
            'average_score': avg_score,
            'instruction_books_count': len(instruction_books),
            'risk_management_count': len(risk_management),
            'instruction_books_avg': sum(r.get('overall_score', 0) for r in instruction_books) / len(instruction_books) if instruction_books else 0,
            'risk_management_avg': sum(r.get('overall_score', 0) for r in risk_management) / len(risk_management) if risk_management else 0,
            'detailed_results': [self._prepare_report_data(result) for result in batch_results]
        }
        
        # 生成批量报告模板
        batch_template = self._get_batch_report_template()
        html_content = batch_template.render(**batch_data)
        
        # 保存报告
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # 同时生成Excel统计表
        excel_path = output_path.replace('.html', '.xlsx')
        self._generate_excel_summary(batch_results, excel_path)
        
        logger.info(f"批量审核报告已生成: {output_path}")
        logger.info(f"Excel统计表已生成: {excel_path}")
        return output_path
    
    def _prepare_report_data(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """准备报告数据"""
        file_path = audit_results.get('file_path', '')
        document_type = audit_results.get('document_type', 'unknown')
        
        report_data = {
            'file_name': Path(file_path).name if file_path else 'Unknown',
            'file_path': file_path,
            'document_type': document_type,
            'document_type_name': '作业指导书' if document_type == 'instruction_book' else '高后果区风险管控方案' if document_type == 'risk_management' else '未知类型',
            'overall_score': audit_results.get('overall_score', 0),
            'processing_time': audit_results.get('processing_time', 0),
            'generation_time': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'has_error': 'error' in audit_results,
            'error_message': audit_results.get('error', ''),
            'score_level': self._get_score_level(audit_results.get('overall_score', 0)),
            'detailed_scores': {},
            'issues_found': audit_results.get('issues_found', []),
            'suggestions': audit_results.get('suggestions', [])
        }
        
        # 根据文档类型添加详细得分
        if document_type == 'instruction_book':
            report_data['detailed_scores'] = {
                '结构完整性': audit_results.get('structure_completeness', {}).get('score', 0),
                '内容完整性': audit_results.get('content_completeness', {}).get('score', 0),
                '语法错误': audit_results.get('grammar_errors', {}).get('score', 0),
                '引用可追溯性': audit_results.get('reference_traceability', {}).get('score', 0),
                '业务逻辑': audit_results.get('business_logic', {}).get('score', 0),
                '人员配备': audit_results.get('personnel_configuration', {}).get('score', 0),
                '应急处置': audit_results.get('emergency_procedures', {}).get('score', 0),
                '处理效率': audit_results.get('processing_efficiency', {}).get('score', 0)
            }
        elif document_type == 'risk_management':
            image_recognition = audit_results.get('image_recognition', {})
            context_logic = audit_results.get('context_logic', {})
            
            report_data['detailed_scores'] = {
                '图片识别能力': image_recognition.get('score', 0),
                '上下文逻辑': context_logic.get('score', 0),
                '处理效率': audit_results.get('processing_efficiency', {}).get('score', 0)
            }
            
            # 添加图片识别详细信息
            if image_recognition:
                report_data['image_recognition_details'] = {
                    '签名检测': image_recognition.get('signature_detection', {}),
                    '内容完整性': image_recognition.get('content_completeness', {}),
                    '标注识别': image_recognition.get('annotation_recognition', {})
                }
        
        return report_data
    
    def _get_score_level(self, score: float) -> str:
        """获取得分等级"""
        if score >= 0.9:
            return "优秀"
        elif score >= 0.8:
            return "良好"
        elif score >= 0.7:
            return "合格"
        elif score >= 0.6:
            return "待改进"
        else:
            return "不合格"
    
    def _generate_excel_summary(self, batch_results: List[Dict[str, Any]], output_path: str):
        """生成Excel统计表"""
        data = []
        
        for result in batch_results:
            row = {
                '文件名': Path(result.get('file_path', '')).name,
                '文档类型': '作业指导书' if result.get('document_type') == 'instruction_book' else '高后果区风险管控方案' if result.get('document_type') == 'risk_management' else '未知',
                '总分': result.get('overall_score', 0) * 100,  # 转换为百分制
                '等级': self._get_score_level(result.get('overall_score', 0)),
                '处理时间(秒)': result.get('processing_time', 0),
                '是否有错误': '是' if 'error' in result else '否',
                '错误信息': result.get('error', '')
            }
            
            # 添加详细得分
            if result.get('document_type') == 'instruction_book':
                row.update({
                    '结构完整性': result.get('structure_completeness', {}).get('score', 0) * 100,
                    '内容完整性': result.get('content_completeness', {}).get('score', 0) * 100,
                    '语法错误': result.get('grammar_errors', {}).get('score', 0) * 100,
                    '引用可追溯性': result.get('reference_traceability', {}).get('score', 0) * 100,
                    '业务逻辑': result.get('business_logic', {}).get('score', 0) * 100,
                    '人员配备': result.get('personnel_configuration', {}).get('score', 0) * 100,
                    '应急处置': result.get('emergency_procedures', {}).get('score', 0) * 100
                })
            elif result.get('document_type') == 'risk_management':
                row.update({
                    '图片识别能力': result.get('image_recognition', {}).get('score', 0) * 100,
                    '上下文逻辑': result.get('context_logic', {}).get('score', 0) * 100
                })
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # 保存到Excel
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
            df.to_excel(writer, sheet_name='审核结果汇总', index=False)
            
            # 添加统计sheet
            stats_data = {
                '统计项': ['总文件数', '平均得分', '作业指导书数量', '风险管控方案数量', '优秀文档数', '不合格文档数'],
                '数值': [
                    len(batch_results),
                    (sum(r.get('overall_score', 0) for r in batch_results) / len(batch_results) * 100) if batch_results else 0,
                    len([r for r in batch_results if r.get('document_type') == 'instruction_book']),
                    len([r for r in batch_results if r.get('document_type') == 'risk_management']),
                    len([r for r in batch_results if r.get('overall_score', 0) >= 0.9]),
                    len([r for r in batch_results if r.get('overall_score', 0) < 0.6])
                ]
            }
            stats_df = pd.DataFrame(stats_data)
            stats_df.to_excel(writer, sheet_name='统计信息', index=False)
    
    def _get_report_template(self) -> Template:
        """获取单个报告模板"""
        template_str = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ document_type_name }}审核报告</title>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .header h1 { margin: 0; font-size: 24px; }
        .score-box { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 10px; margin: 15px 0; text-align: center; }
        .score-box h2 { margin-top: 0; color: #2c3e50; }
        .score-display { font-size: 36px; font-weight: bold; color: #e74c3c; margin: 10px 0; }
        .error-box { background-color: #fee; border-left: 5px solid #e74c3c; padding: 15px; margin: 15px 0; border-radius: 5px; }
        .details-table { width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .details-table th, .details-table td { border: none; padding: 12px; text-align: left; }
        .details-table th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .details-table tr:nth-child(even) { background-color: #f8f9fa; }
        .details-table tr:hover { background-color: #e8f4fd; }
        .issues-list { background-color: #fff3cd; border-left: 5px solid #ffc107; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .suggestions-list { background-color: #d1ecf1; border-left: 5px solid #17a2b8; padding: 15px; border-radius: 5px; margin: 15px 0; }
        .score-bar { width: 100%; height: 20px; background-color: #e0e0e0; border-radius: 10px; overflow: hidden; margin: 5px 0; }
        .score-fill { height: 100%; border-radius: 10px; transition: width 0.3s ease; }
        .score-excellent { background: linear-gradient(90deg, #4CAF50, #8BC34A); }
        .score-good { background: linear-gradient(90deg, #2196F3, #03DAC6); }
        .score-fair { background: linear-gradient(90deg, #FF9800, #FFC107); }
        .score-poor { background: linear-gradient(90deg, #F44336, #E91E63); }
    </style>
</head>
<body>
    <div class="header">
        <h1>{{ document_type_name }}审核报告</h1>
        <p><strong>文件名：</strong>{{ file_name }}</p>
        <p><strong>生成时间：</strong>{{ generation_time }}</p>
        <p><strong>处理时间：</strong>{{ "%.2f"|format(processing_time) }} 秒</p>
    </div>

    {% if has_error %}
    <div class="error-box">
        <h3>❌ 错误信息</h3>
        <p>{{ error_message }}</p>
    </div>
    {% else %}
    <div class="score-box">
        <h2>📊 总体评分</h2>
        <div class="score-display">{{ "%.1f"|format(overall_score * 100) }}分</div>
        <p><strong>评级：{{ score_level }}</strong></p>
        <div class="score-bar">
            <div class="score-fill {% if overall_score >= 0.9 %}score-excellent{% elif overall_score >= 0.8 %}score-good{% elif overall_score >= 0.6 %}score-fair{% else %}score-poor{% endif %}" 
                 style="width: {{ (overall_score * 100)|round }}%"></div>
        </div>
    </div>

    <h3>📋 详细得分</h3>
    <table class="details-table">
        <thead>
            <tr>
                <th>评价项目</th>
                <th>得分</th>
                <th>得分率</th>
                <th>等级</th>
            </tr>
        </thead>
        <tbody>
            {% for item, score in detailed_scores.items() %}
            <tr>
                <td>{{ item }}</td>
                <td>{{ "%.1f"|format(score * 100) }}分</td>
                <td>
                    <div class="score-bar">
                        <div class="score-fill {% if score >= 0.9 %}score-excellent{% elif score >= 0.8 %}score-good{% elif score >= 0.6 %}score-fair{% else %}score-poor{% endif %}" 
                             style="width: {{ (score * 100)|round }}%"></div>
                    </div>
                </td>
                <td>{{ score|score_level }}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>

    {% if issues_found %}
    <div class="issues-list">
        <h3>⚠️ 发现的问题</h3>
        <ul>
            {% for issue in issues_found %}
            <li>{{ issue }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}

    {% if suggestions %}
    <div class="suggestions-list">
        <h3>💡 改进建议</h3>
        <ul>
            {% for suggestion in suggestions %}
            <li>{{ suggestion }}</li>
            {% endfor %}
        </ul>
    </div>
    {% endif %}
    {% endif %}
</body>
</html>
        """
        
        template = Template(template_str)
        
        # 添加自定义过滤器
        def score_level_filter(score):
            return self._get_score_level(score)
        
        template.environment.filters['score_level'] = score_level_filter
        
        return template
    
    def _get_batch_report_template(self) -> Template:
        """获取批量报告模板"""
        template_str = """
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>批量审核报告</title>
    <style>
        body { font-family: 'Microsoft YaHei', Arial, sans-serif; margin: 20px; line-height: 1.6; color: #333; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; }
        .summary-box { background: linear-gradient(135deg, #a8edea 0%, #fed6e3 100%); padding: 20px; border-radius: 10px; margin: 15px 0; }
        .stats-table { width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .stats-table th, .stats-table td { border: none; padding: 12px; text-align: center; }
        .stats-table th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .results-table { width: 100%; border-collapse: collapse; margin: 20px 0; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
        .results-table th, .results-table td { border: none; padding: 10px; text-align: left; }
        .results-table th { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; }
        .results-table tr:nth-child(even) { background-color: #f8f9fa; }
        .results-table tr:hover { background-color: #e8f4fd; }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 批量审核报告</h1>
        <p><strong>生成时间：</strong>{{ generation_time }}</p>
    </div>

    <div class="summary-box">
        <h2>📈 审核概况</h2>
        <table class="stats-table">
            <tr>
                <th>总文件数</th>
                <th>平均得分</th>
                <th>作业指导书</th>
                <th>风险管控方案</th>
            </tr>
            <tr>
                <td><strong>{{ total_files }}</strong></td>
                <td><strong>{{ "%.1f"|format(average_score * 100) }}分</strong></td>
                <td>{{ instruction_books_count }}个<br/>(平均{{ "%.1f"|format(instruction_books_avg * 100) }}分)</td>
                <td>{{ risk_management_count }}个<br/>(平均{{ "%.1f"|format(risk_management_avg * 100) }}分)</td>
            </tr>
        </table>
    </div>

    <h3>📋 详细结果</h3>
    <table class="results-table">
        <thead>
            <tr>
                <th>文件名</th>
                <th>类型</th>
                <th>总分</th>
                <th>等级</th>
                <th>处理时间</th>
                <th>状态</th>
            </tr>
        </thead>
        <tbody>
            {% for result in detailed_results %}
            <tr>
                <td>{{ result.file_name }}</td>
                <td>{{ result.document_type_name }}</td>
                <td>{{ "%.1f"|format(result.overall_score * 100) }}分</td>
                <td>{{ result.score_level }}</td>
                <td>{{ "%.2f"|format(result.processing_time) }}秒</td>
                <td>{% if result.has_error %}❌ 错误{% else %}✅ 成功{% endif %}</td>
            </tr>
            {% endfor %}
        </tbody>
    </table>
</body>
</html>
        """
        
        return Template(template_str) 