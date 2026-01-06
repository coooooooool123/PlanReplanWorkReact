"""
LLM相关工具函数
"""
import json
import re
import logging
import requests
from typing import Dict, List
from config import LLM_CONFIG

logger = logging.getLogger(__name__)


def call_llm(messages: List[Dict], timeout: int = None) -> str:
    """
    调用LLM API
    
    Args:
        messages: 消息列表
        timeout: 超时时间（秒），默认使用配置中的timeout
        
    Returns:
        LLM响应文本
        
    Raises:
        requests.exceptions.RequestException: API调用失败
        ValueError: 响应格式错误
    """
    if timeout is None:
        timeout = LLM_CONFIG.get("timeout", 120)
    
    payload = {
        **LLM_CONFIG,
        "messages": messages
    }
    
    try:
        response = requests.post(
            LLM_CONFIG["api_endpoint"], 
            json=payload, 
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError("LLM响应格式错误：缺少choices字段")
        
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        raise Exception(f"LLM API调用失败: {str(e)}")
    except (KeyError, IndexError) as e:
        raise Exception(f"LLM响应解析失败: {str(e)}, 响应: {result}")


def parse_plan_response(response: str) -> Dict:
    """
    解析LLM响应中的计划JSON
    
    Args:
        response: LLM响应文本
        
    Returns:
        解析后的计划字典
    """
    # 首先尝试从代码块中提取JSON
    json_block_match = re.search(r'```(?:json)?\s*(\{[\s\S]*?\})\s*```', response)
    if json_block_match:
        try:
            plan = json.loads(json_block_match.group(1))
            return _normalize_plan(plan, response, json_block_match.start())
        except Exception as e:
            logger.warning(f"解析JSON代码块失败: {e}")
    
    # 尝试从文本中提取JSON对象
    json_match = None
    for match in re.finditer(r'\{[\s\S]*\}', response):
        try:
            test_json = json.loads(match.group())
            json_match = match
            break
        except:
            continue
    
    if json_match:
        try:
            plan = json.loads(json_match.group())
            return _normalize_plan(plan, response, json_match.start())
        except Exception as e:
            logger.warning(f"解析JSON对象失败: {e}")
    
    # 如果无法解析，返回默认结构
    return _create_fallback_plan(response)


def _normalize_plan(plan: Dict, response: str, json_start_pos: int) -> Dict:
    """规范化计划结构"""
    # 处理多任务模式
    if "sub_plans" in plan:
        for sub_plan in plan.get("sub_plans", []):
            if "steps" not in sub_plan:
                sub_plan["steps"] = []
    else:
        # 单任务模式
        if "steps" not in plan:
            plan["steps"] = []
        if "estimated_steps" not in plan:
            plan["estimated_steps"] = len(plan.get("steps", []))
    
    # 处理goal字段：合并思考部分
    thinking_part = response[:json_start_pos].strip()
    goal_value = str(plan.get("goal", ""))
    
    if "<redacted" in goal_value.lower() or (thinking_part and len(goal_value) < len(thinking_part)):
        if thinking_part:
            if goal_value and "<redacted" not in goal_value.lower():
                plan["goal"] = thinking_part + "\n\n" + goal_value
            else:
                plan["goal"] = thinking_part
        elif goal_value:
            plan["goal"] = goal_value
    elif thinking_part and not goal_value:
        plan["goal"] = thinking_part
    
    return plan


def _create_fallback_plan(response: str) -> Dict:
    """创建回退计划（基于关键词匹配）"""
    steps = []
    
    if "缓冲区" in response or "距离" in response:
        steps.append({
            "step_id": 1, 
            "description": "根据建筑和道路距离筛选空地", 
            "type": "buffer", 
            "params": {}
        })
    if "高程" in response or "海拔" in response:
        steps.append({
            "step_id": len(steps) + 1, 
            "description": "根据高程范围筛选", 
            "type": "elevation", 
            "params": {}
        })
    if "坡度" in response or "倾斜" in response:
        steps.append({
            "step_id": len(steps) + 1, 
            "description": "根据坡度范围筛选", 
            "type": "slope", 
            "params": {}
        })
    
    # 植被类型关键词
    vegetation_keywords = [
        "植被", "草地", "林地", "树木", "耕地", "裸地", "水体", 
        "湿地", "苔原", "稀疏植被", "永久性水体", "雪和冰"
    ]
    if any(keyword in response for keyword in vegetation_keywords):
        steps.append({
            "step_id": len(steps) + 1, 
            "description": "根据植被类型筛选", 
            "type": "vegetation", 
            "params": {}
        })
    
    return {
        "task": "",
        "goal": response,
        "steps": steps,
        "estimated_steps": len(steps)
    }

