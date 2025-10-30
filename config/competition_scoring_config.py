"""
比赛评分细则对齐配置
根据比赛方对输出报告的评分标准，优化后的评分配置
"""

# 场景一：作业指导书审核 - 比赛版评分配置
COMPETITION_SCORING_CRITERIA_SCENE1 = {
    # 1. 整体审核：内容与结构完整性 (权重: 30%)
    "structure_content_completeness": {
        "name": "内容与结构完整性",
        "weight": 0.30,
        "max_score": 30,
        "evaluation_focus": "整体审核",
        "description": "作业区概况、QHSE目标指标、岗位设置与职责、重点作业流程及内容、操作指南、应急处置、风险辨识与控制",
        "search_queries": [
            "作业区 概况 基本情况",
            "QHSE 目标 指标",
            "岗位 设置 职责 分工",
            "作业 流程 内容 步骤",
            "操作 指南 要求 规范",
            "应急 处置 预案 措施",
            "风险 辨识 控制 防范"
        ],
        "context_length": 2000,
        "min_score_threshold": 0.3,
        "must_check_items": [
            "范围明确", "职责清晰", "作业内容完整",
            "相关文件列出", "记录文件明确",
            "覆盖作业区概况", "QHSE目标存在",
            "岗位设置与职责", "重点作业流程",
            "操作指南详细", "应急处置方案",
            "风险辨识与控制"
        ]
    },
    
    # 2. 细节审核 - 文字及语法错误 (权重: 15%)
    "grammar_and_wording": {
        "name": "文字及语法规范性",
        "weight": 0.15,
        "max_score": 15,
        "evaluation_focus": "细节审核 - 文字及语法",
        "description": "全文句子是否通顺、标点符号是否使用正确、专业术语名词或缩写是否准确",
        "search_queries": [
            "全文 段落 句子",
            "文字 表述 描述",
            "专业 术语 缩写 名词"
        ],
        "context_length": 1500,
        "min_score_threshold": 0.2,
        "check_items": [
            "句子通顺性",
            "标点符号正确性",
            "专业术语准确性",
            "缩写规范性",
            "语法错误"
        ]
    },
    
    # 3. 细节审核 - 业务逻辑错误 (权重: 20%)
    "business_logic_consistency": {
        "name": "业务逻辑一致性",
        "weight": 0.20,
        "max_score": 20,
        "evaluation_focus": "细节审核 - 业务逻辑",
        "description": "上下文逻辑是否连贯、上下文语义是否矛盾、时间是否与文字表述相对应",
        "search_queries": [
            "上下文 逻辑 连贯",
            "前后 一致 矛盾",
            "时间 日期 顺序",
            "流程 步骤 顺序"
        ],
        "context_length": 1800,
        "min_score_threshold": 0.25,
        "check_items": [
            "上下文逻辑连贯",
            "内容不矛盾",
            "时间与文字表述对应",
            "流程顺序合理"
        ]
    },
    
    # 4. 细节审核 - 应急处置审核 (权重: 25%)
    "emergency_response_procedure": {
        "name": "应急处置流程完整性",
        "weight": 0.25,
        "max_score": 25,
        "evaluation_focus": "细节审核 - 应急处置",
        "description": "针对生产异常事件处置进行深度审核，审核内容是否合理，处置顺序是否正确，处置流程是否缺失关键步骤",
        "search_queries": [
            "生产 异常 事件 故障",
            "应急 处置 流程 步骤",
            "处理 措施 方法 预案",
            "顺序 程序 流程",
            "关键 步骤 重点 要点"
        ],
        "context_length": 2000,
        "min_score_threshold": 0.3,
        "check_items": [
            "处置流程合理性",
            "处置顺序正确性",
            "关键步骤完整性",
            "应急措施有效性"
        ]
    },
    
    # 5. 模板检测 (权重: 10%)
    "template_compliance": {
        "name": "模板规范性",
        "weight": 0.10,
        "max_score": 10,
        "evaluation_focus": "模板检测",
        "description": "识别是否使用规定模板",
        "search_queries": [
            "模板 格式 规范",
            "章节 结构 编号",
            "标题 层次 编码"
        ],
        "context_length": 1000,
        "min_score_threshold": 0.2,
        "check_items": [
            "使用规定模板",
            "章节结构规范",
            "编号格式正确"
        ]
    }
}


# 场景二：高后果区风险管控方案审核 - 比赛版评分配置
COMPETITION_SCORING_CRITERIA_SCENE2 = {
    # 1. 签字页手签识别 (10%)
    "signature_recognition": {
        "name": "签字页手签识别",
        "weight": 0.10,
        "max_score": 10,
        "evaluation_focus": "签字页手签识别",
        "description": "识别签字页手签痕迹",
        "type": "multimodal_signature",
        "search_queries": [
            "签字 签章 签名 盖章",
            "编制 审核 批准",
            "评审 意见 签发",
            "姓名 日期 时间"
        ],
        "context_length": 800,
        "pages": [1, 2, 3],
        "image_keywords": [
            "签字", "签章", "签名", "盖章", "手签",
            "编制", "审核", "批准", "校对",
            "年", "月", "日"
        ],
        "check_items": [
            "识别签字痕迹",
            "识别手签人员",
            "识别签字日期"
        ]
    },
    
    # 2. 内容完整性 (11%)
    "content_completeness": {
        "name": "内容完整性",
        "weight": 0.11,
        "max_score": 11,
        "evaluation_focus": "内容完整性",
        "description": "人员密集型高后果区影像图、现场图、入场线路图、逃生路线图及应急疏散集合点位置；环境敏感型高后果区影像图、现场图、入场线路图、水体敏感型高后果区围油设施放置图",
        "search_queries": [
            "高后果区 影像图",
            "现场 图片 照片",
            "入场 线路 路线",
            "逃生 路线 疏散",
            "集合点 集结点 位置",
            "水体 敏感 围油 设施",
            "环境 敏感 类型"
        ],
        "context_length": 1500,
        "image_keywords": [
            "影像图", "现场图", "示意图",
            "入场线路", "逃生路线", "疏散路线",
            "集合点", "集结点",
            "围油设施", "水体"
        ],
        "check_items": [
            "高后果区影像图",
            "高后果区现场图",
            "入场线路图",
            "逃生路线图（人员密集型）",
            "应急疏散集合点位置",
            "水体敏感型围油设施放置图（环境敏感型）"
        ]
    },
    
    # 3. 影像图标注识别 (14%)
    "image_annotation_recognition": {
        "name": "影像图标注识别",
        "weight": 0.14,
        "max_score": 14,
        "evaluation_focus": "图片识别能力 - 影像图标注",
        "description": "影像图管道位置（实线）及潜在影响半径（虚线）线条；管道周边的各类入口的建筑物和环境受体的名称和相关信息，包括人员数量、建筑物名称等内容",
        "type": "multimodal_image",
        "search_queries": [
            "影像图 标注",
            "管道 位置 实线",
            "潜在 影响 半径 虚线",
            "建筑物 名称 标注",
            "人员 数量 密集",
            "环境 受体 敏感"
        ],
        "context_length": 1200,
        "image_keywords": [
            "实线", "虚线", "线条",
            "管道位置", "影响半径",
            "建筑物", "人员数量",
            "标注", "名称"
        ],
        "check_items": [
            "管道位置标注（实线）",
            "潜在影响半径（虚线）",
            "建筑物名称标注",
            "人员数量标注",
            "环境受体信息"
        ]
    },
    
    # 4. 入场线路图标注识别 (15%)
    "entry_route_annotation": {
        "name": "入场线路图标注识别",
        "weight": 0.15,
        "max_score": 15,
        "evaluation_focus": "图片识别能力 - 入场线路图标注",
        "description": "入场路线标注及文字说明，入场路线是否合理（路线不能穿山、穿墙、无桥跨河、穿建筑物、不在可行车道路）",
        "type": "multimodal_route",
        "search_queries": [
            "入场 线路 路线",
            "标注 说明 文字",
            "路径 合理 规划"
        ],
        "context_length": 1200,
        "image_keywords": [
            "入场线路", "路线图",
            "标注", "文字说明",
            "路径", "道路"
        ],
        "check_items": [
            "入场路线标注及文字说明",
            "路线合理性：不能穿山",
            "路线合理性：不能穿墙",
            "路线合理性：不能无桥跨河",
            "路线合理性：不能穿建筑物",
            "路线合理性：必须在可行车道路"
        ]
    },
    
    # 5. 逃生路线图标注识别 (15%)
    "evacuation_route_annotation": {
        "name": "逃生路线图、应急疏散集结点标注识别（人员密集型）",
        "weight": 0.15,
        "max_score": 15,
        "evaluation_focus": "图片识别能力 - 逃生路线图标注（人员密集型）",
        "description": "逃生路线、应急疏散集结点位置标注及文字说明，路线和位置是否合理（疏散方向标注应向管道两侧，集结点位置应在潜在影响半径范围以外）",
        "type": "multimodal_evacuation",
        "search_queries": [
            "逃生 路线 疏散",
            "集结点 集合点 位置",
            "应急 疏散 方向",
            "标注 说明 合理性"
        ],
        "context_length": 1200,
        "image_keywords": [
            "逃生路线", "疏散路线",
            "集结点", "集合点",
            "疏散方向", "标注",
            "影响半径"
        ],
        "check_items": [
            "逃生路线标注及文字说明",
            "应急疏散集结点位置标注及文字说明",
            "疏散方向合理性：应向管道两侧",
            "集结点位置合理性：应在潜在影响半径范围以外"
        ]
    },
    
    # 6. 图片标注一致性 (4%)
    "image_text_consistency": {
        "name": "图片标注一致性",
        "weight": 0.04,
        "max_score": 4,
        "evaluation_focus": "上下文逻辑识别能力 - 图片标注一致性",
        "description": "高后果区特征描述部分对建筑物描述与影像图标注是否一致",
        "search_queries": [
            "高后果区 特征 描述",
            "建筑物 描述 信息",
            "影像图 标注 一致"
        ],
        "context_length": 1000,
        "check_items": [
            "建筑物描述与影像图标注一致"
        ]
    },
    
    # 7. 上下文内容一致性 (9%)
    "context_consistency": {
        "name": "上下文内容一致性",
        "weight": 0.09,
        "max_score": 9,
        "evaluation_focus": "上下文逻辑识别能力 - 内容一致性",
        "description": "人防措施中涉及的区段长信息与高后果区基本信息表是否一致；位置信息与高后果区风险评价结果表是否一致；高后果区编号前后是否一致等",
        "search_queries": [
            "人防 措施 区段长",
            "基本 信息表 数据",
            "位置 信息 坐标",
            "风险 评价 结果表",
            "高后果区 编号 一致"
        ],
        "context_length": 1500,
        "check_items": [
            "区段长信息与基本信息表一致",
            "位置信息与风险评价结果表一致",
            "高后果区编号前后一致"
        ]
    },
    
    # 8. 标准遵从度 (4%)
    "standard_compliance": {
        "name": "标准遵从度",
        "weight": 0.04,
        "max_score": 4,
        "evaluation_focus": "标准遵从度",
        "description": "是否参照GB32167（高后果区识别标准）相关规定",
        "search_queries": [
            "GB32167",
            "高后果区 识别 标准",
            "国家标准 规范 规定"
        ],
        "context_length": 1000,
        "check_items": [
            "参照GB32167标准"
        ]
    },
    
    # 9. 特定内容完整性 (4%)
    "specific_content_completeness": {
        "name": "特定内容完整性",
        "weight": 0.04,
        "max_score": 4,
        "evaluation_focus": "内容完整性",
        "description": "文中若存在人员密集型高后果区的表则应包含市政管网交叉位置图；文中若存在输油管道环境敏感类高后果区描述则应包含水体敏感型高后果区围油设施放置图",
        "search_queries": [
            "人员密集型 市政管网 交叉位置图",
            "输油管道 环境敏感 水体敏感",
            "围油设施 放置图"
        ],
        "context_length": 1000,
        "image_keywords": [
            "市政管网", "交叉位置",
            "围油设施", "放置图"
        ],
        "check_items": [
            "人员密集型含市政管网交叉位置图",
            "输油管道环境敏感类含水体敏感型围油设施放置图"
        ]
    },
    
    # 10. 时间逻辑一致性 (4%)
    "time_logic_consistency": {
        "name": "时间逻辑一致性",
        "weight": 0.04,
        "max_score": 4,
        "evaluation_focus": "时间逻辑一致性",
        "description": "封面编制时间、高后果区识别时间、风险评价时间年份应一致，时间逻辑为风险评价时间晚于识别时间",
        "search_queries": [
            "编制 时间 日期",
            "识别 时间 年份",
            "风险评价 时间 晚于"
        ],
        "context_length": 800,
        "check_items": [
            "封面编制时间、识别时间、风险评价时间年份一致",
            "风险评价时间晚于识别时间"
        ]
    },
    
    # 11. 数据逻辑正确性 (4%)
    "data_logic_correctness": {
        "name": "数据逻辑是否正确",
        "weight": 0.04,
        "max_score": 4,
        "evaluation_focus": "数据逻辑是否正确",
        "description": "电位测试结果部分是否超出-0.85V~-1.2V；风险评价结果中可能性、后果值、风险值数据为数值、风险等级为'低、中、较高、高'",
        "search_queries": [
            "电位 测试 结果 -0.85 -1.2",
            "风险 评价 可能性 后果值 风险值",
            "风险 等级 低 中 较高 高"
        ],
        "context_length": 1000,
        "check_items": [
            "电位测试结果在-0.85V~-1.2V范围内",
            "风险评价中可能性、后果值、风险值为数值",
            "风险等级为低、中、较高、高"
        ]
    },
    
    # 12. 文字模板一致性 (5%)
    "text_template_consistency": {
        "name": "文字模板一致性",
        "weight": 0.05,
        "max_score": 5,
        "evaluation_focus": "文字模板一致性",
        "description": "管道本体管控措施、外部环境风险管控、事故状态下前期处置部分描述是否与模板要求一致或包含",
        "search_queries": [
            "管道 本体 管控 措施",
            "外部 环境 风险 管控",
            "事故 状态 前期 处置",
            "模板 要求 规范"
        ],
        "context_length": 1500,
        "check_items": [
            "管道本体管控措施与模板一致",
            "外部环境风险管控与模板一致",
            "事故状态下前期处置与模板一致"
        ]
    }
}


# 配置说明
COMPETITION_CONFIG_INFO = {
    "version": "1.0",
    "update_date": "2025-01-30",
    "description": "根据比赛方评分细则优化的评分配置",
    "scene1_total_weight": sum(item["weight"] for item in COMPETITION_SCORING_CRITERIA_SCENE1.values()),
    "scene2_total_weight": sum(item["weight"] for item in COMPETITION_SCORING_CRITERIA_SCENE2.values()),
    "notes": [
        "场景一权重总和: 1.0 (30% + 15% + 20% + 25% + 10%)",
        "场景二权重总和: 1.0 (10% + 15% + 15% + 15% + 15% + 5% + 10% + 5% + 5% + 5% + 5% + 5%)",
        "所有评分项都与比赛方评分细则对齐",
        "识别效率要求已在系统层面优化（签字页优化等）",
        "兼容性已满足（支持WORD和PDF格式）"
    ]
}


if __name__ == "__main__":
    # 验证权重总和
    print("="*80)
    print("比赛评分配置验证")
    print("="*80)
    
    scene1_total = sum(item["weight"] for item in COMPETITION_SCORING_CRITERIA_SCENE1.values())
    scene2_total = sum(item["weight"] for item in COMPETITION_SCORING_CRITERIA_SCENE2.values())
    
    print(f"\n场景一评分项数量: {len(COMPETITION_SCORING_CRITERIA_SCENE1)}")
    print(f"场景一权重总和: {scene1_total:.2f} {'✅' if abs(scene1_total - 1.0) < 0.01 else '❌'}")
    
    print(f"\n场景二评分项数量: {len(COMPETITION_SCORING_CRITERIA_SCENE2)}")
    print(f"场景二权重总和: {scene2_total:.2f} {'✅' if abs(scene2_total - 1.0) < 0.01 else '❌'}")
    
    print("\n场景一评分项:")
    for key, config in COMPETITION_SCORING_CRITERIA_SCENE1.items():
        print(f"  - {config['name']:20s} 权重: {config['weight']*100:5.1f}%  分值: {config['max_score']}分")
    
    print("\n场景二评分项:")
    for key, config in COMPETITION_SCORING_CRITERIA_SCENE2.items():
        print(f"  - {config['name']:40s} 权重: {config['weight']*100:5.1f}%  分值: {config['max_score']}分")
    
    print("\n" + "="*80)

