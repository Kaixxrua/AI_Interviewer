# app/routers/auth.py
import random
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.orm import Session
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
import os
from dotenv import load_dotenv
from app.database import get_db
from app import model, schemas  # 确保导入了 model 和 schemas
from app.utils import security

load_dotenv()
router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

# 📧 邮件配置
conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USER"),  # 例如 123456@qq.com
    MAIL_PASSWORD=os.getenv("MAIL_PASS"),  # ⚠️ 不是QQ登录密码！
    MAIL_FROM=os.getenv("MAIL_USER"),  # 必须和 USERNAME 一致
    MAIL_PORT=465,  # QQ邮箱 SSL 端口
    MAIL_SERVER="smtp.qq.com",
    MAIL_STARTTLS=False,  # QQ 必须把这个关掉
    MAIL_SSL_TLS=True,  # QQ 必须开启 SSL
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True,
    SUPPRESS_SEND=0,  # 🟢 0 = 开启真发送
)


# ================= 1. 发送验证码接口 =================
@router.post("/send-code")
async def send_verification_code(
    email_data: schemas.EmailSchema,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
):
    email = email_data.email

    # 检查邮箱是否已被注册 (可选)
    if db.query(model.User).filter(model.User.username == email).first():
        raise HTTPException(status_code=400, detail="该邮箱已被注册")

    code = str(random.randint(100000, 999999))

    db_code = model.VerificationCode(email=email, code=code)
    db.add(db_code)
    db.commit()

    message = MessageSchema(
        # 🟢 改一下标题，加个时间戳，防止被当成重复垃圾邮件
        subject=f"【AI面试官】安全验证 - {code}",
        recipients=[email],
        # 🟢 内容多加几个字，太短容易被屏蔽
        body=f"""
        <html>
            <body>
                <h3>欢迎注册 AI 面试官</h3>
                <p>您的验证码是：<strong style='color:blue;font-size:20px;'>{code}</strong></p>
                <p>该验证码 10 分钟内有效，请勿告知他人。</p>
            </body>
        </html>
        """,
        subtype=MessageType.html,
    )

    fm = FastMail(conf)
    await fm.send_message(message)

    print(f"\n{'='*20} 模拟邮件发送 {'='*20}")
    print(f"收件人: {email}")
    print(f"验证码: {code}")
    print(f"{'='*50}\n")

    return {"message": "验证码已发送"}


# ================= 2. 注册接口 =================
@router.post("/register", response_model=schemas.UserOut)
def register(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # 1. 检查用户名
    if db.query(model.User).filter(model.User.username == user.username).first():
        raise HTTPException(status_code=400, detail="用户名已存在")

    # 2. 校验验证码
    verify_record = (
        db.query(model.VerificationCode)
        .filter(
            model.VerificationCode.email == user.email,
            model.VerificationCode.is_used == False,
        )
        .order_by(model.VerificationCode.created_at.desc())
        .first()
    )

    if not verify_record or verify_record.code != user.code:
        raise HTTPException(status_code=400, detail="验证码错误或已失效")

    verify_record.is_used = True

    # 3. 创建用户
    hashed_password = security.get_password_hash(user.password)

    new_user = model.User(
        username=user.username,
        hashed_password=hashed_password,
        # email=user.email (如果你的 User 表有 email 字段请解开)
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user


# ================= 3. 登录接口 (这里修正了) =================
@router.post("/login", response_model=schemas.Token)
def login(user_data: schemas.UserLogin, db: Session = Depends(get_db)):
    # 查找用户
    user = (
        db.query(model.User).filter(model.User.username == user_data.username).first()
    )
    if not user:
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 验证密码
    if not security.verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=400, detail="用户名或密码错误")

    # 生成 Token
    access_token = security.create_access_token(data={"sub": user.username})

    # 🔥🔥🔥 修改这里：返回 user_id 和 username 🔥🔥🔥
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "user_id": user.id,  # 👈 新增这一行
        "username": user.username,  # 👈 新增这一行
    }


# ================= 4. 获取当前用户依赖 =================
async def get_current_user(
    token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)
):
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, security.SECRET_KEY, algorithms=[security.ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = db.query(model.User).filter(model.User.username == username).first()
    if user is None:
        raise credentials_exception
    return user
