<!-- components/CodeBlock/CodeBlock.vue -->
<template>
	<view class="code-card">
		<!-- 1. 顶部栏 -->
		<view class="code-header">
			<view class="lang-tag">
				<text class="dot red"></text>
				<text class="dot yellow"></text>
				<text class="dot green"></text>
				<text class="lang-text">{{ language || 'code' }}</text>
			</view>
			<view class="copy-btn" @click.stop="handleCopy">
				<text class="copy-icon">📋</text>
				<text class="copy-text">复制代码</text>
			</view>
		</view>
		
		<!-- 2. 代码内容区 (强制换行，不滚动) -->
		<view class="code-content">
			<text class="code-text" :user-select="true">{{ code }}</text>
		</view>
	</view>
</template>

<script>
export default {
	props: {
		code: { type: String, default: '' },
		language: { type: String, default: '' }
	},
	methods: {
		handleCopy() {
			uni.setClipboardData({
				data: this.code,
				success: () => {
					uni.showToast({ title: '代码已复制', icon: 'none' });
				}
			});
		}
	}
}
</script>

<style lang="scss" scoped>
.code-card {
	margin: 16rpx 0;
	border-radius: 16rpx;
	overflow: hidden;
	background-color: #1e1e1e; /* 深色背景 */
	border: 1px solid #333;
}

.code-header {
	display: flex;
	justify-content: space-between;
	align-items: center;
	background-color: #2d2d2d;
	padding: 12rpx 24rpx;
	border-bottom: 1px solid #333;
}

.lang-tag {
	display: flex;
	align-items: center;
	gap: 12rpx;
}

/* 模拟 Mac 窗口红黄绿点 */
.dot { width: 18rpx; height: 18rpx; border-radius: 50%; }
.red { background-color: #ff5f56; }
.yellow { background-color: #ffbd2e; }
.green { background-color: #27c93f; }

.lang-text {
	margin-left: 10rpx;
	color: #a0a0a0;
	font-size: 24rpx;
	font-family: monospace;
	text-transform: lowercase;
}

.copy-btn {
	display: flex;
	align-items: center;
	opacity: 0.7;
	transition: opacity 0.2s;
}
.copy-btn:active { opacity: 1; }

.copy-icon { font-size: 24rpx; margin-right: 6rpx; }
.copy-text { font-size: 22rpx; color: #fff; }

.code-content {
	padding: 20rpx 24rpx;
	position: relative;
}

.code-text {
	color: #d4d4d4; /* 浅灰代码色 */
	font-family: 'Menlo', 'Monaco', 'Courier New', monospace;
	font-size: 26rpx;
	line-height: 1.6;
	
	/* 🔥 关键：强制换行，禁止左右滑动 🔥 */
	white-space: pre-wrap; 
	word-break: break-all;
	display: block;
}
</style>