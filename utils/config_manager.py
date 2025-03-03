#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
配置管理模块，负责加载和保存应用程序配置
"""

import os
import json


class ConfigManager:
    """配置管理类，处理程序设置的加载与保存"""
    
    def __init__(self):
        """初始化配置管理器"""
        self.config_file = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'config.json')
        self.config = self._get_default_config()
    
    def _get_default_config(self):
        """获取默认配置"""
        return {
            "window": {
                "width": 1200,
                "height": 800,
                "title": "Hair Ezclick"
            },
            "renderer": {
                "width": 800,
                "height": 600,
                "background_color": [1, 1, 1],  # 白色背景
                "point_size": 2.0
            },
            "view": {
                "zoom": 0.8,
                "front": [0, 0, -1],
                "up": [0, 1, 0]
            },
            "paths": {
                "icons": "icons/",
                "models": "models/",
                "temp": "temp/"
            },
            "backend": {
                "url": "http://localhost:5000/api",
                "timeout": 30
            },
            "editor": {
                "brush_size": 10,
                "default_density": "中",
                "default_align": "选项1"
            }
        }
    
    def load_config(self):
        """加载配置文件，如果不存在则使用默认配置"""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # 合并加载的配置与默认配置，确保所有必要的键都存在
                    self._merge_config(self.config, loaded_config)
            else:
                # 如果配置文件不存在，创建默认配置文件
                self.save_config()
        except Exception as e:
            print(f"加载配置文件出错: {str(e)}")
    
    def _merge_config(self, default_config, loaded_config):
        """递归合并配置，以确保所有必要的键都存在"""
        for key, value in default_config.items():
            if key in loaded_config:
                if isinstance(value, dict) and isinstance(loaded_config[key], dict):
                    self._merge_config(value, loaded_config[key])
                else:
                    default_config[key] = loaded_config[key]
    
    def save_config(self):
        """保存当前配置到文件"""
        try:
            config_dir = os.path.dirname(self.config_file)
            if not os.path.exists(config_dir):
                os.makedirs(config_dir)
                
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(self.config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"保存配置文件出错: {str(e)}")
    
    def get_value(self, section, key, default=None):
        """获取指定配置值"""
        try:
            return self.config[section][key]
        except (KeyError, TypeError):
            return default
    
    def set_value(self, section, key, value):
        """设置指定配置值"""
        if section not in self.config:
            self.config[section] = {}
        self.config[section][key] = value
