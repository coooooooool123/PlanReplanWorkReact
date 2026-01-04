import sys
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).parent
BASE_DIR_PARENT = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR_PARENT) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_PARENT))

def get_equipment_info() -> List[Dict]:
    """获取装备信息列表（包含射程等信息）
    
    注意：如果要修改装备信息，请直接修改此函数，然后运行此脚本更新数据库
    装备信息应该包含：单位名称、装备类型、射程范围等
    """
    return [
        {
            "text": "轻步兵主要装备突击步枪，有效射程300-400米，最大射程800米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "轻步兵", "type": "equipment_info", "range": "300-400", "max_range": "800"}
        },
        {
            "text": "重装步兵主要装备重型机枪，有效射程400-500米，最大射程1000米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "重装步兵", "type": "equipment_info", "range": "400-500", "max_range": "1000"}
        },
        {
            "text": "机械化步兵主要装备轻型坦克，有效射程500-600米，最大射程1200米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "机械化步兵", "type": "equipment_info", "range": "500-600", "max_range": "1200"}
        },
        {
            "text": "坦克部队主要装备重型坦克，有效射程600-700米，最大射程1500米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "坦克", "type": "equipment_info", "range": "600-700", "max_range": "1500"}
        },
        {
            "text": "反坦克步兵主要装备反坦克导弹，有效射程700-800米，最大射程1800米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "反坦克步兵", "type": "equipment_info", "range": "700-800", "max_range": "1800"}
        },
        {
            "text": "自行火炮主要装备自行火炮，有效射程800-900米，最大射程2000米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "自行火炮", "type": "equipment_info", "range": "800-900", "max_range": "2000"}
        },
        {
            "text": "牵引火炮主要装备牵引火炮，有效射程900-1000米，最大射程2200米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "牵引火炮", "type": "equipment_info", "range": "900-1000", "max_range": "2200"}
        },
        {
            "text": "防空部队主要装备防空导弹，有效射程1000-1100米，最大射程2400米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "防空部队", "type": "equipment_info", "range": "1000-1100", "max_range": "2400"}
        },
        {
            "text": "狙击手主要装备狙击步枪，有效射程1100-1200米，最大射程2600米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "狙击手", "type": "equipment_info", "range": "1100-1200", "max_range": "2600"}
        },
        {
            "text": "特种部队主要装备特种武器，有效射程1200-1300米，最大射程2800米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "特种部队", "type": "equipment_info", "range": "1200-1300", "max_range": "2800"}
        },
        {
            "text": "装甲侦察单位主要装备装甲侦察车，有效射程1300-1400米，最大射程3000米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "装甲侦察单位", "type": "equipment_info", "range": "1300-1400", "max_range": "3000"}
        },
        {
            "text": "工兵部队主要装备工兵装备，有效射程1400-1500米，最大射程3200米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "工兵部队", "type": "equipment_info", "range": "1400-1500", "max_range": "3200"}
        },
        {
            "text": "后勤保障部队主要装备后勤保障装备，有效射程1500-1600米，最大射程3400米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "后勤保障部队", "type": "equipment_info", "range": "1500-1600", "max_range": "3400"}
        },
        {
            "text": "指挥单位主要装备指挥装备，有效射程1600-1700米，最大射程3600米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "指挥单位", "type": "equipment_info", "range": "1600-1700", "max_range": "3600"}
        },
        {
            "text": "无人机侦察控制单元主要装备无人机侦察控制装备，有效射程1700-1800米，最大射程3800米。在规划缓冲区距离时，应考虑射程因素以确保火力覆盖范围。",
            "metadata": {"unit": "无人机", "type": "equipment_info", "range": "1700-1800", "max_range": "3800"}
        }
    ]

if __name__ == "__main__":
    print("更新装备信息库...")
    from context_manager import ContextManager
    context_manager = ContextManager()
    count = context_manager.update_equipment_base()
    print(f"✓ 已更新 {count} 条装备信息")

