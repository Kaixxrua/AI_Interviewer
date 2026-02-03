
<template>
  <view class="chat-container">
    
    <!-- 1. 静态宣纸背景 -->
    <view class="paper-bg">
      <view class="grain-overlay"></view>
    </view>

    <!-- 2. 自定义导航栏 -->
    <view class="custom-nav-glass" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="nav-content">
        <view class="menu-btn" @click="openDrawer">
          <text class="menu-icon-ink">☰</text>
        </view>
        <text class="nav-title-ink">{{ isInterviewMode ? '面试考核' : 'AI 助手' }}</text>
        <view class="menu-placeholder"></view>
      </view>
    </view>

    <!-- 3. 侧边栏 Drawer -->
    <view class="drawer-mask" :class="{ show: isDrawerOpen }" @click="closeDrawer"></view>
    <view class="drawer-paper" :class="{ open: isDrawerOpen }" :style="{ paddingTop: statusBarHeight + 'px' }">
      <view class="drawer-header">
        <view class="nav-back-btn" @click="goHome">
          <text class="back-arrow-ink">←</text>
        </view>
        <text class="drawer-title-ink">往昔对话</text>
      </view>

      <scroll-view scroll-y class="drawer-list">
        <view 
          v-for="(item, index) in sessionList" 
          :key="item.id" 
          class="drawer-item-ink" 
          :class="{ active: item.id === sessionId }"
          @click="switchSession(item.id)"
        >
          <text class="item-icon">💬</text>
          <text class="item-text">{{ item.title }}</text>
        </view>
      </scroll-view>

      <view class="drawer-footer">
        <view class="footer-btn-ink" @click="handleNewSession">
          <text class="btn-icon">＋</text>
          <text>开启新篇章</text>
        </view>
      </view>
    </view>

    <!-- 4. 主聊天区域 -->
    
    <!-- 面试模式进度条 -->
    <view v-if="isInterviewMode" class="interview-bookmark">
          <!-- 第一行：标题和标签 -->
          <view class="interview-header-row">
              <text class="interview-tag">{{ interviewInfo.topic }}</text>
              <text class="interview-level text-ellipsis">{{ interviewInfo.difficulty }}</text>
          </view>
          
          <!-- 第二行：进度条和按钮 -->
          <view class="interview-progress-row">
            <view class="progress-container">
                <view class="progress-text">
                  <text>进度</text>
                  <text class="round-count"><text class="highlight">{{ interviewInfo.currentRound }}</text>/{{ interviewInfo.maxRounds }}</text>
                </view>
                <view class="progress-track-ink">
                  <view class="progress-fill-ink" :style="{ width: progressPercentage + '%' }"></view>
                </view>
            </view>
            
            <view 
                class="end-btn-ink" 
                :class="{ disabled: isGenerating }"
                @click="handleRightBtnClick"
            >
                <text>{{ isInterviewFinished ? '阅卷' : '交卷' }}</text>
            </view>
          </view>
    	</view>

    <!-- 记忆设置栏 -->
    <view class="settings-paper">
      <view class="settings-header" @click="toggleSettings">
        <text class="settings-title">⚙️ 记忆容量: {{ memoryLimit }} 轮</text>
        <text class="toggle-icon">{{ showSettings ? '▲' : '▼' }}</text>
      </view>
      <view v-if="showSettings" class="settings-content">
        <view class="slider-box">
          <text class="slider-label">10</text>
          <slider 
            :value="memoryLimit" 
            @change="onLimitChange" 
            min="10" max="20" step="1" 
            activeColor="#1A1A1A" backgroundColor="#E0E0E0" block-color="#1A1A1A" block-size="18" class="memory-slider"
          />
          <text class="slider-label">20</text>
        </view>
        <view class="tips">AI 将铭记最近 {{ memoryLimit }} 次问答</view>
      </view>
    </view>

    <!-- 聊天滚动区 -->
    <scroll-view 
      class="chat-scroll-view" 
      scroll-y="true" 
      :scroll-into-view="scrollIntoViewId"
      :scroll-with-animation="true"
      :enable-back-to-top="true"
      @click="closeActionMenu"
	  @touchstart="onUserTouch"  
	  @touchmove="onUserTouch"
    >
      <view 
        class="message-group" 
        v-for="(msg, index) in messages" 
        :key="msg.id || msg._uuid" 
        :id="'msg-' + index"
      >
        <view class="message-item" :class="msg.role === 'user' ? 'user-side' : 'ai-side'">
          
          <!-- AI 侧 -->
          <template v-if="msg.role === 'assistant'">
            <view class="avatar-container ai" @click.stop="toggleMenu(index)">
                <image src="/static/logo.png" mode="aspectFit" class="avatar-logo-ink"></image>
            </view>
            
            <view class="bubble ai-paper-bubble" 
                  @longpress="toggleMenu(index)" 
                  :class="{ 'active': currentActionIndex === index }">
                
                <view class="markdown-wrapper">
                  <!-- 深度思考 -->
                  <view v-if="msg.thinkingContent || msg.isThinkingStill" class="thinking-accordion">
                    <view class="thinking-header" @click="toggleThinking(index)">
                      <text class="thinking-icon">💭</text>
                      <view class="header-text-area">
                        <text class="thinking-title" v-if="!msg.isThinkingStill">深度思考</text>
                        <view class="thinking-loading" v-else>
                          <text class="thinking-title">思考中...</text>
                          <view class="header-spinner"></view>
                        </view>
                      </view>
                      <text class="thinking-arrow">{{ msg.isThinkingOpen ? '▲' : '▼' }}</text>
                    </view>
                    <view v-if="msg.isThinkingOpen" class="thinking-body">
                      <text>{{ msg.thinkingContent }}</text>
                    </view>
                  </view>
              
                  <!-- 🔥🔥🔥 核心修改：使用 mp-html 渲染文本，CodeBlock 渲染代码 🔥🔥🔥 -->
                  <block v-for="(part, pIndex) in parseMessage(msg.content)" :key="pIndex">
                    <!-- 文本部分：使用 markdown-it 转成 HTML，再用 mp-html 渲染 -->
                    <view v-if="part.type === 'text'" class="md-text-part">
                      <mp-html 
                        :content="renderMarkdownToHtml(part.content)" 
                        :selectable="true" 
                        :tag-style="mpHtmlStyle"
                      />
                    </view>
                    <!-- 代码部分：继续使用你的自定义组件 (效果更好) -->
                    <view v-else-if="part.type === 'code'" class="code-block-wrapper">
                       <CodeBlock :code="part.content" :language="part.lang"></CodeBlock>
                    </view>
                  </block>
              
                  <view v-if="msg.costTime" class="msg-footer">
                    <text>⏱️ {{ msg.costTime }}s</text>
                  </view>
                </view>
                <view class="bubble-menu-icon" @click.stop="toggleMenu(index)">⋮</view>
            </view>
          </template>
      
          <template v-else>
                      <view class="bubble user-ink-bubble" 
                            @longpress="toggleMenu(index)" 
                            :class="{ 'active': currentActionIndex === index }">
                          <!-- ... 气泡内容保持不变 ... -->
                          <view v-if="msg.image && (!msg.file_meta || !msg.file_meta.is_pdf)" class="msg-img-box" @click.stop="previewImage(msg.image)">
                              <!-- 🔥 修改点：mode 改为 aspectFill -->
                              <image :src="msg.image" mode="aspectFill" class="msg-img"></image>
                          </view>
                          <view v-if="msg.file_meta && msg.file_meta.is_pdf" class="msg-file-box" @click.stop="openDocument(msg.image)">
                              <view class="file-icon">📄</view>
                              <view class="file-info">
                                  <text class="file-name">{{ msg.file_meta.name || '文档.pdf' }}</text>
                                  <text class="file-type">PDF 文档</text>
                              </view>
                          </view>
                          <text v-if="msg.content" class="user-text" selectable="false">{{ msg.content }}</text>
                      </view>
                      
                      <!-- 🔥🔥🔥 修改点：用户头像 🔥🔥🔥 -->
                      <view class="avatar-container user" @click.stop="toggleMenu(index)">
                          <image 
                              v-if="userAvatar" 
                              :src="userAvatar" 
                              mode="aspectFill" 
                              class="avatar-user-img"
                          ></image>
                          <text v-else class="user-avatar-text">我</text>
                      </view>
                    </template>
        </view>
    
        <!-- 菜单 -->
        <view class="msg-menu" :class="[msg.role === 'user' ? 'menu-right' : 'menu-left', { 'show': currentActionIndex === index }]">
          <view class="menu-inner-ink">
            <view class="menu-item" @click="handleCopy(msg.content)">
              <text class="menu-icon">📋</text> <text>复制</text>
            </view>
            <view class="menu-item" @click="handleRegenerate(index)" v-if="!isGenerating">
              <text class="menu-icon">🔄</text> <text>重试</text>
            </view>
            <view class="menu-item delete" @click="handleDelete(index)">
              <text class="menu-icon">🗑️</text> <text>删除</text>
            </view>
          </view>
        </view>
      </view>

      <!-- Loading -->
      <view v-if="isAiThinking" class="message-item ai-side" id="msg-loading">
        <view class="avatar-container ai">
             <image src="/static/logo.png" mode="aspectFit" class="avatar-logo-ink"></image>
        </view>
        <view class="bubble loading-bubble-ink">
            <view class="dot-ink"></view><view class="dot-ink"></view><view class="dot-ink"></view>
        </view>
      </view>

      <view style="height: 300rpx; width: 100%;"></view>
    </scroll-view>

    <!-- 5. 底部输入面板 -->
    <view class="input-panel-glass">
      <view v-if="tempFile.path" class="file-preview-area">
          <view v-if="tempFile.type === 'image'" class="image-preview-box">
              <image :src="tempFile.path" mode="aspectFill" class="preview-img"></image>
              <view class="close-btn" @click="clearFile">×</view>
          </view>
          <view v-else class="file-preview-card">
              <view class="file-icon">📄</view>
              <text class="file-name text-ellipsis">{{ tempFile.name }}</text>
              <view class="close-btn-file" @click="clearFile">×</view>
          </view>
      </view>

      <view class="input-card-ink">
        <textarea 
          class="text-area-ink" 
          :maxlength="-1" 
          v-model="inputValue" 
          :placeholder="isSearchOn ? '已开启联网模式...' : '请输入问题...'" 
          cursor-spacing="20" 
          :show-confirm-bar="false" 
          :auto-height="true" 
          @confirm="sendMessage" 
        ></textarea>

        <view class="action-bar">
          <view class="left-actions">
                      <!-- 深度思考按钮 -->
                      <view 
                          class="icon-btn-ink" 
                          :class="{ 'active': isDeepThinking }" 
                          @click="toggleDeepThinking" 
                          @longpress="showDeepTooltip"
                      >
                        <image src="/static/深度思考.png" class="btn-icon-img" mode="aspectFit"></image>
                        
                        <!-- 黑色小气泡 -->
                        <view class="tooltip-ink" :class="{ 'show': showDeepTip }">
                            <text>深度思考</text>
                            <view class="tooltip-arrow"></view>
                        </view>
                      </view>
          
                      <!-- 联网搜索按钮 -->
                      <view 
                          class="icon-btn-ink" 
                          :class="{ 'active': isSearchOn }" 
                          @click="toggleSearch" 
                          @longpress="showSearchTooltip"
                      >
                        <image src="/static/网络.png" class="btn-icon-img" mode="aspectFit"></image>
                        
                        <!-- 黑色小气泡 -->
                        <view class="tooltip-ink" :class="{ 'show': showSearchTip }">
                            <text>联网搜索</text>
                            <view class="tooltip-arrow"></view>
                        </view>
                      </view>
                    </view>
          
          <view class="right-actions">
            <view class="icon-btn-ink upload-btn" @click="handleUpload">
              <text class="btn-icon">⊕</text>
            </view>
            <view v-if="!isGenerating" class="send-btn-ink play-style" :class="{ 'disabled': !inputValue.trim() && !tempFile.path }" @click="sendMessage">
              <text class="btn-symbol">↑</text>
            </view>
            <view v-else class="send-btn-ink stop-style" @click="stopGeneration">
              <text class="btn-symbol">■</text>
            </view>
          </view>
        </view>
      </view>
    </view>
    
    <!-- 6. 报告弹窗 -->
    <view class="report-mask" v-if="showReportModal" @touchmove.stop.prevent>
          <view class="report-card-acrylic">
              <view class="report-header-ink">
                  <text class="report-title">面试评估书</text>
                  <text class="report-date">{{ new Date().toLocaleDateString() }}</text>
              </view>
              <view class="score-section">
                  <view class="score-circle-ink" :class="getScoreClass(reportData.score)">
                      <text class="score-num">{{ reportData.score }}</text>
                      <text class="score-unit">分</text>
                  </view>
                  <text class="score-comment-ink">{{ reportData.comment }}</text>
              </view>
              <scroll-view scroll-y class="report-body">
                  <view class="feedback-item">
                      <view class="feedback-title good">🌟 表现亮点</view>
                      <view v-for="(item, index) in reportData.strengths" :key="'s'+index" class="feedback-text-ink">• {{ item }}</view>
                      <view v-if="!reportData.strengths.length" class="feedback-text-ink empty">暂无明显亮点</view>
                  </view>
                  <view class="feedback-item">
                      <view class="feedback-title bad">💡 改进建议</view>
                      <view v-for="(item, index) in reportData.suggestions" :key="'w'+index" class="feedback-text-ink">• {{ item }}</view>
                       <view v-if="!reportData.suggestions.length" class="feedback-text-ink empty">暂无建议</view>
                  </view>
              </scroll-view>
              <view class="report-footer">
                <view class="footer-btn-group">
                    <button class="btn-secondary-ink" @click="closeReport">回顾对话</button>
                    <button class="btn-primary-ink" @click="goHome">返回首页</button>
                </view>
              </view>
          </view>
      </view>

  </view>
</template>

<script setup>
import { ref, reactive, computed, nextTick, onMounted, onUnmount } from 'vue';
import { onLoad } from '@dcloudio/uni-app';
import { request, uploadFile } from '@/utils/request.js';
import CodeBlock from '@/components/CodeBlock/CodeBlock.vue'; 
// 🔥 移除 zero-markdown-view, 引入 markdown-it
import MarkdownIt from 'markdown-it';

const BASE_URL = 'http://192.168.1.11:8000'; 

// 🔥 初始化 MarkdownIt
const md = new MarkdownIt({
    html: true,
    breaks: true,
    typographer: true
});

// 🔥 定义 mp-html 的标签样式，使其符合水墨风格
const mpHtmlStyle = {
    p: 'font-size: 30rpx; color: #1A1A1A; line-height: 1.7; margin-bottom: 16rpx; font-family: "PingFang SC", serif;',
    strong: 'font-weight: bold; color: #000;',
    li: 'margin-bottom: 10rpx; color: #333;',
    h1: 'font-size: 36rpx; font-weight: bold; margin: 20rpx 0;',
    h2: 'font-size: 34rpx; font-weight: bold; margin: 16rpx 0;',
    table: 'border-collapse: collapse; width: 100%; margin: 20rpx 0;',
    th: 'background-color: #F0F0F0; border: 1px solid #ddd; padding: 10rpx; font-weight: bold;',
    td: 'border: 1px solid #ddd; padding: 10rpx;'
};

// ... 其他 State 保持不变 ...
const isUserInteracting = ref(false);
const userAvatar = ref('');
const showReportModal = ref(false);
const isInterviewFinished = ref(false); 
const reportData = reactive({ score: 0, comment: '', strengths: [], suggestions: [] });
const statusBarHeight = ref(20);
const isDrawerOpen = ref(false);
const showSettings = ref(false);
const scrollIntoViewId = ref('');
const currentActionIndex = ref(-1); 
const showSearchTip = ref(false);
const showDeepTip = ref(false);
const sessionId = ref('');
const sessionList = ref([]);
const memoryLimit = ref(10);
const messages = ref([{ role: 'assistant', content: '你好，我是你的面试官。我已经阅读了你的简历，我们开始吧。', disableMenu: true }]);
const inputValue = ref('');
const isGenerating = ref(false);
const isAiThinking = ref(false);
const isSearchOn = ref(false);
const isDeepThinking = ref(false);
const tempFile = ref({ path: '', name: '', type: '' });
const isInterviewMode = ref(false);
const interviewInfo = reactive({ topic: '', difficulty: '', currentRound: 0, maxRounds: 10 });
let currentRequestTask = null; 
let renderTimer = null; 
let scrollTimer = null; 

// Computed & Lifecycle
const progressPercentage = computed(() => { if (!interviewInfo.maxRounds) return 0; return (interviewInfo.currentRound / interviewInfo.maxRounds) * 100; });
onLoad((options) => {
  const storedAvatar = uni.getStorageSync('user_avatar');
  if (storedAvatar) {
      userAvatar.value = storedAvatar;
  }
  const sysInfo = uni.getSystemInfoSync();
  if (sysInfo.statusBarHeight) statusBarHeight.value = sysInfo.statusBarHeight;
  if (options.mode === 'interview') {
    isInterviewMode.value = true;
    sessionId.value = options.session_id;
    interviewInfo.topic = options.topic || '技术面试';
    interviewInfo.difficulty = options.difficulty || '进阶';
    interviewInfo.currentRound = 0;
    interviewInfo.maxRounds = 10;
    uni.setStorageSync('chat_session_id', sessionId.value);
    isDeepThinking.value = true;
    setTimeout(() => { inputValue.value = "面试官你好，我已准备好，请开始面试。"; sendMessage(); }, 500);
	const sysInfo = uni.getSystemInfoSync();
	  if (sysInfo.statusBarHeight) statusBarHeight.value = sysInfo.statusBarHeight;
  } else if (options.id) {
    sessionId.value = options.id;
    loadHistory();
  } else {
    initNewSession();
  }
  fetchSessionList();
});

// 🔥🔥🔥 新增：将 markdown 文本转为 HTML 给 mp-html 使用
const renderMarkdownToHtml = (text) => {
    if (!text) return '';
    return md.render(text);
};

// ... 核心逻辑：sendMessage, stopGeneration, parseMessage 等保持不变 ...
const stopGeneration = () => {
    if (currentRequestTask) { if(currentRequestTask.abort) currentRequestTask.abort(); currentRequestTask = null; }
    if (renderTimer) { clearInterval(renderTimer); renderTimer = null; }
    isGenerating.value = false; isAiThinking.value = false;
    const lastMsg = messages.value[messages.value.length - 1];
    if (lastMsg && lastMsg.role === 'assistant') lastMsg.isThinkingStill = false;
};

const sendMessage = async () => {
    closeActionMenu();
    const content = inputValue.value.trim();
    if ((!content && !tempFile.value.path) || isGenerating.value) return;
	isUserInteracting.value = false; 
    const currentFile = { ...tempFile.value };
    messages.value.push({ role: 'user', content: content, image: currentFile.path, file_meta: currentFile.type === 'file' ? { is_pdf: true, name: currentFile.name } : null });
    inputValue.value = ''; clearFile(); isAiThinking.value = true; isGenerating.value = true; scrollToBottom();
    if (!sessionId.value) { try { await createBackendSession(); } catch (e) { isGenerating.value = false; isAiThinking.value = false; return; } }
    const token = uni.getStorageSync('access_token');

    if (currentFile.path) {
            const formData = {
                'session_id': sessionId.value,
                // 如果用户没输入文字，默认为"请分析这张图片"
                'content': content || '请分析这张图片', 
                'use_deep_thinking': String(isDeepThinking.value),
                'use_search': String(isSearchOn.value),
                'memory_limit': String(memoryLimit.value)
            };
            
            currentRequestTask = uni.uploadFile({
                url: `${BASE_URL}/api/chat`,
                filePath: currentFile.path,
                name: 'file',
                formData: formData,
                header: { 'Authorization': `Bearer ${token}` },
                success: (uploadRes) => {
                                isAiThinking.value = false;
                                
                                if (uploadRes.statusCode >= 200 && uploadRes.statusCode < 300) {
                                    let aiReply = "";
                                    let msgId = null;
                                    let thinkContent = ""; // 🔥 新增：用于存思考内容
                
                                    try {
                                        // 1. 解析后端数据
                                        // 兼容 SSE 格式和普通 JSON
                                        const rawData = uploadRes.data;
                                        if (rawData.trim().startsWith("data:")) {
                                            // 简单的 SSE 提取逻辑
                                            const lines = rawData.split("\n");
                                            for (let line of lines) {
                                                if (line.startsWith("data:") && line !== 'data: [DONE]') {
                                                    try {
                                                        const json = JSON.parse(line.substring(5));
                                                        if (json.text) aiReply += json.text;
                                                        if (json.type === 'meta_ai') msgId = json.id;
                                                    } catch(e){}
                                                }
                                            }
                                        } else {
                                            // 普通 JSON 提取
                                            const resData = JSON.parse(rawData);
                                            aiReply = resData.data?.answer || resData.answer || resData.content || resData.text || JSON.stringify(resData);
                                            msgId = resData.data?.id || resData.id || null;
                                        }
                
                                        // 🔥🔥🔥 核心修复：手动提取 <think> 标签内容 🔥🔥🔥
                                        // 正则匹配 <think>...</think>，包括换行符
                                        const thinkMatch = aiReply.match(/<think>([\s\S]*?)<\/think>/);
                                        
                                        if (thinkMatch) {
                                            thinkContent = thinkMatch[1]; // 提取思考内容
                                            // 从正文中移除思考标签和内容，剩下的才是回答
                                            aiReply = aiReply.replace(thinkMatch[0], "").trim();
                                        }
                
                                    } catch (e) {
                                        console.warn('解析失败，回退显示原始数据');
                                        aiReply = uploadRes.data;
                                    }
                
                                    // 3. 消息上屏 (带思考内容)
                                    messages.value.push({ 
                                        role: 'assistant', 
                                        content: aiReply, 
                                        // 🔥 注入思考数据
                                        thinkingContent: thinkContent, 
                                        isThinkingOpen: !!thinkContent, // 如果有思考内容，默认展开
                                        isThinkingStill: false,         // 上传模式是一次性返回，不是流式，所以思考已结束
                                        id: msgId 
                                    });
                
                                } else {
                                    messages.value.push({ role: 'assistant', content: `❌ 上传失败 ${uploadRes.statusCode}` });
                                }
                            },
							
                fail: (err) => { 
                    console.error(err);
                    messages.value.push({ role: 'assistant', content: '❌ 网络请求失败' }); 
                },
                complete: () => {
                    isGenerating.value = false; 
                    isAiThinking.value = false; 
                    currentRequestTask = null; 
                    scrollToBottom();
                }
            });
            return;
        }
    // #ifdef APP-PLUS
    const startTime = Date.now();
    let aiMsgIndex = -1; let lastTextLength = 0; let sseAccumulator = ""; let thinkingBuffer = ""; let textBuffer = ""; let streamBuffer = ""; let isThinkingState = false; let isStreamEnded = false;   
    const ensureAiBubble = () => {
        if (aiMsgIndex === -1) {
            isAiThinking.value = false;
            messages.value.push({ role: 'assistant', content: '', thinkingContent: '', isThinkingOpen: true, isThinkingStill: false, startTime: startTime });
            aiMsgIndex = messages.value.length - 1; scrollToBottom();
        }
    };
    renderTimer = setInterval(() => {
        if (thinkingBuffer.length > 0) {
            ensureAiBubble(); const targetMsg = messages.value[aiMsgIndex]; if (!targetMsg.isThinkingStill) targetMsg.isThinkingStill = true;
            let step = 2; if (thinkingBuffer.length > 50) step = 3; if (thinkingBuffer.length > 100) step = 5;
            const chunk = thinkingBuffer.slice(0, step); thinkingBuffer = thinkingBuffer.slice(step);
            if (!targetMsg.thinkingContent) targetMsg.thinkingContent = ""; targetMsg.thinkingContent += chunk;
        } else if (textBuffer.length > 0) {
            ensureAiBubble(); const targetMsg = messages.value[aiMsgIndex]; if (targetMsg.isThinkingStill) targetMsg.isThinkingStill = false;
            let step = 2; if (textBuffer.length > 50) step = 3; if (textBuffer.length > 200) step = 8;
            const chunk = textBuffer.slice(0, step); textBuffer = textBuffer.slice(step); targetMsg.content += chunk; scrollToBottom(); 
        } else if (isStreamEnded && !isThinkingState && sseAccumulator === "") {
            clearInterval(renderTimer); renderTimer = null; isGenerating.value = false;
            if (aiMsgIndex !== -1) messages.value[aiMsgIndex].isThinkingStill = false; scrollToBottom();
        }
    }, 16);
    const xhr = new plus.net.XMLHttpRequest(); currentRequestTask = xhr;
    xhr.open("POST", `${BASE_URL}/api/chat`);
    xhr.setRequestHeader('Authorization', `Bearer ${token}`);
    xhr.setRequestHeader('Content-Type', 'application/x-www-form-urlencoded');
    const bodyParams = [`session_id=${encodeURIComponent(sessionId.value)}`, `content=${encodeURIComponent(content || ' ')}`, `use_deep_thinking=${isDeepThinking.value}`, `use_search=${isSearchOn.value}`, `memory_limit=${memoryLimit.value}`].join('&');
    xhr.onreadystatechange = () => {
        if (xhr.readyState === 3 || xhr.readyState === 4) { const currentResponse = xhr.responseText || ""; if (currentResponse.length > lastTextLength) { const newChunk = currentResponse.substring(lastTextLength); lastTextLength = currentResponse.length; processChunk(newChunk); } }
        if (xhr.readyState === 4) {
            isStreamEnded = true; if (xhr.status !== 200 && aiMsgIndex === -1) { isAiThinking.value = false; messages.value.push({ role: 'assistant', content: `❌ Error: ${xhr.status}` }); }
            if (aiMsgIndex !== -1) { const duration = ((Date.now() - startTime) / 1000).toFixed(2); messages.value[aiMsgIndex].costTime = duration; }
            if (isInterviewMode.value && xhr.status === 200) { if (interviewInfo.currentRound >= interviewInfo.maxRounds) { setTimeout(() => { handleEndInterview(true); }, 1500); } else { interviewInfo.currentRound += 1; } }
            if (xhr.status === 401) { stopGeneration(); uni.removeStorageSync('access_token'); setTimeout(() => uni.reLaunch({ url: '/pages/login/login' }), 1500); }
        }
    };
    xhr.send(bodyParams);
    // ----------------------------------------------------
        // 🧩 SSE 数据解析机 (防断裂增强版)
        // ----------------------------------------------------
// ----------------------------------------------------
    // 🧩 SSE 数据解析机 (带 Debug 和 防断裂)
    // ----------------------------------------------------
    function processChunk(chunkText) {
        ensureAiBubble();
        sseAccumulator += chunkText;

        while (true) {
            const newlineIndex = sseAccumulator.indexOf('\n');
            if (newlineIndex === -1) break;

            const line = sseAccumulator.slice(0, newlineIndex).trim();
            sseAccumulator = sseAccumulator.slice(newlineIndex + 1);

            if (!line || !line.startsWith('data: ')) continue;
            const jsonStr = line.replace('data: ', '').trim();
            if (jsonStr === '[DONE]') continue;

            try {
                const data = JSON.parse(jsonStr);
                if (data.type === 'meta_ai') messages.value[aiMsgIndex].id = data.id;

                let newText = data.text || "";
                if (newText) {
                    // console.log("收到流数据:", newText); // 打开这个可以看到后端发了什么
                    streamBuffer += newText;

                    while (true) {
                        if (!isThinkingState) {
                            // --- 检查是否开始思考 <think> ---
                            const startTag = "<think>";
                            const startTagIndex = streamBuffer.indexOf(startTag);

                            if (startTagIndex !== -1) {
                                // 1. 发现开始标签
                                const contentPart = streamBuffer.slice(0, startTagIndex);
                                textBuffer += contentPart;
                                streamBuffer = streamBuffer.slice(startTagIndex + startTag.length);
                                isThinkingState = true; 
                                
                                // 🔥🔥🔥 UI: 立即强制开启思考框 🔥🔥🔥
                                const targetMsg = messages.value[aiMsgIndex];
                                targetMsg.isThinkingStill = true; // 标记正在思考
                                targetMsg.isThinkingOpen = true;  // 默认展开
                                if (!targetMsg.thinkingContent) targetMsg.thinkingContent = ""; // 初始化为空字符串，防止 undefined
                                
                            } else {
                                // 2. 防切断检测
                                const lastLtIndex = streamBuffer.lastIndexOf('<');
                                if (lastLtIndex !== -1 && (streamBuffer.length - lastLtIndex) < startTag.length) {
                                    textBuffer += streamBuffer.slice(0, lastLtIndex);
                                    streamBuffer = streamBuffer.slice(lastLtIndex);
                                } else {
                                    textBuffer += streamBuffer;
                                    streamBuffer = "";
                                }
                                break; 
                            }
                        } else {
                            // --- 检查是否结束思考 </think> ---
                            const endTag = "</think>";
                            const endTagIndex = streamBuffer.indexOf(endTag);

                            if (endTagIndex !== -1) {
                                // 1. 发现结束标签
                                const thinkingPart = streamBuffer.slice(0, endTagIndex);
                                thinkingBuffer += thinkingPart;
                                streamBuffer = streamBuffer.slice(endTagIndex + endTag.length);
                                isThinkingState = false;
                                
                                // UI: 思考结束
                                const targetMsg = messages.value[aiMsgIndex];
                                targetMsg.isThinkingStill = false; 
                                setTimeout(() => { targetMsg.isThinkingOpen = false; }, 500); // 延迟收起
                                
                            } else {
                                // 2. 防切断检测
                                const lastLtIndex = streamBuffer.lastIndexOf('<');
                                if (lastLtIndex !== -1 && (streamBuffer.length - lastLtIndex) < endTag.length) {
                                    thinkingBuffer += streamBuffer.slice(0, lastLtIndex);
                                    streamBuffer = streamBuffer.slice(lastLtIndex);
                                } else {
                                    thinkingBuffer += streamBuffer;
                                    streamBuffer = "";
                                }
                                break; 
                            }
                        }
                    }
                }
            } catch (e) {
                // ignore
            }
        }
    }
    // #endif
};

// ... 辅助函数 ...
const scrollToBottom = () => { if (scrollTimer) return; if (isUserInteracting.value) return; scrollTimer = setTimeout(() => { nextTick(() => { if (messages.value.length > 0 || isAiThinking.value) { scrollIntoViewId.value = isAiThinking.value ? 'msg-loading' : 'msg-' + (messages.value.length - 1); } }); scrollTimer = null; }, 100); };
const onUserTouch = () => {
    isUserInteracting.value = true;
};
const triggerVibrate = () => { /* #ifdef APP-PLUS */ uni.vibrateShort(); /* #endif */ };
const parseMessage = (content) => {
  if (!content) return [];
  const cleanContent = content.replace(/<think>[\s\S]*?<\/think>/g, '').trim();
  const regex = /```(\w*)\n?([\s\S]*?)(```|$)/g;
  const result = []; let lastIndex = 0; let match;
  while ((match = regex.exec(cleanContent)) !== null) {
    if (match.index > lastIndex) { const text = cleanContent.slice(lastIndex, match.index); if (text.trim()) result.push({ type: 'text', content: text }); }
    const lang = match[1] || 'text'; const code = match[2]; result.push({ type: 'code', lang: lang, content: code.replace(/\n$/, '') }); lastIndex = regex.lastIndex;
  }
  if (lastIndex < cleanContent.length) { const text = cleanContent.slice(lastIndex); if (text.trim()) result.push({ type: 'text', content: text }); }
  return result;
};

// ... UI 交互 ...
const toggleThinking = (index) => { messages.value[index].isThinkingOpen = !messages.value[index].isThinkingOpen; };
const toggleMenu = (index) => { if (isGenerating.value || messages.value[index].disableMenu) return; if (currentActionIndex.value === index) currentActionIndex.value = -1; else { currentActionIndex.value = index; triggerVibrate(); } };
const closeActionMenu = () => { if (currentActionIndex.value !== -1) currentActionIndex.value = -1; };
const handleCopy = (content) => { uni.setClipboardData({ data: content, success: () => { uni.showToast({ title: '已复制', icon: 'none' }); currentActionIndex.value = -1; } }); };
const handleDelete = (index) => { uni.showModal({ title: '删除记忆', content: '确定要删除这条消息吗？', success: async (res) => { if (res.confirm) { const msg = messages.value[index]; const deleteFromId = msg.id; messages.value.splice(index, 1); if (isInterviewMode.value && msg.role === 'assistant' && interviewInfo.currentRound > 0) interviewInfo.currentRound -= 1; currentActionIndex.value = -1; if (deleteFromId && sessionId.value) await request({ url: '/chat/message/delete', method: 'POST', data: { session_id: sessionId.value, message_id: deleteFromId, delete_after: false } }); } } }); };
const handleRightBtnClick = () => { if (isGenerating.value) return; if (isInterviewFinished.value) showReportModal.value = true; else handleEndInterview(false); };
// 重新生成 (修复版：支持图片/文件回填)
// 重新生成 (修复版：避免图片重复显示)
const handleRegenerate = async (index) => {
    currentActionIndex.value = -1; // 关闭菜单
    
    const targetMsg = messages.value[index];
    
    // 临时变量
    let contentToResend = "";
    let imageToResend = "";
    let fileMetaToResend = null;
    let deleteFromId = targetMsg.id; 
    
    // 场景 1：重试 AI 的回答 (需要获取上一条 User 的消息)
    if (targetMsg.role === 'assistant') {
        if (index === 0) return; 
        
        const prevUserMsg = messages.value[index - 1];
        if (prevUserMsg && prevUserMsg.role === 'user') {
            contentToResend = prevUserMsg.content || "";
            imageToResend = prevUserMsg.image || "";
            fileMetaToResend = prevUserMsg.file_meta || null;
            
            // 🔥🔥🔥 核心修复：连同上一条用户消息一起删除 (删除2条) 🔥🔥🔥
            // 这样 sendMessage 再添加新消息时，就不会出现重复了
            messages.value.splice(index - 1, 2);
        }
    } 
    // 场景 2：重试 User 的消息 (直接获取当前消息内容)
    else {
        contentToResend = targetMsg.content || "";
        imageToResend = targetMsg.image || "";
        fileMetaToResend = targetMsg.file_meta || null;
        
        // UI: 删除这条及之后所有
        messages.value.splice(index, messages.value.length - index);
    }

    // 后端同步删除记忆 (保持不变)
    if (deleteFromId && sessionId.value) {
        try {
            await request({
                url: '/chat/message/delete',
                method: 'POST',
                data: {
                    session_id: sessionId.value,
                    message_id: deleteFromId,
                    delete_after: true 
                }
            });
        } catch(e) { console.error('重生成清理记忆失败', e); }
    }

    // 恢复输入框和文件状态
    inputValue.value = contentToResend;

    if (imageToResend) {
        tempFile.value = {
            path: imageToResend,
            type: (fileMetaToResend && fileMetaToResend.is_pdf) ? 'file' : 'image',
            name: (fileMetaToResend && fileMetaToResend.name) ? fileMetaToResend.name : 'image.jpg'
        };
    } else {
        clearFile();
    }
    
    // 触发发送
    nextTick(() => {
        sendMessage(); 
    });
};
const handleEndInterview = (isAuto = false) => { const triggerReport = async () => { if (!isAuto) { messages.value.push({ role: 'user', content: '我回答完毕了，请生成评估报告。' }); scrollToBottom(); } uni.showLoading({ title: 'AI 正在阅卷...', mask: true }); try { const userId = uni.getStorageSync('user_id'); const res = await request({ url: '/report/generate', method: 'POST', data: { user_id: userId || 1, session_id: sessionId.value, question_id: null, chat_history: messages.value.map(m => ({ role: m.role === 'assistant' ? 'model' : 'user', content: m.content })) } }); const report = res.data || res; if (report && (report.score !== undefined)) { reportData.score = report.score; reportData.comment = report.comment; reportData.strengths = report.strengths || []; reportData.suggestions = report.suggestions || []; isInterviewFinished.value = true; showReportModal.value = true; } } catch (e) { console.error('报告生成失败', e); } finally { uni.hideLoading(); } }; if (isAuto) { uni.showToast({ title: '面试结束，生成报告中...', icon: 'none' }); triggerReport(); } else { uni.showModal({ title: '结束面试', content: '确定要交卷吗？', success: (res) => { if (res.confirm) triggerReport(); } }); } };
const goHome = () => { uni.reLaunch({ url: '/pages/index/index' }); };
const closeReport = () => { showReportModal.value = false; };
const clearFile = () => { tempFile.value = { path: '', name: '', type: '' }; };
const previewImage = (url) => { if (url) uni.previewImage({ urls: [url], current: 0 }); };
const openDocument = (url) => { if (!url) return; uni.showLoading({ title: '打开中...' }); uni.downloadFile({ url: url, success: function (res) { uni.openDocument({ filePath: res.tempFilePath, showMenu: true, complete: () => uni.hideLoading() }); }, fail: () => { uni.hideLoading(); uni.showToast({ title: '文件下载失败', icon: 'none' }); } }); };

// 🔥 核心修改：App 原生文件选择器
const handleUpload = () => {
    currentActionIndex.value = -1;
    uni.showActionSheet({
        itemList: ['相册/拍照', '选择文档'],
        success: async (res) => {
            if (res.tapIndex === 0) {
                uni.chooseImage({ count: 1, sizeType: ['compressed'], success: (imgRes) => { tempFile.value = { path: imgRes.tempFilePaths[0], name: '图片.jpg', type: 'image' }; } });
            } else {
                // #ifdef MP-WEIXIN
                wx.chooseMessageFile({ count: 1, type: 'file', extension: ['pdf'], success: (fileRes) => { const file = fileRes.tempFiles[0]; tempFile.value = { path: file.path, name: file.name, type: 'file' }; } });
                // #endif
                // #ifdef H5
                uni.chooseFile({ count: 1, type: 'all', extension: ['.pdf','.md','.txt','.word','.xlsx'], success: (fileRes) => { const file = fileRes.tempFiles[0]; tempFile.value = { path: file.path, name: file.name, type: 'file' }; } });
                // #endif
                // #ifdef APP-PLUS
                try {
                    const fileRes = await chooseFileApp();
                    tempFile.value = { path: fileRes.path, name: fileRes.name, type: 'file' };
                } catch (err) { if(err !== 'cancel') uni.showToast({ title: '无法选择文件', icon: 'none' }); }
                // #endif
            }
        }
    });
};
const chooseFileApp = () => {
    return new Promise((resolve, reject) => {
        if (uni.getSystemInfoSync().platform === 'android') {
            const Intent = plus.android.importClass("android.content.Intent");
            const main = plus.android.runtimeMainActivity();
            const intent = new Intent(Intent.ACTION_GET_CONTENT);
            intent.setType("*/*"); intent.addCategory(Intent.CATEGORY_OPENABLE);
            const CODE_REQUEST = 404;
            main.startActivityForResult(intent, CODE_REQUEST);
            main.onActivityResult = function(requestCode, resultCode, data) {
                if (requestCode === CODE_REQUEST) {
                    if (resultCode === -1 && data) {
                        const uri = data.getData(); plus.android.importClass(uri);
                        let fileName = "未命名文件";
                        try {
                            const ContentResolver = main.getContentResolver(); const Cursor = plus.android.importClass("android.database.Cursor"); const OpenableColumns = plus.android.importClass("android.provider.OpenableColumns");
                            const cursor = ContentResolver.query(uri, null, null, null, null);
                            if (cursor != null && cursor.moveToFirst()) { const nameIndex = cursor.getColumnIndex(OpenableColumns.DISPLAY_NAME); fileName = cursor.getString(nameIndex); cursor.close(); }
                        } catch(e) {}
                        resolve({ path: uri.toString(), name: fileName });
                    } else { reject('cancel'); }
                }
            };
        } else {
            const UIDocumentPickerViewController = plus.ios.importClass("UIDocumentPickerViewController"); const NSArray = plus.ios.importClass("NSArray");
            const types = NSArray.arrayWithObjects("com.adobe.pdf", "public.plain-text", "org.openxmlformats.wordprocessingml.document");
            const documentPicker = parseInt(plus.device.systemVersion) >= 8.0 ? new UIDocumentPickerViewController().initWithDocumentTypesInMode(types, 0) : new UIDocumentPickerViewController().initWithDocumentTypesInMode(types, 0);
            const delegate = plus.ios.implements("UIDocumentPickerDelegate", { "documentPicker:didPickDocumentAtURL:": function(picker, url) { const path = url.path(); const name = url.lastPathComponent(); resolve({ path: "file://" + path, name: name }); }, "documentPickerWasCancelled:": function(picker) { reject('cancel'); } });
            documentPicker.setDelegate(delegate);
            const currentVC = plus.ios.runtimeUIApplication().keyWindow().rootViewController(); currentVC.presentViewControllerAnimatedCompletion(documentPicker, true, null);
        }
    });
};

const fetchSessionList = async () => { try { const res = await request({ url: '/sessions/list' }); sessionList.value = res.data; } catch (e) {} };
const switchSession = (id) => { if (sessionId.value === id) { closeDrawer(); return; } sessionId.value = id; messages.value = []; loadHistory(); closeDrawer(); uni.setStorageSync('chat_session_id', sessionId.value); };
const loadHistory = async () => {
    uni.showLoading({ title: '同步记忆...' });
    try {
        const res = await request({ url: '/chat/history', data: { session_id: sessionId.value } });
        if (res.data) { messages.value = res.data; scrollToBottom(); }
        if (res.interview_meta) {
            isInterviewMode.value = true;
            interviewInfo.topic = res.interview_meta.topic; interviewInfo.difficulty = res.interview_meta.difficulty; interviewInfo.currentRound = res.interview_meta.current_round; interviewInfo.maxRounds = res.interview_meta.max_rounds;
            if (res.interview_meta.status === 'completed') { isInterviewFinished.value = true; if (res.report_data) { reportData.score = res.report_data.score; reportData.comment = res.report_data.comment; reportData.strengths = res.report_data.strengths; reportData.suggestions = res.report_data.suggestions; } } else { isInterviewFinished.value = false; }
        }
    } catch (e) { console.error("加载失败", e); } finally { uni.hideLoading(); }
};
const createBackendSession = async () => { const title = '面试 ' + new Date().toLocaleTimeString('zh-CN', {hour: '2-digit', minute:'2-digit'}); const res = await request({ url: '/sessions/create', method: 'POST', data: { title: title } }); sessionId.value = res.data.session_id; uni.setStorageSync('chat_session_id', sessionId.value); fetchSessionList(); return sessionId.value; };
const initNewSession = async () => {
    closeDrawer();
    if (isInterviewMode.value) {
        uni.showLoading({ title: '重置面试环境...' });
        try { const res = await request({ url: '/chat/interview/start', method: 'POST', data: { topic: interviewInfo.topic, difficulty: interviewInfo.difficulty } }); if (res.code === 200) { sessionId.value = res.data.session_id; uni.setStorageSync('chat_session_id', sessionId.value); interviewInfo.currentRound = 0; messages.value = []; setTimeout(() => { inputValue.value = "面试官你好，上一轮已结束。我准备好开始新的一轮面试了，请出题。"; sendMessage(); }, 500); } } catch (e) { uni.showToast({ title: '重置失败', icon: 'none' }); } finally { uni.hideLoading(); }
    } else { sessionId.value = ''; uni.removeStorageSync('chat_session_id'); isInterviewMode.value = false; interviewInfo.currentRound = 0; messages.value = [{ role: 'assistant', content: '你好，我是你的面试官。我们可以开始新的自由对话了。', disableMenu: true }]; }
    fetchSessionList();
};
const getScoreClass = (score) => { if (score >= 85) return 'score-gold'; if (score >= 60) return 'score-blue'; return 'score-red'; };
const showSearchTooltip = () => { 
    showSearchTip.value = true; 
    // 自动隐藏逻辑：0.5秒后消失
    setTimeout(() => { showSearchTip.value = false; }, 500);
}; const hideSearchTooltip = () => { setTimeout(() => { showSearchTip.value = false; }, 200); };
const showDeepTooltip = () => { 
    showDeepTip.value = true; 
    // 自动隐藏逻辑：0.5秒后消失
    setTimeout(() => { showDeepTip.value = false; }, 500);
}; const hideDeepTooltip = () => { setTimeout(() => { showDeepTip.value = false; }, 200); };
const openDrawer = () => { isDrawerOpen.value = true; fetchSessionList(); }; const closeDrawer = () => { isDrawerOpen.value = false; };
const toggleSettings = () => { showSettings.value = !showSettings.value; }; const onLimitChange = (e) => { memoryLimit.value = e.detail.value; };
const toggleSearch = () => { isSearchOn.value = !isSearchOn.value; triggerVibrate(); }; const toggleDeepThinking = () => { isDeepThinking.value = !isDeepThinking.value; triggerVibrate(); };
</script>

<style lang="scss" scoped>
/* =========================================================
   全局基础
   ========================================================= */
:global(page) {
    background-color: #F7F7F2;
    font-family: 'PingFang SC', 'Noto Serif SC', serif;
    height: 100%;
    overflow: hidden;
}

.chat-container {
    display: flex; flex-direction: column; height: 100vh; overflow: hidden; position: relative;
}

/* 背景纹理 */
.paper-bg {
    position: fixed; top: 0; left: 0; width: 100%; height: 100%; z-index: -1;
    background: radial-gradient(circle at 50% 30%, #FDFDFB 0%, #F2F2EB 100%);
    pointer-events: none;
}
.grain-overlay {
    position: absolute; top: 0; left: 0; width: 100%; height: 100%; opacity: 0.3;
    background-image: url("data:image/svg+xml,%3Csvg viewBox='0 0 200 200' xmlns='http://www.w3.org/2000/svg'%3E%3Cfilter id='noiseFilter'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.85' numOctaves='3' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23noiseFilter)' opacity='0.15'/%3E%3C/svg%3E");
}

/* =========================================================
   1. 导航与侧边栏 (保持亚克力风格)
   ========================================================= */
.custom-nav-glass {
    background: rgba(255, 255, 255, 0.65);
    backdrop-filter: blur(20px);
    border-bottom: 1px solid rgba(0,0,0,0.03);
    z-index: 100; flex-shrink: 0;
}
.nav-content {
    height: 88rpx; display: flex; align-items: center; justify-content: space-between; padding: 0 30rpx;
}
.menu-btn { width: 60rpx; height: 60rpx; display: flex; align-items: center; justify-content: flex-start; }
.menu-icon-ink { font-size: 42rpx; color: #1A1A1A; }
.nav-title-ink { font-size: 34rpx; font-weight: 600; color: #1A1A1A; letter-spacing: 2rpx; }
.menu-placeholder { width: 60rpx; } 
// 用户图片样式
.avatar-user-img {
    width: 100%; 
    height: 100%; 
    border-radius: 50%;
    /* 稍微加一点填充，避免图片贴边太紧，或者你可以去掉 padding */
    display: block;
}
/* 侧边栏 */
.drawer-mask { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.3); z-index: 888; opacity: 0; visibility: hidden; transition: all 0.3s; }
.drawer-mask.show { opacity: 1; visibility: visible; }
.drawer-paper {
    position: fixed; top: 0; left: 0; bottom: 0; width: 80%; max-width: 600rpx;
    background: #F9F9F5; z-index: 999; transform: translateX(-100%);
    transition: transform 0.3s cubic-bezier(0.25, 0.8, 0.25, 1);
    display: flex; flex-direction: column;
    box-shadow: 10rpx 0 40rpx rgba(0,0,0,0.08);
}
.drawer-paper.open { transform: translateX(0); }
.drawer-header { padding: 40rpx 30rpx 20rpx; display: flex; align-items: center; }
.nav-back-btn { width: 60rpx; height: 60rpx; display: flex; align-items: center; }
.back-arrow-ink { font-size: 44rpx; color: #333; }
.drawer-title-ink { font-size: 36rpx; font-weight: bold; color: #1A1A1A; letter-spacing: 2rpx; margin-left: 10rpx; }
.drawer-list { flex: 1; height: 0; padding: 20rpx; box-sizing: border-box; }
.drawer-item-ink {
    display: flex; align-items: center; padding: 28rpx 30rpx; margin-bottom: 12rpx;
    border-radius: 16rpx; color: #555; transition: all 0.2s;
    &.active { background: rgba(0,0,0,0.04); color: #000; font-weight: 600; }
    &:active { transform: scale(0.99); }
}
.msg-img {
    /* 🔥 关键修改：强制限制最大宽高 */
    width: 280rpx;         /* 宽度限制 */
    height: 280rpx;        /* 高度限制，防止长图霸屏 */
    
    display: block;
    
    /* 给图片加一个微弱的白边，防止在黑色气泡里边界不清 */
    border: 1px solid rgba(255,255,255,0.1); 
    
    /* 保持 object-fit 效果 (uni-app 中由 mode="aspectFill" 控制) */
}
.msg-img-box {
    position: relative;
    display: inline-block; /* 防止占满整行 */
    margin-bottom: 8rpx;   /* 图片和下方文字的间距 */
    overflow: hidden;      /* 配合圆角 */
    border-radius: 12rpx;  /* 图片圆角 */
}
.item-icon { margin-right: 20rpx; font-size: 32rpx; opacity: 0.8; }
.item-text { font-size: 28rpx; font-family: serif; }
.drawer-footer { padding: 30rpx; }
.footer-btn-ink {
    background: #1A1A1A; color: #fff; padding: 24rpx; border-radius: 16rpx;
    display: flex; align-items: center; justify-content: center;
    font-weight: 500; letter-spacing: 2rpx;
    box-shadow: 0 8rpx 20rpx rgba(0,0,0,0.15);
}

/* =========================================================
   2. 聊天区域核心样式 (气泡 & 思考框)
   ========================================================= */
.chat-scroll-view { flex: 1; height: 0; width: 100%; box-sizing: border-box; padding: 30rpx; }
.message-group { margin-bottom: 40rpx; }

/* 布局：头像与气泡 */
.message-item { display: flex; align-items: flex-start; width: 100%; }
.ai-side { flex-direction: row; }
.user-side { flex-direction: row; justify-content: flex-end; }

/* 头像容器 */
.avatar-container {
    width: 80rpx; height: 80rpx; border-radius: 50%;
    flex-shrink: 0; display: flex; align-items: center; justify-content: center;
    
    &.ai { margin-right: 20rpx; margin-top: 6rpx; }
    &.user { 
        margin-left: 20rpx; margin-top: 6rpx;
        background: #1A1A1A; border: 2rpx solid #333;
        box-shadow: 0 4rpx 10rpx rgba(0,0,0,0.1);
    }
}
.avatar-logo-ink {
    width: 100%; height: 100%;
    mix-blend-mode: multiply; /* 正片叠底 */
    filter: contrast(1.1) brightness(0.95);
}
.user-avatar-text { color: #fff; font-size: 26rpx; font-weight: bold; }

/* 💡 气泡通用 */
.bubble {
    max-width: 72%; position: relative; word-break: break-all;
    font-size: 30rpx; line-height: 1.75;
    transition: filter 0.2s;
}

/* --- AI 气泡：宣纸信笺风 --- */
.ai-paper-bubble {
    background: #FFFEFA; /* 极淡米白 */
    color: #2B2B2B;      /* 深墨灰字 */
    padding: 24rpx 32rpx;
    
    /* 边框与圆角：模拟纸张 */
    border: 1px solid rgba(0,0,0,0.06);
    border-radius: 4rpx 24rpx 24rpx 24rpx; /* 左上角尖锐，指向头像 */
    
    /* 纸张阴影 */
    box-shadow: 2rpx 4rpx 12rpx rgba(0,0,0,0.04);
}

/* --- User 气泡：黑晶风 --- */
.user-ink-bubble {
    background: #1A1A1A; /* 浓墨黑 */
    color: #F7F7F7;      /* 宣纸白字 */
    padding: 22rpx 30rpx;
    
    border-radius: 24rpx 4rpx 24rpx 24rpx; /* 右上角尖锐 */
    box-shadow: 0 6rpx 16rpx rgba(0,0,0,0.1);
}
.user-text { color: inherit; }

/* 🔥🔥🔥 思考框 (Deep Thinking) - 引用笔记风 🔥🔥🔥 */
.thinking-accordion {
    margin-bottom: 20rpx;
    /* 背景改为极淡的暖黄色/米色，模拟旧纸 */
    background: rgba(245, 245, 235, 0.6); 
    border-radius: 12rpx;
    /* 边框极淡，或者用 dashed 模拟虚线 */
    border: 1px dashed rgba(0,0,0,0.1); 
    overflow: hidden;
    transition: all 0.3s ease;
    /* 左侧加一道稍微深一点的装饰线，像书签 */
    border-left: 6rpx solid rgba(0,0,0,0.15); 
}


.thinking-header {
    display: flex; 
    align-items: center; 
    padding: 16rpx 24rpx;
    /* 头部稍微深一点 */
    background: rgba(0,0,0,0.02); 
    font-size: 24rpx; 
    color: #888; /* 浅墨色 */
    cursor: pointer;
}

.thinking-title {
    font-size: 24rpx; 
    font-weight: 500; 
    letter-spacing: 2rpx;
    font-family: serif; /* 衬线体，更有书卷气 */
    color: #666;
}

/* 思考内容区 */
.thinking-body {
    padding: 24rpx 32rpx;
    font-size: 26rpx;
    /* 字体颜色稍微浅一点，与正文区分 */
    color: #555; 
    line-height: 1.8;
    background: transparent;
    border-top: 1px dashed rgba(0,0,0,0.05);
    white-space: pre-wrap;
    
    /* 关键：斜体 + 衬线，模拟手写批注感 */
    font-family: 'Kaiti', 'STKaiti', serif; 
    font-style: italic; 
    opacity: 0.9;
}

/* 思考加载动画 */
.header-text-area { flex: 1; display: flex; align-items: center; margin-left: 12rpx; }
.header-spinner {
    width: 24rpx; height: 24rpx; 
    border: 3rpx solid #BBB;
    border-top-color: transparent; 
    border-radius: 50%;
    margin-left: 16rpx; 
    animation: spin 1s linear infinite;
}
.thinking-icon { 
    font-size: 28rpx; 
    opacity: 0.6; 
}
.thinking-arrow { 
    font-size: 20rpx; 
    color: #999; 
    margin-left: auto; 
    transition: transform 0.3s;
}

/* Markdown 容器 */
.markdown-wrapper {
    display: flex; flex-direction: column; gap: 16rpx;
    min-width: 80rpx;
}
.code-block-wrapper { margin: 10rpx 0; border-radius: 12rpx; overflow: hidden; }

/* 底部耗时 */
.msg-footer {
    display: flex; justify-content: flex-end;
    margin-top: 8rpx; font-size: 20rpx; color: #CCC; font-family: sans-serif;
}

/* 气泡操作菜单图标 */
.bubble-menu-icon {
    position: absolute; bottom: 6rpx; right: 10rpx;
    font-size: 28rpx; color: rgba(0,0,0,0.15); padding: 10rpx; z-index: 10;
}
.user-ink-bubble .bubble-menu-icon { color: rgba(255,255,255,0.2); }

/* 操作菜单 */
.msg-menu {
    overflow: hidden; max-height: 0; opacity: 0; transition: all 0.3s ease; width: 100%; display: flex;
    &.show { max-height: 100rpx; opacity: 1; margin-top: 10rpx; }
}
.menu-right { justify-content: flex-end; padding-right: 100rpx; }
.menu-left { justify-content: flex-start; padding-left: 100rpx; }
.menu-inner-ink {
    background: #333; border-radius: 12rpx; padding: 12rpx 24rpx;
    display: flex; align-items: center; gap: 30rpx;
    box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.15);
}
.menu-item { display: flex; align-items: center; font-size: 24rpx; color: #fff; }
.menu-icon { margin-right: 8rpx; }
.menu-item.delete { color: #FF6B6B; }

/* Loading 气泡 */
.loading-bubble-ink {
    background: #FFFEFA; border: 1px solid rgba(0,0,0,0.06);
    padding: 24rpx 36rpx; border-radius: 4rpx 24rpx 24rpx 24rpx;
    display: flex; align-items: center; gap: 8rpx;
}
.dot-ink {
    width: 10rpx; height: 10rpx; background: #999; border-radius: 50%;
    animation: bounce 1.4s infinite ease-in-out both;
}
.dot-ink:nth-child(1) { animation-delay: -0.32s; }
.dot-ink:nth-child(2) { animation-delay: -0.16s; }
@keyframes bounce { 0%, 80%, 100% { transform: scale(0); } 40% { transform: scale(1); } }

/* =========================================================
   3. 底部输入 & 辅助功能
   ========================================================= */
.input-panel-glass {
    position: fixed; bottom: 0; left: 0; width: 100%;
    background: rgba(255, 255, 255, 0.7);
    backdrop-filter: blur(25px);
    padding: 20rpx 30rpx; box-sizing: border-box;
    padding-bottom: calc(20rpx + constant(safe-area-inset-bottom));
    padding-bottom: calc(20rpx + env(safe-area-inset-bottom));
    z-index: 99; border-top: 1px solid rgba(255,255,255,0.4);
}

.input-card-ink {
    background: rgba(255,255,255,0.6);
    border: 1px solid rgba(0,0,0,0.05);
    border-radius: 28rpx; padding: 20rpx;
    display: flex; flex-direction: column; gap: 16rpx;
    box-shadow: 0 4rpx 16rpx rgba(0,0,0,0.02);
}

.text-area-ink {
    width: 100%; max-height: 240rpx; min-height: 48rpx;
    font-size: 30rpx; color: #1A1A1A; line-height: 1.5;
    background: transparent;
}

.action-bar { display: flex; justify-content: space-between; align-items: center; }
.left-actions { 
    display: flex; 
    align-items: center; 
    gap: 20rpx; /* 图标之间稍微拉开一点 */
}
.right-actions { display: flex; align-items: center; gap: 20rpx; }
.icon-btn-ink.active { 
    background: #E0E0E0; 
    transform: scale(0.95);
}
.icon-btn-ink {
    width: 72rpx; 
    height: 72rpx; 
    border-radius: 50%; /* 纯圆 */
    display: flex; 
    align-items: center; 
    justify-content: center; 
    position: relative; /* 为了气泡定位 */
    background: rgba(0,0,0,0.03); 
    transition: all 0.2s;
}
.icon-btn-ink .btn-icon-img { 
    width: 40rpx; 
    height: 40rpx; 
    opacity: 0.5; /* 默认稍微淡一点 */
    transition: opacity 0.2s;
}
.icon-btn-ink.active .btn-icon-img {
    opacity: 1; /* 激活时加深 */
}
.tooltip-ink {
    position: absolute; 
    top: -70rpx;        /* 在按钮上方 */
    left: 50%; 
    transform: translateX(-50%); /* 水平居中 */
    
    background: rgba(26, 26, 26, 0.9); /* 浓墨黑背景 */
    padding: 10rpx 18rpx; 
    border-radius: 12rpx;
    
    opacity: 0; 
    visibility: hidden; 
    transition: all 0.2s; 
    pointer-events: none;
    z-index: 100; /* 确保在最上层 */
    
    /* 🔥🔥🔥 核心修复：强制不换行，解决竖排问题 🔥🔥🔥 */
    white-space: nowrap; 
    width: max-content; /* 宽度根据文字自适应 */
}
.tooltip-ink.show { 
    opacity: 1; 
    visibility: visible; 
    top: -85rpx; /* 稍微往上浮动一点的动画 */
}
.tooltip-ink text { 
    color: #fff; 
    font-size: 22rpx; 
    font-weight: 500;
    letter-spacing: 1rpx;
    display: block; /* 确保是块级元素 */
}

/* 气泡底部小三角 */
.tooltip-arrow { 
    position: absolute; 
    bottom: -8rpx; 
    left: 50%; 
    margin-left: -8rpx; 
    width: 0; 
    height: 0; 
    border-left: 8rpx solid transparent; 
    border-right: 8rpx solid transparent; 
    border-top: 8rpx solid rgba(26, 26, 26, 0.9); 
}
.send-btn-ink {
    width: 80rpx; height: 80rpx; border-radius: 24rpx;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.3s;
    &.play-style { background: #1A1A1A; box-shadow: 0 6rpx 16rpx rgba(0,0,0,0.15); }
    &.stop-style { background: #C62828; animation: pulse 2s infinite; }
    &.disabled { background: #E5E5E5; box-shadow: none; pointer-events: none; }
    .btn-symbol { color: #fff; font-size: 36rpx; font-weight: bold; }
    &:active { transform: scale(0.92); }
}

/* 附件预览 */
.file-preview-area { margin-bottom: 12rpx; padding: 0 8rpx; }
.image-preview-box { position: relative; }
.preview-img { width: 140rpx; height: 140rpx; border-radius: 16rpx; border: 1px solid #EEE; }
.close-btn { position: absolute; top: -12rpx; right: -12rpx; width: 40rpx; height: 40rpx; background: rgba(0,0,0,0.6); color: #fff; border-radius: 50%; font-size: 24rpx; text-align: center; line-height: 40rpx; }

/* =========================================================
   4. 面试进度 & 设置 (悬浮组件)
   ========================================================= */
.interview-bookmark {
    background: rgba(255,255,255,0.85); 
    backdrop-filter: blur(12px);
    padding: 24rpx 30rpx; 
    border-bottom: 1px solid rgba(0,0,0,0.05);
    display: flex; 
    flex-direction: column; /* 改为垂直排列 */
    gap: 16rpx;             /* 上下间距 */
    z-index: 90; 
    height: auto;           /* 高度自适应 */
    box-sizing: border-box;
}
.interview-header-row {
    display: flex;
    align-items: center;
    width: 100%;
    gap: 16rpx;
}
.interview-tag { 
    font-size: 32rpx; 
    font-weight: bold; 
    color: #1A1A1A; 
    flex-shrink: 0; 
}
.interview-level { 
    font-size: 24rpx; 
    background: #F2F2F2; 
    padding: 6rpx 16rpx; 
    border-radius: 8rpx; 
    color: #555;
    flex: 1; /* 占满剩余空间 */
    
    /* 文本超长省略 */
    white-space: nowrap; 
    overflow: hidden; 
    text-overflow: ellipsis; 
}
.interview-progress-row {
    display: flex;
    align-items: flex-end; /* 底部对齐 */
    gap: 24rpx;
    width: 100%;
}
.progress-container {
    flex: 1; /* 进度条占满剩余空间 */
    display: flex;
    flex-direction: column;
    gap: 8rpx;
}

.progress-text { 
    display: flex; 
    justify-content: space-between; 
    font-size: 22rpx; 
    color: #888; 
}
.round-count .highlight { color: #C62828; font-weight: bold; font-size: 26rpx; }

.progress-track-ink { 
    width: 100%; 
    height: 10rpx; 
    background: #E0E0E0; 
    border-radius: 5rpx; 
    overflow: hidden; 
}
.progress-fill-ink { 
    height: 100%; 
    background: #1A1A1A; 
    border-radius: 5rpx; 
    transition: width 0.5s ease; 
}
.end-btn-ink { 
    background: #FFF; border: 1px solid #C62828; color: #C62828;
    font-size: 24rpx; padding: 10rpx 24rpx; border-radius: 12rpx; font-weight: bold;
}

.settings-paper { background: rgba(255,255,255,0.5); border-bottom: 1px solid rgba(0,0,0,0.03); }
.settings-header { padding: 16rpx 30rpx; display: flex; justify-content: space-between; font-size: 24rpx; color: #666; }

/* =========================================================
   5. 报告弹窗 (亚克力+印章)
   ========================================================= */
.report-mask {
    position: fixed; top: 0; left: 0; right: 0; bottom: 0;
    background: rgba(0,0,0,0.5); z-index: 9999;
    display: flex; align-items: center; justify-content: center;
    backdrop-filter: blur(6px);
}
.report-card-acrylic {
    width: 620rpx; height: 80vh;
    background: #F9F9F7; /* 宣纸色 */
    border-radius: 32rpx; display: flex; flex-direction: column; overflow: hidden;
    box-shadow: 0 30rpx 80rpx rgba(0,0,0,0.2);
    border: 1px solid rgba(255,255,255,0.5);
}
.report-header-ink { background: #1A1A1A; padding: 40rpx; text-align: center; color: #F7F7F2; }
.report-title { font-size: 36rpx; letter-spacing: 6rpx; font-weight: bold; }
.report-date { font-size: 24rpx; opacity: 0.6; font-family: serif; margin-top: 10rpx; }

.score-circle-ink {
    width: 150rpx; height: 150rpx; border-radius: 50%;
    border: 6rpx solid; display: flex; flex-direction: column; align-items: center; justify-content: center;
    margin: 0 auto 20rpx; transform: rotate(-5deg);
    &.score-gold { border-color: #C0A060; color: #C0A060; }
    &.score-blue { border-color: #333; color: #333; }
    &.score-red { border-color: #B71C1C; color: #B71C1C; }
}
.score-num { font-size: 64rpx; font-weight: bold; font-family: serif; line-height: 1; }
.score-comment-ink { text-align: justify; font-size: 28rpx; color: #444; line-height: 1.6; padding: 0 40rpx; font-family: serif; }

.report-body { padding: 30rpx 40rpx; }
.feedback-title { font-size: 30rpx; font-weight: bold; margin-bottom: 16rpx; }
.feedback-text-ink { font-size: 28rpx; color: #555; margin-bottom: 12rpx; line-height: 1.6; }

.report-footer { padding: 30rpx 40rpx; border-top: 1px solid rgba(0,0,0,0.05); }
.btn-primary-ink { background: #1A1A1A; color: #fff; border-radius: 16rpx; font-size: 30rpx; }
.btn-secondary-ink { background: #E5E5E0; color: #333; border-radius: 16rpx; font-size: 30rpx; }

/* 动画 */
@keyframes spin { to { transform: rotate(360deg); } }
</style>