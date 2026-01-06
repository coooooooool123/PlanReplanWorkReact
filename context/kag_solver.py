"""
KAG推理问答接口
集成KAG开发者模式的推理能力到外层系统
"""
import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

class KAGSolver:
    """KAG推理问答接口"""
    
    def __init__(self, project_path: Optional[str] = None):
        """
        初始化KAG推理器
        
        Args:
            project_path: KAG项目路径，默认为KAG/kag/examples/MilitaryDeployment
        """
        if project_path is None:
            # 默认使用MilitaryDeployment项目
            base_dir = Path(__file__).parent.parent
            self.project_path = base_dir / "KAG" / "kag" / "examples" / "MilitaryDeployment"
        else:
            self.project_path = Path(project_path)
        
        self._solver = None
        self._initialized = False
    
    def _init_solver(self):
        """延迟初始化solver，避免导入错误"""
        if self._initialized:
            return
        
        try:
            # 添加KAG路径
            kag_path = self.project_path.parent.parent.parent.parent
            if str(kag_path) not in sys.path:
                sys.path.insert(0, str(kag_path))
            
            # 导入KAG模块
            from kag.common.registry import import_modules_from_path
            from kag.common.conf import KAG_CONFIG
            from kag.solver.main_solver import SolverPipeline
            
            # 设置工作目录为项目目录
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(str(self.project_path))
                
                # 导入项目模块
                import_modules_from_path(".")
                
                # 从配置创建solver
                self._solver = SolverPipeline.from_config(
                    KAG_CONFIG.all_config["kag_solver_pipeline"]
                )
                
                self._initialized = True
                logger.info("KAG推理器初始化成功")
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"KAG推理器初始化失败: {e}", exc_info=True)
            self._solver = None
            self._initialized = True  # 标记为已初始化，避免重复尝试
    
    def query(self, question: str) -> Dict:
        """
        使用KAG推理引擎回答问题
        
        Args:
            question: 用户问题
            
        Returns:
            包含答案和引用的字典
        """
        self._init_solver()
        
        if self._solver is None:
            logger.warning("KAG推理器未初始化，返回空结果")
            return {
                "answer": "",
                "references": [],
                "error": "KAG推理器未初始化"
            }
        
        try:
            result = self._solver.invoke(question)
            
            # 标准化返回格式
            return {
                "answer": result.get("answer", ""),
                "references": result.get("references", []),
                "raw_result": result
            }
        except Exception as e:
            logger.error(f"KAG推理查询失败: {e}", exc_info=True)
            return {
                "answer": "",
                "references": [],
                "error": str(e)
            }
    
    def query_with_context(self, question: str, context: Optional[List[Dict]] = None) -> Dict:
        """
        带上下文的KAG推理查询
        
        Args:
            question: 用户问题
            context: 额外的上下文信息（可选）
            
        Returns:
            包含答案和引用的字典
        """
        # 如果有上下文，可以将其整合到问题中
        if context:
            context_text = "\n".join([ctx.get("text", "") for ctx in context])
            enhanced_question = f"{question}\n\n相关上下文：\n{context_text}"
        else:
            enhanced_question = question
        
        return self.query(enhanced_question)
    
    def get_kg_data(self) -> Dict:
        """
        获取知识图谱数据（实体和关系）
        
        Returns:
            包含实体和关系的字典
        """
        try:
            # 使用KAG的graph API获取知识图谱数据
            kag_path = self.project_path.parent.parent.parent.parent
            if str(kag_path) not in sys.path:
                sys.path.insert(0, str(kag_path))
            
            from knext.graph.client import GraphClient
            from knext.schema.client import SchemaClient
            from kag.common.conf import KAG_CONFIG
            
            import os
            original_cwd = os.getcwd()
            try:
                os.chdir(str(self.project_path))
                
                # 获取项目配置
                project_config = KAG_CONFIG.all_config.get("project", {})
                host_addr = project_config.get("host_addr", "http://127.0.0.1:8887")
                namespace = project_config.get("namespace", "MilitaryDeploy")
                
                # 创建客户端
                graph_client = GraphClient(host_addr=host_addr)
                schema_client = SchemaClient(host_addr=host_addr)
                
                # 查询所有实体
                entities = []
                relations = []
                
                try:
                    # 获取所有实体类型
                    entity_types = schema_client.list_entity_type(namespace=namespace)
                    
                    for entity_type_info in entity_types:
                        entity_type_name = entity_type_info.get("name", "")
                        if not entity_type_name:
                            continue
                        
                        # 查询该类型的所有实体
                        try:
                            entity_list = graph_client.query_entity(
                                namespace=namespace,
                                entity_type=entity_type_name,
                                limit=1000
                            )
                            if entity_list:
                                entities.extend(entity_list)
                        except Exception as e:
                            logger.debug(f"查询实体类型 {entity_type_name} 失败: {e}")
                    
                    # 查询所有关系
                    try:
                        relation_types = schema_client.list_relation_type(namespace=namespace)
                        for relation_type_info in relation_types:
                            relation_type_name = relation_type_info.get("name", "")
                            if not relation_type_name:
                                continue
                            
                            try:
                                relation_list = graph_client.query_relation(
                                    namespace=namespace,
                                    relation_type=relation_type_name,
                                    limit=1000
                                )
                                if relation_list:
                                    relations.extend(relation_list)
                            except Exception as e:
                                logger.debug(f"查询关系类型 {relation_type_name} 失败: {e}")
                    except Exception as e:
                        logger.warning(f"查询关系失败: {e}")
                        
                except Exception as e:
                    logger.warning(f"从KAG获取知识图谱数据失败: {e}，返回空数据")
                
                return {
                    "entities": entities,
                    "relations": relations,
                    "entity_count": len(entities),
                    "relation_count": len(relations)
                }
            finally:
                os.chdir(original_cwd)
                
        except Exception as e:
            logger.error(f"获取知识图谱数据失败: {e}", exc_info=True)
            return {
                "entities": [],
                "relations": [],
                "entity_count": 0,
                "relation_count": 0,
                "error": str(e)
            }

