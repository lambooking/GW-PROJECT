"""
文本处理模块
"""

import re
import jieba
import jieba.posseg as pseg
from typing import List, Dict, Any, Tuple, Optional
import logging
from collections import Counter

logger = logging.getLogger(__name__)


class TextProcessor:
    """文本处理器"""
    
    def __init__(self):
        # 初始化停用词
        self.stopwords = self._load_stopwords()
        
        # 初始化专业词典
        self._load_professional_dict()
    
    def _load_stopwords(self) -> set:
        """加载停用词表"""
        # 基础停用词
        stopwords = {
            '的', '是', '在', '了', '和', '与', '或', '等', '及', '之', '为', '以',
            '有', '无', '不', '非', '可', '应', '需', '要', '将', '被', '由', '从',
            '到', '于', '对', '向', '把', '给', '让', '使', '通过', '经过', '根据',
            '按照', '依据', '如果', '假如', '当', '则', '但', '而', '然而', '因此',
            '所以', '因为', '由于', '这', '那', '这个', '那个', '这些', '那些'
        }
        return stopwords
    
    def _load_professional_dict(self):
        """加载专业词典"""
        # 添加生产运维相关专业词汇
        professional_words = [
            '作业指导书', '风险管控', '高后果区', '安全环保', '应急处置',
            '技术参数', '操作规程', '质量控制', '设备维护', '故障处理',
            '巡检记录', '检修计划', '运行状态', '监测数据', '报警处理',
            '人员配备', '资质要求', '培训记录', '考核标准', '责任制度'
        ]
        
        for word in professional_words:
            jieba.add_word(word)
    
    def clean_text(self, text: str) -> str:
        """
        清理文本
        
        Args:
            text: 输入文本
            
        Returns:
            清理后的文本
        """
        try:
            # 移除特殊字符但保留中文标点
            text = re.sub(r'[^\u4e00-\u9fff\u3000-\u303f\uff00-\uffef\w\s]', '', text)
            
            # 替换多个空白字符为单个空格
            text = re.sub(r'\s+', ' ', text)
            
            # 移除首尾空白
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"文本清理失败: {e}")
            return text
    
    def segment_text(self, text: str, use_pos: bool = False) -> List[str]:
        """
        文本分词
        
        Args:
            text: 输入文本
            use_pos: 是否使用词性标注
            
        Returns:
            分词结果
        """
        try:
            if use_pos:
                words = []
                for word, pos in pseg.cut(text):
                    if word.strip() and word not in self.stopwords:
                        words.append((word, pos))
                return words
            else:
                words = jieba.lcut(text)
                return [word for word in words if word.strip() and word not in self.stopwords]
                
        except Exception as e:
            logger.error(f"文本分词失败: {e}")
            return []
    
    def extract_keywords(self, text: str, top_k: int = 10) -> List[Tuple[str, float]]:
        """
        提取关键词
        
        Args:
            text: 输入文本
            top_k: 返回前k个关键词
            
        Returns:
            关键词及其权重列表
        """
        try:
            # 分词并过滤停用词
            words = self.segment_text(text)
            
            # 计算词频
            word_freq = Counter(words)
            
            # 计算TF权重
            total_words = len(words)
            keywords = []
            
            for word, freq in word_freq.most_common():
                if len(word) > 1:  # 过滤单字符
                    tf = freq / total_words
                    keywords.append((word, tf))
            
            return keywords[:top_k]
            
        except Exception as e:
            logger.error(f"关键词提取失败: {e}")
            return []
    
    def extract_entities(self, text: str) -> Dict[str, List[str]]:
        """
        提取命名实体
        
        Args:
            text: 输入文本
            
        Returns:
            实体字典
        """
        try:
            entities = {
                'person': [],      # 人员
                'organization': [], # 组织机构
                'location': [],    # 地点
                'time': [],        # 时间
                'equipment': [],   # 设备
                'standard': [],    # 标准规范
                'parameter': []    # 技术参数
            }
            
            # 使用正则表达式提取不同类型的实体
            
            # 提取人员（职位、姓名）
            person_patterns = [
                r'(工程师|技术员|操作员|管理员|负责人|主任|经理|总监)',
                r'(区段长|班长|组长|队长|站长|主管)',
                r'([张李王刘陈杨黄赵周吴徐孙马朱胡郭何林高罗郑梁谢宋唐许邓冯曹彭曾萧田董潘袁于蒋蔡余杜叶程苏魏吕丁任沈姚卢姜崔钟谭陆汪范金石廖贾韦夏邱方侯邹熊孟秦白江阎薛尹段雷黎史龙陶贺顾毛郝龚邵万钱严覃武戴莫孔向汤]\w{1,2})',
            ]
            
            for pattern in person_patterns:
                matches = re.findall(pattern, text)
                entities['person'].extend(matches)
            
            # 提取组织机构
            org_patterns = [
                r'([^，。！？]*(?:公司|企业|集团|厂|站|所|部|处|科|队|组|中心|院|局))',
                r'([^，。！？]*(?:管理处|运营部|技术部|安全部|质量部))'
            ]
            
            for pattern in org_patterns:
                matches = re.findall(pattern, text)
                entities['organization'].extend(matches)
            
            # 提取时间
            time_patterns = [
                r'(\d{4}年\d{1,2}月\d{1,2}日)',
                r'(\d{4}-\d{1,2}-\d{1,2})',
                r'(\d{1,2}:\d{2})',
                r'(每日|每周|每月|每年|定期|不定期)'
            ]
            
            for pattern in time_patterns:
                matches = re.findall(pattern, text)
                entities['time'].extend(matches)
            
            # 提取设备
            equipment_patterns = [
                r'([^，。！？]*(?:设备|装置|机组|泵|阀|表|仪|计|器|系统|管道|容器|罐|塔|炉|锅|机|车|工具))',
                r'([^，。！？]*(?:压缩机|发电机|变压器|开关|控制器|传感器|监测仪))'
            ]
            
            for pattern in equipment_patterns:
                matches = re.findall(pattern, text)
                entities['equipment'].extend(matches)
            
            # 提取标准规范
            standard_patterns = [
                r'(GB[\/T]?\s*\d+[-\.]?\d*[-\.]?\d*)',
                r'([A-Z]+[\/T]?\s*\d+[-\.]?\d*)',
                r'(《[^》]+》)',
                r'([^，。！？]*(?:标准|规范|规程|办法|制度|条例|指南|手册))'
            ]
            
            for pattern in standard_patterns:
                matches = re.findall(pattern, text)
                entities['standard'].extend(matches)
            
            # 提取技术参数
            parameter_patterns = [
                r'(\d+\.?\d*\s*(?:MPa|kPa|bar|psi|Pa))',  # 压力
                r'(\d+\.?\d*\s*(?:℃|°C|K))',              # 温度
                r'(\d+\.?\d*\s*(?:m³/h|L/min|t/h))',      # 流量
                r'(\d+\.?\d*\s*(?:kV|V|mV|A|mA|W|kW|MW))', # 电气参数
                r'(\d+\.?\d*\s*(?:mm|cm|m|km))',          # 长度
                r'(\d+\.?\d*\s*(?:kg|t|g))',              # 重量
            ]
            
            for pattern in parameter_patterns:
                matches = re.findall(pattern, text)
                entities['parameter'].extend(matches)
            
            # 去重并过滤
            for entity_type in entities:
                entities[entity_type] = list(set([e.strip() for e in entities[entity_type] if e.strip()]))
            
            return entities
            
        except Exception as e:
            logger.error(f"实体提取失败: {e}")
            return {}
    
    def check_grammar_errors(self, text: str) -> List[Dict[str, Any]]:
        """
        检查语法错误
        
        Args:
            text: 输入文本
            
        Returns:
            语法错误列表
        """
        errors = []
        
        try:
            # 检查标点符号错误
            punctuation_errors = self._check_punctuation(text)
            errors.extend(punctuation_errors)
            
            # 检查重复内容
            duplication_errors = self._check_duplication(text)
            errors.extend(duplication_errors)
            
            # 检查格式错误
            format_errors = self._check_format(text)
            errors.extend(format_errors)
            
        except Exception as e:
            logger.error(f"语法检查失败: {e}")
        
        return errors
    
    def _check_punctuation(self, text: str) -> List[Dict[str, Any]]:
        """检查标点符号错误"""
        errors = []
        
        # 检查重复标点
        repeated_punct = re.findall(r'[。！？]{2,}', text)
        if repeated_punct:
            errors.append({
                'type': '重复标点',
                'content': repeated_punct,
                'description': '发现重复的标点符号'
            })
        
        # 检查空格问题
        space_issues = re.findall(r'\s{2,}', text)
        if space_issues:
            errors.append({
                'type': '空格问题',
                'content': space_issues,
                'description': '发现多余的空格'
            })
        
        return errors
    
    def _check_duplication(self, text: str) -> List[Dict[str, Any]]:
        """检查重复内容"""
        errors = []
        
        # 检查重复句子
        sentences = re.split(r'[。！？]', text)
        sentence_counts = Counter(sentences)
        
        duplicated_sentences = [sent for sent, count in sentence_counts.items() 
                              if count > 1 and len(sent.strip()) > 5]
        
        if duplicated_sentences:
            errors.append({
                'type': '重复内容',
                'content': duplicated_sentences,
                'description': '发现重复的句子'
            })
        
        return errors
    
    def _check_format(self, text: str) -> List[Dict[str, Any]]:
        """检查格式错误"""
        errors = []
        
        # 检查数字格式
        number_issues = re.findall(r'\d+[，。！？]', text)
        if number_issues:
            errors.append({
                'type': '数字格式',
                'content': number_issues,
                'description': '数字后直接跟标点符号'
            })
        
        return errors
    
    def extract_sections(self, text: str) -> Dict[str, str]:
        """
        提取文档章节
        
        Args:
            text: 输入文本
            
        Returns:
            章节字典
        """
        sections = {}
        
        try:
            # 常见章节标题模式
            section_patterns = [
                r'第?[一二三四五六七八九十\d]+[章节条款部分]\s*[：:：]?\s*([^\n\r]+)',
                r'(\d+\.?\d*)\s*([^\n\r]+)',
                r'([一二三四五六七八九十]+)\s*[、\.]\s*([^\n\r]+)',
                r'(目录|概述|范围|职责|作业内容|相关文件|记录文件|附录)\s*[：:：]?\s*([^\n\r]*)'
            ]
            
            for pattern in section_patterns:
                matches = re.findall(pattern, text, re.MULTILINE)
                for match in matches:
                    if isinstance(match, tuple) and len(match) >= 2:
                        title = match[-1].strip()
                        if title:
                            sections[title] = ""
                    elif isinstance(match, str):
                        title = match.strip()
                        if title:
                            sections[title] = ""
            
            return sections
            
        except Exception as e:
            logger.error(f"章节提取失败: {e}")
            return {}
    
    def calculate_readability(self, text: str) -> Dict[str, float]:
        """
        计算文本可读性
        
        Args:
            text: 输入文本
            
        Returns:
            可读性指标
        """
        try:
            # 基础统计
            char_count = len(text)
            word_count = len(self.segment_text(text))
            sentence_count = len(re.split(r'[。！？]', text))
            
            # 避免除零错误
            if sentence_count == 0 or word_count == 0:
                return {'score': 0.0, 'level': '无法计算'}
            
            # 平均句长
            avg_sentence_length = word_count / sentence_count
            
            # 复杂词汇比例（长度>=4的词）
            words = self.segment_text(text)
            complex_words = [w for w in words if len(w) >= 4]
            complex_ratio = len(complex_words) / word_count if word_count > 0 else 0
            
            # 简化的可读性分数计算
            readability_score = 100 - (avg_sentence_length * 2) - (complex_ratio * 50)
            readability_score = max(0, min(100, readability_score))
            
            # 可读性等级
            if readability_score >= 80:
                level = '易读'
            elif readability_score >= 60:
                level = '较易读'
            elif readability_score >= 40:
                level = '一般'
            elif readability_score >= 20:
                level = '较难读'
            else:
                level = '难读'
            
            return {
                'score': readability_score,
                'level': level,
                'char_count': char_count,
                'word_count': word_count,
                'sentence_count': sentence_count,
                'avg_sentence_length': avg_sentence_length,
                'complex_ratio': complex_ratio
            }
            
        except Exception as e:
            logger.error(f"可读性计算失败: {e}")
            return {'score': 0.0, 'level': '计算失败'}
    
    def normalize_text(self, text: str) -> str:
        """
        文本标准化
        
        Args:
            text: 输入文本
            
        Returns:
            标准化后的文本
        """
        try:
            # 统一标点符号
            text = text.replace('，', '，')
            text = text.replace('。', '。')
            text = text.replace('！', '！')
            text = text.replace('？', '？')
            text = text.replace('：', '：')
            text = text.replace('；', '；')
            
            # 统一引号
            text = re.sub(r'["""]', '"', text)
            text = re.sub(r"[''']", "'", text)
            
            # 统一数字格式
            text = re.sub(r'(\d+)\s*[、.]\s*', r'\1. ', text)
            
            # 统一空格
            text = re.sub(r'\s+', ' ', text)
            
            return text.strip()
            
        except Exception as e:
            logger.error(f"文本标准化失败: {e}")
            return text 