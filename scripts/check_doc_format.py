#!/usr/bin/env python3
"""
检查 .doc 文件的真实格式

用法：
    python scripts/check_doc_format.py <文件路径>
"""

import sys
from pathlib import Path


def check_file_format(file_path: Path):
    """检查文件的真实格式"""
    
    if not file_path.exists():
        print(f"❌ 文件不存在: {file_path}")
        return
    
    print(f"📄 文件: {file_path.name}")
    print(f"📍 路径: {file_path.absolute()}")
    print(f"📏 大小: {file_path.stat().st_size:,} 字节")
    print(f"🏷️  后缀: {file_path.suffix}")
    print()
    
    # 读取文件头（魔数）
    with open(file_path, 'rb') as f:
        magic = f.read(8)
    
    print("🔍 文件头魔数（前8字节）:")
    print(f"   十六进制: {magic.hex()}")
    print(f"   前2字节: {magic[:2]}")
    print()
    
    # 判断文件类型
    print("📋 文件类型判断:")
    
    if magic[:2] == b'PK':
        print("   ✅ ZIP 格式（.docx、.xlsx、.pptx 等）")
        print("   ℹ️  这是一个 Office Open XML 格式文件")
        print("   ℹ️  如果后缀是 .doc，建议改为 .docx")
        is_docx = True
    elif magic[:4] == b'\xd0\xcf\x11\xe0':
        print("   ✅ OLE2/CFB 格式（旧版 .doc、.xls、.ppt）")
        print("   ℹ️  这是旧版 Microsoft Office 二进制格式")
        print("   ℹ️  可以使用 antiword 工具解析（仅文本）")
        is_docx = False
    elif magic[:6] == b'{\\rtf1':
        print("   ⚠️  RTF 格式（富文本格式）")
        print("   ℹ️  这不是真正的 Word 文档")
        print("   ℹ️  建议用 Word 打开并另存为 .docx")
        is_docx = False
    else:
        print("   ❓ 未知格式")
        print("   ℹ️  文件可能损坏或不是 Word 文档")
        print(f"   ℹ️  魔数: {magic[:4].hex()}")
        is_docx = False
    
    print()
    
    # 推荐的处理方式
    print("💡 推荐的处理方式:")
    if file_path.suffix.lower() == '.doc':
        if is_docx:
            print("   1. 将文件重命名为 .docx 后缀")
            print("   2. 或使用 python-docx 库直接解析")
        else:
            print("   1. 使用 Microsoft Word 或 WPS 打开")
            print("   2. 另存为 .docx 格式（推荐）")
            print("   3. 或使用 antiword 提取纯文本（无图片表格）")
    elif file_path.suffix.lower() == '.docx':
        if not is_docx:
            print("   ⚠️  文件后缀为 .docx 但实际不是 DOCX 格式")
            print("   建议用 Word 打开并另存为正确格式")
    
    print()


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("用法: python scripts/check_doc_format.py <文件路径>")
        print()
        print("示例:")
        print("  python scripts/check_doc_format.py data/raw/文档.doc")
        sys.exit(1)
    
    file_path = Path(sys.argv[1])
    check_file_format(file_path)

