const API_URL = '/api';
let systemReady = false;

document.addEventListener('DOMContentLoaded', () => {
    initializeApp();
    setupEventListeners();
    checkSystemHealth();
    loadTierList();
});

function initializeApp() {
    console.log('Initializing TFT Auto Chess Web UI');
}

function setupEventListeners() {
    document.querySelectorAll('.nav-button').forEach(button => {
        button.addEventListener('click', handleTabClick);
    });

    document.getElementById('get-recommendations-btn').addEventListener('click', getRecommendations);
    document.getElementById('demo-btn').addEventListener('click', runDemo);
    document.getElementById('analyze-btn').addEventListener('click', analyzeComposition);
    document.getElementById('refresh-data-btn').addEventListener('click', refreshData);
}

function handleTabClick(e) {
    const tabName = e.target.dataset.tab;
    
    document.querySelectorAll('.nav-button').forEach(btn => btn.classList.remove('active'));
    e.target.classList.add('active');

    document.querySelectorAll('.tab').forEach(tab => tab.classList.remove('active'));
    document.getElementById(`${tabName}-tab`).classList.add('active');
}

async function checkSystemHealth() {
    try {
        const response = await fetch(`${API_URL}/health`);
        const data = await response.json();
        
        const statusEl = document.getElementById('system-status');
        if (data.system) {
            statusEl.textContent = '就绪';
            statusEl.classList.remove('loading');
            statusEl.classList.add('healthy');
            systemReady = true;
        }
        updateSystemInfo();
    } catch (error) {
        console.error('Health check failed:', error);
    }
}

async function updateSystemInfo() {
    try {
        const response = await fetch(`${API_URL}/system/info`);
        const data = await response.json();
        
        document.getElementById('about-status').textContent = '正常';
        document.getElementById('about-champions-count').textContent = `${data.winrate_data_count} 个卡牌`;
        document.getElementById('about-engine-status').textContent = data.recommendation_engine;
    } catch (error) {
        console.error('Failed to get system info:', error);
    }
}

async function getRecommendations() {
    if (!systemReady) {
        showNotification('系统还未就绪', 'warning');
        return;
    }

    const cardsInput = document.getElementById('current-cards').value;
    const level = parseInt(document.getElementById('player-level').value);
    const topN = parseInt(document.getElementById('top-n').value);

    if (!cardsInput.trim()) {
        showNotification('请输入卡牌名称', 'warning');
        return;
    }

    const currentCards = parseCardInput(cardsInput);
    showLoading(true);

    try {
        const response = await fetch(`${API_URL}/recommendations`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                current_cards: currentCards,
                level: level,
                top_n: topN
            })
        });

        const data = await response.json();
        if (data.success) {
            displayRecommendations(data.recommendations);
            showNotification(`成功获取 ${data.count} 个推荐`, 'success');
        }
    } catch (error) {
        showNotification('获取推荐失败', 'error');
    } finally {
        showLoading(false);
    }
}

function displayRecommendations(recommendations) {
    const recommendationsList = document.getElementById('recommendations-list');
    if (recommendations.length === 0) {
        recommendationsList.innerHTML = '<div class="empty-message">未找到推荐</div>';
    } else {
        recommendationsList.innerHTML = recommendations.map((rec, index) => `
            <div class="recommendation-card">
                <div class="recommendation-rank">#${index + 1}</div>
                <div class="recommendation-name">${rec.champion.toUpperCase()}</div>
                <div class="recommendation-score">${rec.percentage}</div>
            </div>
        `).join('');
    }
    document.getElementById('recommendations-result').style.display = 'block';
}

async function runDemo() {
    showLoading(true);
    try {
        const response = await fetch(`${API_URL}/demo`);
        const data = await response.json();
        if (data.success) {
            document.getElementById('current-cards').value = data.cards.join(', ');
            document.getElementById('player-level').value = data.level;
            displayRecommendations(data.recommendations);
            showNotification('演示数据已加载', 'success');
        }
    } catch (error) {
        showNotification('演示失败', 'error');
    } finally {
        showLoading(false);
    }
}

async function analyzeComposition() {
    const cardsInput = document.getElementById('analysis-cards').value;
    if (!cardsInput.trim()) {
        showNotification('请输入卡牌名称', 'warning');
        return;
    }

    const currentCards = parseCardInput(cardsInput);
    showLoading(true);

    try {
        const response = await fetch(`${API_URL}/synergies`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ current_cards: currentCards })
        });

        const data = await response.json();
        if (data.success) {
            displayAnalysis(data);
            showNotification('分析完成', 'success');
        }
    } catch (error) {
        showNotification('分析失败', 'error');
    } finally {
        showLoading(false);
    }
}

function displayAnalysis(data) {
    const activeSynergies = document.getElementById('active-synergies');
    const nearCompletion = document.getElementById('near-completion');

    activeSynergies.innerHTML = Object.entries(data.active_synergies).length === 0 ?
        '<div class="empty-message">暂无活跃羁绊</div>' :
        Object.entries(data.active_synergies).map(([trait, count]) => `
            <div class="synergy-item"><div>${trait}</div><div>已激活: ${count}个</div></div>
        `).join('');

    nearCompletion.innerHTML = data.near_completion.length === 0 ?
        '<div class="empty-message">暂无接近完成的羁绊</div>' :
        data.near_completion.map(item => `
            <div class="synergy-item"><div>${item.trait}</div><div>当前: ${item.current}个, 下一级: ${item.next}个</div></div>
        `).join('');

    document.getElementById('analysis-result').style.display = 'block';
}

async function loadTierList() {
    try {
        const response = await fetch(`${API_URL}/tier-list`);
        const data = await response.json();
        if (data.success) {
            displayTierList(data.tiers);
        }
    } catch (error) {
        console.error('Failed to load tier list:', error);
    }
}

function displayTierList(tiers) {
    const tierListEl = document.getElementById('tier-list');
    const tierOrder = ['S', 'A', 'B', 'C', 'UNRANKED'];
    tierListEl.innerHTML = tierOrder
        .filter(tier => tiers[tier] && tiers[tier].length > 0)
        .map(tier => `
            <div class="tier-section">
                <div class="tier-header">等级 ${tier}</div>
                <div class="tier-champions">
                    ${tiers[tier].map(champion => `<div class="champion-badge">${champion.substring(0, 8)}</div>`).join('')}
                </div>
            </div>
        `).join('');
}

async function refreshData() {
    showLoading(true);
    showNotification('正在更新数据...', 'warning');

    try {
        const response = await fetch(`${API_URL}/refresh-data`, { method: 'POST' });
        const data = await response.json();
        if (data.success) {
            showNotification(data.message, 'success');
            updateSystemInfo();
            loadTierList();
        }
    } catch (error) {
        showNotification('数据更新失败', 'error');
    } finally {
        showLoading(false);
    }
}

function parseCardInput(input) {
    return input.split(/[,\s]+/).map(card => card.trim().toLowerCase()).filter(card => card.length > 0);
}

function showLoading(show) {
    document.getElementById('loading').style.display = show ? 'flex' : 'none';
}

function showNotification(message, type = 'success') {
    const notificationEl = document.getElementById('notification');
    notificationEl.textContent = message;
    notificationEl.className = `notification ${type}`;
    notificationEl.style.display = 'block';
    setTimeout(() => {
        notificationEl.style.display = 'none';
    }, 3000);
}

setInterval(checkSystemHealth, 30000);