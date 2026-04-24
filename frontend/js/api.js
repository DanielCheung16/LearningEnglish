// API基础URL
const API_BASE_URL = '/api';

class APIClient {
    /**
     * 发送HTTP请求的通用方法
     */
    static async request(method, endpoint, body = null) {
        const url = `${API_BASE_URL}${endpoint}`;
        const options = {
            method,
            headers: {
                'Content-Type': 'application/json',
            },
        };

        if (body) {
            options.body = JSON.stringify(body);
        }

        try {
            const response = await fetch(url, options);
            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || `HTTP Error: ${response.status}`);
            }

            return { success: true, data };
        } catch (error) {
            return { success: false, error: error.message };
        }
    }

    // ========== 单词管理 API ==========

    /**
     * 添加新单词
     */
    static async addWord(wordData) {
        return this.request('POST', '/words', wordData);
    }

    /**
     * 获取所有单词
     */
    static async getAllWords() {
        return this.request('GET', '/words');
    }

    /**
     * 获取特定单词
     */
    static async getWord(wordId) {
        return this.request('GET', `/words/${wordId}`);
    }

    /**
     * 更新单词
     */
    static async updateWord(wordId, wordData) {
        return this.request('PUT', `/words/${wordId}`, wordData);
    }

    /**
     * 删除单词
     */
    static async deleteWord(wordId) {
        return this.request('DELETE', `/words/${wordId}`);
    }

    /**
     * 批量删除单词
     */
    static async batchDeleteWords(wordIds) {
        return this.request('POST', '/words/batch-delete', { word_ids: wordIds });
    }

    /**
     * 搜索单词
     */
    static async searchWords(query) {
        return this.request('GET', `/words/search?q=${encodeURIComponent(query)}`);
    }

    /**
     * 批量导入单词
     */
    static async batchImportWords(wordsList) {
        return this.request('POST', '/words/batch-import', { words: wordsList });
    }

    /**
     * 获取单词的音频和音标信息
     */
    static async getAudioInfo(word) {
        return this.request('POST', '/words/audio-info', { word });
    }

    static async verifyAudioConnectivity(word) {
        return this.request('POST', '/words/audio-verify', { word });
    }

    // ========== 复习管理 API ==========

    /**
     * 获取今日需要复习的单词
     */
    static async getTodayReviewList() {
        return this.request('GET', '/review/today');
    }

    /**
     * 获取今天新加入且还没学过一遍的单词
     */
    static async getTodayNewWords() {
        return this.request('GET', '/review/today-new');
    }

    /**
     * 提交复习结果
     */
    static async submitReview(wordId, proficiencyLevel) {
        return this.request('POST', '/review/submit', {
            word_id: wordId,
            proficiency_level: proficiencyLevel
        });
    }

    /**
     * 获取单词的复习历史
     */
    static async getReviewHistory(wordId) {
        return this.request('GET', `/review/history/${wordId}`);
    }

    /**
     * 获取复习统计信息
     */
    static async getReviewStats() {
        return this.request('GET', '/review/stats');
    }

    /**
     * 获取已逾期的复习
     */
    static async getOverdueReviews() {
        return this.request('GET', '/review/overdue');
    }

    /**
     * 重置单词的复习进度
     */
    static async resetWordReview(wordId) {
        return this.request('POST', `/review/reset/${wordId}`);
    }

    /**
     * 获取日期范围内的复习记录
     */
    static async getReviewByDate(startDate, endDate) {
        return this.request('GET', `/review/by-date?start_date=${startDate}&end_date=${endDate}`);
    }

    // ========== 配置管理 API ==========

    /**
     * 获取用户配置
     */
    static async getConfig() {
        return this.request('GET', '/config');
    }

    /**
     * 更新用户配置
     */
    static async updateConfig(config) {
        return this.request('PUT', '/config', config);
    }

    /**
     * 测试邮件配置
     */
    static async testEmailConfig(smtpServer, smtpPort, senderEmail, appPassword) {
        return this.request('POST', '/config/email-test', {
            smtp_server: smtpServer,
            smtp_port: smtpPort,
            sender_email: senderEmail,
            app_password: appPassword
        });
    }

    /**
     * 更新提醒时间
     */
    static async updateReminderTime(reminderTime) {
        return this.request('PUT', '/config/reminder-time', { reminder_time: reminderTime });
    }

    /**
     * 切换提醒开关
     */
    static async toggleReminder(enable) {
        return this.request('PUT', '/config/reminder-toggle', { enable });
    }
}

// 导出API客户端
if (typeof module !== 'undefined' && module.exports) {
    module.exports = APIClient;
}
