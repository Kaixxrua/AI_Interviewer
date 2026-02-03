<template>
  <view class="user-container">
    
    <!-- 1. 静态宣纸背景 (全局统一) -->
    <view class="paper-bg">
      <view class="grain-overlay"></view>
    </view>

    <!-- 顶部留白装饰 (淡墨晕染) -->
    <view class="top-ink-decoration"></view>

    <!-- 2. 个人名帖卡片 -->
    <view class="profile-card-ink animate-slide-down">
      <view class="user-row">
        <!-- 头像区 -->
        <view class="avatar-ink-ring" @click="handleAvatarClick">
          <image 
            class="avatar-img" 
            :src="userInfo.avatar || '/static/default-avatar.png'" 
            mode="aspectFill"
          ></image>
          <!-- 编辑图标 (小印章) -->
          <view class="edit-stamp">
             <text>✎</text>
          </view>
        </view>
        
        <!-- 信息区 -->
        <view class="info-col">
          <text class="username">{{ userInfo.username || '未登录雅客' }}</text>
          <view class="uid-pill" v-if="userInfo.id">
              <text class="uid-text">UID: {{ userInfo.id }}</text>
          </view>
          <text class="bio" v-if="userInfo.id">✨ 积跬步，至千里</text>
          <text class="bio link" v-else @click="navigateTo('/pages/login/login')">点击登录，同步您的数据 ></text>
        </view>
      </view>

      <!-- 数据统计栏 (镇纸风格) -->
      <view class="stats-paper-bar" v-if="userInfo.id">
        <view class="stat-item">
          <text class="val">{{ stats.count }}</text>
          <text class="lbl">模拟次数</text>
        </view>
        <view class="ink-divider"></view>
        <view class="stat-item">
          <text class="val highlight">{{ stats.avg }}</text>
          <text class="lbl">平均得分</text>
        </view>
        <view class="ink-divider"></view>
        <view class="stat-item">
          <text class="val">{{ stats.days }}</text>
          <text class="lbl">坚持天数</text>
        </view>
      </view>
    </view>

    <!-- 3. 功能菜单组 (宣纸列表) -->
    <view class="menu-group animate-fade-in" style="animation-delay: 0.1s">
      <view class="menu-title-ink">常用功能</view>
      <view class="menu-paper-card">
        <view class="menu-item" @click="navigateTo('/pages/History/History')">
          <view class="left">
            <view class="icon-ink blue"><text>📅</text></view>
            <text class="text">面试记录</text>
          </view>
          <text class="ink-arrow">→</text>
        </view>
        
        <view class="menu-item" @click="showToast('会员功能开发中')">
          <view class="left">
            <view class="icon-ink gold"><text>💎</text></view>
            <text class="text">会员中心</text>
          </view>
          <text class="ink-arrow">→</text>
        </view>
      </view>
    </view>

    <view class="menu-group animate-fade-in" style="animation-delay: 0.2s">
      <view class="menu-title-ink">更多服务</view>
      <view class="menu-paper-card">
        <view class="menu-item" @click="showToast('设置功能开发中')">
          <view class="left">
            <view class="icon-ink gray"><text>⚙️</text></view>
            <text class="text">系统设置</text>
          </view>
          <text class="ink-arrow">→</text>
        </view>
        
        <view class="menu-item" @click="showAbout">
          <view class="left">
            <view class="icon-ink gray"><text>ℹ️</text></view>
            <text class="text">关于</text>
          </view>
          <text class="ink-arrow">→</text>
        </view>
      </view>
    </view>

    <!-- 4. 退出登录按钮 (朱砂红字) -->
    <view class="footer-section animate-fade-in" style="animation-delay: 0.3s" v-if="userInfo.id">
      <button class="logout-btn-ink" @click="handleLogout">退出登录</button>
    </view>

    <!-- 底部版权 -->
    <view class="footer-copyright">
        Design by AI Interviewer
    </view>

  </view>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { request } from '@/utils/request.js';

const BASE_URL = 'http://192.168.1.11:8000'; 

const userInfo = reactive({
  id: null,
  username: '',
  avatar: ''
});

const stats = reactive({
  count: 0,
  avg: 0,
  days: 1
});

onShow(() => {
  loadUserData();
  loadStats();
});

const loadUserData = () => {
  const token = uni.getStorageSync('access_token');
  if (token) {
    userInfo.id = uni.getStorageSync('user_id');
    userInfo.username = uni.getStorageSync('username');
    const savedAvatar = uni.getStorageSync('user_avatar');
    if (savedAvatar) userInfo.avatar = savedAvatar;
  } else {
    userInfo.id = null;
    userInfo.username = '';
    userInfo.avatar = '';
  }
};

const loadStats = async () => {
  if (!userInfo.id) return;
  try {
    const res = await request({ url: `/report/stats/${userInfo.id}`, method: 'GET' });
    if (res) {
      stats.count = res.interview_count;
      stats.avg = res.average_score;
    }
  } catch (e) { console.error(e); }
};

const handleAvatarClick = () => {
  if (!userInfo.id) return uni.navigateTo({ url: '/pages/login/login' });
  uni.chooseImage({
    count: 1,
    sizeType: ['compressed'],
    success: (res) => uploadAvatar(res.tempFilePaths[0])
  });
};

const uploadAvatar = (filePath) => {
  uni.showLoading({ title: '上传中...' });
  const token = uni.getStorageSync('access_token');
  uni.uploadFile({
    url: `${BASE_URL}/api/user/upload-avatar`,
    filePath: filePath,
    name: 'file',
    header: { 'Authorization': `Bearer ${token}` },
    formData: { user_id: userInfo.id },
    success: (res) => {
      const data = JSON.parse(res.data);
      if (data.url) {
        userInfo.avatar = data.url;
        uni.setStorageSync('user_avatar', data.url);
        uni.showToast({ title: '修改成功', icon: 'success' });
      }
    },
    complete: () => uni.hideLoading()
  });
};

const handleLogout = () => {
  uni.showModal({
    title: '提示', content: '确定退出登录吗？',
    success: (res) => {
      if (res.confirm) {
        uni.clearStorageSync();
        loadUserData();
        uni.reLaunch({ url: '/pages/login/login' });
      }
    }
  });
};

const navigateTo = (url) => {
  if(!userInfo.id) return uni.navigateTo({ url: '/pages/login/login' });
  uni.navigateTo({ url });
};

const showToast = (msg) => uni.showToast({ title: msg, icon: 'none' });

const showAbout = () => {
  uni.showModal({
    title: '关于 AI 面试官',
    content: '版本号：v2.0.0\n',
    showCancel: false
  });
};
</script>

<style lang="scss" scoped>
/* 全局字体与背景 */
:global(page) {
    background-color: #F7F7F2; /* 宣纸白 */
    font-family: 'PingFang SC', 'Noto Serif SC', serif;
}

.user-container {
    padding: 0 40rpx 100rpx;
    position: relative;
    overflow-x: hidden;
    min-height: 100vh;
}

/* ====================================
   1. 宣纸背景 (全局统一)
   ==================================== */
.paper-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
    background: radial-gradient(circle at 50% 30%, #FDFDFB 0%, #F2F2EB 100%);
    pointer-events: none;
}
.grain-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.4;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.15'/%3E%3C/svg%3E");
}

/* 顶部墨晕装饰 */
.top-ink-decoration {
    position: absolute; top: -100rpx; right: -100rpx;
    width: 500rpx; height: 500rpx;
    background: radial-gradient(circle, rgba(0,0,0,0.03) 0%, transparent 70%);
    border-radius: 50%; pointer-events: none;
}

/* ====================================
   2. 个人名帖卡片
   ==================================== */
.profile-card-ink {
    position: relative; z-index: 1;
    margin-top: calc(80rpx + var(--status-bar-height));
    background: rgba(255,255,255,0.6);
    backdrop-filter: blur(15px);
    border-radius: 32rpx;
    padding: 50rpx 40rpx 40rpx;
    margin-bottom: 60rpx;
    /* 宣纸卡片质感 */
    box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.03);
    border: 1px solid rgba(255,255,255,0.8);
}

.user-row {
    display: flex; align-items: center; margin-bottom: 40rpx;
}

.avatar-ink-ring {
    position: relative;
    width: 130rpx; height: 130rpx;
    margin-right: 32rpx;
    /* 墨线双圈 */
    border: 2rpx solid #333;
    padding: 6rpx;
    border-radius: 50%;
    
    .avatar-img {
        width: 100%; height: 100%;
        border-radius: 50%;
        background: #E0E0E0;
    }
    
    .edit-stamp {
        position: absolute; bottom: 0; right: -10rpx;
        width: 44rpx; height: 44rpx;
        background: #1A1A1A; color: #fff;
        border-radius: 12rpx;
        font-size: 24rpx;
        display: flex; align-items: center; justify-content: center;
        border: 2rpx solid #fff;
    }
}

.info-col {
    display: flex; flex-direction: column;
    
    .username {
        font-size: 44rpx; font-weight: bold; color: #1A1A1A;
        margin-bottom: 12rpx; letter-spacing: 2rpx;
    }
    
    .uid-pill {
        display: inline-flex;
        background: rgba(0,0,0,0.05);
        padding: 4rpx 16rpx; border-radius: 8rpx;
        margin-bottom: 12rpx; align-self: flex-start;
        .uid-text { font-size: 22rpx; color: #555; font-family: 'DIN Alternate', monospace; }
    }
    
    .bio {
        font-size: 26rpx; color: #888; font-family: serif;
        &.link { text-decoration: underline; color: #555; }
    }
}

/* 统计栏 (镇纸) */
.stats-paper-bar {
    display: flex; justify-content: space-around; align-items: center;
    padding-top: 30rpx;
    border-top: 1px dashed rgba(0,0,0,0.1);
    
    .stat-item {
        display: flex; flex-direction: column; align-items: center;
        .val { 
            font-size: 40rpx; font-weight: bold; color: #1A1A1A; font-family: serif;
            &.highlight { color: #C62828; /* 朱砂红 */ }
        }
        .lbl { font-size: 24rpx; color: #888; margin-top: 6rpx; }
    }
    
    .ink-divider { width: 1px; height: 30rpx; background: rgba(0,0,0,0.15); }
}

/* ====================================
   3. 菜单列表 (纸质)
   ==================================== */
.menu-group { margin-bottom: 40rpx; position: relative; z-index: 1; }
.menu-title-ink {
    font-size: 28rpx; font-weight: bold; color: #333;
    margin-bottom: 20rpx; margin-left: 10rpx; letter-spacing: 2rpx;
    opacity: 0.8;
}

.menu-paper-card {
    background: #fff;
    border-radius: 20rpx;
    overflow: hidden;
    box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.02);
    border: 1px solid rgba(0,0,0,0.02);
}

.menu-item {
    display: flex; justify-content: space-between; align-items: center;
    padding: 34rpx 30rpx;
    border-bottom: 1px solid #F9F9F9;
    transition: background 0.2s;
    
    &:last-child { border-bottom: none; }
    &:active { background: #FAF9F6; }
    
    .left {
        display: flex; align-items: center;
        
        .icon-ink {
            width: 70rpx; height: 70rpx;
            border-radius: 16rpx;
            display: flex; align-items: center; justify-content: center;
            margin-right: 24rpx; font-size: 32rpx;
            
            /* 莫兰迪底色 */
            &.blue { background: #E3F2FD; color: #1565C0; }
            &.gold { background: #FFF8E1; color: #F57F17; }
            &.gray { background: #F5F5F0; color: #555; }
        }
        
        .text { font-size: 30rpx; font-weight: 500; color: #333; }
    }
    
    .ink-arrow { font-size: 28rpx; color: #999; opacity: 0.6; }
}

/* ====================================
   4. 底部按钮 & 版权
   ==================================== */
.footer-section { margin-top: 60rpx; }

.logout-btn-ink {
    background: #fff;
    color: #C62828; /* 朱砂红 */
    font-size: 32rpx; font-weight: bold; letter-spacing: 4rpx;
    border-radius: 16rpx;
    padding: 6rpx 0;
    box-shadow: 0 6rpx 20rpx rgba(198, 40, 40, 0.1);
    border: 1px solid rgba(198, 40, 40, 0.1);
    
    &:after { border: none; }
    &:active { opacity: 0.8; transform: scale(0.98); background: #FFFBFB; }
}

.footer-copyright {
    text-align: center; margin-top: 60rpx;
    font-size: 22rpx; color: #AAA; font-family: serif; font-style: italic;
}

/* 动画 */
.animate-slide-down { animation: slideDown 0.8s cubic-bezier(0.2, 0.8, 0.2, 1) forwards; opacity: 0; }
.animate-fade-in { animation: fadeIn 0.8s ease-out forwards; opacity: 0; }

@keyframes slideDown { 
    from { transform: translateY(-30rpx); opacity: 0; }
    to { transform: translateY(0); opacity: 1; }
}
@keyframes fadeIn { 
    to { opacity: 1; }
}
</style>