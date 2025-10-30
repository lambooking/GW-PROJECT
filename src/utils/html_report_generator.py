"""
HTML报告生成器
将JSON格式的评分报告转换为美观的HTML格式
"""
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List

logger = logging.getLogger(__name__)

class HTMLReportGenerator:
    """HTML评分报告生成器"""
    
    def __init__(self):
        self.template_dir = Path(__file__).parent / "templates"
        self.template_dir.mkdir(exist_ok=True)
        
    def generate_html_report(self, json_report: Dict[str, Any], output_path: str) -> str:
        """
        将JSON评分报告转换为HTML格式
        
        Args:
            json_report: JSON格式的评分报告
            output_path: 输出HTML文件路径
            
        Returns:
            生成的HTML文件路径
        """
        try:
            logger.info(f"正在生成HTML报告: {output_path}")
            
            # 生成HTML内容
            html_content = self._generate_html_content(json_report)
            
            # 写入文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ HTML报告已生成: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ HTML报告生成失败: {e}")
            raise
    
    def _generate_html_content(self, report: Dict[str, Any]) -> str:
        """生成完整的HTML内容"""
        
        # 基础信息
        doc_info = report.get("document_info", {})
        summary = report.get("summary", {})
        detailed_scores = report.get("detailed_scores", {})
        score_breakdown = report.get("score_breakdown", {})
        
        # 计算各项得分率
        score_percentages = {}
        for criterion_key, details in detailed_scores.items():
            percentage = (details.get("score", 0) / details.get("max_score", 1)) * 100
            score_percentages[criterion_key] = percentage
        
        # 生成HTML
        html_content = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RAG智能评分报告 - {doc_info.get('file_name', '未知文档')}</title>
    <style>
        {self._get_css_styles()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {self._generate_header(doc_info, summary)}
        {self._generate_summary_section(doc_info, summary, score_percentages)}
        {self._generate_detailed_scores(detailed_scores, score_breakdown)}
        {self._generate_signature_summary_card(detailed_scores)}
        {self._generate_score_visualization()}
        {self._generate_footer(report)}
    </div>
    
    <!-- 图片模态框 -->
    <div id="imageModal" class="modal">
        <span class="close" onclick="closeImageModal()">&times;</span>
        <div class="modal-content">
            <img id="modalImage" src="" alt="放大图片">
        </div>
    </div>
    
    <script>
        {self._generate_chart_script(detailed_scores)}
        {self._generate_image_modal_script()}
    </script>
</body>
</html>
"""
        return html_content
    
    def _get_css_styles(self) -> str:
        """获取CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background-color: #f5f7fa;
        }
        
        .container {
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 40px 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        
        .header h1 {
            font-size: 2.5em;
            margin-bottom: 10px;
            font-weight: 300;
        }
        
        .header .subtitle {
            font-size: 1.2em;
            opacity: 0.9;
        }
        
        .summary-section {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .summary-card {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            text-align: center;
        }
        
        .score-circle {
            width: 120px;
            height: 120px;
            border-radius: 50%;
            margin: 0 auto 20px;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 2em;
            font-weight: bold;
            color: white;
        }
        
        .grade-excellent { background: linear-gradient(45deg, #4CAF50, #45a049); }
        .grade-good { background: linear-gradient(45deg, #2196F3, #1976D2); }
        .grade-medium { background: linear-gradient(45deg, #FF9800, #F57C00); }
        .grade-pass { background: linear-gradient(45deg, #FFC107, #FFA000); }
        .grade-fail { background: linear-gradient(45deg, #F44336, #D32F2F); }
        
        .doc-info {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
        }
        
        .doc-info h3 {
            color: #667eea;
            margin-bottom: 15px;
            font-size: 1.3em;
        }
        
        .info-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 10px;
        }
        
        .info-item {
            padding: 10px;
            background: #f8f9fa;
            border-radius: 5px;
            border-left: 4px solid #667eea;
        }
        
        .detailed-scores {
            margin-top: 40px;
        }
        
        .section-title {
            font-size: 2em;
            color: #333;
            margin-bottom: 30px;
            text-align: center;
            position: relative;
        }
        
        .section-title::after {
            content: '';
            position: absolute;
            bottom: -10px;
            left: 50%;
            transform: translateX(-50%);
            width: 60px;
            height: 3px;
            background: linear-gradient(90deg, #667eea, #764ba2);
        }
        
        .score-item {
            background: white;
            margin-bottom: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            overflow: hidden;
        }
        
        .score-header {
            background: linear-gradient(90deg, #f8f9fa, #e9ecef);
            padding: 20px;
            border-bottom: 1px solid #dee2e6;
        }
        
        .score-title {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .score-title h3 {
            color: #495057;
            font-size: 1.4em;
        }
        
        .score-badge {
            background: #667eea;
            color: white;
            padding: 5px 15px;
            border-radius: 20px;
            font-weight: bold;
        }
        
        .score-progress {
            width: 100%;
            height: 8px;
            background: #e9ecef;
            border-radius: 4px;
            overflow: hidden;
        }
        
        .score-progress-bar {
            height: 100%;
            background: linear-gradient(90deg, #667eea, #764ba2);
            border-radius: 4px;
            transition: width 0.3s ease;
        }
        
        .score-content {
            padding: 20px;
        }
        
        .score-meta {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 20px;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 5px;
        }
        
        .meta-item {
            text-align: center;
        }
        
        .meta-label {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 5px;
        }
        
        .meta-value {
            font-weight: bold;
            color: #495057;
            font-size: 1.1em;
        }
        
        .reasoning {
            line-height: 1.8;
            color: #495057;
            background: #fff;
            padding: 20px;
            border-left: 4px solid #667eea;
            border-radius: 0 5px 5px 0;
        }
        
        .chart-section {
            background: white;
            padding: 30px;
            border-radius: 10px;
            box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            margin-top: 40px;
            text-align: center;
        }
        
        .chart-container {
            max-width: 600px;
            margin: 0 auto;
        }
        
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: #6c757d;
            border-top: 1px solid #dee2e6;
            margin-top: 50px;
        }
        
        .timestamp {
            font-size: 0.9em;
            color: #adb5bd;
        }
        
        .images-section {
            margin-top: 25px;
            padding-top: 20px;
            border-top: 1px solid #e9ecef;
        }
        
        .images-info {
            margin-bottom: 15px;
            font-size: 0.95em;
        }
        
        .images-info small {
            color: #6c757d;
            display: block;
            margin-top: 5px;
        }
        
        .images-gallery {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin-top: 10px;
        }
        
        .image-item {
            text-align: center;
            background: #f8f9fa;
            border-radius: 8px;
            padding: 10px;
            transition: transform 0.2s ease;
        }
        
        .image-item:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }
        
        .image-item img {
            max-width: 100%;
            max-height: 200px;
            object-fit: contain;
            border-radius: 4px;
            cursor: pointer;
            transition: opacity 0.2s ease;
        }
        
        .image-item img:hover {
            opacity: 0.8;
        }
        
        .image-caption {
            margin-top: 8px;
            font-size: 0.9em;
            color: #495057;
            font-weight: 500;
        }
        
        /* 模态框样式 */
        .modal {
            display: none;
            position: fixed;
            z-index: 1000;
            left: 0;
            top: 0;
            width: 100%;
            height: 100%;
            background-color: rgba(0, 0, 0, 0.9);
        }
        
        .modal-content {
            position: absolute;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            max-width: 90%;
            max-height: 90%;
        }
        
        .modal-content img {
            width: 100%;
            height: auto;
            border-radius: 8px;
        }
        
        .close {
            position: absolute;
            top: 15px;
            right: 35px;
            color: #f1f1f1;
            font-size: 40px;
            font-weight: bold;
            cursor: pointer;
        }
        
        .close:hover {
            color: #bbb;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 10px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .summary-section {
                grid-template-columns: 1fr;
            }
            
            .score-title {
                flex-direction: column;
                align-items: flex-start;
                gap: 10px;
            }
            
            .score-meta {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _generate_header(self, doc_info: Dict[str, Any], summary: Dict[str, Any]) -> str:
        """生成页面头部"""
        return f"""
        <header class="header">
            <h1>📊 RAG智能评分报告</h1>
            <div class="subtitle">基于检索增强生成的文档智能评估系统</div>
        </header>
        """
    
    def _generate_summary_section(self, doc_info: Dict[str, Any], summary: Dict[str, Any], percentages: Dict[str, float]) -> str:
        """生成摘要部分"""
        total_score = summary.get("total_score", 0)
        max_score = summary.get("max_total_score", 100)
        percentage = summary.get("percentage", 0)
        grade = summary.get("grade", "未知")
        
        # 根据等级选择样式
        grade_class = {
            "优秀": "grade-excellent",
            "良好": "grade-good", 
            "中等": "grade-medium",
            "及格": "grade-pass"
        }.get(grade, "grade-fail")
        
        return f"""
        <section class="summary-section">
            <div class="summary-card">
                <div class="score-circle {grade_class}">
                    {total_score}<br><small>/{max_score}</small>
                </div>
                <h3>总体评分</h3>
                <p style="font-size: 1.5em; color: #667eea; font-weight: bold;">{percentage:.1f}%</p>
                <p style="font-size: 1.2em; color: #495057; margin-top: 10px;">等级: {grade}</p>
            </div>
            
            <div class="doc-info">
                <h3>📄 文档信息</h3>
                <div class="info-grid">
                    <div class="info-item">
                        <strong>文件名:</strong><br>{doc_info.get('file_name', '未知')}
                    </div>
                    <div class="info-item">
                        <strong>场景类型:</strong><br>{doc_info.get('scene_name', '未知')}
                    </div>
                    <div class="info-item">
                        <strong>页数:</strong><br>{doc_info.get('total_pages', 0)} 页
                    </div>
                    <div class="info-item">
                        <strong>评分项:</strong><br>{summary.get('scoring_criteria_count', 0)} 个维度
                    </div>
                </div>
            </div>
        </section>
        """
    
    def _generate_detailed_scores(self, detailed_scores: Dict[str, Any], score_breakdown: Dict[str, Any]) -> str:
        """生成详细评分部分"""
        html = '<section class="detailed-scores">\n'
        html += '<h2 class="section-title">📋 详细评分</h2>\n'
        
        for criterion_key, details in detailed_scores.items():
            score = details.get("score", 0)
            max_score = details.get("max_score", 1)
            name = details.get("name", "未知")
            reasoning = details.get("reasoning", "无详细说明")
            evaluation_focus = details.get("evaluation_focus", "综合评估")
            
            # 计算进度条百分比
            progress_percentage = (score / max_score) * 100 if max_score > 0 else 0
            
            # 获取权重信息
            breakdown = score_breakdown.get(criterion_key, {})
            weight = breakdown.get("weight", 0) * 100
            weighted_score = breakdown.get("weighted_score", 0)
            
            html += f"""
            <div class="score-item">
                <div class="score-header">
                    <div class="score-title">
                        <h3>{name}</h3>
                        <span class="score-badge">{score}/{max_score}</span>
                    </div>
                    <div class="score-progress">
                        <div class="score-progress-bar" style="width: {progress_percentage:.1f}%"></div>
                    </div>
                </div>
                
                <div class="score-content">
                    <div class="score-meta">
                        <div class="meta-item">
                            <div class="meta-label">得分率</div>
                            <div class="meta-value">{progress_percentage:.1f}%</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">权重</div>
                            <div class="meta-value">{weight:.1f}%</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">加权分</div>
                            <div class="meta-value">{weighted_score:.1f}</div>
                        </div>
                        <div class="meta-item">
                            <div class="meta-label">评估重点</div>
                            <div class="meta-value" style="font-size: 0.9em;">{evaluation_focus}</div>
                        </div>
                    </div>
                    
                    <div class="reasoning">
                        <strong>💭 详细评分理由:</strong><br><br>
                        {self._format_reasoning(reasoning)}
                    </div>
                    
                    {self._generate_images_section(details)}
                </div>
            </div>
            """
        
        html += '</section>\n'
        return html

    def _generate_signature_summary_card(self, detailed_scores: Dict[str, Any]) -> str:
        """签字一致性摘要卡片（若存在签字评分项且包含 summary）。"""
        sig = detailed_scores.get("signature_completeness") or {}
        summary = sig.get("signature_summary")
        if not summary:
            return ""

        coverage = summary.get("coverage", 0)
        roles = summary.get("roles", {})
        date_ok = summary.get("date_order_ok")
        cons_ok = summary.get("consistency_ok")

        date_badge = "✅ 正常" if date_ok is True else ("⚠️ 无法判定" if date_ok is None else "❌ 异常")
        cons_badge = "✅ 通过" if cons_ok is True else ("⚠️ 无法判定" if cons_ok is None else "❌ 未通过")

        role_items = "".join([
            f"<li><strong>{r}</strong>：{info.get('name','未知')}，{info.get('date','无日期')}（置信度 {info.get('confidence',0):.2f}）</li>"
            for r, info in roles.items()
        ])

        return f"""
        <section class="summary-section">
            <div class="summary-card">
                <h3>🖋️ 签字与日期一致性摘要</h3>
                <p style="margin-top:10px">覆盖度：<strong>{coverage:.0%}</strong></p>
                <p>日期时序：{date_badge}；文本一致性：{cons_badge}</p>
                <ul style="text-align:left; margin-top:10px; line-height:1.8">{role_items}</ul>
            </div>
        </section>
        """
    
    def _format_reasoning(self, reasoning: str) -> str:
        """格式化评分理由文本"""
        # 简单的文本格式化
        formatted = reasoning.replace('\n', '<br>')
        
        # 高亮数字评分
        import re
        formatted = re.sub(r'(\d+分)', r'<strong style="color: #667eea;">\1</strong>', formatted)
        
        # 高亮百分比
        formatted = re.sub(r'(\d+\.?\d*%)', r'<strong style="color: #28a745;">\1</strong>', formatted)
        
        return formatted
    
    def _generate_images_section(self, details: Dict[str, Any]) -> str:
        """生成图片展示部分"""
        images_used = details.get("images_used", [])
        images_count = details.get("images_count", 0)
        total_images = details.get("total_images_in_document", 0)
        
        if not images_used:
            if total_images > 0:
                return f"""
                <div class="images-section">
                    <div class="images-info">
                        <strong>🖼️ 图像分析:</strong> 未找到相关图片<br>
                        <small>文档总图片数: {total_images} | 已使用: 0 | 建议补充相关图片以提高评分准确性</small>
                    </div>
                </div>
                """
            return ""
        
        html = f"""
        <div class="images-section">
            <div class="images-info">
                <strong>🖼️ 图像分析:</strong> 已分析 {images_count} 张相关图片<br>
                <small>文档总图片数: {total_images} | 已使用: {images_count} | 以下为发送给AI模型的图片</small>
            </div>
            <div class="images-gallery">
        """
        
        for i, base64_image in enumerate(images_used, 1):
            # 确保base64字符串格式正确
            if not base64_image.startswith('data:image/'):
                base64_image = f"data:image/jpeg;base64,{base64_image}"
            
            html += f"""
                <div class="image-item">
                    <img src="{base64_image}" alt="评分图片 {i}" onclick="showImageModal(this)">
                    <div class="image-caption">图片 {i}</div>
                </div>
            """
        
        html += """
            </div>
        </div>
        """
        
        return html
    
    def _generate_score_visualization(self) -> str:
        """生成评分可视化部分"""
        return """
        <section class="chart-section">
            <h2 class="section-title">📈 评分可视化</h2>
            <div class="chart-container">
                <canvas id="scoreChart" width="400" height="300"></canvas>
            </div>
        </section>
        """
    
    def _generate_chart_script(self, detailed_scores: Dict[str, Any]) -> str:
        """生成图表JavaScript代码"""
        # 准备图表数据
        labels = []
        scores = []
        max_scores = []
        
        for details in detailed_scores.values():
            labels.append(details.get("name", "未知"))
            scores.append(details.get("score", 0))
            max_scores.append(details.get("max_score", 1))
        
        return f"""
        // 创建雷达图
        const ctx = document.getElementById('scoreChart').getContext('2d');
        const scoreChart = new Chart(ctx, {{
            type: 'radar',
            data: {{
                labels: {labels},
                datasets: [{{
                    label: '实际得分',
                    data: {scores},
                    backgroundColor: 'rgba(102, 126, 234, 0.2)',
                    borderColor: 'rgba(102, 126, 234, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
                }}, {{
                    label: '满分',
                    data: {max_scores},
                    backgroundColor: 'rgba(108, 117, 125, 0.1)',
                    borderColor: 'rgba(108, 117, 125, 0.3)',
                    borderWidth: 1,
                    pointBackgroundColor: 'rgba(108, 117, 125, 0.3)',
                    pointBorderColor: '#fff'
                }}]
            }},
            options: {{
                responsive: true,
                maintainAspectRatio: false,
                scales: {{
                    r: {{
                        beginAtZero: true,
                        max: Math.max(...{max_scores}),
                        ticks: {{
                            stepSize: 5
                        }}
                    }}
                }},
                plugins: {{
                    legend: {{
                        position: 'bottom'
                    }},
                    title: {{
                        display: true,
                        text: '各维度评分对比'
                    }}
                }}
            }}
        }});
        """
    
    def _generate_image_modal_script(self) -> str:
        """生成图片模态框JavaScript代码"""
        return """
        function showImageModal(img) {
            const modal = document.getElementById('imageModal');
            const modalImg = document.getElementById('modalImage');
            modal.style.display = 'block';
            modalImg.src = img.src;
            modalImg.alt = img.alt;
        }
        
        function closeImageModal() {
            const modal = document.getElementById('imageModal');
            modal.style.display = 'none';
        }
        
        // 点击模态框背景关闭
        document.getElementById('imageModal').onclick = function(event) {
            if (event.target === this) {
                closeImageModal();
            }
        }
        
        // ESC键关闭模态框
        document.addEventListener('keydown', function(event) {
            if (event.key === 'Escape') {
                closeImageModal();
            }
        });
        """
    
    def _generate_footer(self, report: Dict[str, Any]) -> str:
        """生成页面底部"""
        timestamp = report.get("scoring_timestamp", datetime.now().isoformat())
        
        return f"""
        <footer class="footer">
            <div>
                <p><strong>🤖 RAG智能评分系统</strong></p>
                <p>基于检索增强生成技术的文档智能评估</p>
                <p class="timestamp">报告生成时间: {timestamp}</p>
            </div>
        </footer>
        """
    
    def batch_convert_reports(self, json_reports_dir: str, html_output_dir: str) -> List[str]:
        """
        批量转换JSON报告为HTML
        
        Args:
            json_reports_dir: JSON报告目录
            html_output_dir: HTML输出目录
            
        Returns:
            生成的HTML文件路径列表
        """
        json_dir = Path(json_reports_dir)
        html_dir = Path(html_output_dir)
        html_dir.mkdir(parents=True, exist_ok=True)
        
        generated_files = []
        
        for json_file in json_dir.glob("*.json"):
            if json_file.name.startswith("rag_scoring_report_"):
                try:
                    # 读取JSON报告
                    with open(json_file, 'r', encoding='utf-8') as f:
                        json_report = json.load(f)
                    
                    # 生成HTML文件路径
                    html_filename = json_file.stem + ".html"
                    html_path = html_dir / html_filename
                    
                    # 转换为HTML
                    generated_file = self.generate_html_report(json_report, str(html_path))
                    generated_files.append(generated_file)
                    
                except Exception as e:
                    logger.error(f"转换文件 {json_file} 失败: {e}")
        
        logger.info(f"批量转换完成，共生成 {len(generated_files)} 个HTML文件")
        return generated_files
    
    def generate_batch_summary_html(self, summary: Dict[str, Any], output_path: str) -> str:
        """
        生成批量汇总报告的HTML
        
        Args:
            summary: 批量汇总数据
            output_path: 输出HTML文件路径
            
        Returns:
            生成的HTML文件路径
        """
        try:
            logger.info(f"正在生成批量汇总HTML报告: {output_path}")
            
            # 生成HTML内容
            html_content = self._generate_batch_summary_html_content(summary)
            
            # 写入文件
            output_file = Path(output_path)
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            logger.info(f"✅ 批量汇总HTML报告已生成: {output_file}")
            return str(output_file)
            
        except Exception as e:
            logger.error(f"❌ 批量汇总HTML报告生成失败: {e}")
            raise
    
    def _generate_batch_summary_html_content(self, summary: Dict[str, Any]) -> str:
        """生成批量汇总HTML内容"""
        metadata = summary.get('metadata', {})
        overall = summary.get('overall_stats', {})
        subdirs = summary.get('subdirectory_stats', {})
        score_dist = summary.get('score_distribution', {})
        grade_dist = summary.get('grade_distribution', {})
        timing = summary.get('timing_analysis', {})
        failures = summary.get('failure_analysis', {})
        
        html = f"""
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>批量审核汇总报告</title>
    <style>
        {self._get_batch_summary_css()}
    </style>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <div class="container">
        {self._generate_batch_header(metadata)}
        {self._generate_batch_overall_stats(overall)}
        {self._generate_batch_subdirectory_stats(subdirs)}
        {self._generate_batch_distributions(score_dist, grade_dist)}
        {self._generate_batch_timing_analysis(timing)}
        {self._generate_batch_failure_analysis(failures)}
        {self._generate_batch_charts_section()}
        {self._generate_batch_footer(metadata)}
    </div>
    
    <script>
        {self._generate_batch_charts_script(overall, subdirs, score_dist, grade_dist)}
    </script>
</body>
</html>
"""
        return html
    
    def _get_batch_summary_css(self) -> str:
        """批量汇总报告的CSS样式"""
        return """
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Microsoft YaHei', 'PingFang SC', 'Helvetica Neue', Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
            min-height: 100vh;
        }
        
        .container {
            max-width: 1400px;
            margin: 0 auto;
            padding: 30px;
        }
        
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            text-align: center;
            padding: 50px 30px;
            border-radius: 15px;
            margin-bottom: 40px;
            box-shadow: 0 10px 30px rgba(0, 0, 0, 0.2);
        }
        
        .header h1 {
            font-size: 3em;
            margin-bottom: 15px;
            font-weight: 300;
            text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        .header .subtitle {
            font-size: 1.3em;
            opacity: 0.95;
        }
        
        .header .metadata {
            margin-top: 25px;
            padding-top: 25px;
            border-top: 1px solid rgba(255, 255, 255, 0.3);
            font-size: 1em;
        }
        
        .section {
            background: white;
            padding: 30px;
            border-radius: 12px;
            box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
            margin-bottom: 30px;
        }
        
        .section-title {
            font-size: 1.8em;
            color: #667eea;
            margin-bottom: 25px;
            padding-bottom: 15px;
            border-bottom: 3px solid #667eea;
            display: flex;
            align-items: center;
            gap: 15px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 20px;
        }
        
        .stat-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 25px;
            border-radius: 10px;
            text-align: center;
            border-left: 5px solid #667eea;
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        
        .stat-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 8px 20px rgba(102, 126, 234, 0.3);
        }
        
        .stat-label {
            font-size: 0.95em;
            color: #6c757d;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }
        
        .stat-value {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 5px;
        }
        
        .stat-subtext {
            font-size: 0.9em;
            color: #495057;
        }
        
        .success-rate {
            background: linear-gradient(135deg, #28a745 0%, #20c997 100%);
            color: white;
            border-left-color: #28a745;
        }
        
        .success-rate .stat-value {
            color: white;
        }
        
        .subdir-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .subdir-card {
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border-left: 4px solid #764ba2;
        }
        
        .subdir-name {
            font-size: 1.3em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 15px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        
        .subdir-stats {
            display: grid;
            grid-template-columns: repeat(2, 1fr);
            gap: 10px;
        }
        
        .subdir-stat {
            padding: 10px;
            background: white;
            border-radius: 5px;
            font-size: 0.9em;
        }
        
        .subdir-stat strong {
            color: #667eea;
            display: block;
            margin-bottom: 3px;
        }
        
        .distribution-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
            gap: 30px;
        }
        
        .distribution-item {
            background: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
            transition: background 0.2s ease;
        }
        
        .distribution-item:hover {
            background: #e9ecef;
        }
        
        .distribution-label {
            font-weight: 500;
            color: #495057;
        }
        
        .distribution-value {
            font-size: 1.5em;
            font-weight: bold;
            color: #667eea;
        }
        
        .timing-stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
        }
        
        .timing-item {
            text-align: center;
            padding: 20px;
            background: linear-gradient(135deg, #fff 0%, #f8f9fa 100%);
            border-radius: 8px;
            border: 2px solid #e9ecef;
        }
        
        .timing-label {
            font-size: 0.9em;
            color: #6c757d;
            margin-bottom: 8px;
        }
        
        .timing-value {
            font-size: 1.8em;
            font-weight: bold;
            color: #495057;
        }
        
        .failure-list {
            background: #fff3cd;
            border-left: 4px solid #ffc107;
            padding: 20px;
            border-radius: 5px;
            margin-top: 15px;
        }
        
        .failure-type {
            display: flex;
            justify-content: space-between;
            padding: 10px;
            background: white;
            margin: 5px 0;
            border-radius: 5px;
        }
        
        .chart-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(400px, 1fr));
            gap: 30px;
        }
        
        .chart-container {
            background: white;
            padding: 20px;
            border-radius: 10px;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }
        
        .chart-title {
            font-size: 1.2em;
            font-weight: bold;
            color: #495057;
            margin-bottom: 15px;
            text-align: center;
        }
        
        .footer {
            text-align: center;
            padding: 40px 20px;
            color: white;
            margin-top: 50px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            border-radius: 12px;
        }
        
        .footer p {
            margin: 5px 0;
        }
        
        @media (max-width: 768px) {
            .container {
                padding: 15px;
            }
            
            .header h1 {
                font-size: 2em;
            }
            
            .stats-grid,
            .subdir-grid,
            .distribution-grid,
            .chart-grid {
                grid-template-columns: 1fr;
            }
        }
        """
    
    def _generate_batch_header(self, metadata: Dict[str, Any]) -> str:
        """生成批量报告头部"""
        return f"""
        <header class="header">
            <h1>📊 批量审核汇总报告</h1>
            <div class="subtitle">RAG智能评分系统 - 批量文档评估总结</div>
            <div class="metadata">
                <div>📁 输入目录: {metadata.get('input_directory', '未知')}</div>
                <div>📁 输出目录: {metadata.get('output_directory', '未知')}</div>
                <div>🕐 生成时间: {metadata.get('generated_at', '未知')}</div>
            </div>
        </header>
        """
    
    def _generate_batch_overall_stats(self, overall: Dict[str, Any]) -> str:
        """生成总体统计部分"""
        success_rate = overall.get('success_rate', 0) * 100
        
        return f"""
        <section class="section">
            <h2 class="section-title">📈 总体统计</h2>
            <div class="stats-grid">
                <div class="stat-card">
                    <div class="stat-label">总文件数</div>
                    <div class="stat-value">{overall.get('total_files', 0)}</div>
                    <div class="stat-subtext">待评分文档</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">成功处理</div>
                    <div class="stat-value" style="color: #28a745;">{overall.get('successful', 0)}</div>
                    <div class="stat-subtext">✅ 评分完成</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">处理失败</div>
                    <div class="stat-value" style="color: #dc3545;">{overall.get('failed', 0)}</div>
                    <div class="stat-subtext">❌ 评分失败</div>
                </div>
                <div class="stat-card success-rate">
                    <div class="stat-label">成功率</div>
                    <div class="stat-value">{success_rate:.1f}%</div>
                    <div class="stat-subtext">处理成功比例</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">平均分数</div>
                    <div class="stat-value">{overall.get('average_score', 0):.1f}</div>
                    <div class="stat-subtext">所有文档平均分</div>
                </div>
                <div class="stat-card">
                    <div class="stat-label">最高分数</div>
                    <div class="stat-value" style="color: #ffc107;">{overall.get('max_score', 0):.1f}</div>
                    <div class="stat-subtext">单个文档最高分</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_batch_subdirectory_stats(self, subdirs: Dict[str, Dict[str, Any]]) -> str:
        """生成子目录统计部分"""
        if not subdirs:
            return ""
        
        html = """
        <section class="section">
            <h2 class="section-title">📂 子目录统计</h2>
            <div class="subdir-grid">
        """
        
        for subdir_name, stats in subdirs.items():
            success_rate = stats.get('success_rate', 0) * 100
            html += f"""
                <div class="subdir-card">
                    <div class="subdir-name">📁 {subdir_name}</div>
                    <div class="subdir-stats">
                        <div class="subdir-stat">
                            <strong>文件数</strong>
                            {stats.get('total_files', 0)}
                        </div>
                        <div class="subdir-stat">
                            <strong>成功数</strong>
                            {stats.get('successful', 0)}
                        </div>
                        <div class="subdir-stat">
                            <strong>平均分</strong>
                            {stats.get('average_score', 0):.2f}
                        </div>
                        <div class="subdir-stat">
                            <strong>成功率</strong>
                            {success_rate:.1f}%
                        </div>
                    </div>
                </div>
            """
        
        html += """
            </div>
        </section>
        """
        return html
    
    def _generate_batch_distributions(self, score_dist: Dict[str, int], 
                                     grade_dist: Dict[str, int]) -> str:
        """生成分布统计部分"""
        html = """
        <section class="section">
            <h2 class="section-title">📊 评分分布</h2>
            <div class="distribution-grid">
                <div>
                    <h3 style="margin-bottom: 15px; color: #495057;">分数段分布</h3>
        """
        
        for range_str, count in score_dist.items():
            html += f"""
                    <div class="distribution-item">
                        <span class="distribution-label">{range_str} 分</span>
                        <span class="distribution-value">{count}</span>
                    </div>
            """
        
        html += """
                </div>
                <div>
                    <h3 style="margin-bottom: 15px; color: #495057;">等级分布</h3>
        """
        
        for grade, count in grade_dist.items():
            html += f"""
                    <div class="distribution-item">
                        <span class="distribution-label">{grade}</span>
                        <span class="distribution-value">{count}</span>
                    </div>
            """
        
        html += """
                </div>
            </div>
        </section>
        """
        return html
    
    def _generate_batch_timing_analysis(self, timing: Dict[str, Any]) -> str:
        """生成耗时分析部分"""
        return f"""
        <section class="section">
            <h2 class="section-title">⏱️ 处理耗时分析</h2>
            <div class="timing-stats">
                <div class="timing-item">
                    <div class="timing-label">总耗时</div>
                    <div class="timing-value">{timing.get('total_time', 0):.1f}s</div>
                </div>
                <div class="timing-item">
                    <div class="timing-label">平均耗时</div>
                    <div class="timing-value">{timing.get('average_time', 0):.1f}s</div>
                </div>
                <div class="timing-item">
                    <div class="timing-label">最快</div>
                    <div class="timing-value">{timing.get('min_time', 0):.1f}s</div>
                </div>
                <div class="timing-item">
                    <div class="timing-label">最慢</div>
                    <div class="timing-value">{timing.get('max_time', 0):.1f}s</div>
                </div>
                <div class="timing-item">
                    <div class="timing-label">快速 (≤30s)</div>
                    <div class="timing-value">{timing.get('fast_count', 0)}</div>
                </div>
                <div class="timing-item">
                    <div class="timing-label">正常 (30-60s)</div>
                    <div class="timing-value">{timing.get('normal_count', 0)}</div>
                </div>
                <div class="timing-item">
                    <div class="timing-label">慢速 (>60s)</div>
                    <div class="timing-value">{timing.get('slow_count', 0)}</div>
                </div>
            </div>
        </section>
        """
    
    def _generate_batch_failure_analysis(self, failures: Dict[str, Any]) -> str:
        """生成失败分析部分"""
        if failures.get('total_failures', 0) == 0:
            return """
        <section class="section">
            <h2 class="section-title">✅ 处理结果</h2>
            <div style="text-align: center; padding: 40px; color: #28a745;">
                <h3>🎉 所有文档处理成功！</h3>
                <p style="margin-top: 15px;">没有失败的文档</p>
            </div>
        </section>
            """
        
        html = f"""
        <section class="section">
            <h2 class="section-title">⚠️ 失败分析</h2>
            <div class="failure-list">
                <h3 style="margin-bottom: 15px; color: #495057;">失败统计: {failures.get('total_failures', 0)} 个</h3>
        """
        
        for error_type, count in failures.get('error_types', {}).items():
            html += f"""
                <div class="failure-type">
                    <span>{error_type}</span>
                    <span style="font-weight: bold; color: #dc3545;">{count} 个</span>
                </div>
            """
        
        html += """
            </div>
        </section>
        """
        return html
    
    def _generate_batch_charts_section(self) -> str:
        """生成图表部分"""
        return """
        <section class="section">
            <h2 class="section-title">📈 可视化分析</h2>
            <div class="chart-grid">
                <div class="chart-container">
                    <div class="chart-title">子目录评分对比</div>
                    <canvas id="subdirChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">分数段分布</div>
                    <canvas id="scoreDistChart"></canvas>
                </div>
                <div class="chart-container">
                    <div class="chart-title">等级分布</div>
                    <canvas id="gradeDistChart"></canvas>
                </div>
            </div>
        </section>
        """
    
    def _generate_batch_charts_script(self, overall: Dict[str, Any],
                                      subdirs: Dict[str, Dict[str, Any]],
                                      score_dist: Dict[str, int],
                                      grade_dist: Dict[str, int]) -> str:
        """生成批量报告的图表脚本"""
        # 准备子目录数据
        subdir_labels = list(subdirs.keys())
        subdir_scores = [stats.get('average_score', 0) for stats in subdirs.values()]
        subdir_counts = [stats.get('total_files', 0) for stats in subdirs.values()]
        
        # 准备分数段数据
        score_labels = list(score_dist.keys())
        score_values = list(score_dist.values())
        
        # 准备等级数据
        grade_labels = list(grade_dist.keys())
        grade_values = list(grade_dist.values())
        
        return f"""
        // 子目录评分对比图
        if (document.getElementById('subdirChart')) {{
            const subdirCtx = document.getElementById('subdirChart').getContext('2d');
            new Chart(subdirCtx, {{
                type: 'bar',
                data: {{
                    labels: {subdir_labels},
                    datasets: [{{
                        label: '平均分数',
                        data: {subdir_scores},
                        backgroundColor: 'rgba(102, 126, 234, 0.8)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        borderWidth: 2
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    scales: {{
                        y: {{
                            beginAtZero: true,
                            max: 100
                        }}
                    }},
                    plugins: {{
                        legend: {{
                            display: false
                        }}
                    }}
                }}
            }});
        }}
        
        // 分数段分布图
        if (document.getElementById('scoreDistChart')) {{
            const scoreDistCtx = document.getElementById('scoreDistChart').getContext('2d');
            new Chart(scoreDistCtx, {{
                type: 'pie',
                data: {{
                    labels: {score_labels},
                    datasets: [{{
                        data: {score_values},
                        backgroundColor: [
                            'rgba(76, 175, 80, 0.8)',
                            'rgba(33, 150, 243, 0.8)',
                            'rgba(255, 152, 0, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(244, 67, 54, 0.8)'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}
        
        // 等级分布图
        if (document.getElementById('gradeDistChart')) {{
            const gradeDistCtx = document.getElementById('gradeDistChart').getContext('2d');
            new Chart(gradeDistCtx, {{
                type: 'doughnut',
                data: {{
                    labels: {grade_labels},
                    datasets: [{{
                        data: {grade_values},
                        backgroundColor: [
                            'rgba(76, 175, 80, 0.8)',
                            'rgba(33, 150, 243, 0.8)',
                            'rgba(255, 152, 0, 0.8)',
                            'rgba(255, 193, 7, 0.8)',
                            'rgba(244, 67, 54, 0.8)'
                        ],
                        borderWidth: 2,
                        borderColor: '#fff'
                    }}]
                }},
                options: {{
                    responsive: true,
                    maintainAspectRatio: true,
                    plugins: {{
                        legend: {{
                            position: 'bottom'
                        }}
                    }}
                }}
            }});
        }}
        """
    
    def _generate_batch_footer(self, metadata: Dict[str, Any]) -> str:
        """生成批量报告底部"""
        return f"""
        <footer class="footer">
            <p><strong>🤖 RAG智能评分系统 - 批量审核汇总</strong></p>
            <p>基于检索增强生成技术的批量文档智能评估</p>
            <p style="margin-top: 15px; opacity: 0.9;">报告生成时间: {metadata.get('generated_at', '未知')}</p>
        </footer>
        """