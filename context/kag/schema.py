"""KAG知识图谱Schema定义"""

ENTITY_TYPES = {
    "MilitaryUnit": {
        "description": "军事单位部署规则",
        "properties": {
            "unit_name": {"type": "string", "description": "单位名称"},
            "deployment_rule": {"type": "string", "description": "部署规则文本"},
            "elevation_range": {"type": "string", "description": "高程范围"},
            "slope_range": {"type": "string", "description": "坡度范围"},
            "buffer_distance": {"type": "string", "description": "缓冲距离"},
            "vegetation_types": {"type": "list", "description": "植被类型列表"},
            "type": {"type": "string", "description": "类型标识，如deployment_rule"}
        }
    },
    "Equipment": {
        "description": "装备信息",
        "properties": {
            "equipment_name": {"type": "string", "description": "装备名称"},
            "unit_type": {"type": "string", "description": "所属单位类型"},
            "range": {"type": "string", "description": "有效射程"},
            "max_range": {"type": "string", "description": "最大射程"},
            "type": {"type": "string", "description": "类型标识，如equipment_info"}
        }
    },
}

RELATION_TYPES = {
    "UnitHasEquipment": {
        "description": "单位拥有装备",
        "source_type": "MilitaryUnit",
        "target_type": "Equipment"
    },
}

COLLECTION_TO_ENTITY_TYPE = {
    "knowledge": "MilitaryUnit",
    "equipment": "Equipment"
}

