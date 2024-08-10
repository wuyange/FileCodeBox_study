import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List
from functools import lru_cache

BASE_DIR = Path(__file__).resolve().parent.parent
data_root = BASE_DIR / 'data'

log_root = BASE_DIR / 'logs'

if not log_root.exists():
    log_root.mkdir(parents=True, exist_ok=True)

if not data_root.exists():
    data_root.mkdir(parents=True, exist_ok=True)

class DefaultSettings(BaseSettings):
    # index
    name:str =  '文件快递柜 - FileCodeBox'
    description:str =  '开箱即用的文件快传系统'
    notify_title:str =  '系统通知'
    notify_content:str =  '欢迎使用 FileCodeBox，本程序开源于 <a href="https://github.com/vastsa/FileCodeBox" target="_blank">Github</a> ，欢迎Star和Fork。'
    page_explain:str =  '请勿上传或分享违法内容。根据《中华人民共和国网络安全法》、《中华人民共和国刑法》、《中华人民共和国治安管理处罚法》等相关规定。 传播或存储违法、违规内容，会受到相关处罚，严重者将承担刑事责任。本站坚决配合相关部门，确保网络内容的安全，和谐，打造绿色网络环境。'
    keywords:str =  'FileCodeBox, 文件快递柜, 口令传送箱, 匿名口令分享文本, 文件'
    robotsText:str = 'User-agent: *\nDisallow: /'

    # file
    file_storage:str =  'local'
    max_save_seconds:int = 0
    openUpload:int = 1
    uploadSize:int = 1024 * 1024 * 10
    expireStyle:List[str] = ['day', 'hour', 'minute', 'forever', 'count']
    opacity:float = 0.9
    background:str = ''
    uploadMinute:int = 1
    uploadCount:int = 10
    errorMinute:int = 1
    errorCount:int = 1
    error_count = 2
    error_time_window = 60
    request_count = 10
    request_time_window = 60
    update_count = 2
    update_time_window = 60

    # server
    admin_token:str = 'FileCodeBox2023'
    port:int = 80
    showAdminAddr:int = 0
    
    # redis
    redis_host:str = '127.0.0.1'
    redis_port:int = 6379
    redis_username:str = 'root'
    redis_password:str = 'YS@147258'
    redis_db:int = 1
    
    
class UserSettings(DefaultSettings):
    pass

settings = UserSettings()

