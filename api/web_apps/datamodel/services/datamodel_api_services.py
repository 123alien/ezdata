'''
数据模型管理api服务
'''
import json
from web_apps import db
from utils.query_utils import get_base_query
from utils.auth import set_insert_user, set_update_user, get_auth_token_info
from utils.common_utils import gen_json_response, gen_uuid, parse_json
from web_apps.datamodel.db_models import DataModel
from web_apps.datasource.db_models import DataSource
from web_apps.datamodel.services.datamodel_service import gen_extract_info
from utils.etl_utils import get_reader_model
from utils.web_utils import validate_params
import pandas as pd
import io


def serialize_datamodel_model(obj, ser_type='list'):
    '''
    序列化模型数据
    :param obj:
    :param ser_type:
    :return:
    '''
    dic = obj.to_dict()
    if ser_type == 'list':
        res = {}
        for k in ['id', 'name', 'datasource_id', 'type', 'status', 'can_interface', 'model_conf', 'ext_params', 'create_by', 'create_time', 'update_by', 'update_time', 'del_flag', 'sort_no', 'description', 'depart_list']:
            if k in ['model_conf', 'ext_params', 'depart_list']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'detail':
        for k in ['model_conf', 'depart_list']:
            dic[k] = json.loads(dic[k])
    elif ser_type == 'all_list':
        res = {}
        for k in ['id', 'name', 'datasource_id', 'type']:
            if k in ['model_conf', 'ext_params']:
                res[k] = json.loads(dic[k])
            else:
                res[k] = dic[k]
        return res
    elif ser_type == 'tree':
        res = {
            "type": 'datamodel',
            "icon": '',
            "isLeaf": True,
            "key": str(obj.id),
            "label": str(obj.name),
            "title": str(obj.name),
            "slotTitle": str(obj.name),
            "value": str(obj.id),
        }
        return res
    return dic


def get_datamodel_tree(obj_list):
    '''
    获取数据模型树
    '''
    datasource_ids = list(set([i.datasource_id for i in obj_list]))
    datasource_objs = get_base_query(DataSource).filter(DataSource.id.in_(datasource_ids)).all()
    tree_data = []
    for datasource_obj in datasource_objs:
        dic = {
            "type": 'datasource',
            "icon": '',
            "isLeaf": False,
            "key": str(datasource_obj.id),
            "label": str(datasource_obj.name),
            "title": str(datasource_obj.name),
            "slotTitle": str(datasource_obj.name),
            "value": str(datasource_obj.id)
        }
        child_models = [i for i in obj_list if i.datasource_id == datasource_obj.id]
        dic['children'] = [serialize_datamodel_model(obj, ser_type='tree') for obj in child_models]
        tree_data.append(dic)
    print(tree_data)
    return tree_data


class DataModelApiService(object):
    def __init__(self):
        pass

    def get_obj_tree(self, req_dict):
        '''
        获取数据模型树
        '''
        user_info = get_auth_token_info()
        keyWord = req_dict.get('keyWord', '')
        query = get_base_query(DataModel, sort_create_time=False).filter(DataModel.can_interface == 1, DataModel.status == 1)
        if user_info['username'] != 'admin':
            org_code = user_info.get('org_code')
            query = query.filter(DataModel.depart_list.like(f'%"{org_code}"%'))
        if keyWord != '':
            query = query.filter(DataModel.name.like(f'%"{keyWord}"%'))
        obj_list = query.all()
        res_data = get_datamodel_tree(obj_list)
        return gen_json_response(data=res_data)

    def get_obj_list(self, req_dict):
        '''
        获取列表
        '''
        page = int(req_dict.get('page', 1))
        pagesize = int(req_dict.get('pagesize', 10))
        query = get_base_query(DataModel)
        
        # 名称 查询逻辑
        name = req_dict.get('name', '')
        if name != '':
            query = query.filter(DataModel.name.like("%" + name + "%"))
        # 所属数据源 查询逻辑
        datasource_id = req_dict.get('datasource_id', '')
        if datasource_id != '':
            query = query.filter(DataModel.datasource_id == datasource_id)
        # 类型 查询逻辑
        _type = req_dict.get('type', '')
        if _type != '':
            query = query.filter(DataModel.type == _type)
        # 是否同步 查询逻辑
        is_sync = req_dict.get('is_sync', '')
        if is_sync != '':
            query = query.filter(DataModel.is_sync == is_sync)
        total = query.count()
        query = query.offset((page - 1) * pagesize)
        query = query.limit(pagesize)
        obj_list = query.all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_model(obj, ser_type='list')
            result.append(dic)
        res_data = {
            'records': result,
            'total': total
        }
        return gen_json_response(data=res_data)
    
    def get_obj_all_list(self, req_dict):
        '''
        获取全量列表
        '''
        auth_type = req_dict.get('auth_type', '')
        query = get_base_query(DataModel)
        obj_list = query.all()
        if auth_type != '':
            obj_list = [obj for obj in obj_list if auth_type in parse_json(obj.model_conf, {}).get('auth_type', '').split(',')]
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_model(obj, ser_type='all_list')
            result.append(dic)
        return gen_json_response(data=result)
    
    def get_obj_detail(self, req_dict):
        '''
        获取详情
        '''
        obj_id = req_dict.get('id')
        obj = db.session.query(DataModel).filter(
            DataModel.id == obj_id,
            DataModel.del_flag == 0).first()
        if not obj:
            return gen_json_response(code=400, msg='未找到数据')
        dic = serialize_datamodel_model(obj, ser_type='detail')
        return gen_json_response(data=dic)

    def add_obj(self, req_dict):
        '''
        添加
        '''
        # 名称 判重逻辑
        name = req_dict.get('name', '')
        if name != '':
            exist_obj = db.session.query(DataModel).filter(
                DataModel.datasource_id == req_dict.get('datasource_id', ''),
                DataModel.name == name,
                DataModel.del_flag == 0).first()
            if exist_obj:
                return gen_json_response(code=400, msg='字段"名称"已存在')
        obj = DataModel()
        for key in req_dict:
            if key in ['model_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'depart_list':
                li = req_dict.get(key, "").split(',')
                if li == ['']:
                    li = []
                setattr(obj, key, json.dumps(li))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        obj.id = gen_uuid(res_type='base')
        set_insert_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        # 创建后检查一次状态
        try:
            flag, extract_info = gen_extract_info({
                'model_id': obj.id,
            })
            if not flag:
                return gen_json_response(code=400, msg='未找到查询配置')
            flag, reader = get_reader_model(extract_info)
            if not flag:
                return gen_json_response(code=400, msg=reader)
            flag, res = reader.connect()
            if flag:
                obj.status = 1
            else:
                obj.status = 0
                print(res)
        except Exception as e:
            print(e)
            obj.status = 0
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='添加成功', extends={'success': True})
    
    def edit_obj(self, req_dict):
        '''
        编辑
        '''
        obj_id = req_dict.get('id')
        # 判重逻辑
        exist_query = db.session.query(DataModel).filter(DataModel.id != obj_id, DataModel.del_flag == 0)
        name = req_dict.get('name', '')
        if name != '':
            exist_query = exist_query.filter(DataModel.datasource_id == req_dict.get('datasource_id', ''), DataModel.name == name)
        exist_obj = exist_query.first()
        if exist_obj:
            return gen_json_response(code=400, msg='数据已存在')
        obj = db.session.query(DataModel).filter(DataModel.id == obj_id).first()
        if obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        for key in req_dict:
            if key in ['model_conf']:
                setattr(obj, key, json.dumps(req_dict[key], ensure_ascii=False, indent=2))
            elif key == 'depart_list':
                li = req_dict.get(key, "").split(',')
                if li == ['']:
                    li = []
                setattr(obj, key, json.dumps(li))
            elif key == 'ext_params':
                try:
                    json_value = json.loads(req_dict[key])
                    obj.ext_params = json.dumps(json_value, ensure_ascii=False, indent=2)
                except Exception as e:
                    return gen_json_response(code=400, msg='额外参数必须是json格式')
            else:
                setattr(obj, key, req_dict[key])
        set_update_user(obj)
        db.session.add(obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(msg='编辑成功', extends={'success': True})
    
    def delete_obj(self, req_dict):
        '''
        删除
        '''
        obj_id = req_dict['id']
        del_obj = db.session.query(DataModel).filter(DataModel.id == obj_id).first()
        if del_obj is None:
            return gen_json_response(code=400, msg='未找到数据')
        del_obj.del_flag = 1
        set_update_user(del_obj)
        db.session.add(del_obj)
        db.session.commit()
        db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def delete_batch(self, req_dict):
        '''
        批量删除
        '''
        del_ids = req_dict.get('ids')
        if isinstance(del_ids, str):
            del_ids = del_ids.split(',')
        del_objs = db.session.query(DataModel).filter(DataModel.id.in_(del_ids)).all()
        for del_obj in del_objs:
            del_obj.del_flag = 1
            set_update_user(del_obj)
            db.session.add(del_obj)
            db.session.commit()
            db.session.flush()
        return gen_json_response(code=200, msg='删除成功', extends={'success': True})
    
    def importExcel(self, file):
        '''
        excel导入
        '''
        try:
            df = pd.read_excel(file, dtype=object)
            df.fillna("", inplace=True)
            # 校验上传字段
            data_li = []
            n = 2
            for k, row in df.iterrows():
                row = row.to_dict()
                verify_dict = {
                    "name": {
                        "name": "名称",
                        "required": True
                    },
                    "is_sync": {
                        "name": "是否同步",
                        "required": True
                    }
                }
                not_valid = validate_params(row, verify_dict)
                if not_valid:
                    not_valid = {
                        'code': 400,
                        'msg': f'第{n}行{not_valid}'
                    }
                    return not_valid
                data_li.append(row)
                n += 1
            # 名称 判重逻辑
            name_list = [row.get('name', '') for row in data_li]
            if name_list != []:
                exist_obj = db.session.query(DataModel).filter(
                    DataModel.name.in_(name_list),
                    DataModel.del_flag == 0).first()
                if exist_obj:
                    return gen_json_response(code=400, msg='字段"名称"已存在')
            # 循环导入
            for row in data_li:
                obj = DataModel()
                for key in row:
                    if key in ['model_conf', 'ext_params']:
                        setattr(obj, key, json.dumps(row[key], ensure_ascii=False, indent=2))
                    else:
                        setattr(obj, key, row[key])
                obj.id = gen_uuid(res_type='base')
                set_insert_user(obj)
                db.session.add(obj)
                db.session.commit()
                db.session.flush()
            return gen_json_response(code=200, msg='导入成功', extends={'success': True})
        except Exception as e:
            return gen_json_response(code=500, msg=f'导入错误{e}')
    
    def exportXls(self, req_dict):
        '''
        导出excel
        '''
        selections = req_dict.get('selections', '')
        ids = selections.split(',')
        obj_list = db.session.query(DataModel).filter(DataModel.id.in_(ids)).all()
        result = []
        for obj in obj_list:
            dic = serialize_datamodel_model(obj, ser_type='list')
            result.append(dic)
        df = pd.DataFrame(result)
        print(df)
        # 使用字节流存储
        output = io.BytesIO()
        # 保存文件
        df.to_excel(output, index=False)
        # 文件seek位置，从头(0)开始
        output.seek(0)
        return output

    def get_dashboard_overview(self):
        '''
        获取数据模型总览数据
        '''
        try:
            # 获取总模型数
            total_count = DataModel.query.filter(DataModel.del_flag == 0).count()
            
            # 获取已建立模型数（status=1）
            established_count = DataModel.query.filter(
                DataModel.del_flag == 0,
                DataModel.status == 1
            ).count()
            
            # 获取未建立模型数（status=0）
            unestablished_count = DataModel.query.filter(
                DataModel.del_flag == 0,
                DataModel.status == 0
            ).count()
            
            # 获取可接口模型数（can_interface=1）
            interface_count = DataModel.query.filter(
                DataModel.del_flag == 0,
                DataModel.can_interface == 1
            ).count()
            
            return {
                'total': total_count,
                'established': established_count,
                'unestablished': unestablished_count,
                'interfaceCount': interface_count
            }
        except Exception as e:
            raise Exception(f"获取总览数据失败: {e}")

    def get_type_stats(self):
        '''
        获取数据模型类型统计
        '''
        try:
            from sqlalchemy import func
            results = db.session.query(
                DataModel.type,
                func.count(DataModel.id).label('count')
            ).filter(
                DataModel.del_flag == 0
            ).group_by(DataModel.type).all()
            
            return [{'type': result.type, 'count': result.count} for result in results]
        except Exception as e:
            raise Exception(f"获取类型统计失败: {e}")

    def get_creation_trend(self):
        '''
        获取数据模型创建趋势
        '''
        try:
            from sqlalchemy import func, extract
            from datetime import datetime, timedelta
            
            # 获取最近12个月的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=365)
            
            results = db.session.query(
                extract('year', DataModel.create_time).label('year'),
                extract('month', DataModel.create_time).label('month'),
                func.count(DataModel.id).label('count')
            ).filter(
                DataModel.del_flag == 0,
                DataModel.create_time >= start_date
            ).group_by(
                extract('year', DataModel.create_time),
                extract('month', DataModel.create_time)
            ).order_by(
                extract('year', DataModel.create_time),
                extract('month', DataModel.create_time)
            ).all()
            
            return [{'year': int(result.year), 'month': int(result.month), 'count': result.count} for result in results]
        except Exception as e:
            raise Exception(f"获取创建趋势失败: {e}")

    def get_field_stats(self):
        '''
        获取数据模型字段统计
        '''
        try:
            from web_apps.datamodel.db_models import DataModelField
            from sqlalchemy import func
            
            # 获取字段名称统计（使用field_name代替field_type）
            field_name_stats = db.session.query(
                DataModelField.field_name,
                func.count(DataModelField.id).label('count')
            ).join(DataModel, DataModelField.datamodel_id == DataModel.id).filter(
                DataModel.del_flag == 0,
                DataModelField.del_flag == 0
            ).group_by(DataModelField.field_name).all()
            
            # 获取每个模型的字段数量
            model_field_counts = db.session.query(
                DataModel.name,
                func.count(DataModelField.id).label('field_count')
            ).join(DataModelField, DataModel.id == DataModelField.datamodel_id).filter(
                DataModel.del_flag == 0,
                DataModelField.del_flag == 0
            ).group_by(DataModel.id, DataModel.name).all()
            
            return {
                'fieldTypeStats': [{'type': result.field_name or '未知', 'count': result.count} for result in field_name_stats],
                'modelFieldCounts': [{'model': result.name, 'fieldCount': result.field_count} for result in model_field_counts]
            }
        except Exception as e:
            raise Exception(f"获取字段统计失败: {e}")

    def get_iot_device_data(self):
        '''
        获取物联网设备数据 - 基于图表最新数据时间判断设备状态
        '''
        try:
            from datetime import datetime
            
            # 设备列表
            device_list = [
                {'device_id': 'WIFI2025062501', 'device_name': '07室环境监测', 'location': '07室'},
                {'device_id': 'WIFI2025062502', 'device_name': '08室环境监测', 'location': '08室'},
                {'device_id': 'WIFI2025062503', 'device_name': '09室环境监测', 'location': '09室'},
                {'device_id': 'WIFI2025062504', 'device_name': '02室环境监测', 'location': '02室'},
                {'device_id': 'WIFI2025062505', 'device_name': '01室环境监测', 'location': '01室'},
                {'device_id': 'XZD20250815', 'device_name': '室外环境检测仪', 'location': '室外'},
            ]
            
            # 获取当前时间
            current_time = datetime.now()
            offline_threshold = 10  # 10分钟
            
            device_data = []
            
            # 查找物联网相关的数据模型
            iot_models = db.session.query(DataModel).filter(
                DataModel.del_flag == 0,
                DataModel.status == 1,
                DataModel.name.like('%设备%')
            ).all()
            
            # 为每个设备获取最新数据时间并判断状态
            for device in device_list:
                device_id = device['device_id']
                latest_data_time = None
                
                # 从所有模型中查找该设备的最新数据
                for model in iot_models:
                    try:
                        from web_apps.datamodel.services.datamodel_query_api_service import DataModelQueryApiService
                        query_service = DataModelQueryApiService()
                        
                        # 查询该设备的最新数据
                        result = query_service.query_obj_data({
                            'id': model.id,
                            'page': 1,
                            'pagesize': 100,  # 获取更多数据以找到最新时间
                            'column': 'update_time',
                            'order': 'desc'
                        }, use_auth=False)
                        
                        if result.get('code') == 200 and result.get('data', {}).get('records'):
                            records = result['data']['records']
                            
                            # 查找该设备的最新数据
                            for record in records:
                                dev_num = record.get('device_num') or record.get('device_id')
                                if str(dev_num) == device_id:
                                    update_time = record.get('update_time')
                                    if update_time:
                                        try:
                                            # 解析时间戳
                                            if isinstance(update_time, str):
                                                if 'T' in update_time:
                                                    dt = datetime.fromisoformat(update_time.replace('Z', '+00:00'))
                                                else:
                                                    dt = datetime.strptime(update_time, '%Y-%m-%d %H:%M:%S')
                                                record_time = dt
                                            else:
                                                record_time = datetime.fromtimestamp(float(update_time) / 1000)
                                            
                                            # 更新最新数据时间
                                            if latest_data_time is None or record_time > latest_data_time:
                                                latest_data_time = record_time
                                        except Exception:
                                            continue
                    except Exception as e:
                        print(f"查询模型 {model.name} 数据失败: {e}")
                        continue
                
                # 判断设备状态
                if latest_data_time:
                    time_diff = (current_time - latest_data_time).total_seconds() / 60  # 转换为分钟
                    if time_diff <= offline_threshold:
                        status = '在线'
                    else:
                        status = '离线'
                else:
                    status = '离线'  # 没有数据，认为离线
                
                # 获取该设备的最新环境监测数据
                raw_data = {}
                if latest_data_time:
                    try:
                        import pymongo
                        client = pymongo.MongoClient('mongodb://admin:admin123@localhost:27017/ezdata?authSource=admin')
                        db_mongo = client['ezdata']
                        collection = db_mongo['env_device_factor_snapshot']
                        
                        # 获取该设备的最新因子数据
                        factor_docs = list(collection.find(
                            {'device_num': device_id},
                            sort=[('update_time', -1)]
                        ).limit(10))  # 获取最近10条记录
                        
                        # 提取各种环境因子数据
                        for doc in factor_docs:
                            factor_code = doc.get('factor_code', '')
                            factor_name = doc.get('factor_name', '')
                            factor_value = doc.get('factor_value', 0)
                            
                            # 标准因子代码映射
                            if factor_code == 'TEM' or factor_name == '温度':  # 温度
                                raw_data['TEM'] = factor_value
                            elif factor_code == 'RH' or factor_name == '湿度':  # 湿度
                                raw_data['RH'] = factor_value
                            elif factor_code == 'CO2' or factor_name == 'CO2':  # CO2
                                raw_data['CO2'] = factor_value
                            elif factor_code == 'PM25' or factor_name == 'PM2.5':  # PM2.5
                                raw_data['PM25'] = factor_value
                            elif factor_code == 'PM10' or factor_name == 'PM10':  # PM10
                                raw_data['PM10'] = factor_value
                            elif factor_code == 'NOISE' or factor_name == '噪声':  # 噪声
                                raw_data['NOISE'] = factor_value
                            
                            # 室外环境检测仪的特殊因子代码映射
                            elif factor_code == 'a01001':  # 温度
                                raw_data['TEM'] = factor_value
                            elif factor_code == 'a01002':  # 湿度
                                raw_data['RH'] = factor_value
                            elif factor_code == 'a01006':  # 大气压
                                raw_data['PRESSURE'] = factor_value
                            elif factor_code == 'a01007':  # 风速
                                raw_data['WIND_SPEED'] = factor_value
                            elif factor_code == 'a01008':  # 风向
                                raw_data['WIND_DIRECTION'] = factor_value
                            elif factor_code == 'a34004':  # PM2.5
                                raw_data['PM25'] = factor_value
                            elif factor_code == 'a34002':  # PM10
                                raw_data['PM10'] = factor_value
                        
                        client.close()
                    except Exception as e:
                        print(f"获取设备 {device_id} 环境数据失败: {e}")
                
                device_data.append({
                    'device_id': device_id,
                    'device_name': device['device_name'],
                    'status': status,
                    'location': device['location'],
                    'last_update': latest_data_time.timestamp() * 1000 if latest_data_time else 0,
                    'model_name': '实时设备数据',
                    'model_type': 'realtime',
                    'data_count': 5,  # 环境监测设备有5个因子，电表有1个因子
                    'raw_data': raw_data
                })
            
            return device_data
        except Exception as e:
            raise Exception(f"获取物联网设备数据失败: {e}")

    def _extract_field_value(self, record, possible_fields):
        '''
        从记录中提取字段值，尝试多种可能的字段名
        '''
        for field in possible_fields:
            if field in record and record[field] is not None and str(record[field]).strip():
                return str(record[field]).strip()
        return None

    def _generate_demo_device_data(self):
        '''
        生成演示设备数据
        '''
        import random
        from datetime import datetime, timedelta
        
        device_types = ['温度传感器', '湿度传感器', '压力传感器', '流量计', '摄像头', '门禁设备']
        locations = ['车间A', '车间B', '办公室', '仓库', '机房', '实验室']
        statuses = ['在线', '离线', '维护', '故障']
        
        demo_data = []
        for i in range(6):
            device_type = random.choice(device_types)
            location = random.choice(locations)
            status = random.choice(statuses)
            last_update = datetime.now() - timedelta(hours=random.randint(1, 72))
            
            demo_data.append({
                'model_name': '设备数据',
                'model_type': '物联网设备',
                'device_id': f"DEV_{str(i+1).zfill(3)}",
                'device_name': f"{device_type}_{i+1}",
                'status': status,
                'location': location,
                'last_update': last_update.strftime('%Y-%m-%d %H:%M:%S'),
                'data_count': random.randint(5, 15),
                'raw_data': {}
            })
        
        return demo_data

    def get_device_statistics(self):
        '''
        获取环境监测设备统计信息
        '''
        try:
            device_data = self.get_iot_device_data()
            # 按设备ID去重（同一设备的不同指标只计一次设备）
            unique_map = {}
            for d in device_data:
                dev_id = d.get('device_id') or d.get('model_name')
                if dev_id not in unique_map:
                    unique_map[dev_id] = d
            unique_devices = list(unique_map.values())
            
            # 统计设备状态
            status_stats = {}
            location_stats = {}
            model_stats = {}
            
            for device in unique_devices:
                # 状态统计
                status = device.get('status', '未知')
                status_stats[status] = status_stats.get(status, 0) + 1
                
                # 位置统计
                location = device.get('location', '未知')
                location_stats[location] = location_stats.get(location, 0) + 1
                
                # 模型统计
                model_name = device.get('model_name', '未知')
                model_stats[model_name] = model_stats.get(model_name, 0) + 1
            
            # 计算在线和离线设备数量
            online_devices = status_stats.get('在线', 0)
            offline_devices = status_stats.get('离线', 0)
            
            return {
                'total_devices': len(unique_devices),
                'online_devices': online_devices,
                'offline_devices': offline_devices,
                'status_distribution': [{'name': k, 'value': v} for k, v in status_stats.items()],
                'location_distribution': [{'name': k, 'value': v} for k, v in location_stats.items()],
                'model_distribution': [{'name': k, 'value': v} for k, v in model_stats.items()],
                'recent_devices': device_data[:10]  # 最近10条（包含不同指标）
            }
        except Exception as e:
            raise Exception(f"获取设备统计失败: {e}")

    def get_power_meter_statistics(self):
        '''
        获取电表设备统计信息
        '''
        try:
            from datetime import datetime, timedelta
            import pymongo
            
            # 电表设备列表
            power_meter_devices = [
                {'device_id': 'XZD20250731', 'device_name': '08室电表', 'location': '08室'},
                {'device_id': 'XZD20250732', 'device_name': '07室电表', 'location': '07室'},
                {'device_id': 'XZD20250734', 'device_name': '01室电表', 'location': '01室'},
            ]
            
            # 获取当前时间
            current_time = datetime.now()
            offline_threshold = 10  # 10分钟
            
            device_data = []
            online_count = 0
            offline_count = 0
            
            # 连接MongoDB获取真实数据
            client = pymongo.MongoClient('mongodb://admin:admin123@localhost:27017/ezdata?authSource=admin')
            db_mongo = client['ezdata']
            collection = db_mongo['env_device_factor_snapshot']
            
            # 为每个电表设备获取真实数据
            for device in power_meter_devices:
                device_id = device['device_id']
                
                # 获取该设备的最新数据
                latest_doc = collection.find_one(
                    {'device_num': device_id},
                    sort=[('update_time', -1)]
                )
                
                if latest_doc:
                    latest_time = latest_doc.get('update_time')
                    if latest_time:
                        # 判断设备状态
                        time_diff = (current_time - latest_time).total_seconds() / 60
                        status = '在线' if time_diff <= offline_threshold else '离线'
                        
                        if status == '在线':
                            online_count += 1
                        else:
                            offline_count += 1
                        
                        # 获取累计用电量（从power指标获取）
                        power_docs = list(collection.find(
                            {'device_num': device_id, 'factor_code': 'power'},
                            sort=[('update_time', -1)]
                        ).limit(1))
                        
                        total_power = 0
                        if power_docs:
                            total_power = float(power_docs[0].get('factor_value', 0))
                        
                        # 计算今日用电量（当前power减去今日0:00的power）
                        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0)
                        today_power_docs = list(collection.find(
                            {
                                'device_num': device_id, 
                                'factor_code': 'power',
                                'update_time': {'$gte': today_start}
                            },
                            sort=[('update_time', 1)]
                        ).limit(1))
                        
                        today_power = 0
                        if today_power_docs:
                            today_start_power = float(today_power_docs[0].get('factor_value', 0))
                            today_power = max(0, total_power - today_start_power)
                        
                        # 转换为本地时间字符串
                        if latest_time:
                            if isinstance(latest_time, str):
                                # 如果已经是字符串，直接使用
                                local_time_str = latest_time
                            else:
                                # 如果是datetime对象，转换为本地时间字符串
                                # 直接使用原始时间，不进行时区转换
                                local_time_str = latest_time.strftime('%a, %d %b %Y %H:%M:%S %Z')
                        else:
                            local_time_str = None
                            
                        device_data.append({
                            'device_name': device['device_name'],
                            'device_id': device_id,
                            'location': device['location'],
                            'status': status,
                            'last_update': local_time_str,
                            'total_power': round(total_power, 2),
                            'today_power': round(today_power, 2)
                        })
                    else:
                        offline_count += 1
                        device_data.append({
                            'device_name': device['device_name'],
                            'device_id': device_id,
                            'location': device['location'],
                            'status': '离线',
                            'last_update': None,
                            'total_power': 0,
                            'today_power': 0
                        })
                else:
                    offline_count += 1
                    device_data.append({
                        'device_name': device['device_name'],
                        'device_id': device_id,
                        'location': device['location'],
                        'status': '离线',
                        'last_update': None,
                        'total_power': 0,
                        'today_power': 0
                    })
            
            client.close()
            
            return {
                'total_devices': len(power_meter_devices),
                'online_devices': online_count,
                'offline_devices': offline_count,
                'recent_devices': device_data
            }
            
        except Exception as e:
            print(f"获取电表设备统计失败: {e}")
            return {
                'total_devices': 0,
                'online_devices': 0,
                'offline_devices': 0,
                'recent_devices': []
            }

    def get_device_metrics(self, device_name: str, start_ts: int, end_ts: int):
        '''
        按设备名称与时间范围获取多指标时序数据
        :param device_name: 设备名称（如“07室环境监测”）
        :param start_ts: 开始时间的毫秒时间戳
        :param end_ts: 结束时间的毫秒时间戳
        '''
        try:
            # 统一时区：默认 UTC+8，可通过环境变量覆盖（分钟偏移）
            import os
            from datetime import timezone, timedelta, datetime as _dt
            tz_offset_minutes_env = os.getenv('EZDATA_TZ_OFFSET_MINUTES')
            try:
                tz_offset_minutes = int(tz_offset_minutes_env) if tz_offset_minutes_env is not None else 480
            except Exception:
                tz_offset_minutes = 480
            tz_offset = timedelta(minutes=tz_offset_minutes)

            # 名称→编号映射（可后续改为读库）
            name_to_id = {
                '07室环境监测': 'WIFI2025062501',
                '08室环境监测': 'WIFI2025062502',
                '09室环境监测': 'WIFI2025062503',
                '01室环境监测': 'WIFI2025062505',
                '02室环境监测': 'WIFI2025062504',
                '室外环境检测仪': 'XZD20250815',
                '08室电表': 'XZD20250731',
                '07室电表': 'XZD20250732',
                '01室电表': 'XZD20250734',
            }
            device_num = name_to_id.get(device_name, '')

            # 从“设备数据”模型分页读取一定量数据后在内存中过滤
            from web_apps.datamodel.services.datamodel_query_api_service import DataModelQueryApiService
            query_service = DataModelQueryApiService()

            # 找出包含“设备”的已启用模型
            iot_models = db.session.query(DataModel).filter(
                DataModel.del_flag == 0,
                DataModel.status == 1,
                DataModel.name.like('%设备%')
            ).all()

            # 时间转换函数
            def to_ms(v):
                # 统一把多种 update_time 表达转成毫秒（字符串按本地时区 UTC+offset 解释）
                try:
                    # Mongo 扩展JSON：{"$date": 1754724322000}
                    if isinstance(v, dict) and '$date' in v:
                        return int(v['$date'])
                    # 字符串：2025-09-17T15:08:08Z 或 2025-09-17 15:08:08
                    if isinstance(v, str):
                        if v.endswith('Z'):
                            # UTC 时间，直接解析
                            from datetime import datetime
                            dt = datetime.fromisoformat(v.replace('Z', '+00:00'))
                            return int(dt.timestamp() * 1000)
                        else:
                            # 本地时间，按配置的时区偏移解释
                            from datetime import datetime
                            dt = datetime.fromisoformat(v)
                            # 应用时区偏移
                            dt = dt.replace(tzinfo=timezone(tz_offset))
                            return int(dt.timestamp() * 1000)
                    # 数字：直接返回
                    if isinstance(v, (int, float)):
                        return int(v)
                except Exception as e:
                    print(f"时间解析失败: {v}, 错误: {e}")
                    return None
                return None

            records = []
            for model in iot_models:
                page = 1
                pagesize = 1000  # 单页最多1000
                max_records = 20000  # 最多抓取2万条/模型
                fetched = 0
                # 按更新时间倒序分页，直到覆盖到起始时间或无更多数据
                while True:
                    result = query_service.query_obj_data({
                        'id': model.id,
                        'page': page,
                        'pagesize': pagesize,
                        'column': 'update_time',  # 按更新时间排序
                        'order': 'desc'  # 倒序，最新数据在前
                    }, use_auth=False)
                    if result.get('code') != 200:
                        break
                    data = result.get('data', {})
                    recs = data.get('records', [])
                    if not recs:
                        break
                    records.extend(recs)
                    fetched += len(recs)

                    # 提前退出：如果当前批次的最新时间已早于查询窗口，说明已覆盖到起点
                    latest_time = None
                    for rec in recs:
                        ts = to_ms(rec.get('update_time', ''))
                        if ts and (latest_time is None or ts > latest_time):
                            latest_time = ts
                    if latest_time and latest_time < start_ts:
                        break

                    if len(recs) < pagesize:
                        break  # 没有更多数据
                    if fetched >= max_records:
                        break  # 达到安全上限
                    page += 1

            # 若未命中包含“设备”的模型，回退到所有启用模型中继续查找
            if not iot_models:
                iot_models = db.session.query(DataModel).filter(
                    DataModel.del_flag == 0,
                    DataModel.status == 1,
                ).all()

            # 过滤：设备编号+时间

            filtered = []
            for r in records:
                dev_num = r.get('device_num') or r.get('deviceNum') or r.get('device_id')
                if device_num and str(dev_num) != device_num:
                    continue
                ts = to_ms(r.get('update_time'))
                if ts is None:
                    continue
                if start_ts <= ts <= end_ts:
                    filtered.append(r)

            # 指标分组
            from collections import defaultdict
            series_map = defaultdict(list)
            unit_map = {}
            

            # 用于去重的字典：{code: {timestamp: {value, record_time}}}
            dedup_map = defaultdict(dict)
            
            for r in filtered:
                code = r.get('factor_code') or r.get('code') or ''
                # 注意：不能用 "or" 读取数值，否则 0 会被当作假值丢弃
                val = r.get('factor_value')
                if val is None:
                    val = r.get('value')
                unit = r.get('factor_unit') or r.get('unit') or ''
                ts = to_ms(r.get('update_time'))
                try:
                    val_f = float(str(val))
                except Exception:
                    continue
                
                # 获取记录的创建时间或更新时间作为排序依据
                record_time = r.get('created_at') or r.get('update_time') or r.get('create_time')
                if isinstance(record_time, str):
                    try:
                        if 'T' in record_time:
                            record_timestamp = datetime.fromisoformat(record_time.replace('Z', '+00:00')).timestamp()
                        else:
                            record_timestamp = datetime.strptime(record_time, '%Y-%m-%d %H:%M:%S').timestamp()
                    except:
                        record_timestamp = ts / 1000  # 使用时间戳作为备选
                else:
                    record_timestamp = ts / 1000
                
                # 去重逻辑：同一时间戳只保留最新的记录（基于记录时间）
                # 如果记录时间相同，则保留数值较大的那个（通常表示更新的数据）
                if ts not in dedup_map[code]:
                    dedup_map[code][ts] = {'value': val_f, 'record_time': record_timestamp}
                elif record_timestamp > dedup_map[code][ts]['record_time']:
                    dedup_map[code][ts] = {'value': val_f, 'record_time': record_timestamp}
                elif record_timestamp == dedup_map[code][ts]['record_time'] and val_f > dedup_map[code][ts]['value']:
                    # 如果记录时间相同，保留数值较大的
                    dedup_map[code][ts] = {'value': val_f, 'record_time': record_timestamp}
                unit_map[code] = unit

            # 将去重后的数据转换为列表格式
            for code, time_values in dedup_map.items():
                for ts, data in time_values.items():
                    series_map[code].append({'t': ts, 'v': data['value']})

            # 每个序列按时间排序
            for code in series_map:
                series_map[code] = sorted(series_map[code], key=lambda x: x['t'])
            
            # 判断是否为电表设备
            is_power_device = '电表' in device_name if device_name else False
            
            # 指标代码映射：优先使用标准代码，避免重复显示
            metric_priority = {
                'CO2': ['CO2'],
                'PM10': ['PM10', 'a34002'], 
                'PM25': ['PM25', 'a34004'],
                'TEM': ['TEM', 'a01001'],
                'RH': ['RH', 'a01002'],
                'WIND_SPEED': ['WIND_SPEED', 'a01007'],
                'WIND_DIRECTION': ['WIND_DIRECTION', 'a01008'],
                'PRESSURE': ['PRESSURE', 'a01006']
            }
            
            # 对于电表设备，将所有指标统一映射为power
            if is_power_device:
                # 合并所有电表指标数据到power
                power_series = []
                power_unit = ''
                for code, data in series_map.items():
                    if data:  # 只处理有数据的指标
                        power_series.extend(data)
                        # 优先使用kW单位
                        unit = unit_map.get(code, '')
                        if 'kW' in unit or 'kw' in unit.lower() or '千瓦' in unit:
                            power_unit = unit
                        elif not power_unit and unit:
                            power_unit = unit
                
                # 按时间排序并去重
                if power_series:
                    # 按时间戳排序
                    power_series = sorted(power_series, key=lambda x: x.get('t', 0))
                    # 简单去重：同一时间戳保留最后一个值
                    dedup_power = {}
                    for item in power_series:
                        ts = item.get('t', 0)
                        dedup_power[ts] = item
                    power_series = sorted(dedup_power.values(), key=lambda x: x.get('t', 0))
                    
                    # 统一使用power作为指标名称
                    series_map = {'power': power_series}
                    unit_map = {'power': power_unit or 'kW'}
                    filtered_series = series_map
                else:
                    filtered_series = {}
            else:
                # 环境监测设备的原有逻辑
                # 过滤重复指标，只保留优先级最高的
                filtered_series = {}
                for standard_name, codes in metric_priority.items():
                    best_code = None
                    best_count = 0
                    for code in codes:
                        if code in series_map and len(series_map[code]) > best_count:
                            best_code = code
                            best_count = len(series_map[code])
                    if best_code:
                        filtered_series[best_code] = series_map[best_code]
                
                # 保留其他指标以及未在priority中处理的指标
                for code, data in series_map.items():
                    if code not in filtered_series:
                        # 只排除已经通过priority处理过的低优先级代码
                        excluded_codes = []
                        for standard_name, codes in metric_priority.items():
                            if len(codes) > 1:  # 如果有多个代码选项
                                excluded_codes.extend(codes[1:])  # 排除除第一个外的其他代码
                        
                        if code not in excluded_codes:
                            filtered_series[code] = data
            
            series_map = filtered_series

            return {
                'deviceName': device_name,
                'deviceNum': device_num,
                'units': unit_map,
                'series': series_map,
                'timeRange': {'start': start_ts, 'end': end_ts},
                'tzOffsetMinutes': tz_offset_minutes,
            }
        except Exception as e:
            raise Exception(f"获取设备时序失败: {e}")

    def get_daily_power_trend(self, days=7):
        '''
        获取日用电量趋势数据
        '''
        try:
            from datetime import datetime, timedelta
            import pymongo

            # 电表设备列表
            power_meter_devices = [
                {'device_id': 'XZD20250731', 'device_name': '08室电表', 'location': '08室'},
                {'device_id': 'XZD20250732', 'device_name': '07室电表', 'location': '07室'},
                {'device_id': 'XZD20250734', 'device_name': '01室电表', 'location': '01室'},
            ]

            # 连接MongoDB获取历史数据
            client = pymongo.MongoClient('mongodb://admin:admin123@localhost:27017/ezdata?authSource=admin')
            db_mongo = client['ezdata']
            collection = db_mongo['env_device_factor_snapshot']

            # 获取近N天的数据
            end_date = datetime.now()
            start_date = end_date - timedelta(days=days)
            
            daily_trend = []
            
            for i in range(days):
                current_date = end_date - timedelta(days=i)
                date_str = current_date.strftime('%Y-%m-%d')
                
                # 计算当天的总用电量
                daily_total = 0
                
                for device in power_meter_devices:
                    device_id = device['device_id']
                    
                    # 获取当天的数据范围
                    day_start = current_date.replace(hour=0, minute=0, second=0, microsecond=0)
                    day_end = current_date.replace(hour=23, minute=59, second=59, microsecond=999999)
                    
                    # 获取当天最早的数据
                    start_doc = collection.find_one(
                        {
                            'device_num': device_id,
                            'factor_code': 'power',
                            'update_time': {'$gte': day_start, '$lte': day_end}
                        },
                        sort=[('update_time', 1)]
                    )
                    
                    # 获取当天最新的数据
                    end_doc = collection.find_one(
                        {
                            'device_num': device_id,
                            'factor_code': 'power',
                            'update_time': {'$gte': day_start, '$lte': day_end}
                        },
                        sort=[('update_time', -1)]
                    )
                    
                    # 如果当天没有数据，尝试获取最近的数据
                    if not start_doc and not end_doc:
                        # 获取该设备最近的数据
                        recent_doc = collection.find_one(
                            {
                                'device_num': device_id,
                                'factor_code': 'power'
                            },
                            sort=[('update_time', -1)]
                        )
                        if recent_doc:
                            # 如果最近数据是今天的，使用它
                            if recent_doc.get('update_time').date() == current_date.date():
                                end_doc = recent_doc
                    
                    if start_doc and end_doc:
                        start_power = float(start_doc.get('factor_value', 0))
                        end_power = float(end_doc.get('factor_value', 0))
                        daily_consumption = max(0, end_power - start_power)
                        daily_total += daily_consumption
                    elif end_doc:
                        # 如果只有结束数据，使用结束数据作为当天用电量
                        daily_total += float(end_doc.get('factor_value', 0))
                
                daily_trend.append({
                    'date': date_str,
                    'dayName': current_date.strftime('%a'),
                    'value': round(daily_total, 2)
                })
            
            client.close()
            
            # 按日期正序排列
            daily_trend.reverse()
            
            return daily_trend

        except Exception as e:
            print(f"获取日用电量趋势失败: {e}")
            # 返回模拟数据作为备选
            return [
                {'date': '2025-09-18', 'dayName': 'Wed', 'value': 35},
                {'date': '2025-09-19', 'dayName': 'Thu', 'value': 28},
                {'date': '2025-09-20', 'dayName': 'Fri', 'value': 42},
                {'date': '2025-09-21', 'dayName': 'Sat', 'value': 31},
                {'date': '2025-09-22', 'dayName': 'Sun', 'value': 38},
                {'date': '2025-09-23', 'dayName': 'Mon', 'value': 25},
                {'date': '2025-09-24', 'dayName': 'Tue', 'value': 33}
            ]
