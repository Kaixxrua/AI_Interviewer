<template>
  <view class="container">
    
    <!-- 1. 静态宣纸背景 (全局底纹) -->
    <view class="paper-bg">
      <view class="grain-overlay"></view>
    </view>

    <!-- 2. 顶部 Header (水墨风格) -->
    <view class="ink-header animate-slide-down">
      <view class="header-content" @click="handleUserClick">
        <view class="text-group">
          <text class="greeting">
            {{ hasLogin ? `早安, ${userInfo.name}` : '展信佳，面试官' }}
          </text>
          <text class="subtitle">
            {{ hasLogin ? '今日宜：温故知新，模拟面试' : '提笔入画，开启你的大厂征程' }}
          </text>
        </view>
        
        <!-- 头像：改为素雅的圆环 -->
        <view class="avatar-ring">
          <image 
            v-if="hasLogin && userInfo.avatar" 
            :src="userInfo.avatar" 
            class="avatar-img" 
            mode="aspectFill"
          ></image>
          <view v-else class="avatar-placeholder">
            <text class="char">{{ hasLogin ? userInfo.name[0] : '客' }}</text>
          </view>
        </view>
      </view>

      <!-- 亚克力数据栏 (类似镇纸) -->
      <view class="acrylic-stats" @click="handleStatsClick">
        <view class="glass-shine"></view>
        <view class="stat-box">
          <text class="val">{{ stats.days }}</text>
          <text class="lbl">坚持天数</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-box">
          <text class="val">{{ stats.interviewCount }}</text>
          <text class="lbl">模拟次数</text>
        </view>
        <view class="stat-divider"></view>
        <view class="stat-box">
          <text class="val highlight">{{ stats.avgScore }}</text>
          <text class="lbl">平均得分</text>
        </view>
      </view>
    </view>

    <view class="main-content">
      <!-- 3. 每日一题 -->
      <view class="section-header animate-fade-in" style="animation-delay: 0.1s">
        <text class="section-title">每日一题</text>
        <text class="section-desc">积跬步，至千里</text>
      </view>
      
      <view class="daily-paper-card animate-scale-up" style="animation-delay: 0.2s" @click="handleDailyClick">
        <view class="card-top">
            <text class="tag-ink">{{ dailyQuestion.type }}</text>
            <view class="date-ink">
                <text>{{ new Date().getDate() }}</text>
                <text class="month">/{{ new Date().getMonth()+1 }}月</text>
            </view>
        </view>
        <text class="daily-title">{{ dailyQuestion.title }}</text>
        <view class="daily-footer">
          <text class="action-text">查看解析</text>
          <view class="ink-arrow">→</view>
        </view>
      </view>

      <!-- 4. 专项模拟 -->
      <view class="section-header animate-fade-in" style="margin-top: 60rpx; animation-delay: 0.3s">
        <text class="section-title">专项演练</text>
        <text class="section-desc">术业有专攻</text>
      </view>
      
      <view class="category-grid">
        <view 
          class="cat-item animate-stagger" 
          v-for="(item, index) in categories" 
          :key="index"
          :style="{ animationDelay: (0.4 + index * 0.1) + 's', '--ink-color': item.inkColor }"
          @click="handleCategoryClick(item)"
        >
          <view class="cat-icon-box">
            <text class="cat-emoji">{{ item.icon }}</text>
          </view>
          <text class="cat-name">{{ item.name }}</text>
        </view>
      </view>
    </view>

    <!-- 5. 悬浮按钮 (FAB) - 改为 Logo 印章风格 -->
    <view class="ink-fab animate-float" @click="openAIAssistant">
      <view class="fab-inner">
         <!-- 🔥 替换：这里改成了你的 logo 图片 -->
         <image src="/static/logo.png" mode="aspectFit" class="fab-logo-img"></image>
      </view>
      <text class="fab-label">AI 面试</text>
    </view>

    <!-- 6. 加载动画 (水墨呼吸风格) - 替换原本的 Cyber Core -->
    <view class="loading-overlay" :class="{ show: isConnecting }" v-if="isConnecting" @touchmove.stop.prevent>
        <view class="loading-backdrop"></view> <!-- 模糊层 -->
        
        <view class="loading-content">
            <!-- 水墨呼吸 Logo -->
            <view class="ink-breathing-container">
                <view class="ink-ripple"></view>
                <view class="ink-ripple delay"></view>
                <!-- 🔥 替换：加载时的中心图标也换成 Logo -->
                <image src="/static/logo.png" mode="aspectFit" class="loading-logo"></image>
            </view>
            
            <view class="text-area">
                <text class="main-tip">{{ loadingText }}</text>
                <text class="sub-tip">{{ loadingSubText }}</text>
            </view>
        </view>
    </view>

    <!-- 7. 难度选择弹窗 (亚克力风格) -->
    <view class="modal-mask" :class="{ show: showDifficultyModal }" v-if="showDifficultyModal" @click="closeModal" @touchmove.stop.prevent>
        <view class="bottom-sheet acrylic-sheet" @click.stop>
            <view class="sheet-handle"></view>
            <view class="sheet-header">
                <text class="sheet-title">定制面试环境</text>
                <text class="sheet-sub">{{ selectedCategory?.name }} 专项 · 请选择难度</text>
            </view>
            
            <scroll-view scroll-y class="sheet-body">
                <view class="sheet-section">
                    <text class="sheet-label">当前职级</text>
                    <view class="tags-row">
                        <view 
                            class="tag-item" 
                            :class="{ active: currentIdentity === item.value }"
                            v-for="(item, index) in identityOptions"
                            :key="'id-'+index"
                            @click="currentIdentity = item.value"
                        >
                            {{ item.label }}
                        </view>
                    </view>
                </view>

                <view class="sheet-section">
                    <text class="sheet-label">技术侧重</text>
                    <view class="tags-row">
                        <view 
                            class="tag-item" 
                            :class="{ active: currentFocus === item.value }"
                            v-for="(item, index) in currentFocusOptions"
                            :key="'focus-'+index"
                            @click="currentFocus = item.value"
                        >
                            {{ item.label }}
                        </view>
                    </view>
                </view>
            </scroll-view>

            <view class="sheet-footer">
                <button class="sheet-btn start-btn" @click="startInterview">开始挑战</button>
            </view>
        </view>
    </view>

  </view>
</template>

<script setup>
import { ref, reactive } from 'vue';
import { onShow } from '@dcloudio/uni-app';
import { request } from '../../utils/request.js';

// ================= 数据定义 =================
const hasLogin = ref(false);
const userInfo = reactive({ name: 'User', avatar: '' });
const stats = reactive({ days: 1, interviewCount: 0, avgScore: 0 });

const dailyQuestion = reactive({
    type: 'Python 基础',
    title: '请简述 Python 中 GIL (全局解释器锁) 的概念及其对多线程的影响？'
});

// 🔥 调整配色为低饱和度国画色系 (bg 改为 inkColor 控制图标底色)
const categories = [
    { id: 'python', name: 'Python', icon: '🐍', inkColor: '#E8F5E9' }, // 淡竹青
    { id: 'frontend', name: '前端', icon: '⚛️', inkColor: '#E3F2FD' }, // 淡云蓝
    { id: 'concurrency', name: '高并发', icon: '🏗️', inkColor: '#F3E5F5' }, // 淡紫
    { id: 'algo', name: '算法', icon: '🧮', inkColor: '#FFEBEE' }, // 淡绯红
    { id: 'ai_engineer', name: 'AI全栈', icon: '🧠', inkColor: '#FFF8E1' }, // 淡琥珀
    { id: 'hr', name: 'HR面', icon: '👔', inkColor: '#ECEFF1' } // 淡墨灰
];

const identityOptions = [
    { label: '校招/实习', value: '校招实习生(无经验)，侧重基础原理与学习潜力' },
    { label: '初级 (1-3年)', value: '初级工程师(1-3年)，侧重业务落地与编码规范' },
    { label: '资深 (3-5年)', value: '资深工程师(3-5年)，侧重原理深度与架构理解' },
    { label: '专家 (5年+)', value: '技术专家(5年+)，侧重系统设计、权衡与方法论' }
];

const techFocusMap = {
    'python': [
        { label: '语法基础', value: '基础数据结构、面向对象、装饰器、生成器' },
        { label: 'Web框架', value: 'Django/FastAPI 框架原理、ORM、中间件' },
        { label: '底层原理', value: 'GIL、内存管理、垃圾回收、元类编程' },
        { label: '爬虫/数据', value: 'Scrapy、逆向工程、Pandas数据清洗' }
    ],
    'frontend': [
        { label: 'Vue 生态', value: 'Vue2/3 响应式原理、Diff算法、全家桶' },
        { label: 'React 生态', value: 'Hooks、Fiber、虚拟DOM、状态管理' },
        { label: 'JS/TS 核心', value: '闭包、原型链、EventLoop、TS类型体操' },
        { label: '工程化', value: 'Vite/Webpack、浏览器渲染、首屏优化' }
    ],
    'concurrency': [
        { label: 'Redis缓存', value: 'Redis 数据结构、持久化、集群、缓存一致性' },
        { label: '消息队列', value: 'Kafka/RabbitMQ 积压、丢失、顺序消费' },
        { label: '数据库MySQL', value: '索引优化、锁机制、MVCC、分库分表' },
        { label: '分布式理论', value: 'CAP/BASE、分布式事务(Seata)、分布式锁' }
    ],
    'algo': [
        { label: '基础结构', value: '链表、树、栈、队列、哈希表' },
        { label: 'Top 100', value: 'LeetCode Hot 100 高频题' },
        { label: '动态规划', value: 'DP、背包问题、状态转移' },
        { label: '图论/搜索', value: 'DFS/BFS、最短路径、拓扑排序' }
    ],
    'ai_engineer': [
        { label: 'RAG 架构', value: 'RAG全链路：切片、向量库、检索优化、Rerank' },
        { label: 'Agent 开发', value: 'Function Calling、ReAct框架、多智能体协作' },
        { label: '大模型原理', value: 'Transformer、Attention机制、PEFT微调(LoRA)' },
        { label: 'AI全栈落地', value: 'SSE流式、异步架构、Token成本控制、部署' }
    ],
    'hr': [
        { label: '综合素质', value: '沟通能力、抗压能力、团队协作' },
        { label: '职业规划', value: '离职原因、未来规划、行业看法' },
        { label: '项目复盘', value: 'STAR法则介绍最难忘的项目' },
        { label: '薪资谈判', value: '期望薪资、Offer对比、入职意向' }
    ]
};

const isConnecting = ref(false);
const loadingText = ref('正在连接 AI 面试官');
const loadingSubText = ref('整理卷宗中...'); // 文案微调
const showDifficultyModal = ref(false);
const selectedCategory = ref(null);
const currentIdentity = ref('');
const currentFocus = ref('');
const currentFocusOptions = ref([]);

// ================= 逻辑方法 (保持原有逻辑不变) =================

const checkLoginStatus = () => {
    const token = uni.getStorageSync('access_token');
    const username = uni.getStorageSync('username');
    const avatar = uni.getStorageSync('user_avatar');

    if (token && username) {
        hasLogin.value = true;
        userInfo.name = username;
        userInfo.avatar = avatar || ''; 
    } else {
        hasLogin.value = false;
        userInfo.name = 'User';
        userInfo.avatar = '';
    }
};

const ensureLogin = () => {
    if (!hasLogin.value) {
        uni.showToast({ title: '请先登录体验完整功能', icon: 'none' });
        setTimeout(() => uni.navigateTo({ url: '/pages/login/login' }), 1000);
        return false;
    }
    return true;
};

const fetchUserStats = async () => {
    const userId = uni.getStorageSync('user_id'); 
    if (!userId) return;
    try {
        const res = await request({ url: `/report/stats/${userId}`, method: 'GET' });
        if (res) {
            stats.interviewCount = res.interview_count;
            stats.avgScore = res.average_score;
        }
    } catch (e) { console.error(e); }
};

onShow(() => {
    checkLoginStatus();
    if (hasLogin.value) fetchUserStats();
});

const handleUserClick = () => {
    if (!hasLogin.value) {
        uni.navigateTo({ url: '/pages/login/login' });
    } else {
        uni.showModal({
            title: '提示', content: '确定要退出登录吗？',
            success: (res) => {
                if (res.confirm) {
                    uni.clearStorageSync();
                    hasLogin.value = false;
                    userInfo.name = 'User';
                    userInfo.avatar = '';
                    stats.interviewCount = 0;
                    stats.avgScore = 0;
                    uni.showToast({ title: '已退出', icon: 'none' });
                }
            }
        });
    }
};

const handleDailyClick = () => {
    if (!ensureLogin()) return;
    uni.showToast({ title: '每日一题功能开发中...', icon: 'none' }); 
};

const handleCategoryClick = (item) => {
    if (!ensureLogin()) return;
    selectedCategory.value = item;
    const focusList = techFocusMap[item.id] || techFocusMap['python']; 
    if (focusList) {
        currentFocusOptions.value = focusList;
        currentFocus.value = focusList[0].value;
    } else {
        currentFocusOptions.value = [{ label: '通用模式', value: '通用' }];
        currentFocus.value = '通用';
    }
    currentIdentity.value = identityOptions[0].value;
    showDifficultyModal.value = true;
};

const closeModal = () => { showDifficultyModal.value = false; };

const startInterview = async () => {
    showDifficultyModal.value = false;
    isConnecting.value = true;
    
    const combinedDifficulty = `[${currentIdentity.value}] - ${currentFocus.value}`;
    
    loadingText.value = `正在生成面试题`;
    const categoryName = selectedCategory.value ? selectedCategory.value.name : '专项';
    loadingSubText.value = `${categoryName} | AI 正在阅卷...`;

    try {
        const res = await request({
            url: '/chat/interview/start',
            method: 'POST',
            data: { topic: categoryName, difficulty: combinedDifficulty }
        });

        const result = res.data || res; 
        
        if (result && result.session_id) {
            const sessionId = result.session_id;
            const topic = result.topic;

            setTimeout(() => {
                isConnecting.value = false;
                uni.navigateTo({
                    url: `/pages/Assistant/Assistant?mode=interview&session_id=${sessionId}&topic=${topic}&difficulty=${combinedDifficulty}`
                });
            }, 2000);
        } else {
            throw new Error('返回数据异常');
        }
    } catch (err) {
        isConnecting.value = false;
        console.error("创建会话失败:", err);
        uni.showToast({ title: '连接失败', icon: 'none' });
    }
};

const handleStatsClick = () => { ensureLogin(); };

const openAIAssistant = () => {
    if (!ensureLogin()) return;

    isConnecting.value = true;
    loadingText.value = '正在唤醒 AI 助手';
    loadingSubText.value = '自由对话模式';
    
    setTimeout(() => {
        isConnecting.value = false;
        uni.navigateTo({ url: '/pages/Assistant/Assistant?mode=normal' });
    }, 2000);
};
</script>

<style lang="scss" scoped>
/* 全局字体优化 */
:global(page) {
    background-color: #F7F7F2; /* 宣纸白 */
    font-family: 'PingFang SC', 'Noto Serif SC', serif;
}

.container {
    position: relative;
    padding-bottom: 120rpx;
    min-height: 100vh;
}

/* ====================================
   1. 静态宣纸背景 (复用 Login 页)
   ==================================== */
.paper-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    z-index: -1;
    background: radial-gradient(circle at 50% 30%, #FDFDFB 0%, #F2F2EB 100%);
}
.grain-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%;
    opacity: 0.4;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.15'/%3E%3C/svg%3E");
    pointer-events: none;
}

/* ====================================
   2. 顶部 Header (水墨版)
   ==================================== */
.ink-header {
    padding: calc(60rpx + var(--status-bar-height)) 40rpx 40rpx;
    position: relative; z-index: 2;
}

.header-content {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 40rpx;
}

.text-group .greeting {
    font-size: 44rpx; font-weight: bold; color: #1A1A1A;
    display: block; margin-bottom: 12rpx; letter-spacing: 2rpx;
}
.text-group .subtitle {
    font-size: 26rpx; color: #666; font-family: serif; font-style: italic; opacity: 0.8;
}

/* 头像圆环：更素雅 */
.avatar-ring {
    width: 100rpx; height: 100rpx;
    border-radius: 50%;
    border: 2rpx solid #333; /* 墨色边框 */
    padding: 4rpx;
    
    .avatar-img, .avatar-placeholder {
        width: 100%; height: 100%; border-radius: 50%;
        background-color: #E0E0E0;
        display: flex; align-items: center; justify-content: center;
    }
    .avatar-placeholder .char {
        font-size: 36rpx; color: #555; font-family: serif;
    }
}

/* ====================================
   3. 亚克力数据栏 (镇纸风格)
   ==================================== */
.acrylic-stats {
    position: relative;
    background: rgba(255, 255, 255, 0.4);
    backdrop-filter: blur(20px);
    border-radius: 24rpx;
    padding: 36rpx 0;
    display: flex; justify-content: space-evenly; align-items: center;
    border: 1px solid rgba(255, 255, 255, 0.6);
    box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.04);
}
.glass-shine {
    position: absolute; top: 0; left: 0; right: 0; height: 100%;
    background: linear-gradient(120deg, rgba(255,255,255,0.5) 0%, transparent 50%);
    border-radius: 24rpx; pointer-events: none;
}

.stat-box {
    display: flex; flex-direction: column; align-items: center; z-index: 2;
    .val {
        font-size: 44rpx; font-weight: bold; color: #1A1A1A;
        font-family: serif; /* 衬线体数字更有质感 */
    }
    .lbl { font-size: 22rpx; color: #666; margin-top: 6rpx; }
}
.stat-divider { width: 1px; height: 40rpx; background: rgba(0,0,0,0.1); }

/* ====================================
   4. 内容区 & 每日一题
   ==================================== */
.main-content { padding: 0 40rpx; position: relative; z-index: 2; }

.section-header { margin-bottom: 24rpx; display: flex; align-items: baseline; gap: 16rpx; }
.section-title { font-size: 36rpx; font-weight: bold; color: #1A1A1A; letter-spacing: 2rpx; }
.section-desc { font-size: 24rpx; color: #888; font-family: serif; }

.daily-paper-card {
    background: #fff;
    border-radius: 24rpx;
    padding: 40rpx;
    /* 纸张阴影 */
    box-shadow: 0 10rpx 30rpx rgba(0, 0, 0, 0.05);
    border: 1px solid rgba(0,0,0,0.03);
    position: relative;
    transition: transform 0.2s;
    
    &:active { transform: scale(0.99); }
}

.card-top { display: flex; justify-content: space-between; margin-bottom: 24rpx; }
.tag-ink {
    font-size: 22rpx; color: #333; background: #F0F0F0;
    padding: 6rpx 16rpx; border-radius: 8rpx;
}
.date-ink { 
    font-size: 36rpx; font-weight: bold; color: #1A1A1A; font-family: serif; 
    .month { font-size: 22rpx; color: #888; font-weight: normal; margin-left: 4rpx; }
}

.daily-title {
    font-size: 30rpx; color: #333; line-height: 1.7;
    margin-bottom: 30rpx; font-weight: 500;
    display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden;
}

.daily-footer {
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px dashed #EEE; padding-top: 20rpx;
    
    .action-text { font-size: 24rpx; color: #666; }
    .ink-arrow { font-size: 30rpx; color: #333; opacity: 0.6; }
}

/* ====================================
   5. 专项训练 (Grid)
   ==================================== */
.category-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 24rpx;
}

.cat-item {
    background: rgba(255,255,255,0.7);
    border: 1px solid rgba(255,255,255,0.8);
    border-radius: 20rpx;
    padding: 30rpx 0;
    display: flex; flex-direction: column; align-items: center;
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.02);
    
    &:active { transform: scale(0.98); background: #fff; }
    
    .cat-icon-box {
        width: 90rpx; height: 90rpx;
        border-radius: 24rpx;
        /* 使用传入的淡雅背景色 */
        background-color: var(--ink-color);
        display: flex; align-items: center; justify-content: center;
        margin-bottom: 16rpx;
        .cat-emoji { font-size: 40rpx; }
    }
    
    .cat-name { font-size: 26rpx; color: #444; }
}

/* ====================================
   6. 悬浮印章 (FAB)
   ==================================== */
.ink-fab {
    position: fixed; bottom: 60rpx; right: 40rpx; z-index: 100;
    display: flex; flex-direction: column; align-items: center;
    gap: 10rpx;
}

.fab-inner {
    width: 110rpx; height: 110rpx;
    background: #FFFFFF; /* 改为白色 */
    border-radius: 50%;
    display: flex; align-items: center; justify-content: center;
    /* 阴影加重一点，保证在浅色背景上能看清 */
    box-shadow: 0 10rpx 30rpx rgba(0,0,0,0.15); 
    border: 2rpx solid rgba(0,0,0,0.05); /* 淡淡的边框 */
    
    &:active { transform: scale(0.95); background: #F5F5F5; }
}

/* Logo 图片处理 */


.fab-label {
    font-size: 22rpx; color: #333; font-weight: bold;
    background: rgba(255,255,255,0.8); padding: 4rpx 12rpx; border-radius: 20rpx;
    backdrop-filter: blur(4px);
}

/* ====================================
   7. Loading 动画 (水墨呼吸)
   ==================================== */
.loading-overlay {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    opacity: 0; transition: opacity 0.3s ease;
    &.show { opacity: 1; }
}

.loading-backdrop {
    position: absolute; width: 100%; height: 100%;
    background: rgba(247, 247, 242, 0.95); /* 米白遮罩 */
    backdrop-filter: blur(10px);
}

.loading-content {
    position: relative; z-index: 1;
    display: flex; flex-direction: column; align-items: center;
}

.ink-breathing-container {
    width: 200rpx; height: 200rpx;
    position: relative;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 40rpx;
}

/* Logo 位于中心 */
.loading-logo {
    width: 100rpx; height: 100rpx;
    z-index: 10;
    mix-blend-mode: multiply; /* 正片叠底 */
    animation: breathing 2s ease-in-out infinite;
}

/* 水墨晕染波纹 */
.ink-ripple {
    position: absolute;
    width: 100%; height: 100%;
    border-radius: 50%;
    background: rgba(0,0,0,0.05);
    transform: scale(0.5);
    animation: ripple 2s linear infinite;
}
.ink-ripple.delay { animation-delay: 1s; }

.text-area { text-align: center; }
.main-tip { font-size: 34rpx; color: #1A1A1A; font-weight: bold; margin-bottom: 10rpx; letter-spacing: 4rpx; }
.sub-tip { font-size: 24rpx; color: #888; font-family: serif; }

/* ====================================
   8. 底部弹窗 (亚克力化)
   ==================================== */
.modal-mask {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.4); z-index: 999;
    opacity: 0; pointer-events: none; transition: opacity 0.3s;
    display: flex; align-items: flex-end;
    &.show { opacity: 1; pointer-events: auto; }
}

.acrylic-sheet {
    width: 100%;
    background: rgba(255, 255, 255, 0.85); /* 提高透明度 */
    backdrop-filter: blur(25px);
    border-top-left-radius: 40rpx; border-top-right-radius: 40rpx;
    padding: 20rpx 40rpx 60rpx;
    transform: translateY(100%); transition: transform 0.4s cubic-bezier(0.19, 1, 0.22, 1);
    box-shadow: 0 -10rpx 40rpx rgba(0,0,0,0.05);
    
    .modal-mask.show & { transform: translateY(0); }
}

.sheet-handle { width: 80rpx; height: 8rpx; background: #CCC; border-radius: 4rpx; margin: 20rpx auto 40rpx; }
.sheet-title { font-size: 36rpx; font-weight: bold; color: #1A1A1A; }
.sheet-sub { font-size: 24rpx; color: #666; margin-top: 8rpx; font-family: serif; }

.sheet-section { margin-bottom: 40rpx; }
.sheet-label { font-size: 28rpx; font-weight: bold; color: #333; margin-bottom: 20rpx; display: block; }
.tags-row { display: flex; flex-wrap: wrap; gap: 20rpx; }

.tag-item {
    background: rgba(255,255,255,0.5);
    padding: 16rpx 28rpx; border-radius: 16rpx;
    font-size: 26rpx; color: #555;
    border: 1px solid rgba(0,0,0,0.05);
    transition: all 0.2s;
    
    &.active {
        background: #1A1A1A; color: #fff; border-color: #1A1A1A;
    }
}

.start-btn {
    width: 100%; height: 96rpx; line-height: 96rpx;
    background: #1A1A1A; color: #fff;
    border-radius: 16rpx; font-size: 32rpx; letter-spacing: 4rpx;
    box-shadow: 0 10rpx 20rpx rgba(0,0,0,0.1);
    margin-top: 20rpx;
    &:active { transform: scale(0.98); }
}

/* 动画定义 */
@keyframes slideDown { from { opacity: 0; transform: translateY(-20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }
@keyframes scaleUp { from { opacity: 0; transform: scale(0.95); } to { opacity: 1; transform: scale(1); } }
@keyframes staggerUp { from { opacity: 0; transform: translateY(20px); } to { opacity: 1; transform: translateY(0); } }
@keyframes float { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-8rpx); } }

/* 加载动画：呼吸与扩散 */
@keyframes breathing { 0%, 100% { transform: scale(1); opacity: 0.8; } 50% { transform: scale(1.1); opacity: 1; } }
@keyframes ripple { 0% { transform: scale(0.5); opacity: 0.6; } 100% { transform: scale(1.5); opacity: 0; } }
</style>