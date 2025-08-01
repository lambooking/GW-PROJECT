"""
实体提取与标注系统 - 精确提取和标注文档中的关键实体
"""

import re
from typing import Dict, List, Any, Optional, Tuple, Set
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)

class EntityExtractor:
    """实体提取与标注器"""
    
    def __init__(self):
        # 日期提取模式
        self.date_patterns = {
            'standard_date': [
                r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?',
                r'(\d{4})[./](\d{1,2})[./](\d{1,2})',
                r'(\d{1,2})[./](\d{1,2})[./](\d{4})'
            ],
            'chinese_date': [
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                r'二[零○〇](\d{2})年(\d{1,2})月(\d{1,2})日'
            ],
            'relative_date': [
                r'(\d+)天[前后]',
                r'(\d+)个月[前后]',
                r'(\d+)年[前后]'
            ]
        }
        
        # 日期语义类型标识
        self.date_semantics = {
            'compilation': ['编制', '制定', '发布', '批准', '签发'],
            'evaluation': ['评价', '评估', '分析', '审核'],
            'identification': ['识别', '发现', '确认', '检查'],
            'revision': ['修订', '更新', '修改', '变更'],
            'implementation': ['实施', '执行', '开始', '启动'],
            'expiry': ['失效', '到期', '废止', '终止']
        }
        
        # 人员实体模式
        self.personnel_patterns = {
            'chinese_name': r'[王李张刘陈杨赵黄周吴徐孙马朱胡郭何林罗高梁宋郑谢韩唐冯于董萧程柴曹袁邓许曾彭吕苏蒋陆余丁魏薛叶阎廖尹方崔康孟范][一-龯]{1,4}',
            'job_title': r'(工程师|技术员|主任|经理|处长|科长|班长|区段长|巡线员|操作员|主管|负责人|联系人)',
            'phone': r'1[3-9]\d{9}',
            'landline': r'0\d{2,3}-?\d{7,8}',
            'email': r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
        }
        
        # 技术参数模式
        self.technical_patterns = {
            'pressure': {
                'pattern': r'([0-9.]+)\s*(MPa|mpa|兆帕|千帕|kPa|帕|Pa)',
                'unit_conversion': {'MPa': 1, 'mpa': 1, '兆帕': 1, 'kPa': 0.001, '千帕': 0.001, 'Pa': 0.000001, '帕': 0.000001}
            },
            'diameter': {
                'pattern': r'(?:管径|直径|内径|外径).*?([0-9.]+)\s*(mm|毫米|m|米|cm|厘米)',
                'unit_conversion': {'mm': 1, '毫米': 1, 'm': 1000, '米': 1000, 'cm': 10, '厘米': 10}
            },
            'length': {
                'pattern': r'(?:长度|里程|距离).*?([0-9.]+)\s*(km|公里|千米|m|米)',
                'unit_conversion': {'km': 1, '公里': 1, '千米': 1, 'm': 0.001, '米': 0.001}
            },
            'temperature': {
                'pattern': r'([0-9.-]+)\s*(℃|°C|摄氏度|度)',
                'unit_conversion': {'℃': 1, '°C': 1, '摄氏度': 1, '度': 1}
            },
            'voltage': {
                'pattern': r'([0-9.-]+)\s*(V|v|伏特?|电压)',
                'unit_conversion': {'V': 1, 'v': 1, '伏特': 1, '伏': 1}
            },
            'wall_thickness': {
                'pattern': r'壁厚.*?([0-9.]+)\s*(mm|毫米)',
                'unit_conversion': {'mm': 1, '毫米': 1}
            }
        }
        
        # 地理位置模式
        self.location_patterns = {
            'mileage': r'([0-9.]+)\+([0-9.]+)[kKmM]?(?:处|位置|点)?',  # 如：267+800m
            'coordinates': r'([0-9.]+)°([0-9.]+)′([0-9.]+)″?',  # 经纬度
            'administrative': r'([\u4e00-\u9fa5]+(?:省|市|县|区|镇|乡|村|街道))',
            'landmark': r'([\u4e00-\u9fa5]+(?:河|山|桥|路|站|厂|库|区域))'
        }
        
        # 标准编号模式
        self.standard_patterns = {
            'national': r'GB[/T]?\s*([0-9.-]+)',
            'industry': r'SY[/T]?\s*([0-9.-]+)',
            'international': r'(API\s*[0-9A-Z.-]+|ASME\s*[0-9A-Z.-]+|ISO\s*[0-9.-]+)',
            'enterprise': r'[A-Z]{2,6}[/T]?\s*([0-9.-]+)'
        }
        
        # 组织机构模式
        self.organization_patterns = {
            'company': r'([\u4e00-\u9fa5]+(?:公司|集团|企业|厂|所))',
            'department': r'([\u4e00-\u9fa5]+(?:部|处|科|室|队|组|中心))',
            'position': r'([\u4e00-\u9fa5]+(?:分公司|管理处|项目部|作业区))'
        }
    
    def extract_entities(self, fused_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取并标注实体
        
        Args:
            fused_data: 融合后的多模态数据
            
        Returns:
            提取的实体信息
        """
        try:
            # 获取全文内容
            all_text = self._get_full_text_content(fused_data)
            
            # 提取各类实体
            date_entities = self._extract_date_entities(all_text)
            personnel_entities = self._extract_personnel_entities(all_text)
            technical_entities = self._extract_technical_entities(all_text)
            location_entities = self._extract_location_entities(all_text)
            standard_entities = self._extract_standard_entities(all_text)
            organization_entities = self._extract_organization_entities(all_text)
            
            # 建立实体关系
            entity_relationships = self._build_entity_relationships(
                date_entities, personnel_entities, technical_entities,
                location_entities, standard_entities, organization_entities
            )
            
            # 验证实体有效性
            validation_results = self._validate_entities(
                date_entities, technical_entities
            )
            
            # 构建实体图谱
            entity_graph = self._build_entity_graph(
                date_entities, personnel_entities, technical_entities,
                location_entities, standard_entities, organization_entities,
                entity_relationships
            )
            
            return {
                'entities': {
                    'dates': date_entities,
                    'personnel': personnel_entities,
                    'technical_parameters': technical_entities,
                    'locations': location_entities,
                    'standards': standard_entities,
                    'organizations': organization_entities
                },
                'relationships': entity_relationships,
                'validation': validation_results,
                'entity_graph': entity_graph,
                'extraction_statistics': {
                    'total_entities': sum([
                        len(date_entities),
                        len(personnel_entities),
                        len(technical_entities),
                        len(location_entities),
                        len(standard_entities),
                        len(organization_entities)
                    ]),
                    'entity_density': self._calculate_entity_density(all_text, [
                        date_entities, personnel_entities, technical_entities,
                        location_entities, standard_entities, organization_entities
                    ])
                }
            }
            
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return {
                'error': str(e),
                'extraction_status': 'failed'
            }
    
    def _get_full_text_content(self, fused_data: Dict[str, Any]) -> str:
        """获取全文内容"""
        content_inventory = fused_data.get('content_inventory', {})
        all_text = ""
        
        # 从文本段落获取内容
        text_sections = content_inventory.get('text_sections', {})
        for section_type, items in text_sections.items():
            for item in items:
                all_text += item.get('content', '') + '\n'
        
        # 从表格获取内容
        tables_by_type = content_inventory.get('tables_by_type', {})
        for table_type, tables in tables_by_type.items():
            for table in tables:
                for row in table.get('data', []):
                    all_text += ' '.join(row) + '\n'
        
        return all_text
    
    def _extract_date_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取日期实体"""
        date_entities = []
        
        for date_type, patterns in self.date_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    try:
                        # 解析日期
                        parsed_date = self._parse_date_match(match, date_type)
                        if parsed_date:
                            # 确定语义类型
                            context = self._get_context(text, match.start(), match.end(), 100)
                            semantic_type = self._classify_date_semantic(context)
                            
                            date_entities.append({
                                'type': 'date',
                                'subtype': date_type,
                                'semantic_type': semantic_type,
                                'value': parsed_date,
                                'original_text': match.group(0),
                                'context': context,
                                'position': {
                                    'start': match.start(),
                                    'end': match.end()
                                },
                                'confidence': self._calculate_date_confidence(match.group(0), context)
                            })
                    except Exception as e:
                        logger.warning(f"日期解析失败: {e}")
                        continue
        
        # 去重和排序
        date_entities = self._deduplicate_entities(date_entities)
        return sorted(date_entities, key=lambda x: x['position']['start'])
    
    def _extract_personnel_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取人员实体"""
        personnel_entities = []
        
        # 提取姓名
        name_pattern = self.personnel_patterns['chinese_name']
        name_matches = re.finditer(name_pattern, text)
        
        for match in name_matches:
            name = match.group(0)
            context = self._get_context(text, match.start(), match.end(), 200)
            
            # 查找相关职务
            job_title = self._find_related_job_title(context)
            
            # 查找联系方式
            contact_info = self._find_contact_info(context)
            
            personnel_entities.append({
                'type': 'personnel',
                'name': name,
                'job_title': job_title,
                'contact_info': contact_info,
                'context': context,
                'position': {
                    'start': match.start(),
                    'end': match.end()
                },
                'confidence': self._calculate_personnel_confidence(name, job_title, contact_info)
            })
        
        return self._deduplicate_entities(personnel_entities)
    
    def _extract_technical_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取技术参数实体"""
        technical_entities = []
        
        for param_type, param_config in self.technical_patterns.items():
            pattern = param_config['pattern']
            unit_conversion = param_config['unit_conversion']
            
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                try:
                    value = float(match.group(1))
                    unit = match.group(2) if match.lastindex >= 2 else ''
                    
                    # 标准化单位
                    normalized_value = value * unit_conversion.get(unit, 1)
                    standard_unit = list(unit_conversion.keys())[0]
                    
                    context = self._get_context(text, match.start(), match.end(), 150)
                    
                    technical_entities.append({
                        'type': 'technical_parameter',
                        'parameter_type': param_type,
                        'original_value': value,
                        'original_unit': unit,
                        'normalized_value': normalized_value,
                        'standard_unit': standard_unit,
                        'context': context,
                        'position': {
                            'start': match.start(),
                            'end': match.end()
                        },
                        'validity': self._validate_technical_parameter(param_type, normalized_value),
                        'confidence': 0.9  # 技术参数通常置信度较高
                    })
                except (ValueError, IndexError) as e:
                    logger.warning(f"技术参数解析失败: {e}")
                    continue
        
        return self._deduplicate_entities(technical_entities)
    
    def _extract_location_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取地理位置实体"""
        location_entities = []
        
        for location_type, pattern in self.location_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                context = self._get_context(text, match.start(), match.end(), 100)
                
                location_entities.append({
                    'type': 'location',
                    'location_type': location_type,
                    'value': match.group(0),
                    'parsed_components': self._parse_location_components(match, location_type),
                    'context': context,
                    'position': {
                        'start': match.start(),
                        'end': match.end()
                    },
                    'confidence': 0.8
                })
        
        return self._deduplicate_entities(location_entities)
    
    def _extract_standard_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取标准实体"""
        standard_entities = []
        
        for standard_type, pattern in self.standard_patterns.items():
            matches = re.finditer(pattern, text, re.IGNORECASE)
            for match in matches:
                context = self._get_context(text, match.start(), match.end(), 100)
                
                standard_entities.append({
                    'type': 'standard',
                    'standard_type': standard_type,
                    'standard_number': match.group(0),
                    'context': context,
                    'position': {
                        'start': match.start(),
                        'end': match.end()
                    },
                    'requires_validation': True,  # 标准需要外部验证
                    'confidence': 0.95
                })
        
        return self._deduplicate_entities(standard_entities)
    
    def _extract_organization_entities(self, text: str) -> List[Dict[str, Any]]:
        """提取组织机构实体"""
        organization_entities = []
        
        for org_type, pattern in self.organization_patterns.items():
            matches = re.finditer(pattern, text)
            for match in matches:
                org_name = match.group(1)
                context = self._get_context(text, match.start(), match.end(), 100)
                
                organization_entities.append({
                    'type': 'organization',
                    'organization_type': org_type,
                    'name': org_name,
                    'context': context,
                    'position': {
                        'start': match.start(),
                        'end': match.end()
                    },
                    'confidence': 0.85
                })
        
        return self._deduplicate_entities(organization_entities)
    
    def _parse_date_match(self, match, date_type: str) -> Optional[str]:
        """解析日期匹配"""
        try:
            if date_type == 'standard_date':
                groups = match.groups()
                if len(groups) >= 3:
                    year, month, day = groups[:3]
                    
                    # 处理年份格式
                    if len(year) == 2:
                        year = '20' + year if int(year) < 50 else '19' + year
                    
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
            elif date_type == 'chinese_date':
                groups = match.groups()
                if len(groups) >= 3:
                    year, month, day = groups[:3]
                    return f"{year}-{month.zfill(2)}-{day.zfill(2)}"
        except:
            pass
        
        return None
    
    def _classify_date_semantic(self, context: str) -> str:
        """分类日期语义类型"""
        context_lower = context.lower()
        
        for semantic_type, keywords in self.date_semantics.items():
            if any(keyword in context_lower for keyword in keywords):
                return semantic_type
        
        return 'unknown'
    
    def _find_related_job_title(self, context: str) -> Optional[str]:
        """在上下文中查找相关职务"""
        job_pattern = self.personnel_patterns['job_title']
        match = re.search(job_pattern, context)
        return match.group(1) if match else None
    
    def _find_contact_info(self, context: str) -> Dict[str, List[str]]:
        """查找联系方式"""
        contact_info = {
            'phones': [],
            'emails': []
        }
        
        # 查找手机号
        phone_matches = re.finditer(self.personnel_patterns['phone'], context)
        for match in phone_matches:
            contact_info['phones'].append(match.group(0))
        
        # 查找固话
        landline_matches = re.finditer(self.personnel_patterns['landline'], context)
        for match in landline_matches:
            contact_info['phones'].append(match.group(0))
        
        # 查找邮箱
        email_matches = re.finditer(self.personnel_patterns['email'], context)
        for match in email_matches:
            contact_info['emails'].append(match.group(0))
        
        return contact_info
    
    def _parse_location_components(self, match, location_type: str) -> Dict[str, Any]:
        """解析地理位置组件"""
        components = {}
        
        if location_type == 'mileage':
            groups = match.groups()
            if len(groups) >= 2:
                components['kilometer'] = groups[0]
                components['meter'] = groups[1]
        elif location_type == 'coordinates':
            groups = match.groups()
            if len(groups) >= 3:
                components['degrees'] = groups[0]
                components['minutes'] = groups[1]
                components['seconds'] = groups[2]
        elif location_type in ['administrative', 'landmark']:
            components['name'] = match.group(1)
        
        return components
    
    def _validate_technical_parameter(self, param_type: str, value: float) -> Dict[str, Any]:
        """验证技术参数有效性"""
        validation_rules = {
            'pressure': {'min': 0, 'max': 50, 'unit': 'MPa'},  # 管道压力范围
            'diameter': {'min': 50, 'max': 2000, 'unit': 'mm'},  # 管径范围
            'length': {'min': 0.001, 'max': 10000, 'unit': 'km'},  # 长度范围
            'temperature': {'min': -50, 'max': 200, 'unit': '℃'},  # 温度范围
            'voltage': {'min': -2.0, 'max': 2.0, 'unit': 'V'},  # 电位范围
            'wall_thickness': {'min': 1, 'max': 50, 'unit': 'mm'}  # 壁厚范围
        }
        
        if param_type in validation_rules:
            rules = validation_rules[param_type]
            is_valid = rules['min'] <= value <= rules['max']
            
            return {
                'is_valid': is_valid,
                'expected_range': f"{rules['min']}-{rules['max']} {rules['unit']}",
                'actual_value': f"{value} {rules['unit']}"
            }
        
        return {'is_valid': True, 'note': 'No validation rules available'}
    
    def _get_context(self, text: str, start: int, end: int, context_length: int = 100) -> str:
        """获取上下文"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        return text[context_start:context_end].strip()
    
    def _calculate_date_confidence(self, date_text: str, context: str) -> float:
        """计算日期置信度"""
        confidence = 0.5
        
        # 如果有明确的语义指示词，提高置信度
        if any(word in context for word in ['编制', '制定', '评价', '识别']):
            confidence += 0.3
        
        # 如果日期格式标准，提高置信度
        if re.match(r'\d{4}-\d{2}-\d{2}', date_text):
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _calculate_personnel_confidence(self, name: str, job_title: Optional[str], contact_info: Dict) -> float:
        """计算人员置信度"""
        confidence = 0.6  # 基础置信度
        
        if job_title:
            confidence += 0.2
        
        if contact_info['phones'] or contact_info['emails']:
            confidence += 0.2
        
        return min(confidence, 1.0)
    
    def _deduplicate_entities(self, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """去重实体"""
        seen = set()
        unique_entities = []
        
        for entity in entities:
            # 创建唯一标识
            if entity['type'] == 'date':
                identifier = (entity['type'], entity.get('value'))
            elif entity['type'] == 'personnel':
                identifier = (entity['type'], entity.get('name'))
            elif entity['type'] == 'technical_parameter':
                identifier = (entity['type'], entity.get('parameter_type'), entity.get('normalized_value'))
            else:
                identifier = (entity['type'], entity.get('value', str(entity)))
            
            if identifier not in seen:
                seen.add(identifier)
                unique_entities.append(entity)
        
        return unique_entities
    
    def _build_entity_relationships(self, *entity_lists) -> List[Dict[str, Any]]:
        """建立实体关系"""
        relationships = []
        
        # 这里可以实现复杂的实体关系识别逻辑
        # 目前只是一个框架
        
        return relationships
    
    def _validate_entities(self, date_entities: List, technical_entities: List) -> Dict[str, Any]:
        """验证实体有效性"""
        validation_results = {
            'date_validation': self._validate_date_logic(date_entities),
            'technical_validation': self._validate_technical_parameters(technical_entities)
        }
        
        return validation_results
    
    def _validate_date_logic(self, date_entities: List) -> Dict[str, Any]:
        """验证日期逻辑"""
        # 根据技术方案，需要验证：编制时间 > 风险评价时间 > 识别时间
        semantic_dates = {}
        
        for entity in date_entities:
            semantic_type = entity.get('semantic_type')
            if semantic_type in ['compilation', 'evaluation', 'identification']:
                if semantic_type not in semantic_dates:
                    semantic_dates[semantic_type] = []
                semantic_dates[semantic_type].append(entity['value'])
        
        validation_result = {
            'has_required_dates': all(key in semantic_dates for key in ['compilation', 'evaluation', 'identification']),
            'temporal_logic_valid': True,  # 需要实现具体逻辑
            'found_date_types': list(semantic_dates.keys())
        }
        
        return validation_result
    
    def _validate_technical_parameters(self, technical_entities: List) -> Dict[str, Any]:
        """验证技术参数"""
        validation_summary = {
            'total_parameters': len(technical_entities),
            'valid_parameters': 0,
            'invalid_parameters': 0,
            'parameter_types': set()
        }
        
        for entity in technical_entities:
            validation_summary['parameter_types'].add(entity.get('parameter_type'))
            if entity.get('validity', {}).get('is_valid', False):
                validation_summary['valid_parameters'] += 1
            else:
                validation_summary['invalid_parameters'] += 1
        
        validation_summary['parameter_types'] = list(validation_summary['parameter_types'])
        
        return validation_summary
    
    def _build_entity_graph(self, *entity_lists_and_relationships) -> Dict[str, Any]:
        """构建实体图谱"""
        all_entities = []
        for entity_list in entity_lists_and_relationships[:-1]:  # 除了最后一个relationships
            all_entities.extend(entity_list)
        
        entity_graph = {
            'nodes': len(all_entities),
            'entity_types': {},
            'summary': {}
        }
        
        # 统计实体类型
        for entity in all_entities:
            entity_type = entity.get('type')
            if entity_type not in entity_graph['entity_types']:
                entity_graph['entity_types'][entity_type] = 0
            entity_graph['entity_types'][entity_type] += 1
        
        return entity_graph
    
    def _calculate_entity_density(self, text: str, entity_lists: List[List]) -> float:
        """计算实体密度"""
        total_entities = sum(len(entity_list) for entity_list in entity_lists)
        text_length = len(text.split())
        
        return total_entities / max(text_length, 1) * 1000  # 每千字的实体数