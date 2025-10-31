'''
数据模型管理模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.datamodel.services.datamodel_api_services import DataModelApiService
from web_apps.datamodel.services.datamodel_query_api_service import DataModelQueryApiService
from web_apps.datamodel.services.prediction_service import DevicePredictionService
from utils.etl_utils import get_writer_model
from bson import ObjectId
from datetime import datetime
datamodel_bp = Blueprint('datamodel', __name__)


@datamodel_bp.route('/query', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_query():
    '''
    模型数据查询
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelQueryApiService().query_obj_data(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/etl_preview', methods=['POST'])
@validate_user
@validate_permissions([])
def etl_preview():
    '''
    数据集成预览
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "task_params": {
            "name": "任务配置",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelQueryApiService().etl_preview(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/tree', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_tree():
    '''
    模型树查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_tree(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_list(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_all_list(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_detail():
    '''
    详情
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().get_obj_detail(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/getInfoById', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_info():
    '''
    模型查询信息，组成查询需要结构
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelQueryApiService().get_obj_info(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/operate', methods=['POST'])
@validate_user
@validate_permissions(['datamodel:operate'])
def datamodel_operate():
    '''
    操作模型
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "模型id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelQueryApiService().operate_obj(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions(['datamodel:add'])
def datamodel_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "name": {
            "name": "名称",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().add_obj(req_dict)
    
    # 如果是股票历史数据接口，自动更新默认参数
    if res_data.get('code') == 200 and '股票历史数据接口' in req_dict.get('name', ''):
        try:
            _update_stock_defaults_from_model(req_dict)
        except Exception as e:
            print(f'更新股票默认参数失败: {e}')
    
    return jsonify(res_data)


@datamodel_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions(['datamodel:edit'])
def datamodel_edit():
    '''
    编辑
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        },
        "name": {
            "name": "名称",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().edit_obj(req_dict)
    
    # 如果是股票历史数据接口，自动更新默认参数
    if res_data.get('code') == 200 and '股票历史数据接口' in req_dict.get('name', ''):
        try:
            _update_stock_defaults_from_model(req_dict)
        except Exception as e:
            print(f'更新股票默认参数失败: {e}')
    
    return jsonify(res_data)


@datamodel_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['datamodel:delete'])
def datamodel_delete():
    '''
    删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "id": {
            "name": "id",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().delete_obj(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions(['datamodel:delete'])
def datamodel_deleteBatch():
    '''
    批量删除
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "ids": {
            "name": "id列表",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = DataModelApiService().delete_batch(req_dict)
    return jsonify(res_data)


@datamodel_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = DataModelApiService().importExcel(file)
    return jsonify(res_data)


@datamodel_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def datamodel_exportXls():
    '''
    导出excel
    '''
    req_dict = get_req_para(request)
    verify_dict = {
        "selections": {
            "name": "选择项",
            "required": True
        }
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    try:
        output_file = DataModelApiService().exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))


# Dashboard API 路由
@datamodel_bp.route('/dashboard/overview', methods=['GET'])
@validate_user
@validate_permissions([])
def get_dashboard_overview():
    '''
    获取数据模型总览数据
    '''
    try:
        result = DataModelApiService().get_dashboard_overview()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取总览数据失败：{e}"))


@datamodel_bp.route('/dashboard/type-stats', methods=['GET'])
@validate_user
@validate_permissions([])
def get_type_stats():
    '''
    获取数据模型类型统计
    '''
    try:
        result = DataModelApiService().get_type_stats()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取类型统计失败：{e}"))


@datamodel_bp.route('/dashboard/trend', methods=['GET'])
@validate_user
@validate_permissions([])
def get_creation_trend():
    '''
    获取数据模型创建趋势
    '''
    try:
        result = DataModelApiService().get_creation_trend()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取创建趋势失败：{e}"))


@datamodel_bp.route('/dashboard/dataflow', methods=['GET'])
@validate_user
@validate_permissions([])
def get_dataflow():
    """
    返回数据流向图所需的节点与连线（示例数据）。
    后续可改为从数据库或配置动态生成。
    """
    try:
        nodes = [
            {"name": "外部数据源"},
            {"name": "数据采集"},
            {"name": "ETL/清洗"},
            {"name": "对象存储MinIO"},
            {"name": "关系型数据库MySQL"},
            {"name": "向量索引TrustRAG"},
            {"name": "数据模型"},
            {"name": "知识库"},
            {"name": "API服务"},
            {"name": "仪表盘/应用"},
        ]
        links = [
            {"source": "外部数据源", "target": "数据采集", "value": 20},
            {"source": "数据采集", "target": "ETL/清洗", "value": 20},
            {"source": "ETL/清洗", "target": "对象存储MinIO", "value": 12},
            {"source": "ETL/清洗", "target": "关系型数据库MySQL", "value": 8},
            {"source": "对象存储MinIO", "target": "向量索引TrustRAG", "value": 6},
            {"source": "关系型数据库MySQL", "target": "数据模型", "value": 8},
            {"source": "向量索引TrustRAG", "target": "知识库", "value": 6},
            {"source": "数据模型", "target": "API服务", "value": 6},
            {"source": "API服务", "target": "仪表盘/应用", "value": 6},
            {"source": "知识库", "target": "仪表盘/应用", "value": 4},
        ]
        return jsonify(gen_json_response(data={"nodes": nodes, "links": links}))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取数据流向失败：{e}"))

@datamodel_bp.route('/dashboard/field-stats', methods=['GET'])
@validate_user
@validate_permissions([])
def get_field_stats():
    '''
    获取数据模型字段统计
    '''
    try:
        result = DataModelApiService().get_field_stats()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取字段统计失败：{e}"))


@datamodel_bp.route('/dashboard/iot-devices', methods=['GET'])
def get_iot_devices():
    '''
    获取物联网设备数据
    '''
    try:
        result = DataModelApiService().get_iot_device_data()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取设备数据失败：{e}"))


@datamodel_bp.route('/dashboard/device-stats', methods=['GET'])
def get_device_statistics():
    '''
    获取环境监测设备统计信息
    '''
    try:
        result = DataModelApiService().get_device_statistics()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取设备统计失败：{e}"))

@datamodel_bp.route('/dashboard/power-meter-stats', methods=['GET'])
def get_power_meter_statistics():
    '''
    获取电表设备统计信息
    '''
    try:
        result = DataModelApiService().get_power_meter_statistics()
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取电表设备统计失败：{e}"))

@datamodel_bp.route('/dashboard/device-metrics', methods=['GET'])
def get_device_metrics():
    '''
    获取设备多指标时序
    '''
    try:
        req = get_req_para(request)
        print(f"device-metrics 请求参数: {req}")
        device_name = req.get('deviceName') or req.get('device_name')
        start_ts = int(req.get('start') or 0)
        end_ts = int(req.get('end') or 0)
        print(f"解析后参数: device_name={device_name}, start={start_ts}, end={end_ts}")
        if not device_name or not start_ts or not end_ts:
            return jsonify(gen_json_response(code=400, msg='参数缺失'))
        result = DataModelApiService().get_device_metrics(device_name, start_ts, end_ts)
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        print(f"device-metrics 错误: {e}")
        return jsonify(gen_json_response(code=500, msg=f"获取设备时序失败：{e}"))

@datamodel_bp.route('/dashboard/daily-power-trend', methods=['GET'])
def get_daily_power_trend():
    '''
    获取日用电量趋势数据
    '''
    try:
        req = get_req_para(request)
        days = int(req.get('days', 7))
        result = DataModelApiService().get_daily_power_trend(days)
        return jsonify(gen_json_response(data=result))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"获取日用电量趋势失败：{e}"))


@datamodel_bp.route('/dashboard/device-prediction', methods=['POST'])
def predict_device_metrics():
    '''
    设备指标LSTM预测接口
    请求参数:
        deviceName: 设备名称
        metric: 指标名称（可选，默认'power'）
        start: 开始时间戳（毫秒）
        end: 结束时间戳（毫秒）
        predictionSteps: 预测未来多少个点（可选，默认36，约3小时）
        timeSteps: LSTM时间窗口大小（可选，默认30）
    '''
    try:
        req = get_req_para(request)
        device_name = req.get('deviceName') or req.get('device_name')
        metric = req.get('metric', 'power')
        start_ts = int(req.get('start', 0))
        end_ts = int(req.get('end', 0))
        prediction_steps = int(req.get('predictionSteps', 36))
        time_steps = int(req.get('timeSteps', 30))
        
        if not device_name or not start_ts or not end_ts:
            return jsonify(gen_json_response(code=400, msg='参数缺失：需要deviceName、start、end'))
        
        # 获取历史数据
        datamodel_service = DataModelApiService()
        metrics_data = datamodel_service.get_device_metrics(device_name, start_ts, end_ts)
        
        if not metrics_data or 'series' not in metrics_data:
            return jsonify(gen_json_response(code=404, msg='未找到设备数据'))
        
        series = metrics_data.get('series', {})
        
        # 如果指定了metric，只预测该metric；否则预测所有可用的metric
        metrics_to_predict = [metric] if metric in series else list(series.keys())
        
        if not metrics_to_predict:
            return jsonify(gen_json_response(code=404, msg=f'未找到指标数据: {metric}'))
        
        # 调用预测服务
        prediction_service = DevicePredictionService()
        results = {}
        
        for m in metrics_to_predict:
            data_points = series.get(m, [])
            if not data_points or len(data_points) < 10:
                continue
            
            prediction_result = prediction_service.predict_device_metric(
                data_points=data_points,
                metric_name=m,
                prediction_steps=prediction_steps,
                time_steps=time_steps,
                epochs=30  # 可以调整训练轮数
            )
            
            if prediction_result.get('success'):
                results[m] = prediction_result
        
        if results:
            return jsonify(gen_json_response(data={
                'deviceName': device_name,
                'predictions': results,
                'predictionSteps': prediction_steps
            }))
        else:
            return jsonify(gen_json_response(code=500, msg='预测失败：数据不足或模型训练失败'))
            
    except Exception as e:
        import traceback
        error_detail = traceback.format_exc()
        return jsonify(gen_json_response(code=500, msg=f"预测失败：{str(e)}"))


# 物联网设备上报接口：实时写入 MongoDB
@datamodel_bp.route('/ingest', methods=['POST'])
@validate_user
@validate_permissions([])
def datamodel_ingest():
    '''
    设备数据上报写入接口（实时写入 MongoDB）
    - 参数：
      id / model_id: 数据模型ID（指向Mongo集合）
      data: 字典或数组，设备数据内容
      load_type: 可选，insert/update/upsert，默认 upsert
      only_fields: 可选，数组，作为更新匹配键，默认 ["device_id", "_id", "device_num"]
    '''
    req_dict = get_req_para(request)
    # 兼容 id / model_id
    model_id = req_dict.get('model_id') or req_dict.get('id')
    data = req_dict.get('data')
    load_type = req_dict.get('load_type', 'upsert')
    only_fields = req_dict.get('only_fields') or ["device_id", "_id", "device_num"]

    verify_dict = {
        "model_id": {"name": "模型ID", "required": True},
        "data": {"name": "数据", "required": True},
    }
    # 填充入参用于校验
    check_payload = {"model_id": model_id, "data": data}
    not_valid = validate_params(check_payload, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))

    def _normalize(value):
        # 递归规范化 Mongo 扩展JSON
        if isinstance(value, dict):
            # $date 处理
            if '$date' in value and len(value) == 1:
                v = value['$date']
                if isinstance(v, str):
                    try:
                        # 兼容结尾 Z
                        v2 = v.replace('Z', '+00:00') if 'Z' in v else v
                        return datetime.fromisoformat(v2)
                    except Exception:
                        return v
                return v
            # $oid 处理
            if '$oid' in value and len(value) == 1:
                try:
                    return ObjectId(str(value['$oid']))
                except Exception:
                    return value['$oid']
            # 其他键递归
            return {k: _normalize(v) for k, v in value.items()}
        if isinstance(value, list):
            return [_normalize(i) for i in value]
        return value

    try:
        load_info = {
            'model_id': model_id,
            'load_type': load_type,
            'only_fields': only_fields,
        }
        flag, writer = get_writer_model(load_info)
        if not flag:
            return jsonify(gen_json_response(code=400, msg=writer))

        data_norm = _normalize(data)
        ok, res = writer.write(data_norm)
        if not ok:
            return jsonify(gen_json_response(code=400, msg=res))

        return jsonify(gen_json_response(data=res, msg='写入成功'))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"写入失败：{e}"))


@datamodel_bp.route('/dashboard/adjust-time', methods=['POST'])
@validate_user
@validate_permissions([])
def adjust_device_time_to_date():
    '''
    维护接口：将“设备数据”记录的 update_time 统一改到指定日期（默认今天），可选按设备名称过滤，支持试运行。
    请求参数：
      - target_date: 字符串，目标日期，格式 YYYY-MM-DD，默认今天本地日期
      - device_names: 数组或以逗号分隔的字符串，按设备名称过滤（与看板中的“07室环境监测”等一致）；可选
      - limit: 每个模型处理的最大记录数（分页累计），默认 1000
      - dry_run: 是否试运行，仅统计不落库，默认 true
    响应：{ updated: 数量, scanned: 数量, models: [...], dry_run: bool }
    '''
    try:
        req = get_req_para(request)
        target_date_str = req.get('target_date')
        device_names = req.get('device_names')
        limit = int(req.get('limit') or 1000)
        dry_run = str(req.get('dry_run', 'true')).lower() in ['true', '1', 'yes']

        # 设备名过滤解析
        if isinstance(device_names, str):
            if device_names.strip() == '':
                device_names = []
            else:
                device_names = [i.strip() for i in device_names.split(',') if i.strip()]
        elif not isinstance(device_names, list):
            device_names = []

        # 目标日期（本地）
        from datetime import timezone, timedelta, date
        import os
        tz_offset_minutes_env = os.getenv('EZDATA_TZ_OFFSET_MINUTES')
        try:
            tz_offset_minutes = int(tz_offset_minutes_env) if tz_offset_minutes_env is not None else 480
        except Exception:
            tz_offset_minutes = 480
        tz_offset = timedelta(minutes=tz_offset_minutes)
        if target_date_str:
            try:
                target_date = datetime.strptime(target_date_str, '%Y-%m-%d').date()
            except Exception:
                return jsonify(gen_json_response(code=400, msg='target_date 格式应为 YYYY-MM-DD'))
        else:
            target_date = date.today()

        # 查找“设备”相关模型
        svc = DataModelApiService()
        from web_apps.datamodel.services.datamodel_query_api_service import DataModelQueryApiService
        query_svc = DataModelQueryApiService()
        from web_apps.datamodel.db_models import DataModel
        from utils.etl_utils import get_writer_model
        from bson import ObjectId

        iot_models = DataModel.query.filter(
            DataModel.del_flag == 0,
            DataModel.status == 1,
            DataModel.name.like('%设备%')
        ).all()

        def to_ms(v):
            # 与服务保持一致：多格式转毫秒
            try:
                if isinstance(v, dict) and '$date' in v:
                    return int(v['$date'])
                if isinstance(v, (int, float)) or (isinstance(v, str) and str(v).isdigit()):
                    vi = int(v)
                    return vi * 1000 if vi < 1_000_000_000_000 else vi
                if isinstance(v, str):
                    s = v.strip().replace('T', ' ').split('.')[0]
                    for fmt in ('%Y-%m-%d %H:%M:%S', '%Y/%m/%d %H:%M:%S', '%Y-%m-%d %H:%M', '%Y/%m/%d %H:%M'):
                        try:
                            dt = datetime.strptime(s, fmt)
                            return int(dt.timestamp() * 1000)
                        except Exception:
                            pass
                return None
            except Exception:
                return None

        updated = 0
        scanned = 0
        touched_models = []

        for m in iot_models:
            touched_models.append({'id': m.id, 'name': m.name})
            page = 1
            pagesize = 200
            processed_this_model = 0
            while processed_this_model < limit:
                res = query_svc.query_obj_data({'id': m.id, 'page': page, 'pagesize': pagesize}, use_auth=False)
                if res.get('code') != 200:
                    break
                recs = res.get('data', {}).get('records', [])
                if not recs:
                    break
                for r in recs:
                    if processed_this_model >= limit:
                        break
                    scanned += 1
                    # 设备名过滤（如传感器数据使用 factor_name 作为名称）
                    r_name = r.get('device_name') or r.get('factor_name') or r.get('name')
                    if device_names and (r_name not in device_names):
                        continue

                    old_ms = to_ms(r.get('update_time'))
                    if old_ms is None:
                        continue
                    # 将时间对齐到目标日期：保留原时分秒（本地），仅替换日期
                    from datetime import datetime as _dt
                    local_dt = _dt.fromtimestamp(old_ms / 1000.0)
                    new_local_dt = _dt(
                        year=target_date.year,
                        month=target_date.month,
                        day=target_date.day,
                        hour=local_dt.hour,
                        minute=local_dt.minute,
                        second=local_dt.second,
                        microsecond=0
                    )
                    new_ms = int(new_local_dt.timestamp() * 1000)

                    if dry_run:
                        updated += 1
                        processed_this_model += 1
                        continue

                    load_info = {
                        'model_id': m.id,
                        'load_type': 'upsert',
                        'only_fields': ['_id'],
                    }
                    flag, writer = get_writer_model(load_info)
                    if not flag:
                        return jsonify(gen_json_response(code=500, msg=f'获取writer失败: {writer}'))

                    # 以 _id 匹配更新，保留原结构，替换 update_time
                    doc = dict(r)
                    if isinstance(doc.get('_id'), dict) and '$oid' in doc['_id']:
                        try:
                            doc['_id'] = ObjectId(str(doc['_id']['$oid']))
                        except Exception:
                            pass
                    doc['update_time'] = {'$date': new_ms}

                    ok, resw = writer.write(doc)
                    if not ok:
                        return jsonify(gen_json_response(code=500, msg=f'写入失败: {resw}'))
                    updated += 1
                    processed_this_model += 1

                if len(recs) < pagesize:
                    break
                page += 1

        return jsonify(gen_json_response(data={
            'updated': updated,
            'scanned': scanned,
            'models': touched_models,
            'dry_run': dry_run,
            'target_date': str(target_date)
        }, msg='ok'))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f'时间统一更新失败：{e}'))


# ================= 金融数据：AkShare 股票K线（强绑定） =================

@datamodel_bp.route('/stock/kline', methods=['GET'])
@validate_user
@validate_permissions([])
def stock_kline():
    """
    获取股票K线数据，支持多种数据接口函数
    参数：model_id、function_name、symbol、start(YYYYMMDD)、end(YYYYMMDD)、adjust(qfq/hfq/none)
    """
    try:
        # 延迟导入，避免未安装报错
        try:
            import akshare as ak  # type: ignore
        except Exception:
            return jsonify(gen_json_response(code=500, msg='后端未安装 akshare'))

        from utils.web_utils import get_req_para as _get
        req = _get(request)
        
        # 获取参数
        function_name = req.get('function_name', 'A股日频率数据-东方财富')
        raw_symbol = (req.get('symbol') or '000001.SZ')
        adjust = (str(req.get('adjust') or 'qfq')).lower()
        
        import datetime as _dt
        end = req.get('end') or _dt.datetime.now().strftime('%Y%m%d')
        start = req.get('start') or (_dt.datetime.now() - _dt.timedelta(days=365)).strftime('%Y%m%d')

        # 根据函数名调用不同的AkShare接口
        data = None
        try:
            from utils.cache_utils import redis_cli
            cache_key = f'stock:kline:{function_name}:{raw_symbol}:{start}:{end}:{adjust}'
            cache_v = redis_cli.get(cache_key)
            if cache_v:
                import json as _json
                data = _json.loads(cache_v)
        except Exception:
            data = None

        if data is None:
            # 根据函数名选择对应的AkShare接口
            try:
                if 'A股日频率数据-东方财富' in function_name:
                    # 兼容多种写法：000001.SZ / 000001 / sz000001 / SH600000
                    import re as _re
                    m = _re.search(r'(\d{6})', str(raw_symbol))
                    symbol = (m.group(1) if m else str(raw_symbol)).upper()
                    adj = 'qfq' if adjust == 'qfq' else ('hfq' if adjust == 'hfq' else None)
                    df = ak.stock_zh_a_hist(symbol=symbol, start_date=start, end_date=end, adjust=adj)
                elif '美股日频率数据-雅虎财经' in function_name:
                    # 美股数据，symbol格式如 AAPL, TSLA
                    symbol = str(raw_symbol).upper()
                    df = ak.stock_us_daily(symbol=symbol)
                    # 美股数据需要按时间范围过滤
                    if df is not None and not df.empty:
                        import pandas as pd
                        df['date'] = pd.to_datetime(df['date'])
                        start_date = pd.to_datetime(start, format='%Y%m%d')
                        end_date = pd.to_datetime(end, format='%Y%m%d')
                        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                        df = df.sort_values('date')
                elif '港股日频率数据-腾讯' in function_name:
                    # 港股数据，symbol格式如 00700.HK
                    symbol = str(raw_symbol).upper()
                    df = ak.stock_hk_daily(symbol=symbol)
                    # 港股数据需要按时间范围过滤
                    if df is not None and not df.empty:
                        import pandas as pd
                        df['date'] = pd.to_datetime(df['date'])
                        start_date = pd.to_datetime(start, format='%Y%m%d')
                        end_date = pd.to_datetime(end, format='%Y%m%d')
                        df = df[(df['date'] >= start_date) & (df['date'] <= end_date)]
                        df = df.sort_values('date')
                else:
                    # 默认使用A股接口
                    import re as _re
                    m = _re.search(r'(\d{6})', str(raw_symbol))
                    symbol = (m.group(1) if m else str(raw_symbol)).upper()
                    adj = 'qfq' if adjust == 'qfq' else ('hfq' if adjust == 'hfq' else None)
                    df = ak.stock_zh_a_hist(symbol=symbol, start_date=start, end_date=end, adjust=adj)
            except Exception as e:
                print(f"AkShare数据获取异常: {e}")
                import traceback
                traceback.print_exc()
                df = None
            
            if df is None or df.empty:
                data = []
            else:
                try:
                    # 统一列名映射
                    column_mapping = {
                        '日期': 'date', '开盘': 'open', '最高': 'high', '最低': 'low', '收盘': 'close', '成交量': 'volume',
                        'Date': 'date', 'Open': 'open', 'High': 'high', 'Low': 'low', 'Close': 'close', 'Volume': 'volume'
                    }
                    df = df.rename(columns=column_mapping)
                    
                    cols = ['date', 'open', 'high', 'low', 'close', 'volume']
                    # 只保留存在的列
                    available_cols = [col for col in cols if col in df.columns]
                    
                    if not available_cols:
                        data = []
                    else:
                        df = df[available_cols]
                        # 确保数据不为空
                        if len(df) == 0:
                            data = []
                        else:
                            data = df.to_dict(orient='records')
                except Exception as e:
                    print(f"数据处理失败: {e}")
                    import traceback
                    traceback.print_exc()
                    data = []
            
            # 写缓存
            try:
                from utils.cache_utils import redis_cli
                import json as _json
                redis_cli.set(cache_key, _json.dumps(data), ex=1800)
            except Exception:
                pass

        return jsonify(gen_json_response(data=data))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f'akshare获取失败: {e}'))


@datamodel_bp.route('/stock/defaults', methods=['GET', 'POST'])
@validate_user
@validate_permissions([])
def stock_defaults():
    """
    读取/保存股票K线默认参数，暂存于 Redis：key=stock:kline:defaults
    GET -> {symbol,start,end,adjust,updated_at}
    POST -> 保存同字段
    """
    key = 'stock:kline:defaults'
    import json as _json
    import datetime as _dt
    from utils.cache_utils import redis_cli

    if request.method == 'GET':
        v = redis_cli.get(key)
        if not v:
            now = _dt.datetime.now()
            return jsonify(gen_json_response(data={
                'symbol': '000001.SZ',
                'adjust': 'qfq',
                'end': now.strftime('%Y%m%d'),
                'start': (now - _dt.timedelta(days=365)).strftime('%Y%m%d'),
                'updated_at': now.isoformat(),
            }))
        try:
            return jsonify(gen_json_response(data=_json.loads(v)))
        except Exception:
            return jsonify(gen_json_response(code=500, msg='默认参数解析失败'))

    # POST 保存
    req = get_req_para(request)
    symbol = (req.get('symbol') or '000001.SZ').upper()
    adjust = (str(req.get('adjust') or 'qfq')).lower()
    start = req.get('start')
    end = req.get('end')
    payload = {
        'symbol': symbol,
        'adjust': adjust,
        'start': start,
        'end': end,
        'updated_at': _dt.datetime.now().isoformat(),
    }
    redis_cli.set(key, _json.dumps(payload))
    return jsonify(gen_json_response(data=payload, msg='已保存默认参数'))


def _update_stock_defaults_from_model(model_data):
    """
    从数据模型配置中提取股票默认参数并保存到Redis
    """
    try:
        import json as _json
        import datetime as _dt
        from utils.cache_utils import redis_cli
        
        # 解析model_conf
        model_conf = model_data.get('model_conf', '{}')
        if isinstance(model_conf, str):
            try:
                conf = _json.loads(model_conf)
            except:
                conf = {}
        else:
            conf = model_conf or {}
        
        # 提取参数
        symbol = conf.get('symbol', '000001.SZ')
        adjust = conf.get('adjust', 'qfq')
        start = conf.get('start', (_dt.datetime.now() - _dt.timedelta(days=365)).strftime('%Y%m%d'))
        end = conf.get('end', _dt.datetime.now().strftime('%Y%m%d'))
        
        # 保存到Redis
        key = 'stock:kline:defaults'
        payload = {
            'symbol': symbol,
            'adjust': adjust,
            'start': start,
            'end': end,
            'updated_at': _dt.datetime.now().isoformat(),
        }
        redis_cli.set(key, _json.dumps(payload))
        print(f'已更新股票默认参数: {payload}')
        
    except Exception as e:
        print(f'更新股票默认参数失败: {e}')
        raise
