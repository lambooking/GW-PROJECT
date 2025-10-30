#!/usr/bin/env python3
"""
文档格式检查工具
检查目录中的文档文件是否为有效格式，识别损坏或格式错误的文件
"""
import sys
import zipfile
from pathlib import Path
from typing import List, Dict, Any
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(message)s'
)
logger = logging.getLogger(__name__)


class DocumentFormatChecker:
    """文档格式检查器"""
    
    SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.doc'}
    
    def __init__(self):
        """初始化检查器"""
        pass
    
    def check_docx_format(self, file_path: Path) -> Dict[str, Any]:
        """
        检查DOCX文件格式是否有效
        
        Args:
            file_path: DOCX文件路径
            
        Returns:
            检查结果字典
        """
        result = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'valid': False,
            'error': None,
            'file_size': 0,
            'suggestions': []
        }
        
        try:
            # 检查文件是否存在
            if not file_path.exists():
                result['error'] = '文件不存在'
                result['suggestions'].append('检查文件路径是否正确')
                return result
            
            # 获取文件大小
            result['file_size'] = file_path.stat().st_size
            
            if result['file_size'] == 0:
                result['error'] = '文件为空（0字节）'
                result['suggestions'].append('文件可能未正确下载或保存')
                return result
            
            # DOCX文件本质上是ZIP压缩包，尝试作为ZIP打开
            with zipfile.ZipFile(file_path, 'r') as zip_ref:
                # 检查是否包含DOCX必需的文件
                namelist = zip_ref.namelist()
                
                # DOCX必需包含的文件
                required_files = [
                    '[Content_Types].xml',
                    'word/document.xml'
                ]
                
                missing_files = []
                for req_file in required_files:
                    if req_file not in namelist:
                        missing_files.append(req_file)
                
                if missing_files:
                    result['error'] = f'DOCX结构不完整，缺少: {", ".join(missing_files)}'
                    result['suggestions'].append('用Microsoft Word打开并重新保存')
                    result['suggestions'].append('或使用其他工具转换为标准DOCX格式')
                    return result
                
                # 文件格式有效
                result['valid'] = True
                result['error'] = None
                
        except zipfile.BadZipFile:
            result['error'] = '不是有效的ZIP/DOCX格式'
            result['suggestions'].append('文件可能已损坏或不是真正的DOCX格式')
            result['suggestions'].append('尝试用Microsoft Word打开并另存为新文件')
            result['suggestions'].append('检查文件是否被错误重命名（如PDF改名为DOCX）')
            
        except Exception as e:
            result['error'] = f'检查失败: {str(e)}'
            result['suggestions'].append('文件可能被锁定或无读取权限')
        
        return result
    
    def check_pdf_format(self, file_path: Path) -> Dict[str, Any]:
        """
        检查PDF文件格式是否有效
        
        Args:
            file_path: PDF文件路径
            
        Returns:
            检查结果字典
        """
        result = {
            'file_path': str(file_path),
            'file_name': file_path.name,
            'valid': False,
            'error': None,
            'file_size': 0,
            'suggestions': []
        }
        
        try:
            if not file_path.exists():
                result['error'] = '文件不存在'
                return result
            
            result['file_size'] = file_path.stat().st_size
            
            if result['file_size'] == 0:
                result['error'] = '文件为空（0字节）'
                return result
            
            # 读取文件头，检查PDF magic number
            with open(file_path, 'rb') as f:
                header = f.read(8)
                if header.startswith(b'%PDF-'):
                    result['valid'] = True
                else:
                    result['error'] = '不是有效的PDF格式'
                    result['suggestions'].append('文件头不是PDF标识')
                    result['suggestions'].append('文件可能已损坏或被错误重命名')
                    
        except Exception as e:
            result['error'] = f'检查失败: {str(e)}'
        
        return result
    
    def check_directory(self, directory: str) -> Dict[str, Any]:
        """
        检查目录中所有文档文件的格式
        
        Args:
            directory: 目录路径
            
        Returns:
            检查结果汇总
        """
        dir_path = Path(directory)
        
        if not dir_path.exists():
            logger.error(f"❌ 目录不存在: {directory}")
            return {'error': '目录不存在'}
        
        logger.info(f"📁 正在扫描目录: {directory}")
        logger.info("="*80)
        
        # 收集所有文档文件
        all_files = []
        for ext in self.SUPPORTED_EXTENSIONS:
            all_files.extend(dir_path.rglob(f'*{ext}'))
        
        if not all_files:
            logger.warning("⚠️  未找到任何文档文件")
            return {'total': 0, 'valid': 0, 'invalid': 0, 'details': []}
        
        logger.info(f"找到 {len(all_files)} 个文档文件\n")
        
        # 检查每个文件
        valid_files = []
        invalid_files = []
        
        for i, file_path in enumerate(all_files, 1):
            logger.info(f"[{i}/{len(all_files)}] 检查: {file_path.relative_to(dir_path)}")
            
            # 根据文件类型选择检查方法
            if file_path.suffix.lower() == '.docx':
                result = self.check_docx_format(file_path)
            elif file_path.suffix.lower() == '.pdf':
                result = self.check_pdf_format(file_path)
            else:
                # .doc 文件暂时跳过详细检查
                result = {
                    'file_path': str(file_path),
                    'file_name': file_path.name,
                    'valid': True,
                    'error': None,
                    'file_size': file_path.stat().st_size,
                    'suggestions': ['DOC格式需要特殊工具解析']
                }
            
            if result['valid']:
                logger.info(f"  ✅ 有效 - {result['file_size']:,} 字节")
                valid_files.append(result)
            else:
                logger.error(f"  ❌ 无效 - {result['error']}")
                if result['suggestions']:
                    for suggestion in result['suggestions']:
                        logger.warning(f"     💡 {suggestion}")
                invalid_files.append(result)
            
            logger.info("")
        
        # 打印汇总
        logger.info("="*80)
        logger.info("📊 检查结果汇总")
        logger.info("="*80)
        logger.info(f"总文件数: {len(all_files)}")
        logger.info(f"有效文件: {len(valid_files)} ✅")
        logger.info(f"无效文件: {len(invalid_files)} ❌")
        logger.info(f"有效率: {len(valid_files)/len(all_files)*100:.1f}%")
        
        if invalid_files:
            logger.info("\n❌ 无效文件列表:")
            for result in invalid_files:
                rel_path = Path(result['file_path']).relative_to(dir_path)
                logger.error(f"  - {rel_path}")
                logger.error(f"    错误: {result['error']}")
        
        logger.info("\n" + "="*80)
        
        return {
            'total': len(all_files),
            'valid': len(valid_files),
            'invalid': len(invalid_files),
            'valid_files': valid_files,
            'invalid_files': invalid_files
        }


def main():
    """主函数"""
    if len(sys.argv) < 2:
        print("=" * 80)
        print("文档格式检查工具")
        print("=" * 80)
        print("\n用法:")
        print("  python scripts/check_document_format.py <目录路径>")
        print("\n示例:")
        print("  python scripts/check_document_format.py /path/to/documents")
        print("\n功能:")
        print("  - 递归扫描目录中的所有文档文件（PDF、DOCX、DOC）")
        print("  - 检查文件格式是否有效")
        print("  - 识别损坏或格式错误的文件")
        print("  - 提供修复建议")
        print("=" * 80)
        return
    
    directory = sys.argv[1]
    
    checker = DocumentFormatChecker()
    results = checker.check_directory(directory)
    
    # 如果有无效文件，返回非零退出码
    if results.get('invalid', 0) > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()

