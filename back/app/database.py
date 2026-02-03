# app/database.py
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# 格式: mysql+pymysql://用户名:密码@地址:端口/数据库名
SQLALCHEMY_DATABASE_URL = "mysql+pymysql://root:123456@localhost:3306/ai_interview"

engine = create_engine(SQLALCHEMY_DATABASE_URL, pool_recycle=3600)  # 防止长时间连接断开

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


# 依赖项：用于在 API 中获取数据库会话
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
