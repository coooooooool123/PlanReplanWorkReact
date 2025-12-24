import json
import os
from pathlib import Path
from typing import Dict, List, Optional
import chromadb
from chromadb.config import Settings
from sentence_transformers import SentenceTransformer
from config import PATHS, CHROMA_CONFIG, EMBEDDING_MODEL, RAG_CONFIG


class ContextManager:
    def __init__(self):
        self.static_context: Dict[str, str] = {}
        self.embedding_model = SentenceTransformer(EMBEDDING_MODEL)
        self._init_chroma()
        self._load_static_context()
    
    def _init_chroma(self):
        os.makedirs(PATHS["chroma_db_dir"], exist_ok=True)
        self.chroma_client = chromadb.PersistentClient(
            path=PATHS["chroma_db_dir"],
            settings=Settings(anonymized_telemetry=False)
        )
        self._ensure_collections()
    
    def _ensure_collections(self):
        for collection_name in [CHROMA_CONFIG["collection_tasks"], 
                                CHROMA_CONFIG["collection_executions"],
                                CHROMA_CONFIG["collection_knowledge"]]:
            try:
                self.chroma_client.get_collection(collection_name)
            except:
                self.chroma_client.create_collection(collection_name)
    
    def _load_static_context(self):
        static_file = PATHS["static_context_dir"] / "prompts.json"
        if static_file.exists():
            with open(static_file, "r", encoding="utf-8") as f:
                self.static_context = json.load(f)
        else:
            self._init_default_prompts()
            self._save_static_context()
        
        self._init_rag_data()
    
    def _init_default_prompts(self):
        self.static_context = {
            "plan_prompt": """你是一个任务规划助手，负责将用户的任务分解为可执行的步骤。

你的职责：
1. 理解用户任务的目标和要求
2. 将任务分解为清晰的步骤
3. 不涉及具体工具，只描述需要做什么

可用工具类型：
- buffer_filter: 缓冲区筛选（根据建筑和道路距离筛选）
- elevation_filter: 高程筛选（根据高程范围筛选）
- slope_filter: 坡度筛选（根据坡度范围筛选）

输出格式（JSON）：
{
    "task": "用户原始任务",
    "goal": "任务目标描述",
    "steps": [
        {"step_id": 1, "description": "步骤描述", "type": "buffer/elevation/slope"},
        ...
    ],
    "estimated_steps": 步骤数量
}

注意：只描述任务目标，不指定具体工具和参数。""",
            
            "replan_prompt": """你是一个重新规划助手，当执行失败时需要调整计划。

你的职责：
1. 分析执行失败的原因
2. 根据可用工具重新规划
3. 生成包含具体工具和参数的详细计划

可用工具：
{tools_info}

输出格式（JSON）：
{
    "task": "用户原始任务",
    "goal": "调整后的任务目标",
    "steps": [
        {"step_id": 1, "tool": "buffer_filter_tool", "params": {"buffer_distance": 500}},
        {"step_id": 2, "tool": "elevation_filter_tool", "params": {"input_geojson_path": "...", "min_elev": 100, "max_elev": 500}},
        ...
    ],
    "required_tools": ["buffer_filter_tool", "elevation_filter_tool"],
    "reason": "重新规划的原因"
}""",
            
            "work_prompt": """你是一个执行助手，负责根据计划步骤执行具体操作。

你的职责：
1. 分析步骤描述，理解需要做什么
2. 选择合适的工具和参数
3. 返回执行动作

可用工具：
- buffer_filter_tool: 缓冲区筛选工具
  参数: buffer_distance (必需), utm_crs (可选)
  
- elevation_filter_tool: 高程筛选工具
  参数: input_geojson_path (必需), min_elev (可选), max_elev (可选)
  
- slope_filter_tool: 坡度筛选工具
  参数: input_geojson_path (必需), min_slope (可选), max_slope (可选)

输出格式（JSON）：
{
    "tool": "工具名称",
    "params": {
        "参数名": "参数值"
    }
}

注意：
- buffer_filter_tool的输出可以作为elevation_filter_tool和slope_filter_tool的input_geojson_path
- 如果步骤描述包含"距离"、"缓冲区"等关键词，使用buffer_filter_tool
- 如果步骤描述包含"高程"、"海拔"等关键词，使用elevation_filter_tool
- 如果步骤描述包含"坡度"、"倾斜"等关键词，使用slope_filter_tool""",
            
            "system_prompt": """你是一个专业的空地分析智能体，专门处理地理空间数据的筛选和分析任务。

你的能力包括：
1. 理解用户的地理空间分析需求
2. 规划合理的分析流程
3. 执行地理空间筛选操作
4. 根据执行结果调整策略

工作原则：
- 仔细分析用户需求
- 合理规划执行步骤
- 准确选择工具和参数
- 及时处理错误和异常"""
        }
    
    def _save_static_context(self):
        os.makedirs(PATHS["static_context_dir"], exist_ok=True)
        static_file = PATHS["static_context_dir"] / "prompts.json"
        with open(static_file, "w", encoding="utf-8") as f:
            json.dump(self.static_context, f, ensure_ascii=False, indent=2)
    
    def save_static_context(self, context_type: str, content: str):
        self.static_context[context_type] = content
        self._save_static_context()
    
    def load_static_context(self, context_type: str) -> str:
        return self.static_context.get(context_type, "")
    
    def add_to_rag(self, text: str, metadata: Dict, collection: str = "default"):
        if collection == "default":
            collection = CHROMA_CONFIG["collection_executions"]
        
        coll = self.chroma_client.get_collection(collection)
        embedding = self.embedding_model.encode(text).tolist()
        
        existing = coll.get()
        new_id = f"{collection}_{len(existing['ids']) if existing['ids'] else 0}"
        
        coll.add(
            embeddings=[embedding],
            documents=[text],
            metadatas=[metadata],
            ids=[new_id]
        )
    
    def load_dynamic_context(self, query: str, top_k: int = None, collection: str = "default") -> List[Dict]:
        if top_k is None:
            top_k = RAG_CONFIG["top_k"]
        
        if collection == "default":
            collection = CHROMA_CONFIG["collection_executions"]
        
        coll = self.chroma_client.get_collection(collection)
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = coll.query(
            query_embeddings=[query_embedding],
            n_results=top_k
        )
        
        contexts = []
        if results["documents"] and len(results["documents"][0]) > 0:
            for i, doc in enumerate(results["documents"][0]):
                contexts.append({
                    "text": doc,
                    "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                    "distance": results["distances"][0][i] if results["distances"] else None
                })
        
        return contexts
    
    def save_context(self, context_id: str, data: Dict):
        context_file = PATHS["context_dir"] / f"{context_id}.json"
        with open(context_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    
    def load_context(self, context_id: str) -> Optional[Dict]:
        context_file = PATHS["context_dir"] / f"{context_id}.json"
        if context_file.exists():
            with open(context_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return None
    
    def compress_context(self, context: Dict, max_tokens: int = 2000) -> Dict:
        if len(str(context)) < max_tokens:
            return context
        
        compressed = {
            "summary": str(context)[:max_tokens],
            "full_length": len(str(context))
        }
        return compressed
    
    def _get_military_units_rules(self) -> List[Dict]:
        """获取军事单位部署规则列表
        
        注意：如果要修改部署规则，请修改此方法，然后运行 update_knowledge.py 更新数据库
        """
        return [
                {
                    "text": "轻步兵适合部署在中等高程区域，地形起伏不大，坡度以缓坡或平缓地形为主。配置位置应与居民区保持100-300米的缓冲距离，既能避免直接暴露于民用区域，又便于利用建筑边缘与自然掩体展开机动作战。",
                    "metadata": {"unit": "轻步兵", "type": "deployment_rule"}
                },
                {
                    "text": "重装步兵适合配置在较低至中等高程的防御阵地，坡度不宜过大，以平缓或中等坡度为宜。部署位置通常与居民区保持200-500米缓冲距离，确保火力展开空间，同时避免对居民区造成直接影响。",
                    "metadata": {"unit": "重装步兵", "type": "deployment_rule"}
                },
                {
                    "text": "机械化步兵更适合部署在中等高程的过渡地带，坡度应保持在低至中等坡度范围，以保障装甲车辆通行。配置位置与居民区的缓冲距离建议控制在300-600米之间，兼顾快速机动与战场安全。",
                    "metadata": {"unit": "机械化步兵", "type": "deployment_rule"}
                },
                {
                    "text": "坦克部队适合部署在低至中等高程的开阔区域，整体坡度应尽量平缓，避免复杂起伏影响机动。配置位置通常要求与居民区保持500-1000米缓冲距离，减少城市地形对装甲单位的限制。",
                    "metadata": {"unit": "坦克部队", "type": "deployment_rule"}
                },
                {
                    "text": "反坦克步兵适合部署在中等至较高高程的伏击位置，坡度可为中等坡度或局部陡坡，便于形成俯射角度。与居民区之间应保持150-400米缓冲距离，既能隐蔽部署，又不靠近高密度民用区域。",
                    "metadata": {"unit": "反坦克步兵", "type": "deployment_rule"}
                },
                {
                    "text": "自行火炮通常部署在中等高程或背坡地形，坡度以缓坡为主，利于火炮稳定展开。配置位置与居民区应保持600-1000米缓冲距离，以确保安全并减少反侦察风险。",
                    "metadata": {"unit": "自行火炮", "type": "deployment_rule"}
                },
                {
                    "text": "牵引火炮适合配置在相对固定的中低高程阵地，地形坡度应较小且稳定。与居民区的缓冲距离一般控制在400-800米之间，确保持续火力覆盖而不干扰民用区域。",
                    "metadata": {"unit": "牵引火炮", "type": "deployment_rule"}
                },
                {
                    "text": "防空部队适合部署在中等至较高高程位置，坡度以平缓或中等坡度为宜，保证雷达与火力视野。部署点与居民区的缓冲距离建议为300-700米，既保证空域覆盖，又降低暴露风险。",
                    "metadata": {"unit": "防空部队", "type": "deployment_rule"}
                },
                {
                    "text": "狙击手适合配置在较高高程制高点，局部坡度可为中等或陡坡，形成良好射界。配置位置通常与居民区保持50-200米缓冲距离，便于利用城市边缘地形进行隐蔽观察。",
                    "metadata": {"unit": "狙击手", "type": "deployment_rule"}
                },
                {
                    "text": "特种部队适合部署在高程变化明显的复杂地形，坡度可从缓坡到陡坡不等，以增加行动隐蔽性。与居民区之间宜保持200-500米缓冲距离，确保渗透行动不暴露于高密度区域。",
                    "metadata": {"unit": "特种部队", "type": "deployment_rule"}
                },
                {
                    "text": "装甲侦察单位适合部署在中低高程区域，整体坡度应较为平缓，便于快速进出。配置位置与居民区的缓冲距离一般为300-600米，以降低被发现概率。",
                    "metadata": {"unit": "装甲侦察单位", "type": "deployment_rule"}
                },
                {
                    "text": "工兵部队多部署在中低高程的关键节点区域，坡度应相对平缓，方便工程作业。与居民区保持100-400米缓冲距离，既便于保障基础设施，又避免过度靠近居民区。",
                    "metadata": {"unit": "工兵部队", "type": "deployment_rule"}
                },
                {
                    "text": "后勤保障部队适合部署在低高程、安全区域，坡度应平缓稳定，便于物资运输。配置位置通常与居民区保持500-1000米缓冲距离，减少战场干扰风险。",
                    "metadata": {"unit": "后勤保障部队", "type": "deployment_rule"}
                },
                {
                    "text": "指挥单位适合部署在中等高程、地形相对隐蔽的位置，坡度以缓坡或平台地形为宜。与居民区之间的缓冲距离通常控制在300-600米，在安全与通信效率之间取得平衡。",
                    "metadata": {"unit": "指挥单位", "type": "deployment_rule"}
                },
                {
                    "text": "无人机侦察控制单元适合部署在中高高程区域，坡度应较小，确保设备稳定运行。与居民区保持400-800米缓冲距离，避免电磁与安全干扰。",
                    "metadata": {"unit": "无人机侦察控制单元", "type": "deployment_rule"}
                }
            ]
    
    def update_knowledge_base(self):
        """更新knowledge集合，清除旧数据并重新初始化军事单位部署规则"""
        try:
            knowledge_coll = self.chroma_client.get_collection(CHROMA_CONFIG["collection_knowledge"])
            existing_ids = knowledge_coll.get()["ids"]
            
            if existing_ids:
                knowledge_coll.delete(ids=existing_ids)
            
            military_units = self._get_military_units_rules()
            
            for i, unit in enumerate(military_units):
                embedding = self.embedding_model.encode(unit["text"]).tolist()
                knowledge_coll.add(
                    embeddings=[embedding],
                    documents=[unit["text"]],
                    metadatas=[unit["metadata"]],
                    ids=[f"knowledge_{i}"]
                )
            
            return len(military_units)
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise Exception(f"更新知识库失败: {str(e)}")
    
    def _init_rag_data(self):
        knowledge_coll = self.chroma_client.get_collection(CHROMA_CONFIG["collection_knowledge"])
        executions_coll = self.chroma_client.get_collection(CHROMA_CONFIG["collection_executions"])
        
        existing_knowledge = knowledge_coll.get()
        existing_knowledge_ids = existing_knowledge["ids"]
        
        should_init = len(existing_knowledge_ids) == 0
        
        if not should_init:
            metadatas = existing_knowledge.get("metadatas", [])
            has_military_units = any(
                meta.get("type") == "deployment_rule" and "unit" in meta 
                for meta in metadatas if meta
            )
            if not has_military_units:
                should_init = True
                knowledge_coll.delete(ids=existing_knowledge_ids)
        
        if should_init:
            military_units = self._get_military_units_rules()
            
            for i, unit in enumerate(military_units):
                embedding = self.embedding_model.encode(unit["text"]).tolist()
                knowledge_coll.add(
                    embeddings=[embedding],
                    documents=[unit["text"]],
                    metadatas=[unit["metadata"]],
                    ids=[f"knowledge_{i}"]
                )
            print(f"已初始化 {len(military_units)} 条军事单位部署规则到knowledge集合")
        
        if len(executions_coll.get()["ids"]) == 0:
            sample_executions = [
                {
                    "text": "使用buffer_filter_tool，设置buffer_distance为500米，成功筛选出空地区域",
                    "metadata": {"tool": "buffer_filter_tool", "success": True}
                },
                {
                    "text": "使用elevation_filter_tool，设置min_elev为100，max_elev为500，成功筛选出符合高程要求的区域",
                    "metadata": {"tool": "elevation_filter_tool", "success": True}
                },
                {
                    "text": "先使用buffer_filter_tool筛选空地，然后使用elevation_filter_tool进一步筛选高程",
                    "metadata": {"tool": "chain", "success": True}
                }
            ]
            
            for i, execution in enumerate(sample_executions):
                embedding = self.embedding_model.encode(execution["text"]).tolist()
                executions_coll.add(
                    embeddings=[embedding],
                    documents=[execution["text"]],
                    metadatas=[execution["metadata"]],
                    ids=[f"execution_{i}"]
                )
