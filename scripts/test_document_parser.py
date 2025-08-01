#!/usr/bin/env python3
"""
测试文档解析器功能
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.data_processing.document_parser import DocumentParser
import json
from pathlib import Path

def test_document_parsing():
    """测试文档解析功能"""
    parser = DocumentParser()
    
    # 测试文件路径
    test_files = [
        "data/raw/场景1(1).pdf",
        "data/raw/场景2(1).docx"
    ]
    
    for file_path in test_files:
        print(f"\n{'='*50}")
        print(f"正在处理文件: {file_path}")
        print(f"{'='*50}")
        
        try:
            # 解析文档
            result = parser.parse_document(file_path)
            
            print(f"文件类型: {result['file_type']}")
            print(f"总页数: {result['total_pages']}")
            print(f"提取的文本段落数: {len(result['text_content'])}")
            print(f"表格数量: {len(result['tables'])}")
            print(f"图片数量: {len(result['images'])}")
            
            # 显示文本内容
            print(f"\n--- 文本内容预览 ---")
            for i, text_item in enumerate(result['text_content'][:3]):  # 只显示前3个
                if result['file_type'] == 'docx':
                    print(f"段落 {i+1} ({text_item['type']}): {text_item['content'][:200]}...")
                else:  # PDF
                    print(f"页面 {text_item['page_number']}: {text_item['content'][:200]}...")
            
            # 显示表格信息
            if result['tables']:
                print(f"\n--- 表格信息 ---")
                for i, table in enumerate(result['tables']):
                    print(f"表格 {i+1}: {len(table['data'])} 行 x {len(table['data'][0]) if table['data'] else 0} 列")
                    if table['data']:
                        print(f"  表头: {table['data'][0]}")
            
            # 显示图片信息
            if result['images']:
                print(f"\n--- 图片信息 ---")
                for i, img in enumerate(result['images']):
                    print(f"图片 {i+1}: {img['filename']}, 大小: {len(img['data'])} 字节")
                    
                    # 尝试OCR识别第一张图片的文字
                    if i == 0:
                        print("正在对第一张图片进行OCR识别...")
                        ocr_text = parser.extract_text_from_image(img['data'])
                        print(f"OCR识别结果: {ocr_text[:200]}...")
            
            # 保存结果到JSON文件用于详细查看
            output_file = f"output/test_results_{Path(file_path).stem}.json"
            os.makedirs("output", exist_ok=True)
            
            # 创建可序列化的结果（移除二进制数据）
            serializable_result = result.copy()
            if 'images' in serializable_result:
                for img in serializable_result['images']:
                    img['data'] = f"<binary_data_{len(img['data'])}_bytes>"
            
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(serializable_result, f, ensure_ascii=False, indent=2)
            
            print(f"\n详细结果已保存到: {output_file}")
            
        except Exception as e:
            print(f"处理文件 {file_path} 时出错: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_document_parsing() 