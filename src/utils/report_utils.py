from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Dict, Optional

from src.utils.html_report_generator import HTMLReportGenerator


def save_scoring_report(
    scoring_result: Dict,
    file_stem: str,
    output_dir: str,
    timestamp: Optional[str] = None,
    separate_html_dir: bool = False,
) -> Dict[str, Optional[str]]:
    """保存评分结果为 JSON 和 HTML 文件。

    参数:
    - scoring_result: 评分结果字典
    - file_stem: 原始文件名的 stem（不含扩展名），用于生成报告文件名
    - output_dir: 输出目录（JSON 一定保存在此目录）
    - timestamp: 可选时间戳；默认使用当前时间
    - separate_html_dir: 是否将 HTML 保存到 output_dir/html 子目录

    返回:
    - dict: {"json_path": str, "html_path": Optional[str]}
    """

    # 生成时间戳与基础名称
    ts = timestamp or datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"rag_scoring_report_{file_stem}_{ts}"

    # 确保目录存在
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # 保存 JSON
    json_file = output_path / f"{base_name}.json"
    json_file.write_text(
        __serialize_json(scoring_result), encoding="utf-8"
    )

    # 生成 HTML
    html_path: Optional[Path] = None
    try:
        generator = HTMLReportGenerator()
        if separate_html_dir:
            html_dir = output_path / "html"
            html_dir.mkdir(parents=True, exist_ok=True)
            html_path = html_dir / f"{base_name}.html"
        else:
            html_path = output_path / f"{base_name}.html"

        generator.generate_html_report(scoring_result, str(html_path))
    except Exception:
        # HTML 生成失败不应中断主流程
        html_path = None

    return {
        "json_path": str(json_file),
        "html_path": str(html_path) if html_path else None,
    }


def __serialize_json(data: Dict) -> str:
    """以统一方式序列化 JSON，确保中文与日期可写入。"""
    import json

    return json.dumps(data, indent=2, ensure_ascii=False, default=str)


