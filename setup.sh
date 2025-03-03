#!/bin/bash

# Hair Ezclick - 环境安装脚本
echo "开始安装 Hair Ezclick 环境..."

# 检查Python版本
python_version=$(python3 --version 2>&1 | awk '{print $2}')
echo "检测到Python版本: $python_version"

# 检查是否已安装Conda
if command -v conda &> /dev/null; then
    echo "找到Conda安装..."
    
    # 创建Conda环境
    read -p "是否创建新的Conda环境 'open3d_ezclick'? (y/n): " create_env
    if [ "$create_env" = "y" ]; then
        echo "创建Conda环境 'open3d_ezclick'..."
        conda create -y --name open3d_ezclick python=3.9
        echo "激活环境..."
        eval "$(conda shell.bash hook)"
        conda activate open3d_ezclick
    else
        echo "跳过环境创建..."
    fi
else
    echo "未找到Conda，将在当前Python环境中安装依赖..."
fi

# 安装基础依赖
echo "安装基础依赖..."
pip install -U pip
pip install open3d PySide6 numpy requests

# 安装可视化和数据处理依赖
echo "安装可视化和数据处理依赖..."
pip install matplotlib scipy pandas

# 创建项目目录结构
read -p "是否创建项目目录结构? (y/n): " create_dirs
if [ "$create_dirs" = "y" ]; then
    echo "创建项目目录结构..."
    mkdir -p utils gui renderer icons
    
    # 创建__init__.py文件
    echo '"""工具包，包含各种辅助功能类"""' > utils/__init__.py
    echo '"""图形界面包，包含所有UI相关组件"""' > gui/__init__.py
    echo '"""渲染器包，负责3D模型的渲染"""' > renderer/__init__.py
    
    echo "项目目录结构创建完成！"
fi

echo "检查安装的依赖库..."
pip list | grep -E 'open3d|PySide6|numpy|requests|matplotlib|scipy|pandas'

echo "安装完成！"
echo "请运行 'python run.py' 启动应用程序。"
