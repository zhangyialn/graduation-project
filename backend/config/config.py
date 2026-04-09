# config.py
import os
from dotenv import load_dotenv, find_dotenv

# 加载环境变量
load_dotenv(find_dotenv())

class Config:
    
    # 数据库配置
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'mysql+pymysql://root:123456@localhost:3306/graduation-project')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT配置
    JWT_SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-this-in-production')
    JWT_ACCESS_TOKEN_EXPIRES = 3600
    JWT_REFRESH_TOKEN_EXPIRES = 604800
    BOOTSTRAP_ADMIN_KEY = os.getenv('BOOTSTRAP_ADMIN_KEY', '')
    BOOTSTRAP_TOKEN_EXPIRES = int(os.getenv('BOOTSTRAP_TOKEN_EXPIRES', '600'))
    BOOTSTRAP_LOCAL_ONLY = os.getenv('BOOTSTRAP_LOCAL_ONLY', 'true').lower() == 'true'

    # 腾讯云文本翻译（TMT）配置
    TENCENT_SECRET_ID = os.getenv('TENCENT_SECRET_ID', 'AKIDMmyxhEXq7NXUO4VhfOs65pjSxBByWrxt')
    TENCENT_SECRET_KEY = os.getenv('TENCENT_SECRET_KEY', 'mKqIYmzykH1hFj6KL9j5D7oIYaNvELDs')
    TENCENT_TMT_REGION = os.getenv('TENCENT_TMT_REGION', 'ap-beijing')
    TENCENT_TMT_TIMEOUT = int(os.getenv('TENCENT_TMT_TIMEOUT', '5'))