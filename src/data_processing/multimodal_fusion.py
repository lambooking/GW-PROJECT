"""
多模态内容融合模块 - 整合文本、表格、图片信息，建立跨模态关联
"""

from typing import Dict, List, Any, Optional, Tuple
import re
import logging
from collections import defaultdict
import numpy as np

logger = logging.getLogger(__name__)

class MultimodalFusion:
    """多模态内容融合器"""
    
    def __init__(self):
        # 图表类型识别关键词
        self.diagram_keywords = {
            'hca_image': ['高后果区影像图', '影像图', 'HCA影像'],
            'site_image': ['现场图', '现场照片', '实地图'],
            'entry_route': ['入场线路图', '入场路线', '进入路线'],
            'escape_route': ['逃生路线图', '疏散路线', '逃生线路'],
            'evacuation_point': ['疏散集合点', '集合点', '疏散点'],
            'emergency_supplies': ['应急物资', '物资存放点', '应急装备'],
            'pipeline_layout': ['管道布置图', '管线图', '管道走向'],
            'cross_section': ['断面图', '剖面图', '截面图']
        }
        
        # 表格类型识别关键词
        self.table_keywords = {
            'basic_info': ['基本信息', '基础信息', '概况'],
            'risk_assessment': ['风险评价', '风险评估', '风险分析'],
            'personnel_info': ['人员信息', '联系人', '负责人'],
            'technical_params': ['技术参数', '设计参数', '运行参数'],
            'test_results': ['测试结果', '检测数据', '监测数据'],
            'control_measures': ['管控措施', '控制措施', '防护措施'],
            'emergency_contacts': ['应急联系人', '紧急联系', '联系方式']
        }
    
    def fuse_multimodal_content(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        融合多模态内容
        
        Args:
            structured_data: 结构化提取的数据
            
        Returns:
            融合后的多模态数据
        """
        try:
            # 基础信息
            basic_info = structured_data.get('basic_info', {})
            classification = structured_data.get('classification', {})
            scenario = classification.get('scenario', 'unknown')
            
            # 分类和关联内容
            categorized_content = self._categorize_content(structured_data)
            
            # 建立跨模态关联
            cross_modal_links = self._establish_cross_modal_links(categorized_content)
            
            # 根据场景进行特定融合
            if scenario == 'scenario_one':
                scenario_fusion = self._fuse_scenario_one(categorized_content)
            elif scenario == 'scenario_two':
                scenario_fusion = self._fuse_scenario_two(categorized_content)
            else:
                scenario_fusion = {}
            
            # 构建融合结果
            fused_result = {
                'document_metadata': {
                    'scenario': scenario,
                    'scenario_name': classification.get('scenario_name'),
                    'confidence': classification.get('confidence'),
                    'basic_info': basic_info
                },
                'content_inventory': {
                    'text_sections': categorized_content.get('text_sections', {}),
                    'tables_by_type': categorized_content.get('tables_by_type', {}),
                    'images_by_type': categorized_content.get('images_by_type', {}),
                    'total_counts': {
                        'text_items': len(structured_data.get('text_content', [])),
                        'tables': len(structured_data.get('tables', [])),
                        'images': len(structured_data.get('images', []))
                    }
                },
                'cross_modal_links': cross_modal_links,
                'scenario_specific_fusion': scenario_fusion,
                'extracted_entities': self._extract_key_entities(structured_data),
                'quality_indicators': self._assess_content_quality(categorized_content)
            }
            
            return fused_result
            
        except Exception as e:
            logger.error(f"多模态融合失败: {e}")
            return {
                'error': str(e),
                'fusion_status': 'failed'
            }
    
    def _categorize_content(self, structured_data: Dict[str, Any]) -> Dict[str, Any]:
        """对内容进行分类和组织"""
        categorized = {
            'text_sections': defaultdict(list),
            'tables_by_type': defaultdict(list),
            'images_by_type': defaultdict(list)
        }
        
        # 分类文本内容
        text_content = structured_data.get('text_content', [])
        for item in text_content:
            content = item.get('content', '')
            section_type = self._classify_text_section(content)
            categorized['text_sections'][section_type].append(item)
        
        # 分类表格
        tables = structured_data.get('tables', [])
        for table in tables:
            table_type = self._classify_table(table)
            categorized['tables_by_type'][table_type].append(table)
        
        # 分类图片 (基于OCR结果)
        images = structured_data.get('images', [])
        for image in images:
            # 这里可以加入图像分类逻辑
            image_type = self._classify_image(image)
            categorized['images_by_type'][image_type].append(image)
        
        return categorized
    
    def _classify_text_section(self, content: str) -> str:
        """分类文本段落"""
        content_lower = content.lower()
        
        # 检查各种类型
        if any(keyword in content_lower for keyword in ['目录', '内容']):
            return 'table_of_contents'
        elif any(keyword in content_lower for keyword in ['范围', '适用范围']):
            return 'scope'
        elif any(keyword in content_lower for keyword in ['职责', '责任']):
            return 'responsibilities'
        elif any(keyword in content_lower for keyword in ['作业内容', '操作步骤', '作业流程']):
            return 'work_procedures'
        elif any(keyword in content_lower for keyword in ['应急', '紧急', '事故']):
            return 'emergency_procedures'
        elif any(keyword in content_lower for keyword in ['安全', '防护', '注意事项']):
            return 'safety_requirements'
        elif any(keyword in content_lower for keyword in ['培训', '教育', '学习']):
            return 'training'
        elif any(keyword in content_lower for keyword in ['风险评价', '风险评估', '风险分析']):
            return 'risk_assessment'
        elif any(keyword in content_lower for keyword in ['管控措施', '控制措施', '防护措施']):
            return 'control_measures'
        elif any(keyword in content_lower for keyword in ['高后果区', 'HCA']):
            return 'hca_description'
        elif any(keyword in content_lower for keyword in ['附录', '附件']):
            return 'appendix'
        else:
            return 'general_content'
    
    def _classify_table(self, table: Dict[str, Any]) -> str:
        """分类表格类型"""
        # 获取表格数据
        table_data = table.get('data', [])
        if not table_data:
            return 'unknown_table'
        
        # 将表格内容转为字符串进行分析
        table_text = ' '.join([' '.join(row) for row in table_data])
        table_text_lower = table_text.lower()
        
        # 检查表格类型关键词
        for table_type, keywords in self.table_keywords.items():
            if any(keyword in table_text_lower for keyword in keywords):
                return table_type
        
        # 基于表格结构判断
        if len(table_data) > 1 and len(table_data[0]) >= 2:
            header_row = ' '.join(table_data[0]).lower()
            
            if any(keyword in header_row for keyword in ['姓名', '联系', '电话']):
                return 'personnel_info'
            elif any(keyword in header_row for keyword in ['参数', '数值', '单位']):
                return 'technical_params'
            elif any(keyword in header_row for keyword in ['时间', '日期', '结果']):
                return 'test_results'
        
        return 'general_table'
    
    def _classify_image(self, image: Dict[str, Any]) -> str:
        """分类图片类型"""
        filename = image.get('filename', '').lower()
        
        # 基于文件名分类
        for img_type, keywords in self.diagram_keywords.items():
            if any(keyword in filename for keyword in keywords):
                return img_type
        
        # 基于图片在文档中的位置和大小进行粗略分类
        page_number = image.get('page_number', 1)
        width = image.get('width', 0)
        height = image.get('height', 0)
        
        # 大尺寸图片可能是重要的图表
        if width > 800 or height > 600:
            return 'large_diagram'
        elif width < 200 and height < 200:
            return 'small_icon_or_logo'
        else:
            return 'medium_diagram'
    
    def _establish_cross_modal_links(self, categorized_content: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """建立跨模态关联"""
        links = defaultdict(list)
        
        # 文本-表格关联
        text_sections = categorized_content.get('text_sections', {})
        tables_by_type = categorized_content.get('tables_by_type', {})
        
        for text_type, text_items in text_sections.items():
            for table_type, table_items in tables_by_type.items():
                similarity = self._calculate_semantic_similarity(text_type, table_type)
                if similarity > 0.7:  # 高相似度阈值
                    links['text_table_links'].append({
                        'text_type': text_type,
                        'table_type': table_type,
                        'similarity': similarity,
                        'text_count': len(text_items),
                        'table_count': len(table_items)
                    })
        
        # 文本-图片关联
        images_by_type = categorized_content.get('images_by_type', {})
        for text_type, text_items in text_sections.items():
            for image_type, image_items in images_by_type.items():
                similarity = self._calculate_semantic_similarity(text_type, image_type)
                if similarity > 0.6:  # 图片关联阈值稍低
                    links['text_image_links'].append({
                        'text_type': text_type,
                        'image_type': image_type,
                        'similarity': similarity,
                        'text_count': len(text_items),
                        'image_count': len(image_items)
                    })
        
        # 表格-图片关联
        for table_type, table_items in tables_by_type.items():
            for image_type, image_items in images_by_type.items():
                similarity = self._calculate_semantic_similarity(table_type, image_type)
                if similarity > 0.6:
                    links['table_image_links'].append({
                        'table_type': table_type,
                        'image_type': image_type,
                        'similarity': similarity,
                        'table_count': len(table_items),
                        'image_count': len(image_items)
                    })
        
        return dict(links)
    
    def _calculate_semantic_similarity(self, type1: str, type2: str) -> float:
        """计算语义相似度（简化版）"""
        # 定义相关性映射
        related_pairs = {
            ('risk_assessment', 'risk_assessment'): 1.0,
            ('personnel_info', 'personnel_info'): 1.0,
            ('technical_params', 'technical_params'): 1.0,
            ('hca_description', 'hca_image'): 0.9,
            ('emergency_procedures', 'escape_route'): 0.8,
            ('emergency_procedures', 'evacuation_point'): 0.8,
            ('safety_requirements', 'control_measures'): 0.7,
            ('work_procedures', 'technical_params'): 0.6,
        }
        
        # 检查直接匹配
        if (type1, type2) in related_pairs:
            return related_pairs[(type1, type2)]
        elif (type2, type1) in related_pairs:
            return related_pairs[(type2, type1)]
        
        # 基于关键词重叠计算相似度
        keywords1 = set(type1.split('_'))
        keywords2 = set(type2.split('_'))
        
        if keywords1 & keywords2:  # 有交集
            return len(keywords1 & keywords2) / len(keywords1 | keywords2)
        
        return 0.0
    
    def _fuse_scenario_one(self, categorized_content: Dict[str, Any]) -> Dict[str, Any]:
        """场景一特定融合逻辑（作业指导书）"""
        fusion_result = {
            'required_sections_status': {},
            'procedure_completeness': {},
            'safety_coverage': {}
        }
        
        text_sections = categorized_content.get('text_sections', {})
        
        # 检查必需章节
        required_sections = [
            'scope', 'responsibilities', 'work_procedures', 
            'emergency_procedures', 'safety_requirements', 'training'
        ]
        
        for section in required_sections:
            fusion_result['required_sections_status'][section] = {
                'present': section in text_sections,
                'content_count': len(text_sections.get(section, []))
            }
        
        # 检查程序完整性
        if 'work_procedures' in text_sections:
            procedures = text_sections['work_procedures']
            fusion_result['procedure_completeness'] = {
                'has_procedures': len(procedures) > 0,
                'procedure_count': len(procedures),
                'detailed_steps': self._analyze_procedure_details(procedures)
            }
        
        return fusion_result
    
    def _fuse_scenario_two(self, categorized_content: Dict[str, Any]) -> Dict[str, Any]:
        """场景二特定融合逻辑（高后果区风险管控方案）"""
        fusion_result = {
            'required_components_status': {},
            'diagram_completeness': {},
            'data_consistency': {}
        }
        
        text_sections = categorized_content.get('text_sections', {})
        tables_by_type = categorized_content.get('tables_by_type', {})
        images_by_type = categorized_content.get('images_by_type', {})
        
        # 检查必需组件
        required_components = [
            'hca_description', 'risk_assessment', 'control_measures', 'emergency_procedures'
        ]
        
        for component in required_components:
            fusion_result['required_components_status'][component] = {
                'text_present': component in text_sections,
                'table_present': component in tables_by_type,
                'text_count': len(text_sections.get(component, [])),
                'table_count': len(tables_by_type.get(component, []))
            }
        
        # 检查图表完整性
        required_diagrams = ['hca_image', 'site_image', 'entry_route', 'escape_route']
        for diagram in required_diagrams:
            fusion_result['diagram_completeness'][diagram] = {
                'present': diagram in images_by_type,
                'count': len(images_by_type.get(diagram, []))
            }
        
        # 检查数据一致性（基础版）
        fusion_result['data_consistency'] = self._check_basic_data_consistency(
            text_sections, tables_by_type
        )
        
        return fusion_result
    
    def _analyze_procedure_details(self, procedures: List[Dict]) -> Dict[str, Any]:
        """分析程序详细程度"""
        total_content = ""
        for proc in procedures:
            total_content += proc.get('content', '') + " "
        
        # 检查是否包含详细步骤
        step_patterns = [
            r'\d+[\.、]\s*',  # 数字编号
            r'第[一二三四五六七八九十\d]+步',  # 步骤编号
            r'步骤\s*\d+',  # 步骤数字
        ]
        
        step_count = 0
        for pattern in step_patterns:
            step_count += len(re.findall(pattern, total_content))
        
        return {
            'total_content_length': len(total_content),
            'estimated_steps': step_count,
            'has_detailed_steps': step_count >= 3,
            'content_density': len(total_content.split()) / max(len(procedures), 1)
        }
    
    def _check_basic_data_consistency(self, text_sections: Dict, tables_by_type: Dict) -> Dict[str, Any]:
        """检查基础数据一致性"""
        consistency_result = {
            'personnel_consistency': False,
            'date_consistency': False,
            'technical_consistency': False
        }
        
        # 这里可以实现更复杂的一致性检查逻辑
        # 目前只是一个框架
        
        if 'personnel_info' in text_sections and 'personnel_info' in tables_by_type:
            consistency_result['personnel_consistency'] = True
        
        if 'risk_assessment' in text_sections and 'risk_assessment' in tables_by_type:
            consistency_result['date_consistency'] = True
        
        return consistency_result
    
    def _extract_key_entities(self, structured_data: Dict[str, Any]) -> Dict[str, List]:
        """提取关键实体"""
        entities = {
            'dates': [],
            'personnel': [],
            'technical_parameters': [],
            'standards': []
        }
        
        # 从结构化数据中提取实体
        dates_info = structured_data.get('dates_info', {})
        if 'dates_found' in dates_info:
            entities['dates'] = dates_info['dates_found']
        
        personnel_info = structured_data.get('personnel_info', {})
        if 'names_found' in personnel_info:
            entities['personnel'] = personnel_info['names_found']
        
        technical_params = structured_data.get('technical_params', {})
        for param_type, params in technical_params.items():
            entities['technical_parameters'].extend(params)
        
        standards_info = structured_data.get('standards_info', {})
        if 'standards_found' in standards_info:
            entities['standards'] = standards_info['standards_found']
        
        return entities
    
    def _assess_content_quality(self, categorized_content: Dict[str, Any]) -> Dict[str, Any]:
        """评估内容质量"""
        text_sections = categorized_content.get('text_sections', {})
        tables_by_type = categorized_content.get('tables_by_type', {})
        images_by_type = categorized_content.get('images_by_type', {})
        
        return {
            'content_diversity': {
                'text_types': len(text_sections),
                'table_types': len(tables_by_type),
                'image_types': len(images_by_type)
            },
            'content_balance': {
                'text_dominance': len(text_sections) / max(len(tables_by_type) + len(images_by_type), 1),
                'multimodal_ratio': (len(tables_by_type) + len(images_by_type)) / max(len(text_sections), 1)
            },
            'completeness_score': min(len(text_sections) / 5.0, 1.0)  # 基于文本类型多样性
        }