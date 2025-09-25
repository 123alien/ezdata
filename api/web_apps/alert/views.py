'''
告警模块api
'''
from flask import jsonify, request
from flask import Blueprint
from utils.auth import validate_user, validate_permissions
from utils.web_utils import get_req_para, validate_params, generate_download_file
from utils.common_utils import gen_json_response
from web_apps.alert.services.alert_api_services import AlertApiService
alert_bp = Blueprint('alert', __name__)
    

@alert_bp.route('/list', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_list():
    '''
    列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.get_obj_list(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/queryAllList', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_all_list():
    '''
    全量列表查询接口
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.get_obj_all_list(req_dict)
    return jsonify(res_data)


@alert_bp.route('/checkDeviceAlerts', methods=['POST'])
@validate_user
@validate_permissions([])
def check_device_alerts():
    '''
    检查设备告警
    '''
    try:
        from web_apps.alert.services.device_alert_service import DeviceAlertService
        service = DeviceAlertService()
        service.check_all_device_alerts()
        return jsonify(gen_json_response(msg='设备告警检查完成'))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"检查设备告警失败：{e}"))


@alert_bp.route('/createDefaultStrategies', methods=['POST'])
@validate_user
@validate_permissions([])
def create_default_strategies():
    '''
    创建默认告警策略
    '''
    try:
        from web_apps.alert.strategys.device_alert_strategys import create_default_alert_strategies
        create_default_alert_strategies()
        return jsonify(gen_json_response(msg='默认告警策略创建完成'))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"创建默认策略失败：{e}"))

@alert_bp.route('/testNotification', methods=['POST'])
@validate_user
@validate_permissions([])
def test_notification():
    '''
    测试通知功能
    '''
    try:
        from web_apps.alert.services.notification_service import NotificationService
        req = get_req_para(request)
        method = req.get('method', 'platform')
        receiver = req.get('receiver', 'admin')
        
        notification_service = NotificationService()
        result = notification_service.test_notification(method, receiver)
        
        if result:
            return jsonify(gen_json_response(msg=f'{method}通知测试成功'))
        else:
            return jsonify(gen_json_response(code=500, msg=f'{method}通知测试失败'))
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"测试通知失败：{e}"))
    

@alert_bp.route('/queryById', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_detail():
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
    res_data = AlertApiService.get_obj_detail(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/add', methods=['POST'])
@validate_user
@validate_permissions([])
def alert_add():
    '''
    添加
    '''
    req_dict = get_req_para(request)
    verify_dict = {
    }
    not_valid = validate_params(req_dict, verify_dict)
    if not_valid:
        return jsonify(gen_json_response(code=400, msg=not_valid))
    res_data = AlertApiService.add_obj(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/edit', methods=['POST', 'PUT'])
@validate_user
@validate_permissions([])
def alert_edit():
    '''
    编辑
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
    res_data = AlertApiService.edit_obj(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/delete', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def alert_delete():
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
    res_data = AlertApiService.delete_obj(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/deleteBatch', methods=['POST', 'DELETE'])
@validate_user
@validate_permissions([])
def alert_deleteBatch():
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
    res_data = AlertApiService.delete_batch(req_dict)
    return jsonify(res_data)
    

@alert_bp.route('/importExcel', methods=['POST'])
@validate_user
@validate_permissions([])
def alert_importExcel():
    '''
    excel导入
    '''
    file = request.files.get('file', '')
    if file == '':
        res_data = gen_json_response(code=400, msg='请上传文件')
    else:
        res_data = AlertApiService.importExcel(file)
    return jsonify(res_data)
    

@alert_bp.route('/exportXls', methods=['GET'])
@validate_user
@validate_permissions([])
def alert_exportXls():
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
        output_file = AlertApiService.exportXls(req_dict)
        return generate_download_file(output_file, 'output')
    except Exception as e:
        return jsonify(gen_json_response(code=500, msg=f"未知错误：{e}"))
