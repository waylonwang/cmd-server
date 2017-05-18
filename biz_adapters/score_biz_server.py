import json

import requests

from msg_src_adapter import ConfigurationError


class ScoreBizAdapter():
    '''
    积分业务系统适配器，作为CloudValley QQBot项目架构层MVC模式的Model层，通过HTTP API方式承接积分相关的数据存储与查询服务
    '''

    def __init__(self, config: dict):
        '''
        初始化
        :param config: 配置项
        '''
        if not config.get('api_url'):
            raise ConfigurationError
        self.api_url = config['api_url']
        self.api_key = config.get('api_key')
        self.session = requests.Session()
        if self.api_key:
            self.session.headers['Authorization'] = json.dumps({'api_key': self.api_key})

    def post(self, api: str, **kwargs):
        '''
        POST方法
        :param api: API URL
        :param kwargs: 参数
        :return: 对象
        '''
        result = self.session.post(self.api_url + api, params=kwargs).json()
        if result.get('success') == 1:
            return result.get('data')
        else:
            return None

    def put(self, api, **kwargs):
        '''
        PUT方法
        :param api: API URL
        :param kwargs: 参数
        :return: 对象
        '''
        result = self.session.put(self.api_url + api, params=kwargs).json()
        if result.get('success') == 1:
            return result.get('data')
        else:
            return None

    def patch(self, api, **kwargs):
        '''
        PATCH方法
        :param api: API URL
        :param kwargs: 参数
        :return: 对象
        '''
        result = self.session.patch(self.api_url + api, params=kwargs).json()
        if result.get('success') == 1:
            return result.get('data')
        else:
            return None

    def get(self, api, **kwargs):
        '''
        GET方法
        :param api: API URL
        :param kwargs: 参数
        :return: 对象 
        '''
        result = self.session.get(self.api_url + api, params=kwargs).json()
        if result.get('success') == 1:
            return result.get('data')
        else:
            return None

    def delete(self, api, **kwargs):
        '''
        DELETE方法
        :param api: API URL
        :param kwargs: 参数
        :return: 对象  
        '''
        result = self.session.delete(self.api_url + api, params=kwargs).json()
        if result.get('success') == 1:
            return result.get('data')
        else:
            return None
