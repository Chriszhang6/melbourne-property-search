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

        // 将换行符转换为HTML段落
        let formattedText = analysis
            .toString()  // 确保输入是字符串
            .split('\n')
            .filter(line => line.trim() !== '')
            .map(line => {
                const trimmedLine = line.trim();
                
                // 处理一级标题 (#)，确保标题前没有多余的空格
                if (trimmedLine.match(/^#\s+/)) {
                    const titleText = trimmedLine.replace(/^#\s+/, '').trim();
                    return `<h2 class="primary-title">${titleText}</h2>\n\n`;  // 添加两个换行
                }
                
                // 处理二级标题 (##)，确保标题前没有多余的空格
                if (trimmedLine.match(/^##\s+/)) {
                    const titleText = trimmedLine.replace(/^##\s+/, '').trim();
                    return `<h3 class="secondary-title">${titleText}</h3>\n\n`;  // 添加两个换行
                }

                // 处理总结部分的优势和劣势
                if (trimmedLine.startsWith('优势：')) {
                    return `<div class="advantages"><h4>优势：</h4><ul>${formatList(trimmedLine.substring(3))}</ul></div>\n\n`;
                }
                if (trimmedLine.startsWith('劣势：')) {
                    return `<div class="disadvantages"><h4>劣势：</h4><ul>${formatList(trimmedLine.substring(3))}</ul></div>\n\n`;
                }

                // 处理表格
                if (trimmedLine.includes('|')) {
                    return formatTable(trimmedLine) + '\n';
                }

                // 处理列表
                if (trimmedLine.startsWith('- ')) {
                    return `<li>${trimmedLine.substring(2)}</li>\n`;
                }
                if (trimmedLine.match(/^[a-zA-Z\u4e00-\u9fa5]\d*\./)) {
                    return `<li>${trimmedLine.substring(trimmedLine.indexOf('.') + 1).trim()}</li>\n`;
                }

                // 普通段落
                return `<p>${trimmedLine}</p>\n\n`;  // 添加两个换行
            })
            .join('');  // 不再需要额外的换行，因为我们在每个元素后都添加了换行

        // 将连续的li元素包装在ul中
        formattedText = formattedText.replace(/<li>.*?<\/li>(?:\s*<li>.*?<\/li>)+/g, match => {
            return `<ul>${match}</ul>\n\n`;  // 为列表添加额外的间距
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