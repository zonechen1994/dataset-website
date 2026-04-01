#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
时区处理工具模块
统一处理应用中的时间和时区问题
"""

from datetime import datetime, timezone, timedelta
import pytz
import os

# 中国时区
CHINA_TZ = pytz.timezone('Asia/Shanghai')

def get_china_time():
    """获取中国当前时间"""
    return datetime.now(CHINA_TZ)

def get_china_datetime():
    """获取中国当前时间（不带时区信息，用于数据库存储）"""
    return datetime.now(CHINA_TZ).replace(tzinfo=None)

def utc_to_china(utc_dt):
    """将UTC时间转换为中国时间"""
    if utc_dt is None:
        return None
    
    # 如果没有时区信息，假设是UTC
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=pytz.UTC)
    
    # 转换为中国时区
    china_dt = utc_dt.astimezone(CHINA_TZ)
    return china_dt.replace(tzinfo=None)

def china_to_utc(china_dt):
    """将中国时间转换为UTC时间"""
    if china_dt is None:
        return None
    
    # 如果没有时区信息，假设是中国时区
    if china_dt.tzinfo is None:
        china_dt = CHINA_TZ.localize(china_dt)
    
    # 转换为UTC
    utc_dt = china_dt.astimezone(pytz.UTC)
    return utc_dt.replace(tzinfo=None)

def format_china_time(dt, format_str='%Y-%m-%d %H:%M:%S'):
    """格式化显示中国时间"""
    if dt is None:
        return "未知"
    
    # 如果是UTC时间，先转换为中国时间
    if isinstance(dt, datetime):
        # 假设数据库中存储的是UTC时间，转换为中国时间显示
        china_dt = utc_to_china(dt)
        return china_dt.strftime(format_str)
    
    return str(dt)

def get_timestamp_filename():
    """获取带时间戳的文件名前缀（中国时间）"""
    return get_china_time().strftime('%Y%m%d_%H%M%S_')

def get_current_time_str():
    """获取当前时间字符串（中国时间）"""
    return get_china_time().strftime('%Y-%m-%d %H:%M:%S')

def ensure_timezone_env():
    """确保环境变量设置了正确的时区"""
    os.environ['TZ'] = 'Asia/Shanghai'
    
    # 在某些系统上需要调用tzset
    try:
        import time
        time.tzset()
    except (AttributeError, ImportError):
        # Windows系统没有tzset
        pass

# 模块加载时自动设置时区
ensure_timezone_env()

if __name__ == '__main__':
    # 测试时区转换
    print("时区工具测试：")
    print(f"中国当前时间: {get_china_time()}")
    print(f"中国当前时间(无时区): {get_china_datetime()}")
    print(f"UTC当前时间: {datetime.utcnow()}")
    print(f"格式化时间: {get_current_time_str()}")
    print(f"文件名时间戳: {get_timestamp_filename()}")
    
    # 测试转换
    utc_time = datetime.utcnow()
    china_time = utc_to_china(utc_time)
    print(f"UTC {utc_time} -> 中国时间 {china_time}")