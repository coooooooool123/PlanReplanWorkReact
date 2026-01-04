import sys
from pathlib import Path
from typing import List, Dict

BASE_DIR = Path(__file__).parent
BASE_DIR_PARENT = BASE_DIR.parent

if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
if str(BASE_DIR_PARENT) not in sys.path:
    sys.path.insert(0, str(BASE_DIR_PARENT))

def get_military_units_rules() -> List[Dict]:
    """获取军事单位部署规则列表
    
    注意：如果要修改部署规则，请直接修改此函数，然后运行此脚本更新数据库
    """
    return [
        {
            "text": "步兵适合部署在中等高程区域，地形起伏不大，坡度以缓坡或平缓地形为主。部署地表类型可为树、灌木或草地，有利于隐蔽与灵活机动。配置位置与居民区及建筑保持100-300米缓冲距离，便于利用建筑边缘与自然掩体展开机动作战。",
            "metadata": {"unit": "步兵", "type": "deployment_rule"}
        },
        {
            "text": "重装步兵适合配置在较低至中等高程的防御阵地，坡度以平缓或中等坡度为宜。部署区域地表类型可为草地或裸地/稀疏植被，满足火力展开与阵地稳定需求。部署位置与居民区和建筑保持200-500米缓冲距离。",
            "metadata": {"unit": "重装步兵", "type": "deployment_rule"}
        },
        {
            "text": "机械化步兵更适合部署在中等高程的过渡地带，坡度为低至中等坡度，以保障装甲车辆通行。地表类型可选择草地或耕地。配置位置与居民区保持300-600米缓冲距离，兼顾机动效率与安全。",
            "metadata": {"unit": "机械化步兵", "type": "deployment_rule"}
        },
        {
            "text": "坦克部队适合部署在低至中等高程的开阔区域，整体坡度较为平缓。部署地表类型可为草地、耕地或裸地/稀疏植被，满足装甲单位机动与展开需求。配置位置与居民区和建筑保持500-1000米缓冲距离。",
            "metadata": {"unit": "坦克", "type": "deployment_rule"}
        },
        {
            "text": "反坦克步兵适合部署在中等至较高高程的伏击位置，坡度为中等坡度或局部陡坡。部署区域地表类型可为灌木、树或建筑边缘，利于隐蔽与形成俯射角度。与居民区保持150-400米缓冲距离。",
            "metadata": {"unit": "反坦克步兵", "type": "deployment_rule"}
        },
        {
            "text": "自行火炮通常部署在中等高程或背坡地形，坡度以缓坡为主，利于火炮稳定展开。部署地表类型可为草地或裸地/稀疏植被。配置位置与居民区保持600-1000米缓冲距离。",
            "metadata": {"unit": "自行火炮", "type": "deployment_rule"}
        },
        {
            "text": "牵引火炮适合配置在相对固定的中低高程阵地，地形坡度较小且稳定。部署区域地表类型可为草地或耕地。与居民区保持400-800米缓冲距离，确保持续火力覆盖。",
            "metadata": {"unit": "牵引火炮", "type": "deployment_rule"}
        },
        {
            "text": "防空部队适合部署在中等至较高高程位置，坡度为平缓或中等坡度。部署地表类型可为裸地/稀疏植被或草地，有利于雷达与火力视野展开。与居民区保持300-700米缓冲距离。",
            "metadata": {"unit": "防空", "type": "deployment_rule"}
        },
        {
            "text": "狙击手适合配置在较高高程制高点，局部坡度为中等或陡坡。部署区域地表类型可为树、灌木或建筑阴影区域，利于隐蔽观察与精确射击。与居民区保持50-200米缓冲距离。",
            "metadata": {"unit": "狙击手", "type": "deployment_rule"}
        },
        {
            "text": "特种部队适合部署在高程变化明显的复杂地形，坡度范围从缓坡到陡坡不等。部署地表类型可组合树、灌木、草地或湿地边缘，以提升渗透与隐蔽能力。与居民区保持200-500米缓冲距离。",
            "metadata": {"unit": "特种部队", "type": "deployment_rule"}
        },
        {
            "text": "装甲侦察单位适合部署在中低高程区域，整体坡度较为平缓，便于快速进出。部署地表类型可为草地或耕地。与居民区保持300-600米缓冲距离，以降低被发现概率。",
            "metadata": {"unit": "装甲侦察单位", "type": "deployment_rule"}
        },
        {
            "text": "工兵部队多部署在中低高程的关键节点区域，坡度相对平缓，便于工程作业展开。部署地表类型可为草地、耕地或建筑边缘区域。与居民区保持100-400米缓冲距离。",
            "metadata": {"unit": "工兵部队", "type": "deployment_rule"}
        },
        {
            "text": "后勤保障部队适合部署在低高程、安全区域，坡度平缓稳定，便于物资运输。部署地表类型可为建筑周边、草地或耕地。与居民区保持500-1000米缓冲距离。",
            "metadata": {"unit": "后勤保障部队", "type": "deployment_rule"}
        },
        {
            "text": "指挥单位适合部署在中等高程、地形相对隐蔽的位置，坡度为缓坡或平台地形。部署区域地表类型可为树、灌木或建筑掩护区。与居民区保持300-600米缓冲距离。",
            "metadata": {"unit": "指挥单位", "type": "deployment_rule"}
        },
        {
            "text": "无人机适合部署在中高高程区域，坡度较小，确保设备稳定运行。部署地表类型可为裸地/稀疏植被或低矮草地。与居民区保持400-800米缓冲距离。",
            "metadata": {"unit": "无人机", "type": "deployment_rule"}
        }
    ]

if __name__ == "__main__":
    print("更新知识库...")
    from context_manager import ContextManager
    context_manager = ContextManager()
    count = context_manager.update_knowledge_base()
    print(f"✓ 已更新 {count} 条军事单位部署规则")