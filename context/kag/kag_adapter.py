import json
import logging
import time
from typing import Dict, List, Optional
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer
import requests

logger = logging.getLogger(__name__)

class KAGAdapter:
    """OpenSPG KAG适配器，提供知识图谱构建和查询接口"""
    
    def __init__(self, embedding_model_name: str, llm_config: Dict, kag_config: Dict, kg_storage_path: str):
        self.embedding_model_name = embedding_model_name
        self.llm_config = llm_config
        self.kag_config = kag_config
        self.kg_storage_path = Path(kg_storage_path)
        self.kg_storage_path.mkdir(parents=True, exist_ok=True)
        
        self.embedding_model = SentenceTransformer(embedding_model_name)
        
        self.entities = {}
        self.relations = []
        self.entity_embeddings = {}
        
        self._load_kg()
    
    def _load_kg(self):
        """从文件加载知识图谱"""
        kg_file = self.kg_storage_path / "kg.json"
        if kg_file.exists():
            try:
                with open(kg_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.entities = data.get("entities", {})
                    self.relations = data.get("relations", [])
                    self.entity_embeddings = data.get("embeddings", {})
                logger.info(f"已加载知识图谱: {len(self.entities)} 个实体, {len(self.relations)} 个关系")
            except Exception as e:
                logger.warning(f"加载知识图谱失败: {e}，将创建新的知识图谱")
                self.entities = {}
                self.relations = []
                self.entity_embeddings = {}
        else:
            logger.info("知识图谱文件不存在，将创建新的知识图谱")
    
    def _save_kg(self):
        """保存知识图谱到文件"""
        kg_file = self.kg_storage_path / "kg.json"
        try:
            data = {
                "entities": self.entities,
                "relations": self.relations,
                "embeddings": self.entity_embeddings
            }
            with open(kg_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f"已保存知识图谱: {len(self.entities)} 个实体, {len(self.relations)} 个关系")
        except Exception as e:
            logger.error(f"保存知识图谱失败: {e}")
            raise
    
    def _embed_text(self, text: str, prefix: str = "passage") -> List[float]:
        """对文本进行embedding"""
        prefixed_text = f"{prefix}: {text}"
        return self.embedding_model.encode(prefixed_text).tolist()
    
    def add_entity(self, entity_type: str, entity_id: str, properties: Dict, text: str = None):
        """添加实体到知识图谱"""
        if text is None:
            text = properties.get("text", "")
        
        entity = {
            "id": entity_id,
            "type": entity_type,
            "properties": properties,
            "text": text,
            "created_at": int(time.time() * 1000)
        }
        
        self.entities[entity_id] = entity
        
        embedding = self._embed_text(text, "passage")
        self.entity_embeddings[entity_id] = embedding
        
        self._save_kg()
        logger.debug(f"已添加实体: {entity_type}/{entity_id}")
    
    def add_relation(self, relation_type: str, source_id: str, target_id: str, properties: Dict = None):
        """添加关系到知识图谱"""
        if properties is None:
            properties = {}
        
        relation = {
            "type": relation_type,
            "source": source_id,
            "target": target_id,
            "properties": properties,
            "created_at": int(time.time() * 1000)
        }
        
        self.relations.append(relation)
        self._save_kg()
        logger.debug(f"已添加关系: {relation_type} ({source_id} -> {target_id})")
    
    def query(self, query_text: str, entity_types: List[str] = None, top_k: int = 5, 
              max_distance: float = 0.35, use_llm_reasoning: bool = False) -> List[Dict]:
        """查询知识图谱
        
        Args:
            query_text: 查询文本
            entity_types: 限制查询的实体类型列表
            top_k: 返回top_k个结果
            max_distance: 最大距离阈值
            use_llm_reasoning: 是否使用LLM进行逻辑推理
        
        Returns:
            查询结果列表，每个结果包含text、metadata、distance等字段
        """
        query_embedding = self._embed_text(query_text, "query")
        
        candidates = []
        
        for entity_id, entity in self.entities.items():
            if entity_types and entity["type"] not in entity_types:
                continue
            
            entity_embedding = self.entity_embeddings.get(entity_id)
            if entity_embedding is None:
                continue
            
            distance = self._cosine_distance(query_embedding, entity_embedding)
            
            if distance <= max_distance:
                candidates.append({
                    "entity_id": entity_id,
                    "entity_type": entity["type"],
                    "text": entity.get("text", ""),
                    "metadata": entity.get("properties", {}),
                    "distance": distance,
                    "semantic_score": 1.0 - distance
                })
        
        candidates.sort(key=lambda x: x["distance"])
        
        if use_llm_reasoning and candidates:
            candidates = self._llm_rerank(query_text, candidates)
        
        results = candidates[:top_k]
        
        for result in results:
            result["keyword_score"] = 0.0
            result["metadata_boost"] = 0.0
            result["final_score"] = result.get("semantic_score", 1.0 - result["distance"])
            result["collection"] = result.get("entity_type", "unknown")
        
        return results
    
    def _cosine_distance(self, vec1: List[float], vec2: List[float]) -> float:
        """计算余弦距离"""
        vec1 = np.array(vec1)
        vec2 = np.array(vec2)
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        if norm1 == 0 or norm2 == 0:
            return 1.0
        cosine_sim = dot_product / (norm1 * norm2)
        return 1.0 - cosine_sim
    
    def _llm_rerank(self, query: str, candidates: List[Dict]) -> List[Dict]:
        """使用LLM对候选结果进行重排序"""
        try:
            prompt = f"""根据以下查询，对候选结果进行排序，返回最相关的top {len(candidates)}个结果。

查询: {query}

候选结果:
{json.dumps([{"text": c["text"], "metadata": c["metadata"]} for c in candidates], ensure_ascii=False, indent=2)}

请返回JSON格式的排序结果，格式: [{{"index": 0, "relevance_score": 0.9}}]
"""
            
            response = requests.post(
                self.llm_config["api_endpoint"],
                json={
                    "model": self.llm_config["model"],
                    "messages": [
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3,
                    "max_tokens": 1000
                },
                timeout=self.llm_config.get("timeout", 30)
            )
            
            if response.status_code == 200:
                result = response.json()
                content = result.get("choices", [{}])[0].get("message", {}).get("content", "")
                try:
                    rerank_scores = json.loads(content)
                    if isinstance(rerank_scores, list):
                        score_map = {item["index"]: item.get("relevance_score", 0.5) for item in rerank_scores}
                        for i, candidate in enumerate(candidates):
                            if i in score_map:
                                candidate["llm_score"] = score_map[i]
                                candidate["final_score"] = (candidate["semantic_score"] * 0.7 + score_map[i] * 0.3)
                        candidates.sort(key=lambda x: x.get("final_score", x["semantic_score"]), reverse=True)
                except:
                    pass
        except Exception as e:
            logger.warning(f"LLM重排序失败: {e}，使用原始排序")
        
        return candidates
    
    def delete_entity(self, entity_id: str):
        """删除实体"""
        if entity_id in self.entities:
            del self.entities[entity_id]
        if entity_id in self.entity_embeddings:
            del self.entity_embeddings[entity_id]
        
        self.relations = [r for r in self.relations if r["source"] != entity_id and r["target"] != entity_id]
        
        self._save_kg()
        logger.debug(f"已删除实体: {entity_id}")
    
    def get_entity(self, entity_id: str) -> Optional[Dict]:
        """获取实体"""
        return self.entities.get(entity_id)
    
    def get_entities_by_type(self, entity_type: str) -> List[Dict]:
        """根据类型获取所有实体"""
        entities = []
        for entity_id, entity in self.entities.items():
            if entity.get("type") == entity_type:
                entities.append({
                    "id": entity_id,
                    "type": entity["type"],
                    "properties": entity.get("properties", {}),
                    "text": entity.get("text", "")
                })
        return entities

