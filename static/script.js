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
            // 搜索完成后立即更新API使用量
            updateAPIUsage();

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
            <div class="loading-content" style="width: 100%; text-align: center;">
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
                <p class="disclaimer">注意：本报告中的数据仅供参考，具体信息请以官方发布为准。</p>
            </div>
            <div class="report-content">
                ${formatAnalysis(analysis)}
            </div>
            <button class="print-button" onclick="downloadPDF()">
                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 10v6m0 0l-3-3m3 3l3-3m2 8H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
                </svg>
                下载PDF
            </button>
        `;

        // 滚动到报告部分
        reportSection.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    function downloadPDF() {
        const reportContent = document.querySelector('.report-section');
        const suburb = reportContent.querySelector('h2').textContent;
        
        // 创建一个新的打印窗口
        const printWindow = window.open('', '_blank');
        printWindow.document.write(`
            <html>
            <head>
                <title>${suburb}</title>
                <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap" rel="stylesheet">
                <link href="/static/style.css" rel="stylesheet">
                <style>
                    body {
                        padding: 2rem;
                        font-family: 'Inter', sans-serif;
                    }
                    @page {
                        size: A4;
                        margin: 2cm;
                    }
                </style>
            </head>
            <body>
                ${reportContent.innerHTML}
            </body>
            </html>
        `);
        
        // 等待样式加载完成后打印
        setTimeout(() => {
            printWindow.print();
            printWindow.close();
        }, 1000);
    }

    function formatAnalysis(analysis) {
        // 添加空值检查
        if (!analysis) {
            console.error('分析内容为空');
            return '<p>暂无分析内容</p>';
        }

        let sections = {
            summary: '',
            advantages: '',
            disadvantages: '',
            suggestions: '',
            references: '',
            content: []
        };

        let currentSection = 'content';
        let tableContent = [];
        let listContent = [];

        // 将换行符转换为HTML段落
        analysis.toString().split('\n').forEach(line => {
            const trimmedLine = line.trim();
            if (!trimmedLine) return;

            // 处理总结部分
            if (trimmedLine.startsWith('总结：')) {
                sections.summary = `<div class="report-summary">
                    <h3>总结</h3>
                    <p>${trimmedLine.substring(3)}</p>
                </div>`;
                return;
            }

            // 处理优势
            if (trimmedLine.startsWith('优势：')) {
                sections.advantages = `<div class="advantages">
                    <h4>优势</h4>
                    <ul>${formatList(trimmedLine.substring(3))}</ul>
                </div>`;
                return;
            }

            // 处理劣势
            if (trimmedLine.startsWith('劣势：')) {
                sections.disadvantages = `<div class="disadvantages">
                    <h4>劣势</h4>
                    <ul>${formatList(trimmedLine.substring(3))}</ul>
                </div>`;
                return;
            }

            // 处理建议部分
            if (trimmedLine.startsWith('建议：')) {
                sections.suggestions = `<div class="suggestions">
                    <h3>建议</h3>
                    <p>${trimmedLine.substring(3)}</p>
                </div>`;
                return;
            }

            // 处理参考资料部分
            if (trimmedLine.startsWith('参考资料：')) {
                sections.references = `<div class="references">
                    <h3>参考资料</h3>
                    <p>${trimmedLine.substring(5)}</p>
                </div>`;
                return;
            }

            // 处理一级标题
            if (trimmedLine.match(/^#\s+/)) {
                if (tableContent.length > 0) {
                    sections.content.push(formatTableComplete(tableContent));
                    tableContent = [];
                }
                if (listContent.length > 0) {
                    sections.content.push(`<ul>${listContent.join('')}</ul>`);
                    listContent = [];
                }
                sections.content.push(`<h2 class="primary-title">${trimmedLine.replace(/^#\s+/, '').trim()}</h2>`);
                return;
            }

            // 处理二级标题
            if (trimmedLine.match(/^##\s+/)) {
                if (tableContent.length > 0) {
                    sections.content.push(formatTableComplete(tableContent));
                    tableContent = [];
                }
                if (listContent.length > 0) {
                    sections.content.push(`<ul>${listContent.join('')}</ul>`);
                    listContent = [];
                }
                sections.content.push(`<h3 class="secondary-title">${trimmedLine.replace(/^##\s+/, '').trim()}</h3>`);
                return;
            }

            // 处理表格
            if (trimmedLine.includes('|')) {
                tableContent.push(trimmedLine);
                return;
            }

            // 处理列表
            if (trimmedLine.startsWith('- ') || trimmedLine.match(/^\d+\./)) {
                listContent.push(`<li>${trimmedLine.replace(/^-\s+|^\d+\.\s*/, '')}</li>`);
                return;
            }

            // 处理普通段落
            if (tableContent.length > 0) {
                sections.content.push(formatTableComplete(tableContent));
                tableContent = [];
            }
            if (listContent.length > 0) {
                sections.content.push(`<ul>${listContent.join('')}</ul>`);
                listContent = [];
            }
            sections.content.push(`<p>${trimmedLine}</p>`);
        });

        // 处理最后的表格或列表
        if (tableContent.length > 0) {
            sections.content.push(formatTableComplete(tableContent));
        }
        if (listContent.length > 0) {
            sections.content.push(`<ul>${listContent.join('')}</ul>`);
        }

        // 组合所有内容
        return `
            ${sections.summary}
            ${sections.content.join('\n')}
            ${sections.advantages}
            ${sections.disadvantages}
            ${sections.suggestions}
            ${sections.references}
        `;
    }

    function formatTableComplete(tableContent) {
        if (tableContent.length < 2) return ''; // 至少需要表头和分隔行

        let html = '<table class="comparison-table">\n<thead>\n';
        let isHeader = true;
        let hasBody = false;

        tableContent.forEach((row, index) => {
            if (row.replace(/[\s\-|]/g, '') === '') {
                isHeader = false;
                hasBody = true;
                html += '</thead>\n<tbody>\n';
            } else if (isHeader) {
                const cells = row.split('|').map(cell => cell.trim()).filter(cell => cell);
                html += '<tr>' + cells.map(cell => `<th>${cell}</th>`).join('') + '</tr>\n';
            } else if (hasBody) {
                const cells = row.split('|').map(cell => cell.trim()).filter(cell => cell);
                html += '<tr>' + cells.map(cell => `<td>${cell}</td>`).join('') + '</tr>\n';
            }
        });

        html += hasBody ? '</tbody>\n</table>' : '</thead>\n</table>';
        return html;
    }

    function formatList(text) {
        return text.split('，')
            .filter(item => item.trim())
            .map(item => `<li>${item.trim()}</li>`)
            .join('');
    }
});

// API使用量更新函数
async function updateAPIUsage() {
    try {
        const response = await fetch('/usage');
        if (!response.ok) {
            throw new Error('服务器响应错误');
        }
        const data = await response.json();
        const costElement = document.getElementById('api-cost');
        if (costElement) {
            costElement.textContent = data.total_cost.toFixed(4);
            // 根据使用量调整颜色
            const usagePercentage = (data.total_cost / data.budget_limit) * 100;
            const icon = document.querySelector('.api-usage i');
            if (usagePercentage >= 90) {
                icon.style.color = '#f44336'; // 红色
            } else if (usagePercentage >= 70) {
                icon.style.color = '#ff9800'; // 橙色
            } else {
                icon.style.color = '#4CAF50'; // 绿色
            }
        }
    } catch (error) {
        console.error('更新API使用量失败:', error);
    }
}

// 页面加载时更新API使用量
document.addEventListener('DOMContentLoaded', () => {
    updateAPIUsage();
    // 每5分钟更新一次
    setInterval(updateAPIUsage, 5 * 60 * 1000);
}); 