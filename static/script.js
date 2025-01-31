// 等待 DOM 加载完成
document.addEventListener('DOMContentLoaded', function() {
    const searchForm = document.getElementById('searchForm');
    const searchInput = document.getElementById('searchInput');
    const loadingContainer = document.getElementById('loadingContainer');
    const reportSection = document.getElementById('reportSection');
    const errorContainer = document.getElementById('errorContainer');

    searchForm.addEventListener('submit', async function(e) {
        e.preventDefault();
        const suburb = searchInput.value.trim();
        
        if (!suburb) {
            showError('请输入区域名称');
            return;
        }

        // 显示加载动画
        showLoading();
        hideError();
        hideReport();

        // 记录开始时间
        const startTime = new Date();

        try {
            const response = await fetch('/search', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ suburb: suburb })
            });

            if (!response.ok) {
                throw new Error('服务器响应错误');
            }

            const data = await response.json();
            
            if (data.error) {
                showError(data.error);
                return;
            }

            // 计算分析时间
            const endTime = new Date();
            const analysisTime = ((endTime - startTime) / 1000).toFixed(1);

            displayReport(suburb, data.analysis, analysisTime);

        } catch (error) {
            showError('分析过程中发生错误，请稍后重试');
            console.error('Error:', error);
        } finally {
            hideLoading();
        }
    });

    function showLoading() {
        loadingContainer.style.display = 'flex';
        loadingContainer.innerHTML = `
            <div class="loading-content">
                <div class="spinner"></div>
                <p>正在生成专业分析报告，请稍候...</p>
            </div>
        `;
    }

    function hideLoading() {
        loadingContainer.style.display = 'none';
    }

    function showError(message) {
        errorContainer.style.display = 'block';
        errorContainer.innerHTML = `<div class="error-message">${message}</div>`;
    }

    function hideError() {
        errorContainer.style.display = 'none';
    }

    function hideReport() {
        reportSection.style.display = 'none';
    }

    function displayReport(suburb, analysis, analysisTime) {
        const currentDate = new Date().toLocaleDateString('zh-CN', {
            year: 'numeric',
            month: 'long',
            day: 'numeric'
        });

        reportSection.style.display = 'block';
        reportSection.innerHTML = `
            <div class="report-header">
                <h2>${suburb} 区域分析报告</h2>
                <p class="report-date">生成日期：${currentDate}</p>
                <p class="analysis-time">分析耗时：${analysisTime} 秒</p>
            </div>
            <div class="report-content">
                ${formatAnalysis(analysis)}
            </div>
        `;

        // 滚动到报告部分
        reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function formatAnalysis(analysis) {
        // 将换行符转换为HTML段落
        let formattedText = analysis
            .split('\n')
            .filter(line => line.trim() !== '')
            .map(line => {
                const trimmedLine = line.trim();
                
                // 处理一级标题
                if (/^\d+\.\s+/.test(trimmedLine)) {
                    return `<h2 class="primary-title">${trimmedLine}</h2>`;
                }
                
                // 处理特殊的一级标题（总结、建议、参考来源）
                if (trimmedLine === '总结') {
                    return `<h2 class="primary-title">5. ${trimmedLine}</h2>`;
                }
                if (trimmedLine === '建议') {
                    return `<h2 class="primary-title">6. ${trimmedLine}</h2>`;
                }
                if (trimmedLine === '参考来源') {
                    return `<h2 class="primary-title">7. ${trimmedLine}</h2>`;
                }
                
                // 处理二级标题
                const secondaryTitles = {
                    '2.1 公立学校': true,
                    '2.2 私立学校': true,
                    '2.3 短板': true,
                    '3.1 公立医院': true,
                    '3.2 私立医疗机构': true,
                    '3.3 短板': true,
                    '4.1 单元房（Unit）': true,
                    '4.2 独立屋（House）': true,
                    '4.3 增长推动因素': true,
                    '4.4 风险提示': true
                };
                
                // 检查是否是二级标题
                const titleMatch = trimmedLine.match(/^\d+\.\d+\s+(.+)$/);
                if (titleMatch && secondaryTitles[trimmedLine]) {
                    return `<h3 class="secondary-title">${trimmedLine}</h3>`;
                }

                // 处理总结部分的优势和劣势
                if (trimmedLine.startsWith('优势：')) {
                    return `<div class="advantages"><h4>优势：</h4><ul>${formatList(trimmedLine.substring(3))}</ul></div>`;
                }
                if (trimmedLine.startsWith('劣势：')) {
                    return `<div class="disadvantages"><h4>劣势：</h4><ul>${formatList(trimmedLine.substring(3))}</ul></div>`;
                }

                // 处理表格
                if (trimmedLine.includes('|')) {
                    return formatTable(trimmedLine);
                }

                // 处理列表
                if (trimmedLine.startsWith('- ')) {
                    return `<li>${trimmedLine.substring(2)}</li>`;
                }
                if (trimmedLine.match(/^[a-zA-Z\u4e00-\u9fa5]\d*\./)) {
                    return `<li>${trimmedLine.substring(trimmedLine.indexOf('.') + 1).trim()}</li>`;
                }

                // 普通段落
                return `<p>${trimmedLine}</p>`;
            })
            .join('');

        // 将连续的li元素包装在ul中
        formattedText = formattedText.replace(/<li>.*?<\/li>(?:\s*<li>.*?<\/li>)+/g, match => {
            return `<ul>${match}</ul>`;
        });

        return formattedText;
    }

    // 格式化优势劣势列表
    function formatList(text) {
        return text.split('，')
            .filter(item => item.trim())
            .map(item => `<li>${item.trim()}</li>`)
            .join('');
    }

    function formatTable(tableContent) {
        // 检查是否是表格分隔行
        if (tableContent.replace(/[\s\-|]/g, '') === '') {
            return '';
        }

        const cells = tableContent.split('|').map(cell => cell.trim()).filter(cell => cell);
        
        // 检测是否是表头
        const isHeader = tableContent.includes('---');
        
        if (isHeader) {
            return `<table class="comparison-table">
                        <thead>
                            <tr>
                                ${cells.map(cell => `<th>${cell}</th>`).join('')}
                            </tr>
                        </thead>
                        <tbody>`;
        } else {
            return `<tr>${cells.map(cell => `<td>${cell}</td>`).join('')}</tr>`;
        }
    }
}); 