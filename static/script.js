function searchSuburb() {
    const suburbInput = document.getElementById('suburb-input');
    const loadingDiv = document.getElementById('loading');
    const gptAnalysis = document.getElementById('gpt-analysis');

    // 清空之前的结果
    gptAnalysis.innerHTML = '';

    // 显示加载动画
    loadingDiv.classList.remove('d-none');

    // 发送搜索请求
    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            suburb: suburbInput.value
        })
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏加载动画
        loadingDiv.classList.add('d-none');

        if (data.error) {
            gptAnalysis.innerHTML = `<div class="error-message">${data.error}</div>`;
            return;
        }

        // 显示GPT分析结果
        const formattedAnalysis = formatAnalysis(data.analysis);
        gptAnalysis.innerHTML = formattedAnalysis;
    })
    .catch(error => {
        console.error('Error:', error);
        loadingDiv.classList.add('d-none');
        gptAnalysis.innerHTML = '<div class="error-message">分析过程中出现错误，请稍后重试</div>';
    });
}

function formatAnalysis(text) {
    if (!text) return '';

    // 将文本中的换行符转换为HTML换行
    let formatted = text.replace(/\n/g, '<br>');

    // 添加标题样式
    formatted = formatted.replace(/^([\d\.]+\s+[^：:]+[：:])/gm, '<h3>$1</h3>');
    
    // 添加子标题样式
    formatted = formatted.replace(/^([^-\n]+)：/gm, '<h4>$1：</h4>');
    
    // 添加列表项样式
    formatted = formatted.replace(/^-\s+(.+)$/gm, '<li>$1</li>');
    
    // 将连续的列表项包装在ul标签中
    formatted = formatted.replace(/(<li>.+<\/li>\n?)+/g, '<ul>$&</ul>');

    // 处理表格样式
    if (formatted.includes('优势') && formatted.includes('劣势')) {
        formatted = formatted.replace(/优势\t劣势/, '<table class="comparison-table"><tr><th>优势</th><th>劣势</th></tr>');
        formatted = formatted.replace(/([^\n]+)\t([^\n]+)/g, '<tr><td>$1</td><td>$2</td></tr>');
        formatted += '</table>';
    }

    return formatted;
}

// 添加回车键搜索功能
document.getElementById('suburb-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchSuburb();
    }
}); 