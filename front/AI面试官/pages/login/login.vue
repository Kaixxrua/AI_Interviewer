<template>
  <view class="login-page">
    
    <!-- 1. 静态宣纸背景 (纯 CSS 模拟纹理) -->
    <view class="paper-bg">
      <view class="grain-overlay"></view>
    </view>

    <!-- 2. Logo 区域 (浮在宣纸上) -->
    <view class="header-floating animate-float-down">
      <view class="logo-wrapper">
        <image src="/static/logo.png" mode="widthFix" class="ink-logo"></image>
      </view>
      <view class="text-group">
        <text class="title">AI 面试官</text>
        <text class="subtitle">{{ isLogin ? '墨染职场，对答如流' : '提笔入画，开启征程' }}</text>
      </view>
    </view>

    <!-- 3. 亚克力表单卡片 -->
    <view class="acrylic-card animate-float-up">
      <!-- 玻璃反光条 -->
      <view class="glass-shine"></view>
      
      <!-- 表单区 -->
      <view class="form-compact">
        <!-- 用户名 -->
        <view class="minimal-input" :class="{ active: activeField === 'username' }">
          <input 
            type="text" 
            v-model="username" 
            placeholder="用户名" 
            placeholder-class="ph-style"
            @focus="activeField = 'username'"
            @blur="activeField = ''"
          />
          <view class="ink-stroke"></view>
        </view>

        <!-- 密码 -->
        <view class="minimal-input" :class="{ active: activeField === 'password' }">
          <input 
            type="password" 
            v-model="password" 
            placeholder="密码" 
            placeholder-class="ph-style"
            @focus="activeField = 'password'"
            @blur="activeField = ''"
          />
          <view class="ink-stroke"></view>
        </view>
        
        <!-- 邮箱 (注册用) -->
        <view class="minimal-input" v-if="!isLogin" :class="{ active: activeField === 'email' }">
          <input 
            type="text" 
            v-model="email" 
            placeholder="邮箱" 
            placeholder-class="ph-style"
            @focus="activeField = 'email'"
            @blur="activeField = ''"
          />
          <view class="ink-stroke"></view>
        </view>

        <!-- 验证码 (注册用) -->
        <view class="code-row" v-if="!isLogin">
          <view class="minimal-input code-box" :class="{ active: activeField === 'code' }">
            <input 
              type="number" 
              v-model="code" 
              placeholder="验证码" 
              placeholder-class="ph-style"
              maxlength="6"
              @focus="activeField = 'code'"
              @blur="activeField = ''"
            />
            <view class="ink-stroke"></view>
          </view>
          <view class="text-btn-code" :class="{ disabled: timer > 0 }" @click="handleSendCode">
            {{ timer > 0 ? `${timer}s` : '获取' }}
          </view>
        </view>
      </view>

      <!-- 按钮区 -->
      <view class="action-area">
        <button 
          class="ink-btn" 
          hover-class="btn-press" 
          @click="handleSubmit" 
          :loading="loading"
        >
          {{ isLogin ? '登 录' : '注 册' }}
        </button>

        <text class="toggle-link" @click="toggleMode">
          {{ isLogin ? '注册账号' : '返回登录' }}
        </text>
      </view>

    </view>

    <!-- 底部版权 -->
    <view class="footer-mini">
      Design by AI Interviewer
    </view>

  </view>
</template>

<script setup>
import { ref } from 'vue';
import { request } from '@/utils/request.js';

const activeField = ref('');
const isLogin = ref(true);
const username = ref('');
const password = ref('');
const email = ref('');
const code = ref('');
const loading = ref(false);
const timer = ref(0);

const passwordRegex = /^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[\s\S]{8,}$/;
const emailRegex = /^[a-zA-Z0-9._-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,6}$/;

const toggleMode = () => {
  isLogin.value = !isLogin.value;
  username.value = ''; password.value = ''; email.value = ''; code.value = '';
  activeField.value = '';
};

const handleSendCode = async () => {
  if (timer.value > 0) return;
  if (!email.value || !emailRegex.test(email.value)) return uni.showToast({ title: '邮箱格式错误', icon: 'none' });

  try {
    uni.showLoading({ title: '发送中...' });
    await request({ url: '/auth/send-code', method: 'POST', data: { email: email.value } });
    uni.hideLoading();
    uni.showToast({ title: '已发送', icon: 'success' });
    timer.value = 60;
    const interval = setInterval(() => { timer.value--; if (timer.value <= 0) clearInterval(interval); }, 1000);
  } catch (e) { uni.hideLoading(); }
};

const handleSubmit = async () => {
  if (!username.value || !password.value) return uni.showToast({ title: '请填写完整', icon: 'none' });
  if (!isLogin.value) {
    if (!passwordRegex.test(password.value)) return uni.showToast({ title: '密码强度不足(8位+大小写+数字)', icon: 'none' });
    if (!email.value || !code.value) return uni.showToast({ title: '请验证邮箱', icon: 'none' });
  }

  loading.value = true;
  try {
    if (isLogin.value) {
      const res = await request({ url: '/auth/login', method: 'POST', data: { username: username.value, password: password.value } });
      uni.setStorageSync('access_token', res.access_token);
      uni.setStorageSync('username', username.value);
      uni.setStorageSync('user_id', res.user_id);
      uni.showToast({ title: '登录成功', icon: 'success' });
      setTimeout(() => uni.reLaunch({ url: '/pages/index/index' }), 500);
    } else {
      await request({ url: '/auth/register', method: 'POST', data: { username: username.value, password: password.value, email: email.value, code: code.value } });
      uni.showToast({ title: '注册成功', icon: 'success' });
      isLogin.value = true;
    }
  } catch (e) {
     const errorMsg = e.data?.detail?.[0]?.msg || e.data?.detail || '请求失败';
     uni.showToast({ title: errorMsg, icon: 'none' });
  } finally {
    loading.value = false;
  }
};
</script>

<style lang="scss" scoped>
/* 全局背景 */
:global(page) {
    background-color: #F7F7F2;
    font-family: 'PingFang SC', 'Noto Serif SC', serif;
}

.login-page {
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    justify-content: center;
    align-items: center;
    position: relative;
    overflow: hidden;
}

/* ====================================
   1. 宣纸质感背景 (核心代码)
   ==================================== */
.paper-bg {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    z-index: 0;
    /* 基础米色渐变，中间亮，四周微暗，模拟光照 */
    background: radial-gradient(circle at 50% 40%, #FDFDFB 0%, #F0EFE2 100%);
}

/* 宣纸纹理噪点层 */
.grain-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0.5; /* 调整纹理深浅 */
    /* 这里的 base64 是一个极小的噪点图片，重复平铺形成纸张纤维感 */
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.15'/%3E%3C/svg%3E");
    pointer-events: none;
}

/* ====================================
   2. 头部 Logo
   ==================================== */
.header-floating {
    position: relative; z-index: 10;
    display: flex; flex-direction: column; align-items: center;
    margin-bottom: 60rpx;
    animation: fadeInDown 1s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.logo-wrapper {
    width: 180rpx; height: 180rpx;
    margin-bottom: 24rpx;
}

.ink-logo {
    width: 100%; height: 100%;
    display: block;
    /* 关键：正片叠底，让Logo像是“印”在纸上 */
    mix-blend-mode: multiply;
    /* 增加对比度，去除图片白底 */
    filter: contrast(1.2) brightness(1.02);
}

.text-group { text-align: center; }
.title {
    font-size: 48rpx; font-weight: bold; color: #1A1A1A;
    letter-spacing: 8rpx; margin-bottom: 12rpx;
}
.subtitle {
    font-size: 26rpx; color: #666; font-family: serif;
    letter-spacing: 2rpx; opacity: 0.8; font-style: italic;
}

/* ====================================
   3. 亚克力卡片 (静止版优化)
   ==================================== */
.acrylic-card {
    position: relative; z-index: 10;
    width: 600rpx;
    padding: 60rpx 40rpx;
    
    /* 静态背景下，稍微增加一点不透明度，提升质感 */
    background: rgba(255, 255, 255, 0.5); 
    backdrop-filter: blur(15px);
    -webkit-backdrop-filter: blur(15px);
    
    border-radius: 32rpx;
    border: 1px solid rgba(255, 255, 255, 0.8); /* 边框更亮，突出玻璃感 */
    
    /* 阴影更柔和 */
    box-shadow: 0 40rpx 80rpx rgba(0, 0, 0, 0.08);
    
    animation: fadeInUp 1s cubic-bezier(0.2, 0.8, 0.2, 1);
}

.glass-shine {
    position: absolute; top: 0; left: 0; right: 0; height: 100%;
    background: linear-gradient(120deg, rgba(255,255,255,0.6) 0%, transparent 40%);
    border-radius: 32rpx; pointer-events: none;
}

/* ====================================
   4. 表单与交互
   ==================================== */
.form-compact { margin-bottom: 40rpx; }

.minimal-input {
    position: relative; height: 96rpx;
    background: rgba(255, 255, 255, 0.6); /* 输入框更白 */
    border-radius: 12rpx;
    display: flex; align-items: center; padding: 0 30rpx;
    margin-bottom: 24rpx;
    transition: all 0.3s;
    
    input { flex: 1; font-size: 30rpx; color: #1A1A1A; height: 100%; }
    .ph-style { color: #888; font-size: 28rpx; }
    
    .ink-stroke {
        position: absolute; bottom: 0; left: 0; width: 0%; height: 4rpx;
        background: #1A1A1A; transition: width 0.4s ease-out;
        border-radius: 4rpx;
    }
    
    &.active {
        background: #fff;
        box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
        .ink-stroke { width: 100%; }
    }
}

.code-row { display: flex; gap: 20rpx; align-items: center; }
.code-box { flex: 1; margin-bottom: 0; }
.text-btn-code {
    font-size: 28rpx; color: #1A1A1A; font-weight: 600; padding: 0 10rpx;
    &.disabled { color: #aaa; }
}

.action-area { display: flex; flex-direction: column; align-items: center; }

.ink-btn {
    width: 100%; height: 96rpx; line-height: 96rpx;
    background: #1A1A1A; color: #fff;
    border-radius: 12rpx;
    font-size: 32rpx; letter-spacing: 4rpx;
    box-shadow: 0 10rpx 20rpx rgba(0,0,0,0.15);
    margin-bottom: 30rpx;
    
    &:active { transform: scale(0.98); opacity: 0.9; }
    &:after { border: none; }
}

.toggle-link {
    font-size: 26rpx; color: #555; padding: 20rpx;
    text-decoration: underline; text-underline-offset: 4rpx;
    opacity: 0.8;
}

.footer-mini {
    position: absolute; bottom: 40rpx;
    font-size: 22rpx; color: #999; letter-spacing: 2rpx;
    opacity: 0.5; font-family: serif;
}

/* 简单的入场位移 */
@keyframes fadeInDown { from { opacity: 0; transform: translateY(-30rpx); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeInUp { from { opacity: 0; transform: translateY(30rpx); } to { opacity: 1; transform: translateY(0); } }
</style>