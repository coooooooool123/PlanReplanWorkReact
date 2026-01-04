import sys
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from context_manager import ContextManager
from context.kag.schema import COLLECTION_TO_ENTITY_TYPE

def view_kag_entities():
    """查看KAG知识图谱中的所有实体"""
    print("=" * 60)
    print("KAG知识图谱实体查看")
    print("=" * 60)
    
    context_manager = ContextManager()
    kag = context_manager.kag
    
    entity_types = ["MilitaryUnit", "Equipment", "Task", "Execution"]
    
    total_count = 0
    for entity_type in entity_types:
        entities = kag.get_entities_by_type(entity_type)
        count = len(entities)
        total_count += count
        
        print(f"\n【{entity_type}】实体数量: {count}")
        if entities:
            print("-" * 60)
            for i, entity in enumerate(entities[:10], 1):
                print(f"  {i}. ID: {entity['id']}")
                props = entity.get('properties', {})
                if 'unit' in props:
                    print(f"     单位: {props['unit']}")
                if 'type' in props:
                    print(f"     类型: {props['type']}")
                text = entity.get('text', '')[:50]
                if text:
                    print(f"     内容: {text}...")
                print()
            
            if count > 10:
                print(f"  ... 还有 {count - 10} 个实体未显示")
            print()
    
    print(f"\n总计: {total_count} 个实体")
    print("=" * 60)

def view_kag_relations():
    """查看KAG知识图谱中的所有关系"""
    print("=" * 60)
    print("KAG知识图谱关系查看")
    print("=" * 60)
    
    context_manager = ContextManager()
    kag = context_manager.kag
    
    relations = kag.relations
    count = len(relations)
    
    print(f"\n关系总数: {count}")
    
    if relations:
        print("-" * 60)
        relation_types = {}
        for relation in relations:
            rel_type = relation.get('type', 'Unknown')
            if rel_type not in relation_types:
                relation_types[rel_type] = []
            relation_types[rel_type].append(relation)
        
        for rel_type, rels in relation_types.items():
            print(f"\n【{rel_type}】关系数量: {len(rels)}")
            for i, rel in enumerate(rels[:5], 1):
                print(f"  {i}. {rel['source']} -> {rel['target']}")
                if rel.get('properties'):
                    print(f"     属性: {rel['properties']}")
            if len(rels) > 5:
                print(f"  ... 还有 {len(rels) - 5} 个关系未显示")
    else:
        print("\n当前没有定义关系")
    
    print("\n" + "=" * 60)

def view_kag_summary():
    """查看KAG知识图谱摘要信息"""
    print("=" * 60)
    print("KAG知识图谱摘要")
    print("=" * 60)
    
    context_manager = ContextManager()
    kag = context_manager.kag
    
    print(f"\n知识图谱存储路径: {kag.kg_storage_path}")
    print(f"Embedding模型: {kag.embedding_model_name}")
    
    entity_types = ["MilitaryUnit", "Equipment", "Task", "Execution"]
    print("\n实体统计:")
    for entity_type in entity_types:
        entities = kag.get_entities_by_type(entity_type)
        print(f"  {entity_type}: {len(entities)} 个")
    
    print(f"\n关系总数: {len(kag.relations)}")
    print(f"实体总数: {len(kag.entities)}")
    print(f"Embedding向量数: {len(kag.entity_embeddings)}")
    
    print("\n" + "=" * 60)

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="查看KAG知识图谱内容")
    parser.add_argument("--entities", action="store_true", help="查看所有实体")
    parser.add_argument("--relations", action="store_true", help="查看所有关系")
    parser.add_argument("--summary", action="store_true", help="查看摘要信息")
    parser.add_argument("--all", action="store_true", help="查看所有信息")
    
    args = parser.parse_args()
    
    if args.all or (not args.entities and not args.relations and not args.summary):
        view_kag_summary()
        print("\n")
        view_kag_entities()
        print("\n")
        view_kag_relations()
    else:
        if args.summary:
            view_kag_summary()
        if args.entities:
            view_kag_entities()
        if args.relations:
            view_kag_relations()

