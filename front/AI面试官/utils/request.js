// utils/request.js

// ⚠️ 注意：如果你是在 浏览器 调试，用 localhost。
// ⚠️ 如果是用 手机/模拟器 调试，必须把 localhost 换成你电脑的局域网 IP (比如 192.168.1.5)
const BASE_URL = 'http://192.168.1.11:8000/api'; 

export const request = (options) => {
    return new Promise((resolve, reject) => {
        // 1. 获取本地存储的 Token
        const token = uni.getStorageSync('access_token');

        // 2. 组装 Header
        let header = {
            'content-type': 'application/json',
            ...options.header // 允许覆盖
        };
        
        // 如果有 Token，自动挂载到 Authorization
        if (token) {
            header['Authorization'] = 'Bearer ' + token;
        }

        uni.request({
            url: BASE_URL + options.url,
            method: options.method || 'GET',
            data: options.data || {},
            header: header,
            success: (res) => {
                // 3. 统一处理后端返回的状态码
                if (res.statusCode === 200) {
                    resolve(res.data);
                } else if (res.statusCode === 401) {
                    // 401 代表 Token 过期或未登录
                    uni.removeStorageSync('access_token');
                    uni.showToast({ title: '请重新登录', icon: 'none' });
                    setTimeout(() => {
                        uni.reLaunch({ url: '/pages/login/index' });
                    }, 1500);
                    reject(res);
                } else {
                    uni.showToast({
                        title: res.data.detail || '请求出错',
                        icon: 'none'
                    });
                    reject(res);
                }
            },
            fail: (err) => {
                uni.showToast({ title: '网络连接失败', icon: 'none' });
                reject(err);
            }
        });
    });
};

// 导出上传图片的方法 (上传图片的 header 比较特殊)
export const uploadFile = (filePath, formData) => {
    return new Promise((resolve, reject) => {
        const token = uni.getStorageSync('access_token');
        
        uni.uploadFile({
            url: BASE_URL + '/chat', // 这一行可能需要根据你实际上传接口调整，如果是 /chat 接口直接传图
            filePath: filePath,
            name: 'image',
            formData: formData,
            header: {
                'Authorization': 'Bearer ' + token
            },
            success: (res) => {
                if (res.statusCode === 200) {
                    resolve(JSON.parse(res.data)); // uploadFile 返回的是字符串，需要 parse
                } else {
                    reject(res);
                }
            },
            fail: (err) => {
                reject(err);
            }
        });
    });
};