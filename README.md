ezdata
===============

项目介绍
-----------------------------------

ezdata 是基于python后端和vue3前端开发的数据处理分析和任务调度系统。  
[![Ask DeepWiki](https://deepwiki.com/badge.svg)](https://deepwiki.com/xuwei95/ezdata)

![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/ezdata.gif?raw=true "在这里输入图片标题")

其主要功能如下
- 多数据源管理，支持连接文件，关系型数据库，nosql数据库，时序数据库，图数据库等多种数据源。
- 各数据源抽象为统一数据模型，支持创建，删除，字段管理，自定义查询取数，封装数据查询api接口等各种功能。
- 集成llm模块，支持数据问答功能，使用数据对话方式实现交互式数据分析，ai自动输出数据结论，数据表格，统计报表等内容。
- 低代码数据集成，可视化处理流中每一步结果，可使用分布式pandas引擎拓展至tb级大型数据集，使用多种内置转换算法或自定义代码快速实现数据传输管道。
- 单任务和dag任务工作流调度，内置python，shell，数据集成等多种任务模版，也支持使用内置表单引擎和编写动态执行代码自定义任务模版，支持分布式worker执行，任务队列管理，任务失败重试，任务失败告警，任务运行日志及执行历史查看等调度系统功能。

项目链接
-----------------------------------
- 项目官网：  [http://www.ezdata.cloud](http://www.ezdata.cloud)

- 在线演示 ： [在线演示](http://124.220.57.72)

[comment]: <> (- 开发文档：  [主项目文档]&#40;http://www.ezdata.cloud/docs/hello.html&#41;)

项目源码
-----------------------------------
| 仓库  | 地址   |
|--------------------|--------------------|
| Github | [ezdata](https://github.com/xuwei95/ezdata) 
| 码云  | [ezdata](https://gitee.com/xuwei95/ezdata) 
| gitcode  | [ezdata](https://gitcode.com/xuwei95/ezdata) 


系统效果
----
##### 主页
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/dashboard.png?raw=true "在这里输入图片标题")
##### 数据源管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datasource.png?raw=true "在这里输入图片标题")
##### 数据模型管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datamodel.png?raw=true "在这里输入图片标题")
##### 数据自定义查询及接口封装
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/data_query.png?raw=true "在这里输入图片标题")
##### 数据对话，交互式数据分析
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datachat_msg.png?raw=true "在这里输入图片标题")
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datachat_table.png?raw=true "在这里输入图片标题")
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/datachat_chart.png?raw=true "在这里输入图片标题")
##### 数据集成
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/etl.png?raw=true "在这里输入图片标题")
##### 任务模版管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/task_template.png?raw=true "在这里输入图片标题")
##### 任务调度
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/task_scheduler.png?raw=true "在这里输入图片标题")
##### dag任务工作流
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/dag_detail.png?raw=true "在这里输入图片标题")
##### worker执行节点管理
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/worker_ops.png?raw=true "在这里输入图片标题")
##### 数据可视化大屏
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/bigscreen1.png?raw=true "在这里输入图片标题")
![输入图片说明](https://raw.githubusercontent.com/xuwei95/ezdata_press/master/images/bigscreen2.png?raw=true "在这里输入图片标题")



后端启动
----
### 依赖安装
```
pip install -r requirements.txt -i https://pypi.doubanio.com/simple
```
### 系统web接口服务
```
python web_api.py
```
### 系统任务调度接口服务
```
python scheduler_api.py
```
## celery相关
启动worker
- windows
```
celery -A tasks worker -P eventlet
```
- linux
```
celery -A tasks worker
```
启动flower
```
celery -A tasks flower
```

分支与发布策略
-----------------------------------
- 主分支（main）：始终保持可发布状态，保护分支，仅允许通过 Pull Request 合并。
- 开发分支（develop，可选）：用于日常集成，按需创建；也可以直接从 feature 向 main 发起 PR。
- 功能分支（feature/*）：从 main（或 develop）拉出，完成后通过 PR 合并，命名如 `feature/etl-scheduler-opt`。
- 修复分支（fix/* 或 hotfix/*）：用于缺陷修复或紧急修复，完成后合并回 main，并尽可能回合到 develop。
- 发布标签（tags）：使用语义化版本 `vX.Y.Z` 打标签，例如 `v1.2.0`。补丁修复递增 Z、向后兼容新增递增 Y、破坏式变更递增 X。

提交信息规范
-----------------------------------
- `feat:` 新功能；`fix:` 缺陷修复；`docs:` 文档；`chore:` 杂项；`refactor:` 重构；`perf:` 性能优化；`test:` 测试；`build:` 构建配置；`ci:` CI 配置。
- 示例：`feat(task): 增加 DAG 任务模板的并发控制`。

发布流程（示例）
-----------------------------------
1. 功能与修复合并到 main 后，更新版本号并生成变更日志。
2. 创建发布标签：`git tag vX.Y.Z && git push origin vX.Y.Z`。
3. 触发构建/镜像流水线并产出产物（如 Docker 镜像、前端构建包）。

