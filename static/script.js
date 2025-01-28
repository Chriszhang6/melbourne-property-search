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

function displayGPTAnalysis(analysis) {
    const analysisHtml = `
        <div class="analysis-content">
            ${analysis.split('\n').map(paragraph => 
                paragraph.trim() ? `<p class="mb-3">${paragraph}</p>` : ''
            ).join('')}
        </div>
    `;
    document.getElementById('gpt-analysis').innerHTML = analysisHtml;
}

function displayResults(data) {
    // 显示基础设施信息
    const infrastructureHtml = data.infrastructure.map(item => `
        <div class="result-item mb-3">
            <h6>${item.title}</h6>
            <p class="mb-1">${item.summary}</p>
            ${item.date ? `<small class="text-muted">日期: ${item.date}</small>` : ''}
            ${item.link ? `<br><a href="${item.link}" target="_blank" class="small">查看详情</a>` : ''}
        </div>
    `).join('');
    document.getElementById('infrastructure-results').innerHTML = infrastructureHtml || '未找到相关信息';

    // 显示犯罪率统计
    const crimeHtml = data.crime.map(item => `
        <div class="result-item mb-3">
            <h6>${item.title}</h6>
            <p class="mb-1">${item.summary}</p>
            ${item.date ? `<small class="text-muted">日期: ${item.date}</small>` : ''}
            ${item.link ? `<br><a href="${item.link}" target="_blank" class="small">查看详情</a>` : ''}
        </div>
    `).join('');
    document.getElementById('crime-results').innerHTML = crimeHtml || '未找到相关信息';

    // 显示房价走势
    const propertyHtml = data.property.map(item => `
        <div class="result-item mb-3">
            <h6>${item.title}</h6>
            <p class="mb-1">${item.summary}</p>
            ${item.date ? `<small class="text-muted">日期: ${item.date}</small>` : ''}
            ${item.link ? `<br><a href="${item.link}" target="_blank" class="small">查看详情</a>` : ''}
        </div>
    `).join('');
    document.getElementById('property-results').innerHTML = propertyHtml || '未找到相关信息';
}

// 添加回车键搜索功能
document.getElementById('suburb-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchSuburb();
    }
}); 