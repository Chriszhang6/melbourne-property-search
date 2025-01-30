function searchSuburb() {
    const suburbInput = document.getElementById('suburb-input');
    const suburb = suburbInput.value.trim();
    
    if (!suburb) {
        alert('请输入区域名称或邮编');
        return;
    }
    
    // 显示加载动画
    document.getElementById('loading').classList.remove('d-none');
    
    // 清空之前的结果
    clearResults();
    
    // 发送搜索请求
    fetch('/search', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ suburb: suburb })
    })
    .then(response => response.json())
    .then(data => {
        // 隐藏加载动画
        document.getElementById('loading').classList.add('d-none');
        
        if (data.error) {
            alert(data.error);
            return;
        }
        
        // 显示GPT分析结果
        displayGPTAnalysis(data.analysis);
        
        // 显示原始搜索结果
        displayResults(data.raw_results);
    })
    .catch(error => {
        console.error('Error:', error);
        document.getElementById('loading').classList.add('d-none');
        alert('搜索出错，请稍后重试');
    });
}

function clearResults() {
    document.getElementById('infrastructure-results').innerHTML = '';
    document.getElementById('crime-results').innerHTML = '';
    document.getElementById('property-results').innerHTML = '';
    document.getElementById('gpt-analysis').innerHTML = '';
}

function displayResults(data) {
    // 显示教育资源信息
    const infrastructureHtml = data.infrastructure.map(item => `
        <li class="result-item">
            <h4>${item.title}</h4>
            <p>${item.summary}</p>
            <div class="result-meta">
                ${item.date ? `<span class="date">发布日期: ${item.date}</span>` : ''}
                ${item.link ? `<a href="${item.link}" target="_blank" class="more-link">查看详情 →</a>` : ''}
            </div>
        </li>
    `).join('');
    document.getElementById('infrastructure-results').innerHTML = infrastructureHtml || '<li>暂无相关信息</li>';

    // 显示医疗资源信息
    const crimeHtml = data.crime.map(item => `
        <li class="result-item">
            <h4>${item.title}</h4>
            <p>${item.summary}</p>
            <div class="result-meta">
                ${item.date ? `<span class="date">发布日期: ${item.date}</span>` : ''}
                ${item.link ? `<a href="${item.link}" target="_blank" class="more-link">查看详情 →</a>` : ''}
            </div>
        </li>
    `).join('');
    document.getElementById('crime-results').innerHTML = crimeHtml || '<li>暂无相关信息</li>';

    // 显示治安状况信息
    const propertyHtml = data.property.map(item => `
        <li class="result-item">
            <h4>${item.title}</h4>
            <p>${item.summary}</p>
            <div class="result-meta">
                ${item.date ? `<span class="date">发布日期: ${item.date}</span>` : ''}
                ${item.link ? `<a href="${item.link}" target="_blank" class="more-link">查看详情 →</a>` : ''}
            </div>
        </li>
    `).join('');
    document.getElementById('property-results').innerHTML = propertyHtml || '<li>暂无相关信息</li>';
}

function displayGPTAnalysis(analysis) {
    const analysisHtml = `
        <div class="analysis-content">
            ${analysis.split('\n').map(paragraph => 
                paragraph.trim() ? `<p>${paragraph}</p>` : ''
            ).join('')}
        </div>
    `;
    document.getElementById('gpt-analysis').innerHTML = analysisHtml;
}

// 添加回车键搜索功能
document.getElementById('suburb-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchSuburb();
    }
}); 