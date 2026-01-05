from fastapi import FastAPI, HTTPException, Body  # type: ignore
from fastapi.middleware.cors import CORSMiddleware  # type: ignore
from fastapi.responses import JSONResponse, FileResponse  # type: ignore
from pydantic import BaseModel, Field  # type: ignore
from typing import Dict, Any, Optional, List
import uvicorn  # type: ignore
import threading
from pathlib import Path
import sys
import logging
import os
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

BASE_DIR = Path(__file__).parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

try:
    from orchestrator import Orchestrator
    from context_manager import ContextManager
    from config import PATHS
except ImportError:
    BASE_DIR_PARENT = BASE_DIR.parent
    if str(BASE_DIR_PARENT) not in sys.path:
        sys.path.insert(0, str(BASE_DIR_PARENT))
    from orchestrator import Orchestrator
    from context_manager import ContextManager
    from config import PATHS

# 从KAG项目导入工具函数
try:
    kag_path = BASE_DIR / "KAG" / "kag" / "examples" / "MilitaryDeployment"
    if str(kag_path) not in sys.path:
        sys.path.insert(0, str(kag_path))
    from KAG.kag.examples.MilitaryDeployment.utils import COLLECTION_TO_ENTITY_TYPE
except ImportError:
    # 向后兼容
    COLLECTION_TO_ENTITY_TYPE = {
        "knowledge": "MilitaryUnit",
        "equipment": "Equipment"
    }

app = FastAPI(
    title="空地智能体API服务",
    description="空地计算智能体系统的API接口",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 延迟初始化，避免启动时阻塞
orchestrator = None
context_manager = None

def get_orchestrator():
    """获取Orchestrator实例（延迟初始化）"""
    global orchestrator
    if orchestrator is None:
        orchestrator = Orchestrator()
    return orchestrator

def get_context_manager():
    """获取ContextManager实例（延迟初始化）"""
    global context_manager
    if context_manager is None:
        context_manager = ContextManager()
    return context_manager

class TaskRequest(BaseModel):
    task: str = Field(..., description="任务描述")

class PlanRequest(BaseModel):
    task: str = Field(..., description="任务描述")

class ReplanRequest(BaseModel):
    plan: Dict[str, Any] = Field(..., description="原计划")
    feedback: str = Field(..., description="用户反馈意见")

class ExecuteRequest(BaseModel):
    plan: Dict[str, Any] = Field(..., description="执行计划")

class TaskResponse(BaseModel):
    success: bool
    result: Dict[str, Any]
    message: Optional[str] = None


@app.get("/")
async def root():
    return {
        "service": "空地智能体API服务",
        "version": "1.0.0",
        "endpoints": {
            "/api/plan": "POST - 生成计划",
            "/api/replan": "POST - 根据反馈重新规划",
            "/api/execute": "POST - 执行计划",
            "/api/task": "POST - 提交任务（完整流程）",
            "/api/tools": "GET - 获取工具列表",
            "/api/kg": "GET - 获取知识图谱信息（实体和关系统计）",
            "/api/kg/entities": "GET - 获取实体列表",
            "/api/kg/relations": "GET - 获取关系列表",
            "/api/kag/query": "POST - 使用KAG推理能力回答问题",
            "/api/knowledge/update": "PUT - 批量更新knowledge集合",
            "/api/results": "GET - 获取所有结果文件列表",
            "/api/results/{filename}": "GET - 获取特定结果文件内容",
            "/docs": "GET - API文档"
        }
    }

@app.post("/api/plan", response_model=TaskResponse)
async def generate_plan(request: PlanRequest):
    try:
        result = get_orchestrator().generate_plan(request.task)
        return TaskResponse(
            success=result.get("success", False),
            result=result,
            message="计划生成完成"
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"生成计划错误: {str(e)}")
        logger.error(error_detail)

        error_msg = str(e)
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."

        raise HTTPException(status_code=500, detail=f"生成计划时出错: {error_msg}")

@app.post("/api/replan", response_model=TaskResponse)
async def replan_with_feedback(request: ReplanRequest):
    try:
        import traceback
        import logging
        logger = logging.getLogger(__name__)

        logger.info(f"收到重新规划请求，反馈: {request.feedback[:100]}")

        result = get_orchestrator().replan_with_feedback(request.plan, request.feedback)

        logger.info("重新规划成功")
        return TaskResponse(
            success=result.get("success", False),
            result=result,
            message="重新规划完成"
        )
    except Exception as e:
        import traceback
        import logging
        logger = logging.getLogger(__name__)

        error_detail = traceback.format_exc()
        logger.error(f"重新规划错误: {str(e)}")
        logger.error(error_detail)

        error_msg = str(e)
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."

        raise HTTPException(
            status_code=500,
            detail=f"重新规划时出错: {error_msg}"
        )

@app.post("/api/execute", response_model=TaskResponse)
async def execute_plan(request: ExecuteRequest):
    try:
        result = get_orchestrator().execute_plan(request.plan)
        return TaskResponse(
            success=result.get("success", False),
            result=result,
            message="执行完成" if result.get("success") else "执行失败"
        )
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        logger.error(f"执行计划错误: {str(e)}")
        logger.error(error_detail)

        error_msg = str(e)
        if len(error_msg) > 500:
            error_msg = error_msg[:500] + "..."

        raise HTTPException(status_code=500, detail=f"执行计划时出错: {error_msg}")

@app.post("/api/task", response_model=TaskResponse)
async def submit_task(request: TaskRequest):
    try:
        result = get_orchestrator().execute_task(request.task)
        return TaskResponse(
            success=result.get("success", False),
            result=result,
            message="任务执行完成" if result.get("success") else "任务执行失败"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"执行任务时出错: {str(e)}")

@app.get("/api/tools")
async def get_tools():
    tools = {}
    for name, tool in get_orchestrator().work_agent.tools.items():
        tools[name] = {
            "name": tool.name,
            "description": tool.description,
            "parameters": tool.parameters
        }
    return {"tools": tools}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/kg")
async def get_kg_info():
    """获取知识图谱基本信息（实体和关系统计）"""
    try:
        kg_data = get_context_manager().get_kg_data()
        
        return {
            "success": True,
            "entity_count": kg_data.get("entity_count", 0),
            "relation_count": kg_data.get("relation_count", 0),
            "entities": kg_data.get("entities", []),
            "relations": kg_data.get("relations", [])
        }
    except Exception as e:
        logger.error(f"获取知识图谱信息失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取知识图谱信息失败: {str(e)}")

@app.get("/api/kg/entities")
async def get_kg_entities(entity_type: str = None, limit: int = 100):
    """获取知识图谱实体列表"""
    try:
        kg_data = get_context_manager().get_kg_data()
        entities = kg_data.get("entities", [])
        
        # 如果指定了实体类型，进行过滤
        if entity_type:
            entities = [e for e in entities if e.get("type") == entity_type]
        
        # 限制返回数量
        entities = entities[:limit]
        
        return {
            "success": True,
            "count": len(entities),
            "entities": entities
        }
    except Exception as e:
        logger.error(f"获取知识图谱实体失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取实体失败: {str(e)}")

@app.get("/api/kg/relations")
async def get_kg_relations(relation_type: str = None, limit: int = 100):
    """获取知识图谱关系列表"""
    try:
        kg_data = get_context_manager().get_kg_data()
        relations = kg_data.get("relations", [])
        
        # 如果指定了关系类型，进行过滤
        if relation_type:
            relations = [r for r in relations if r.get("type") == relation_type]
        
        # 限制返回数量
        relations = relations[:limit]
        
        return {
            "success": True,
            "count": len(relations),
            "relations": relations
        }
    except Exception as e:
        logger.error(f"获取知识图谱关系失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取关系失败: {str(e)}")

@app.post("/api/kg/entities")
async def add_kg_entity(request: Dict = Body(...)):
    """添加实体到知识图谱（已废弃，请使用KAG开发者模式构建知识库）"""
    raise HTTPException(
        status_code=410,
        detail="此接口已废弃。请使用KAG开发者模式来构建和更新知识库。"
    )

@app.delete("/api/kg/entities/{entity_id}")
async def delete_kg_entity(entity_id: str):
    """删除知识图谱中的实体（已废弃，请使用KAG开发者模式管理知识库）"""
    raise HTTPException(
        status_code=410,
        detail="此接口已废弃。请使用KAG开发者模式来管理知识库。"
    )


@app.put("/api/knowledge/update")
async def update_knowledge_base():
    """
    批量更新knowledge集合（已废弃）
    
    注意：此接口已废弃。请使用KAG开发者模式来构建和更新知识库：
    1. 将文本数据文件放置在 KAG/kag/examples/MilitaryDeployment/builder/data/ 目录下
    2. 运行 KAG/kag/examples/MilitaryDeployment/builder/indexer.py 构建知识库
    """
    raise HTTPException(
        status_code=410, 
        detail="此接口已废弃。请使用KAG开发者模式来构建知识库。"
    )

@app.post("/api/kag/query")
async def kag_query(request: Dict = Body(...)):
    """
    使用KAG推理能力回答问题
    
    请求体：
    {
        "question": "轻步兵应该部署在什么位置？"
    }
    """
    try:
        question = request.get("question", "")
        if not question:
            raise HTTPException(status_code=400, detail="问题不能为空")
        
        context_manager = get_context_manager()
        result = context_manager.query_with_kag_reasoning(question)
        
        return {
            "success": True,
            "answer": result.get("answer", ""),
            "references": result.get("references", []),
            "method": result.get("method", "kag_reasoning")
        }
    except Exception as e:
        logger.error(f"KAG推理查询失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"KAG推理查询失败: {str(e)}")

@app.get("/api/results")
async def get_results_list():
    """获取所有结果文件列表"""
    try:
        result_dir = PATHS["result_dir"]
        if not result_dir.exists():
            return {
                "success": True,
                "results": [],
                "count": 0
            }

        result_files = list(result_dir.glob("*.geojson"))
        result_files.sort(key=lambda x: x.stat().st_mtime, reverse=True)

        results = []
        for file_path in result_files:
            stat = file_path.stat()
            results.append({
                "filename": file_path.name,
                "size": stat.st_size,
                "modified_time": stat.st_mtime,
                "modified_time_str": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(stat.st_mtime))
            })

        return {
            "success": True,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        logger.error(f"获取结果文件列表失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取结果文件列表失败: {str(e)}")

@app.get("/api/results/{filename}")
async def get_result_file(filename: str):
    """获取特定结果文件内容（GeoJSON）"""
    try:
        result_dir = PATHS["result_dir"]
        file_path = result_dir / filename

        if not file_path.resolve().is_relative_to(result_dir.resolve()):
            raise HTTPException(status_code=403, detail="访问被拒绝")

        if not file_path.exists():
            raise HTTPException(status_code=404, detail=f"文件 {filename} 不存在")

        if not filename.endswith('.geojson'):
            raise HTTPException(status_code=400, detail="只支持GeoJSON文件")

        return FileResponse(
            path=str(file_path),
            media_type="application/geo+json",
            filename=filename
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取结果文件失败: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"获取结果文件失败: {str(e)}")

def run_api_server(port: int = 8000):
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")