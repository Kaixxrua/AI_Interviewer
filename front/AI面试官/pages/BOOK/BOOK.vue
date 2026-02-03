<template>
  <view class="bank-container">
    
    <!-- 1. 静态宣纸背景 (全局统一) -->
    <view class="paper-bg">
      <view class="grain-overlay"></view>
    </view>

    <!-- ================= 2. 顶部搜索区 (水墨风格) ================= -->
    <view class="header-ink animate-slide-down">
      <!-- 搜索栏 -->
      <view class="search-row">
        <view class="search-capsule">
          <text class="search-icon">🔎</text>
          <input 
            class="search-input" 
            v-model="searchKeyword" 
            placeholder="搜寻考点..." 
            placeholder-class="input-ph"
            confirm-type="search"
            @confirm="onSearch" 
          />
        </view>
        <!-- 筛选按钮 (类似印章) -->
        <view class="filter-trigger" @click="toggleFilter" :class="{ active: showFilter }">
          <view class="icon-box">🌪️</view>
        </view>
      </view>

      <!-- 分类 Tab 栏 -->
      <scroll-view scroll-x class="category-tabs" :scroll-into-view="'tab-' + currentTabId" scroll-with-animation :show-scrollbar="false">
        <view 
          class="tab-pill" 
          v-for="(item, index) in categories" 
          :key="item.id"
          :id="'tab-' + item.id"
          :class="{ active: currentTabId === item.id }"
          @click="switchTab(item.id)"
        >
          {{ item.name }}
        </view>
      </scroll-view>
      
      <!-- 筛选下拉面板 (亚克力) -->
      <view class="filter-dropdown" :class="{ show: showFilter }">
          <view class="filter-section">
              <text class="section-label">学习状态</text>
              <view class="tag-wrap">
                  <view class="filter-tag" :class="{ active: filterStatus === 'all' }" @click="filterStatus = 'all'">全部</view>
                  <view class="filter-tag" :class="{ active: filterStatus === 'unmastered' }" @click="filterStatus = 'unmastered'">📝 待练</view>
                  <view class="filter-tag" :class="{ active: filterStatus === 'mastered' }" @click="filterStatus = 'mastered'">✅ 已懂</view>
              </view>
          </view>
          <view class="filter-section">
              <text class="section-label">难度等级</text>
              <view class="tag-wrap">
                  <view class="filter-tag" 
                        :class="{ active: filterDifficulty === level }" 
                        v-for="level in ['全部', '简单', '中等', '困难']" 
                        :key="level"
                        @click="filterDifficulty = level">
                      {{ level }}
                  </view>
              </view>
          </view>
          <view class="filter-reset" @click="resetFilters">重置筛选条件 ↺</view>
      </view>
    </view>

    <!-- ================= 3. 题目列表区 ================= -->
    <scroll-view scroll-y class="question-list" :scroll-top="scrollTop" enable-back-to-top>
      <view class="list-padding">
          <view 
            class="question-paper-card animate-fade-in" 
            v-for="(item, index) in questionList" 
            :key="item.id"
            :style="{ animationDelay: (index * 0.05) + 's' }"
            @click="openDetail(item)"
          >
            <view class="card-top">
              <view class="meta-row">
                <!-- 难度标签 (淡雅色) -->
                <view class="tag-ink difficulty" :class="getDifficultyClass(item.difficulty)">{{ item.difficulty }}</view>
                <view class="tag-ink type">{{ item.type }}</view>
              </view>
              <!-- 状态印章 -->
              <view class="status-stamp" :class="{ show: item.mastered }">
                  已阅
              </view>
            </view>
            
            <text class="q-title">{{ item.title }}</text>
            
            <view class="card-bottom">
              <text class="tap-hint">点击查看解析</text>
              <view class="ink-arrow">→</view>
            </view>
          </view>

          <!-- 空状态 -->
          <view v-if="questionList.length === 0 && !isLoading" class="empty-state animate-scale-up">
              <text class="empty-icon">🍃</text>
              <text class="empty-text">空空如也</text>
              <text class="empty-sub">换个条件试试？</text>
          </view>
          
          <!-- 分页栏 -->
          <view class="pagination-bar" v-if="questionList.length > 0 || page > 1">
                <view class="page-ctrl" :class="{ disabled: page === 1 || isLoading }" @click="changePage(-1)">👈</view>
                <text class="page-num">{{ page }}</text>
                <view class="page-ctrl" :class="{ disabled: !hasMore || isLoading }" @click="changePage(1)">👉</view>
          </view>
          
          <view style="height: 120rpx;"></view> <!-- 底部留白 -->
      </view>
    </scroll-view>

    <!-- ================= 4. 详情弹窗 (亚克力磨砂) ================= -->
    <view class="detail-mask" :class="{ show: isDetailOpen }" @click="closeDetail" @touchmove.stop.prevent>
        <view class="detail-acrylic-card" @click.stop>
            <view class="card-handle"></view>
            <view class="modal-header">
                <view class="modal-tags">
                    <text class="modal-tag">{{ currentQuestion.type }}</text>
                    <text class="modal-tag diff">{{ currentQuestion.difficulty }}</text>
                </view>
                <view class="modal-close" @click="closeDetail">×</view>
            </view>
            
            <scroll-view scroll-y class="modal-content">
                <text class="modal-title">{{ currentQuestion.title }}</text>
                
                <view class="knowledge-block">
                    <view class="block-label">💡 核心考点</view>
                    <text class="block-text">{{ currentQuestion.keyPoints }}</text>
                </view>

                <view class="knowledge-block answer">
                    <view class="block-label">📝 参考解析</view>
                    <text class="block-text">{{ currentQuestion.briefAnswer }}</text>
                </view>
            </scroll-view>

            <view class="modal-footer">
                <button class="action-btn secondary" @click="toggleMaster">
                    {{ currentQuestion.mastered ? '标记未练' : '标记已懂' }}
                </button>
                <button class="action-btn primary" @click="startAiPractice">
                    <text class="btn-icon">🤖</text> 模拟面试此题
                </button>
            </view>
        </view>
    </view>

  </view>
</template>

<script setup>
import { ref, reactive, computed, onMounted, watch } from 'vue';
import { request } from '../../utils/request.js';
import { onReachBottom } from '@dcloudio/uni-app';

// ... 数据逻辑保持完全一致 ...
const searchKeyword = ref('');
const currentTabId = ref('all');
const showFilter = ref(false);
const filterDifficulty = ref('全部');
const filterStatus = ref('all'); 
const isDetailOpen = ref(false);
const currentQuestion = ref({});
const questionList = ref([]); 
const isLoading = ref(false);
const page = ref(1);
const pageSize = ref(20);
const hasMore = ref(true);
const scrollTop = ref(0);

const categories = [
    { id: 'all', name: '全部' },
    { id: 'python', name: 'Python' },
    { id: 'frontend', name: '前端' },
    { id: 'concurrency', name: '高并发' },
    { id: 'algo', name: '算法' },
    { id: 'mysql', name: 'MySQL' },
    { id: 'redis', name: 'Redis' },
    { id: 'network', name: '计算机网络' },
    { id: 'hr', name: 'HR行为面' },
];

const fetchQuestions = async (targetPage = 1) => {
    isLoading.value = true;
    try {
        const params = {
            page: targetPage,
            page_size: pageSize.value,
        };
        if (currentTabId.value !== 'all') {
             const mapName = categories.find(c => c.id === currentTabId.value)?.name;
             params.category = mapName || currentTabId.value;
        }
        if (filterDifficulty.value !== '全部') params.difficulty = filterDifficulty.value;
        if (filterStatus.value !== 'all') params.status = filterStatus.value;
        if (searchKeyword.value) params.keyword = searchKeyword.value;

        const res = await request({ url: '/questions/list', method: 'GET', data: params });

        const newItems = res.map(item => ({
            id: item.id,
            type: item.category,
            difficulty: item.difficulty,
            freq: item.freq,
            mastered: item.is_mastered,
            title: item.title,
            briefAnswer: item.content,
            keyPoints: '点击详情查看完整解析与考点分析'
        }));

        questionList.value = newItems;
        page.value = targetPage;
		scrollTop.value = scrollTop.value === 0 ? 0.1 : 0;
        hasMore.value = newItems.length >= pageSize.value;

    } catch (e) {
        console.error(e);
        uni.showToast({ title: '加载失败', icon: 'none' });
    } finally {
        isLoading.value = false;
    }
};

const resetFilters = () => {
    filterDifficulty.value = '全部';
    filterStatus.value = 'all';
};
const changePage = (step) => {
    const target = page.value + step;
    if (target < 1) return;
    fetchQuestions(target);
};
watch([currentTabId, filterDifficulty, filterStatus], () => { fetchQuestions(1); });
const onSearch = () => { fetchQuestions(1); };
onMounted(() => { fetchQuestions(1); });

const toggleFilter = () => { showFilter.value = !showFilter.value; };
const switchTab = (id) => { currentTabId.value = id; showFilter.value = false; };

// 🟢 配色类名映射
const getDifficultyClass = (diff) => {
    if (diff === '简单') return 'easy';
    if (diff === '中等') return 'medium';
    return 'hard';
};

const openDetail = (item) => { currentQuestion.value = item; isDetailOpen.value = true; };
const closeDetail = () => { isDetailOpen.value = false; };

const toggleMaster = async () => {
    const q = currentQuestion.value;
    const oldStatus = q.mastered;
    q.mastered = !oldStatus;
    try {
        await request({ url: `/questions/toggle_master?question_id=${q.id}`, method: 'POST' });
        const listItem = questionList.value.find(i => i.id === q.id);
        if (listItem) listItem.mastered = q.mastered;
        uni.showToast({ title: q.mastered ? '已标记' : '已取消', icon: 'none' });
    } catch (e) {
        q.mastered = oldStatus; 
        uni.showToast({ title: '操作失败', icon: 'none' });
    }
};

const startAiPractice = () => {
    const q = currentQuestion.value;
    const prompt = `面试官你好，我想进行单题突击训练。请针对"${q.title}"这道题对我进行面试。`;
    uni.setStorageSync('auto_send_message', prompt);
    isDetailOpen.value = false;
    uni.navigateTo({
        url: `/pages/Assistant/Assistant?mode=interview&topic=${q.type}&difficulty=专项练习`
    });
};
</script>

<style lang="scss" scoped>
/* 全局字体与背景 */
:global(page) {
    background-color: #F7F7F2; /* 宣纸白 */
    font-family: 'PingFang SC', 'Noto Serif SC', serif;
}

.bank-container {
    display: flex; flex-direction: column; height: 100vh; overflow: hidden; position: relative;
}

/* ====================================
   1. 宣纸背景 (复用)
   ==================================== */
.paper-bg {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; z-index: 0;
    background: radial-gradient(circle at 50% 30%, #FDFDFB 0%, #F2F2EB 100%);
    pointer-events: none;
}
.grain-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.4;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.15'/%3E%3C/svg%3E");
}

/* ====================================
   2. 头部搜索 (水墨风)
   ==================================== */
.header-ink {
    position: relative; z-index: 100;
    /*  हल्का 磨砂，不完全遮挡宣纸 */
    background: rgba(255, 255, 255, 0.6);
    backdrop-filter: blur(15px);
    border-bottom: 1px solid rgba(0,0,0,0.05);
    display: flex; flex-direction: column;
}

.search-row {
    padding: calc(var(--status-bar-height) + 20rpx) 30rpx 20rpx;
    display: flex; align-items: center; gap: 20rpx;
}

.search-capsule {
    flex: 1; height: 80rpx;
    background: #fff; /* 纯白纸张感 */
    border-radius: 16rpx; /* 方润圆角 */
    display: flex; align-items: center; padding: 0 30rpx;
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
    
    .search-icon { font-size: 32rpx; margin-right: 16rpx; opacity: 0.6; }
    .search-input { flex: 1; font-size: 28rpx; color: #1A1A1A; height: 100%; }
    .input-ph { color: #999; font-family: serif; }
}

.filter-trigger {
    width: 80rpx; height: 80rpx;
    background: #fff; border-radius: 16rpx;
    display: flex; align-items: center; justify-content: center;
    box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05);
    border: 1px solid rgba(0,0,0,0.05);
    
    .icon-box { font-size: 40rpx; transition: transform 0.3s; }
    &.active { background: #1A1A1A; .icon-box { color: #fff; transform: rotate(180deg); } }
}

/* Tab 栏 */
.category-tabs { white-space: nowrap; height: 100rpx; padding: 0 10rpx; }
.tab-pill {
    display: inline-block; padding: 10rpx 32rpx; margin: 0 10rpx;
    background: transparent; color: #666; font-size: 28rpx;
    border-radius: 12rpx; font-weight: 500; transition: all 0.2s;
    position: relative; top: 16rpx;
    border: 1px solid transparent;
    
    &.active {
        background: #1A1A1A; color: #fff; /* 浓墨黑底白字 */
        box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.2);
    }
}

/* 筛选下拉 (亚克力) */
.filter-dropdown {
    overflow: hidden; max-height: 0;
    background: rgba(255,255,255,0.9);
    backdrop-filter: blur(20px);
    transition: max-height 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    border-bottom: 1px solid rgba(0,0,0,0.05);
    &.show { max-height: 500rpx; padding-bottom: 30rpx; }
}
.filter-section { padding: 20rpx 40rpx; }
.section-label { font-size: 24rpx; color: #333; margin-bottom: 20rpx; display: block; font-weight: bold; }
.tag-wrap { display: flex; gap: 20rpx; flex-wrap: wrap; }
.filter-tag {
    padding: 10rpx 30rpx; background: #F5F5F0; color: #555;
    font-size: 26rpx; border-radius: 12rpx;
    border: 1px solid transparent; transition: all 0.2s;
    
    &.active {
        background: #1A1A1A; color: #fff; border-color: #1A1A1A;
    }
}
.filter-reset { text-align: center; color: #666; font-size: 24rpx; margin-top: 10rpx; padding: 10rpx; text-decoration: underline; }

/* ====================================
   3. 列表区
   ==================================== */
.question-list { flex: 1; height: 0; position: relative; z-index: 1; }
.list-padding { padding: 30rpx; }

.question-paper-card {
    background: #fff;
    border-radius: 20rpx;
    padding: 40rpx;
    margin-bottom: 30rpx;
    /* 纸张微阴影 */
    box-shadow: 0 6rpx 20rpx rgba(0,0,0,0.03);
    border: 1px solid rgba(0,0,0,0.04);
    position: relative;
    transition: transform 0.1s;
    
    &:active { transform: scale(0.99); }
}

.card-top { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 24rpx; }
.meta-row { display: flex; gap: 12rpx; }

/* 标签样式 (淡雅色) */
.tag-ink {
    font-size: 20rpx; padding: 6rpx 16rpx; border-radius: 8rpx; font-weight: 500;
    &.type { background: #F5F5F0; color: #666; }
    /* 莫兰迪色系 */
    &.difficulty.easy { background: #E8F5E9; color: #2E7D32; }   /* 浅绿 */
    &.difficulty.medium { background: #FFF3E0; color: #EF6C00; } /* 浅橙 */
    &.difficulty.hard { background: #FFEBEE; color: #C62828; }   /* 浅红 */
}

/* 状态印章 */
.status-stamp {
    font-size: 22rpx; color: #C62828; border: 2rpx solid #C62828;
    padding: 2rpx 8rpx; border-radius: 6rpx; transform: rotate(-10deg);
    opacity: 0; transition: opacity 0.3s;
    font-family: serif; font-weight: bold;
    &.show { opacity: 0.8; }
}

.q-title {
    font-size: 32rpx; color: #1A1A1A; font-weight: 600;
    line-height: 1.6; margin-bottom: 30rpx; display: block;
}

.card-bottom {
    display: flex; justify-content: space-between; align-items: center;
    border-top: 1px dashed #E0E0E0; padding-top: 20rpx;
    
    .tap-hint { font-size: 24rpx; color: #999; font-family: serif; }
    .ink-arrow { font-size: 30rpx; color: #333; opacity: 0.6; }
}

/* 分页 & 空状态 */
.pagination-bar {
    display: flex; justify-content: center; align-items: center; gap: 40rpx; margin-top: 20rpx;
    .page-ctrl {
        width: 80rpx; height: 80rpx; background: #fff; border-radius: 50%;
        display: flex; align-items: center; justify-content: center;
        box-shadow: 0 4rpx 12rpx rgba(0,0,0,0.05); font-size: 36rpx;
        &:active { transform: scale(0.9); }
        &.disabled { opacity: 0.5; pointer-events: none; background: #F5F5F0; }
    }
    .page-num { font-size: 32rpx; font-weight: bold; color: #1A1A1A; }
}
.empty-state {
    padding-top: 100rpx; display: flex; flex-direction: column; align-items: center;
    .empty-icon { font-size: 100rpx; margin-bottom: 20rpx; opacity: 0.4; filter: grayscale(1); }
    .empty-text { font-size: 30rpx; color: #666; font-weight: 500; }
    .empty-sub { font-size: 24rpx; color: #999; margin-top: 10rpx; font-family: serif; }
}

/* ====================================
   4. 详情弹窗 (亚克力)
   ==================================== */
.detail-mask {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%;
    background: rgba(0,0,0,0.4); z-index: 999;
    opacity: 0; visibility: hidden; transition: all 0.3s;
    display: flex; align-items: flex-end;
    &.show { opacity: 1; visibility: visible; }
}

.detail-acrylic-card {
    width: 100%; height: 85vh;
    /* 强磨砂效果 */
    background: rgba(255, 255, 255, 0.9);
    backdrop-filter: blur(20px);
    border-top-left-radius: 40rpx; border-top-right-radius: 40rpx;
    display: flex; flex-direction: column;
    transform: translateY(100%); transition: transform 0.3s cubic-bezier(0.2, 0.8, 0.2, 1);
    box-shadow: 0 -20rpx 60rpx rgba(0,0,0,0.1);
    
    .detail-mask.show & { transform: translateY(0); }
}

.card-handle {
    width: 80rpx; height: 8rpx; background: #CCC; border-radius: 4rpx;
    align-self: center; margin-top: 20rpx; margin-bottom: 10rpx;
}

.modal-header {
    padding: 20rpx 40rpx; display: flex; justify-content: space-between; align-items: center;
    .modal-tags { display: flex; gap: 16rpx; }
    .modal-tag { 
        font-size: 22rpx; padding: 6rpx 16rpx; background: #F5F5F0; color: #666; border-radius: 8rpx;
        &.diff { background: #E3F2FD; color: #007AFF; }
    }
    .modal-close { font-size: 44rpx; color: #999; padding: 10rpx; }
}

.modal-content { flex: 1; padding: 0 40rpx; box-sizing: border-box; height: 0; }

.modal-title {
    font-size: 36rpx; font-weight: bold; color: #1A1A1A; 
    line-height: 1.5; margin-bottom: 40rpx; display: block;
}

.knowledge-block {
    background: rgba(255,255,255,0.6); padding: 30rpx; border-radius: 20rpx; margin-bottom: 30rpx;
    border: 1px solid rgba(0,0,0,0.03);
    
    .block-label { font-size: 26rpx; font-weight: bold; color: #333; margin-bottom: 16rpx; }
    .block-text { font-size: 30rpx; color: #555; line-height: 1.7; text-align: justify; }
    
    &.answer { 
        background: #F8F9FA; 
        .block-label { color: #1A1A1A; } 
    }
}

.modal-footer {
    padding: 30rpx 40rpx calc(30rpx + env(safe-area-inset-bottom));
    display: flex; gap: 30rpx;
    background: rgba(255,255,255,0.8);
    border-top: 1px solid rgba(0,0,0,0.05);
}

.action-btn {
    flex: 1; height: 100rpx; border-radius: 20rpx;
    display: flex; align-items: center; justify-content: center;
    font-size: 30rpx; font-weight: 600; border: none;
    
    /* 方案 B: 按钮高对比度 */
    &.secondary { background: #F5F5F0; color: #333; }
    &.primary { 
        background: #1A1A1A; color: #fff; /* 墨黑按钮 */
        box-shadow: 0 10rpx 20rpx rgba(0,0,0,0.15); 
        .btn-icon { margin-right: 10rpx; }
    }
    
    &:active { transform: scale(0.98); }
    &::after { border: none; }
}

/* 动画类 */
.animate-slide-down { animation: slideDown 0.6s ease-out forwards; }
.animate-fade-in { animation: fadeIn 0.6s ease-out forwards; opacity: 0; }
.animate-scale-up { animation: scaleUp 0.5s ease-out forwards; opacity: 0; }

@keyframes slideDown { from { transform: translateY(-20rpx); opacity: 0; } to { transform: translateY(0); opacity: 1; } }
@keyframes fadeIn { to { opacity: 1; } }
@keyframes scaleUp { from { transform: scale(0.95); opacity: 0; } to { transform: scale(1); opacity: 1; } }
</style>