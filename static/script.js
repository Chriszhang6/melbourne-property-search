async function searchSuburb() {
    const suburb = document.getElementById('suburb').value.trim();
    if (!suburb) {
        alert('请输入区域名称');
        return;
    }

    // 显示加载动画
    document.getElementById('loading').style.display = 'block';
    document.getElementById('result').style.display = 'none';

    try {
        const response = await fetch('/search', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ suburb }),
        });

        const data = await response.json();

        if (data.error) {
            throw new Error(data.error);
        }

        // 显示结果
        const resultDiv = document.getElementById('result');
        resultDiv.textContent = data.analysis;
        resultDiv.style.display = 'block';
    } catch (error) {
        alert('发生错误：' + error.message);
    } finally {
        // 隐藏加载动画
        document.getElementById('loading').style.display = 'none';
    }
}

function displayAnalysis(analysis) {
    // 将分析结果中的链接转换为HTML链接
    const processedAnalysis = analysis.replace(/\[(.*?)\]\((https?:\/\/[^\s\)]+)\)/g, '<a href="$2" target="_blank">$1</a>');
    
    // 处理Markdown格式
    const formattedAnalysis = processedAnalysis
        .split('\n')
        .map(line => {
            // 处理标题
            if (line.match(/^#+\s/)) {
                const level = line.match(/^#+/)[0].length;
                return `<h${level}>${line.replace(/^#+\s+/, '')}</h${level}>`;
            }
            // 处理列表项
            else if (line.trim().startsWith('-')) {
                return `<ul><li>${line.replace(/^-\s+/, '')}</li></ul>`;
            }
            // 处理表格
            else if (line.includes('|')) {
                return `<div class="table-row">${line.split('|').map(cell => `<div class="table-cell">${cell.trim()}</div>`).join('')}</div>`;
            }
            // 处理普通段落
            else if (line.trim()) {
                return `<p>${line}</p>`;
            }
            return '';
        })
        .join('');

    document.getElementById('gpt-analysis').innerHTML = formattedAnalysis;
}

// 添加回车键搜索功能
document.getElementById('suburb-input').addEventListener('keypress', function(e) {
    if (e.key === 'Enter') {
        searchSuburb();
    }
}); 