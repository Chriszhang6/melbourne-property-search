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
                // 处理一级标题（数字开头或特定标题）
                if (/^\d+\./.test(line) || line.startsWith('总结：')) {
                    const titleText = line.startsWith('总结：') ? line : line.substring(line.indexOf('.') + 1).trim();
                    // 如果是总结，使用5作为编号
                    return `<h2 class="primary-title">${line.startsWith('总结：') ? '5. ' + titleText : line}</h2>`;
                }
                
                // 处理二级标题（x.x格式）
                if (/^\d+\.\d+/.test(line)) {
                    const titleText = line.substring(line.indexOf('.', line.indexOf('.') + 1) + 1).trim();
                    return `<h3 class="secondary-title"><strong>${line.split('.', 2).join('.')} ${titleText}</strong></h3>`;
                }

                // 处理特殊的一级标题（医疗资源和房价趋势）
                if (line.trim() === '医疗资源') {
                    return `<h2 class="primary-title">3. ${line}</h2>`;
                }
                if (line.trim() === '房价趋势与推动因素') {
                    return `<h2 class="primary-title">4. ${line}</h2>`;
                }

                // 处理表格
                if (line.includes('|')) {
                    return formatTable(line);
                }

                // 处理列表
                if (line.startsWith('- ')) {
                    return `<li>${line.substring(2)}</li>`;
                }
                if (line.match(/^[a-zA-Z\u4e00-\u9fa5]\d*\./)) {
                    return `<li>${line.substring(line.indexOf('.') + 1).trim()}</li>`;
                }

                // 普通段落
                return `<p>${line}</p>`;
            })
            .join('');

        // 将连续的li元素包装在ul中
        formattedText = formattedText.replace(/<li>.*?<\/li>(?:\s*<li>.*?<\/li>)+/g, match => {
            return `<ul>${match}</ul>`;
        });

        return formattedText;
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