#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据接口模块，用于与后端服务进行数据交换
"""

import json
import requests
from PySide6.QtCore import QObject, Signal


class DataInterface(QObject):
    """数据接口类，处理与后端服务的通信"""
    
    # 信号定义
    data_received = Signal(dict)
    model_received = Signal(str)  # 接收到模型后发出的信号，参数为临时文件路径
    connection_error = Signal(str)
    processing_complete = Signal(dict)
    
    def __init__(self, config=None):
        """初始化数据接口"""
        super().__init__()
        self.config = config
        self.base_url = config.get_value("backend", "url", "http://localhost:5000/api") if config else "http://localhost:5000/api"
        self.timeout = config.get_value("backend", "timeout", 30) if config else 30
        self.session = requests.Session()
    
    def connect_to_backend(self):
        """测试与后端的连接"""
        try:
            response = self.session.get(f"{self.base_url}/status", timeout=self.timeout)
            if response.status_code == 200:
                return True, "连接成功"
            else:
                return False, f"连接失败: HTTP {response.status_code}"
        except requests.RequestException as e:
            return False, f"连接错误: {str(e)}"
    
    def send_model_to_backend(self, file_path, params=None):
        """
        将模型文件发送到后端进行处理
        
        Args:
            file_path (str): 模型文件路径
            params (dict): 附加参数
            
        Returns:
            bool: 是否成功
            str: 成功或错误信息
        """
        try:
            url = f"{self.base_url}/process_model"
            
            with open(file_path, 'rb') as f:
                files = {'model': f}
                
                data = {}
                if params:
                    data = params
                
                response = self.session.post(url, files=files, data=data, timeout=self.timeout)
                
                if response.status_code == 200:
                    result = response.json()
                    self.processing_complete.emit(result)
                    return True, "处理成功"
                else:
                    return False, f"处理失败: HTTP {response.status_code}"
        except Exception as e:
            self.connection_error.emit(str(e))
            return False, f"发送错误: {str(e)}"
    
    def get_model_from_backend(self, model_id):
        """
        从后端获取处理后的模型
        
        Args:
            model_id (str): 模型ID
            
        Returns:
            bool: 是否成功
            str: 成功则返回临时文件路径，失败则返回错误信息
        """
        import tempfile
        import os
        
        try:
            url = f"{self.base_url}/get_model/{model_id}"
            response = self.session.get(url, timeout=self.timeout, stream=True)
            
            if response.status_code == 200:
                # 创建临时文件保存模型
                temp_dir = tempfile.gettempdir()
                file_path = os.path.join(temp_dir, f"temp_model_{model_id}.pcd")
                
                with open(file_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.model_received.emit(file_path)
                return True, file_path
            else:
                error_msg = f"获取模型失败: HTTP {response.status_code}"
                self.connection_error.emit(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"获取模型错误: {str(e)}"
            self.connection_error.emit(error_msg)
            return False, error_msg
    
    def send_edit_request(self, model_id, edit_data):
        """
        发送编辑请求到后端
        
        Args:
            model_id (str): 模型ID
            edit_data (dict): 编辑数据
            
        Returns:
            bool: 是否成功
            str: 成功或错误信息
        """
        try:
            url = f"{self.base_url}/edit_model/{model_id}"
            headers = {'Content-Type': 'application/json'}
            
            response = self.session.post(
                url, 
                data=json.dumps(edit_data), 
                headers=headers, 
                timeout=self.timeout
            )
            
            if response.status_code == 200:
                result = response.json()
                self.data_received.emit(result)
                return True, "编辑请求已发送"
            else:
                error_msg = f"编辑请求失败: HTTP {response.status_code}"
                self.connection_error.emit(error_msg)
                return False, error_msg
        except Exception as e:
            error_msg = f"发送编辑请求错误: {str(e)}"
            self.connection_error.emit(error_msg)
            return False, error_msg
