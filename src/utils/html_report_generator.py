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