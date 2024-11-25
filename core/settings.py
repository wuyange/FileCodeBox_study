import json
from pathlib import Path
from pydantic_settings import BaseSettings
from typing import List

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
    notify_content:str =  '欢迎使用 FileCodeBox'
    page_explain:str =  '请勿上传或分享违法内容。根据《中华人民共和国网络安全法》、《中华人民共和国刑法》、《中华人民共和国治安管理处罚法》等相关规定。 传播或存储违法、违规内容，会受到相关处罚，严重者将承担刑事责任。本站坚决配合相关部门，确保网络内容的安全，和谐，打造绿色网络环境。'
    keywords:str =  'FileCodeBox, 文件快递柜, 口令传送箱, 匿名口令分享文本, 文件'
    robotsText:str = 'User-agent: *\nDisallow: /'

    # file
    file_storage:str =  'local'
    max_save_seconds:int = 0
    openUpload:int = 1
    textSize:int = 2000
    uploadSize:int = 1024 * 1024 * 10 * 1024
    expireStyle:List[str] = ['day', 'hour', 'minute', 'forever', 'count']
    opacity:float = 0.9
    background:str = ''
    error_count:int = 100
    error_time_window:int = 60
    request_count:int = 10
    request_time_window:int = 120
    update_count:int = 2
    update_time_window:int = 60
    
    # github
    client_id:str = 'Ov23liXjjeEA88J7Oof7'
    client_secrets:str = '98a0c01358b141719801f5dec3d60dc884d62f10'
    redirect_uri:str = 'http://101.35.228.190/admin/callback'

    # server
    admin_token:str = 'FileCodeBox2023'
    port:int = 80
    showAdminAddr:int = 0
    
    # redis
    redis_host:str = '101.35.228.190'
    redis_port:int = 6379
    redis_username:str = 'default'
    redis_password:str = 'YS@147258'
    redis_db:int = 1
    
    #mysql
    # mysql_host:str = 'cd-cdb-ewkh09j8.sql.tencentcdb.com'
    # mysql_password:str = 'YS147258'
    mysql_host:str = 'localhost'
    mysql_password:str = '123456'
    mysql_user:str = 'root'
    mysql_port:int = 3306
    mysql_database:str = 'filecodebox'
    mysql_echo:bool = True
    mysql_pool_size:int = 20
    mysql_max_overflow:int = 0
    mysql_driver:str = 'mysql+aiomysql'
    
    
class UserSettings(DefaultSettings):
    pass

settings = UserSettings()

