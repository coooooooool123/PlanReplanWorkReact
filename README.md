# 空地智能体系统

一个基于 Plan-to-Execute 架构的智能体系统，专门用于地理空间数据的筛选和分析任务。系统采用 ReAct 架构的执行智能体，支持交互式计划审查和数据库管理功能。

## 系统架构

### Plan-to-Execute 架构

系统采用三阶段工作流程：
1. **Plan（规划）**: 根据用户任务生成初始计划，使用RAG检索相似任务
2. **Replan（重新规划）**: 执行失败时调整计划，或根据用户反馈修改计划
3. **Work（执行）**: ReAct架构的执行智能体，根据计划调用工具完成任务

## 目录结构

```
AIgen/
├── orchestrator.py          # 流程控制器
├── plan.py                  # 规划模块
├── replan.py                # 重新规划模块
├── context_manager.py       # 上下文管理（静态/动态RAG）
├── config.py                # 配置（LLM、路径、ChromaDB等）
├── main.py                  # 主入口（启动前后端）
├── api_server.py            # FastAPI后端服务
├── frontend.py              # Streamlit前端界面
├── update_knowledge.py      # 知识库更新脚本（可选）
├── work/
│   ├── agent.py             # ReAct执行智能体
│   └── tools/               # 工具集合
│       ├── base_tool.py
│       ├── buffer_filter_tool.py
│       ├── elevation_filter_tool.py
│       └── slope_filter_tool.py
├── data/                    # 数据目录
│   ├── nj_merged.osm        # OSM数据文件
│   └── dem.tif              # DEM高程数据
├── result/                  # 结果输出目录
└── context/                 # 上下文存储
    ├── static/              # 静态上下文（提示词）
    │   └── prompts.json
    └── dynamic/             # 动态上下文（RAG）
        └── chroma_db/       # ChromaDB向量数据库
```

## 核心模块

### Orchestrator（流程控制器）
协调 plan、replan、work 三个模块的执行流程，支持：
- `generate_plan()`: 生成初始计划
- `replan_with_feedback()`: 根据用户反馈重新规划
- `execute_plan()`: 执行计划

### Plan（规划模块）
- 使用RAG检索相似历史任务和知识库
- 生成不涉及具体工具的高层计划
- 支持从knowledge集合检索军事单位部署规则

### Replan（重新规划模块）
- 分析执行失败原因
- 根据可用工具重新规划
- 支持用户反馈驱动的重新规划

### WorkAgent（执行智能体）
- ReAct架构：Think → Act → Observe循环
- 根据计划步骤选择并调用工具
- 自动处理工具链式调用（前一个工具的输出作为下一个工具的输入）

### ContextManager（上下文管理）
- **静态上下文**: 提示词管理（plan_prompt, replan_prompt, work_prompt, system_prompt）
- **动态上下文**: RAG检索（ChromaDB向量数据库）
  - `tasks`集合: 历史任务和计划
  - `executions`集合: 执行记录和结果
  - `knowledge`集合: 领域知识（军事单位部署规则等）
- **上下文压缩**: 自动压缩过长的上下文

## 工具系统

三个独立的地理空间筛选工具：

1. **buffer_filter_tool**: 缓冲区筛选
   - 根据建筑和道路距离筛选空地区域
   - 参数: `buffer_distance`（必需）, `utm_crs`（可选）
   - 输出: GeoJSON文件（自动保存到result目录）

2. **elevation_filter_tool**: 高程筛选
   - 根据高程范围筛选区域
   - 参数: `input_geojson_path`（必需）, `min_elev`, `max_elev`（可选）
   - 支持链式调用（使用buffer_filter的输出）

3. **slope_filter_tool**: 坡度筛选
   - 根据坡度范围筛选区域
   - 参数: `input_geojson_path`（必需）, `min_slope`, `max_slope`（可选）
   - 支持链式调用（使用buffer_filter或elevation_filter的输出）

所有工具的输出文件自动保存到 `AIgen/result/` 目录，文件名包含时间戳和参数信息。

## 快速开始

### 1. 启动系统

```bash
cd AIgen
python main.py
```

这将同时启动：
- **后端API服务**: http://localhost:8000
- **前端界面**: http://localhost:8501

### 2. 使用前端界面

1. 打开浏览器访问 http://localhost:8501
2. 在"智能体任务"标签页：
   - 输入任务描述（如："计算距离建筑和道路500米以上的空地，高程在100-500米之间"）
   - 点击"生成计划"
   - 审查计划，可提出修改意见
   - 确认后执行计划
   - 查看结果地图和统计信息

3. 在"数据库管理"标签页：
   - 选择集合（knowledge/tasks/executions）
   - 查看、添加、删除数据
   - 批量更新knowledge集合（重新初始化军事单位部署规则）

4. 在"历史结果"标签页：
   - 查看所有历史执行结果
   - 在地图上可视化结果

### 3. 使用API接口

#### 生成计划
```bash
curl -X POST "http://localhost:8000/api/plan" \
  -H "Content-Type: application/json" \
  -d '{"task": "计算距离建筑500米以上的空地"}'
```

#### 根据反馈重新规划
```bash
curl -X POST "http://localhost:8000/api/replan" \
  -H "Content-Type: application/json" \
  -d '{
    "plan": {...},
    "feedback": "缓冲区距离改为600米"
  }'
```

#### 执行计划
```bash
curl -X POST "http://localhost:8000/api/execute" \
  -H "Content-Type: application/json" \
  -d '{"plan": {...}}'
```

#### 数据库管理
```bash
# 获取集合数据
curl "http://localhost:8000/api/knowledge?collection=knowledge"

# 添加数据
curl -X POST "http://localhost:8000/api/knowledge" \
  -H "Content-Type: application/json" \
  -d '{
    "text": "新的部署规则...",
    "metadata": {"unit": "新单位", "type": "deployment_rule"},
    "collection": "knowledge"
  }'

# 删除记录
curl -X DELETE "http://localhost:8000/api/knowledge/knowledge_0?collection=knowledge"

# 批量更新knowledge集合
curl -X PUT "http://localhost:8000/api/knowledge/update"
```

完整API文档: http://localhost:8000/docs

## 配置说明

### LLM配置（config.py）

```python
LLM_CONFIG = {
    "api_endpoint": "http://192.168.1.200:11434/v1/chat/completions",
    "model": "qwen3:32b",
    "temperature": 0.7,
    "max_tokens": 2000
}
```

### 数据路径

- OSM文件: `AIgen/data/nj_merged.osm`
- DEM文件: `AIgen/data/dem.tif`
- 结果目录: `AIgen/result/`

### ChromaDB配置

- 数据库路径: `AIgen/context/dynamic/chroma_db/`
- 集合: `tasks`, `executions`, `knowledge`
- 嵌入模型: `sentence-transformers/all-MiniLM-L6-v2`

## 知识库管理

### Knowledge集合内容

knowledge集合存储了15种军事单位的部署规则：
- 轻步兵、重装步兵、机械化步兵
- 坦克部队、反坦克步兵
- 自行火炮、牵引火炮
- 防空部队、狙击手
- 特种部队、装甲侦察单位
- 工兵部队、后勤保障部队
- 指挥单位、无人机侦察控制单元

每条规则包含：
- 适合的高程范围
- 坡度要求
- 与居民区的缓冲距离
- 部署策略说明

### 更新知识库

**方法1**: 使用前端界面
- 在"数据库管理"标签页选择knowledge集合
- 点击"批量更新（重新初始化军事单位规则）"按钮

**方法2**: 使用API
```bash
curl -X PUT "http://localhost:8000/api/knowledge/update"
```

**方法3**: 使用脚本
```bash
python update_knowledge.py
```

## 工作流程示例

### 完整流程

1. **用户输入任务**: "为轻步兵寻找合适的部署位置"
2. **Plan阶段**: 
   - 从knowledge集合检索轻步兵部署规则
   - 生成计划：缓冲区筛选 → 高程筛选 → 坡度筛选
3. **用户审查计划**: 可提出修改意见
4. **Replan阶段**（如需要）: 根据反馈调整计划
5. **Work阶段**: 
   - 执行buffer_filter_tool（距离居民区100-300米）
   - 执行elevation_filter_tool（中等高程）
   - 执行slope_filter_tool（缓坡或平缓地形）
6. **结果输出**: GeoJSON文件保存到result目录，前端显示地图

## 技术栈

- **后端**: FastAPI
- **前端**: Streamlit
- **向量数据库**: ChromaDB
- **嵌入模型**: sentence-transformers/all-MiniLM-L6-v2
- **地理空间处理**: geopandas, shapely, rasterio
- **LLM**: 本地模型（Ollama兼容API）

## 依赖安装

```bash
pip install fastapi uvicorn streamlit
pip install chromadb sentence-transformers
pip install geopandas shapely rasterio pyproj
pip install folium requests
```

## 注意事项

1. **数据文件**: 确保 `data/nj_merged.osm` 和 `data/dem.tif` 文件存在
2. **LLM服务**: 确保LLM API服务可访问（默认: http://192.168.1.200:11434）
3. **端口占用**: 确保8000和8501端口未被占用
4. **结果目录**: 系统会自动创建 `result/` 目录

## 开发说明

### 添加新工具

1. 在 `work/tools/` 目录创建新工具文件
2. 继承 `BaseTool` 类
3. 实现 `execute()` 和 `validate_params()` 方法
4. 在 `work/agent.py` 中注册工具

### 修改提示词

1. 使用前端"数据库管理"功能
2. 或直接编辑 `context/static/prompts.json`
3. 或调用 `context_manager.save_static_context()`

### 扩展知识库

1. 使用前端界面添加数据
2. 或使用API接口批量导入
3. 或修改 `context_manager.py` 中的 `update_knowledge_base()` 方法

## 许可证

MIT License