"""
结构化数据提取器 - 将解析后的文档内容转换为便于AI分析的结构化格式
"""

import re
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class StructuredDataExtractor:
    """结构化数据提取器"""
    
    def __init__(self):
        # 技术参数模式
        self.technical_patterns = {
            'pressure': r'([0-9.]+)\s*(MPa|mpa|兆帕)',
            'diameter': r'([0-9.]+)\s*(mm|毫米|米)',
            'length': r'([0-9.]+)\s*(km|公里|千米|m|米)',
            'temperature': r'([0-9.-]+)\s*(℃|°C|度)',
            'voltage': r'([0-9.-]+)\s*(V|v|伏)',
            'wall_thickness': r'壁厚.*?([0-9.]+)\s*(mm|毫米)'
        }
        
        # 日期模式
        self.date_patterns = [
            r'(\d{4})[年/-](\d{1,2})[月/-](\d{1,2})[日]?',
            r'(\d{4})[./](\d{1,2})[./](\d{1,2})',
            r'(\d{1,2})[./](\d{1,2})[./](\d{4})',
        ]
        
        # 人员角色模式
        self.personnel_patterns = {
            'engineer': r'工程师|技术员',
            'inspector': r'巡线员|巡检员|巡护员',
            'supervisor': r'区段长|负责人|主管',
            'operator': r'操作员|操作工',
            'manager': r'经理|主任|处长'
        }
        
        # 标准编号模式
        self.standard_patterns = [
            r'GB[/T]?\s*[0-9.-]+',
            r'SY[/T]?\s*[0-9.-]+',
            r'API\s*[0-9A-Z.-]+',
            r'ASME\s*[0-9A-Z.-]+',
            r'ISO\s*[0-9.-]+'
        ]
    
    def extract_structured_data(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """
        提取结构化数据
        
        Args:
            parsed_content: 解析后的文档内容
            
        Returns:
            结构化数据字典
        """
        try:
            # 获取分类信息
            classification = parsed_content.get('classification', {})
            scenario = classification.get('scenario', 'unknown')
            
            # 提取基础信息
            basic_info = self._extract_basic_info(parsed_content)
            
            # 提取文档结构信息
            structure_info = self._extract_structure_info(parsed_content)
            
            # 提取技术参数
            technical_params = self._extract_technical_parameters(parsed_content)
            
            # 提取人员信息
            personnel_info = self._extract_personnel_info(parsed_content)
            
            # 提取标准信息
            standards_info = self._extract_standards_info(parsed_content)
            
            # 提取日期信息
            dates_info = self._extract_dates_info(parsed_content)
            
            # 根据场景提取特定信息
            if scenario == 'scenario_one':
                scenario_specific = self._extract_scenario_one_specific(parsed_content)
            elif scenario == 'scenario_two':
                scenario_specific = self._extract_scenario_two_specific(parsed_content)
            else:
                scenario_specific = {}
            
            return {
                'basic_info': basic_info,
                'classification': classification,
                'structure_info': structure_info,
                'technical_params': technical_params,
                'personnel_info': personnel_info,
                'standards_info': standards_info,
                'dates_info': dates_info,
                'scenario_specific': scenario_specific,
                'extraction_metadata': {
                    'extraction_time': datetime.now().isoformat(),
                    'total_content_items': len(parsed_content.get('text_content', [])),
                    'total_tables': len(parsed_content.get('tables', [])),
                    'total_images': len(parsed_content.get('images', []))
                }
            }
            
        except Exception as e:
            logger.error(f"结构化数据提取失败: {e}")
            return {
                'error': str(e),
                'extraction_metadata': {
                    'extraction_time': datetime.now().isoformat(),
                    'status': 'failed'
                }
            }
    
    def _extract_basic_info(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取基础文档信息"""
        basic_info = {
            'file_type': parsed_content.get('file_type'),
            'total_pages': parsed_content.get('total_pages', 0),
            'title': None,
            'document_number': None,
            'version': None
        }
        
        # 从第一页内容中提取标题和文档编号
        text_content = parsed_content.get('text_content', [])
        if text_content:
            first_page_content = ""
            for item in text_content[:5]:  # 前几个内容项
                first_page_content += item.get('content', '') + '\n'
            
            # 提取标题（通常在文档开头）
            title_match = re.search(r'(.*作业指导书|.*风险管控方案|.*操作规程)', first_page_content)
            if title_match:
                basic_info['title'] = title_match.group(1).strip()
            
            # 提取文档编号
            doc_num_patterns = [
                r'文件编码[：:]\s*([A-Z0-9/.-]+)',
                r'编号[：:]\s*([A-Z0-9/.-]+)',
                r'文档编号[：:]\s*([A-Z0-9/.-]+)'
            ]
            for pattern in doc_num_patterns:
                match = re.search(pattern, first_page_content)
                if match:
                    basic_info['document_number'] = match.group(1)
                    break
            
            # 提取版本信息
            version_patterns = [
                r'版本[：:]\s*([A-Z0-9.]+)',
                r'修改码[：:]\s*([A-Z0-9.]+)',
                r'发行版本[：:]\s*([A-Z0-9.]+)'
            ]
            for pattern in version_patterns:
                match = re.search(pattern, first_page_content)
                if match:
                    basic_info['version'] = match.group(1)
                    break
        
        return basic_info
    
    def _extract_structure_info(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取文档结构信息"""
        text_content = parsed_content.get('text_content', [])
        
        # 统计章节结构
        headers = []
        chapters = 0
        sections = 0
        subsections = 0
        
        for item in text_content:
            if item.get('type') == 'header':
                level = item.get('level', 0)
                content = item.get('content', '')
                headers.append({
                    'level': level,
                    'content': content,
                    'page_number': item.get('page_number')
                })
                
                if level == 1:
                    chapters += 1
                elif level == 2:
                    sections += 1
                elif level == 3:
                    subsections += 1
        
        # 检查是否有目录
        has_toc = False
        toc_pages = []
        for item in text_content:
            content = item.get('content', '').lower()
            if '目录' in content or 'contents' in content:
                has_toc = True
                toc_pages.append(item.get('page_number'))
        
        # 检查附录
        appendices = []
        for item in text_content:
            content = item.get('content', '')
            if re.search(r'附录\s*[A-Z]', content):
                appendices.append({
                    'name': content,
                    'page_number': item.get('page_number')
                })
        
        return {
            'headers_count': len(headers),
            'chapters_count': chapters,
            'sections_count': sections,
            'subsections_count': subsections,
            'has_table_of_contents': has_toc,
            'toc_pages': toc_pages,
            'appendices': appendices,
            'headers': headers[:20]  # 只保留前20个标题
        }
    
    def _extract_technical_parameters(self, parsed_content: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """提取技术参数"""
        all_text = self._get_all_text(parsed_content)
        
        technical_params = {}
        
        for param_type, pattern in self.technical_patterns.items():
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            params = []
            
            for match in matches:
                value = match.group(1)
                unit = match.group(2) if match.lastindex >= 2 else ''
                context = self._get_context(all_text, match.start(), match.end())
                
                params.append({
                    'value': value,
                    'unit': unit,
                    'context': context,
                    'full_match': match.group(0)
                })
            
            if params:
                technical_params[param_type] = params
        
        return technical_params
    
    def _extract_personnel_info(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取人员信息"""
        all_text = self._get_all_text(parsed_content)
        
        personnel_info = {
            'roles_found': {},
            'names_found': [],
            'contact_info': []
        }
        
        # 提取角色信息
        for role_type, pattern in self.personnel_patterns.items():
            matches = re.finditer(pattern, all_text)
            count = len(list(matches))
            if count > 0:
                personnel_info['roles_found'][role_type] = count
        
        # 提取姓名（中文姓名模式）
        name_pattern = r'[（(]?([王李张刘陈杨赵黄周吴徐孙马朱胡郭何林罗高梁宋郑谢韩唐冯于董萧程柴曹袁邓许曾彭吕苏蒋陆余丁魏薛叶阎廖尹方崔康孟范][一-龯]{1,3})[）)]?'
        name_matches = re.finditer(name_pattern, all_text)
        for match in name_matches:
            name = match.group(1)
            context = self._get_context(all_text, match.start(), match.end(), 50)
            personnel_info['names_found'].append({
                'name': name,
                'context': context
            })
        
        # 提取联系方式
        phone_pattern = r'1[3-9]\d{9}'
        phone_matches = re.finditer(phone_pattern, all_text)
        for match in phone_matches:
            phone = match.group(0)
            context = self._get_context(all_text, match.start(), match.end(), 30)
            personnel_info['contact_info'].append({
                'type': 'phone',
                'value': phone,
                'context': context
            })
        
        return personnel_info
    
    def _extract_standards_info(self, parsed_content: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """提取标准信息"""
        all_text = self._get_all_text(parsed_content)
        
        standards_found = []
        
        for pattern in self.standard_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                standard_num = match.group(0)
                context = self._get_context(all_text, match.start(), match.end())
                
                standards_found.append({
                    'standard_number': standard_num,
                    'context': context,
                    'type': self._classify_standard(standard_num)
                })
        
        return {
            'standards_found': standards_found,
            'total_count': len(standards_found)
        }
    
    def _extract_dates_info(self, parsed_content: Dict[str, Any]) -> Dict[str, List[Dict]]:
        """提取日期信息"""
        all_text = self._get_all_text(parsed_content)
        
        dates_found = []
        
        for pattern in self.date_patterns:
            matches = re.finditer(pattern, all_text)
            for match in matches:
                try:
                    # 解析日期
                    groups = match.groups()
                    if len(groups) >= 3:
                        year, month, day = groups[:3]
                        
                        # 处理年份格式
                        if len(year) == 2:
                            year = '20' + year if int(year) < 50 else '19' + year
                        
                        date_str = f"{year}-{month.zfill(2)}-{day.zfill(2)}"
                        context = self._get_context(all_text, match.start(), match.end())
                        
                        dates_found.append({
                            'date': date_str,
                            'original_format': match.group(0),
                            'context': context,
                            'semantic_type': self._classify_date_type(context)
                        })
                except:
                    continue
        
        return {
            'dates_found': dates_found,
            'total_count': len(dates_found)
        }
    
    def _extract_scenario_one_specific(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取场景一特定信息（作业指导书）"""
        all_text = self._get_all_text(parsed_content)
        
        scenario_info = {
            'core_modules_found': {},
            'safety_requirements': [],
            'operational_procedures': [],
            'emergency_procedures': []
        }
        
        # 检查核心模块
        core_modules = [
            ('job_conditions', '岗位条件'),
            ('responsibilities', '职责|岗位职责'),
            ('work_guidance', '作业指引|作业指导'),
            ('inspection', '巡检|巡查'),
            ('operation_standards', '操作规范|操作标准'),
            ('emergency', '应急|紧急'),
            ('training', '培训|教育')
        ]
        
        for module_key, module_pattern in core_modules:
            if re.search(module_pattern, all_text, re.IGNORECASE):
                scenario_info['core_modules_found'][module_key] = True
            else:
                scenario_info['core_modules_found'][module_key] = False
        
        # 提取安全要求
        safety_patterns = [
            r'(安全.*?要求.*?)(?:\n|。)',
            r'(禁止.*?)(?:\n|。)',
            r'(必须.*?安全.*?)(?:\n|。)'
        ]
        
        for pattern in safety_patterns:
            matches = re.finditer(pattern, all_text, re.IGNORECASE)
            for match in matches:
                scenario_info['safety_requirements'].append(match.group(1))
        
        return scenario_info
    
    def _extract_scenario_two_specific(self, parsed_content: Dict[str, Any]) -> Dict[str, Any]:
        """提取场景二特定信息（高后果区风险管控方案）"""
        all_text = self._get_all_text(parsed_content)
        
        scenario_info = {
            'hca_type': None,
            'risk_assessment_found': False,
            'control_measures_found': False,
            'emergency_plan_found': False,
            'signature_page_found': False,
            'diagrams_info': {
                'total_images': len(parsed_content.get('images', [])),
                'required_diagrams': []
            }
        }
        
        # 识别高后果区类型
        if re.search(r'人员密集型', all_text):
            scenario_info['hca_type'] = 'personnel_intensive'
        elif re.search(r'环境敏感型', all_text):
            scenario_info['hca_type'] = 'environment_sensitive'
        
        # 检查必要组件
        if re.search(r'风险评价|风险评估', all_text):
            scenario_info['risk_assessment_found'] = True
        
        if re.search(r'管控措施|控制措施', all_text):
            scenario_info['control_measures_found'] = True
        
        if re.search(r'应急预案|应急响应', all_text):
            scenario_info['emergency_plan_found'] = True
        
        if re.search(r'签字|签名', all_text):
            scenario_info['signature_page_found'] = True
        
        # 检查必需图表
        required_diagrams = [
            '影像图', '现场图', '入场线路图', '逃生路线图', '疏散集合点', '应急物资'
        ]
        
        for diagram in required_diagrams:
            if re.search(diagram, all_text):
                scenario_info['diagrams_info']['required_diagrams'].append(diagram)
        
        return scenario_info
    
    def _get_all_text(self, parsed_content: Dict[str, Any]) -> str:
        """获取所有文本内容"""
        all_text = ""
        
        # 文本内容
        for item in parsed_content.get('text_content', []):
            all_text += item.get('content', '') + '\n'
        
        # 表格内容
        for table in parsed_content.get('tables', []):
            for row in table.get('data', []):
                all_text += ' '.join(row) + '\n'
        
        return all_text
    
    def _get_context(self, text: str, start: int, end: int, context_length: int = 100) -> str:
        """获取匹配项的上下文"""
        context_start = max(0, start - context_length)
        context_end = min(len(text), end + context_length)
        return text[context_start:context_end].strip()
    
    def _classify_standard(self, standard_num: str) -> str:
        """分类标准类型"""
        if standard_num.startswith('GB'):
            return 'national_standard'
        elif standard_num.startswith('SY'):
            return 'industry_standard'
        elif standard_num.startswith('API'):
            return 'international_standard'
        else:
            return 'other_standard'
    
    def _classify_date_type(self, context: str) -> str:
        """根据上下文分类日期类型"""
        context_lower = context.lower()
        
        if any(word in context_lower for word in ['编制', '制定', '发布']):
            return 'compilation_date'
        elif any(word in context_lower for word in ['评价', '评估']):
            return 'evaluation_date'
        elif any(word in context_lower for word in ['识别', '分析']):
            return 'identification_date'
        elif any(word in context_lower for word in ['修订', '更新']):
            return 'revision_date'
        else:
            return 'unknown_date'