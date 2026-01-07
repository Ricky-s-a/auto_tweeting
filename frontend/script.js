document.addEventListener('DOMContentLoaded', () => {
    fetchProfile();
    fetchHistory();
    fetchTweets();
});

const API_BASE = '/api';

// ... fetchProfile ...

async function fetchHistory() {
    try {
        const response = await fetch(`${API_BASE}/history`);
        if (!response.ok) return; // Silent fail if no history yet
        const data = await response.json();

        // If we have less than 2 points, maybe show a "Start tracking..." message or just empty chart
        renderChart(data);

    } catch (error) {
        console.error("History error:", error);
    }
}

async function fetchProfile() {
    const profileSection = document.getElementById('profile-section');
    const statsSection = document.getElementById('stats-section');

    try {
        const response = await fetch(`${API_BASE}/me`);
        if (!response.ok) throw new Error('Failed to fetch profile');
        const data = await response.json();

        renderProfile(data);
        renderStats(data.public_metrics);

    } catch (error) {
        console.error(error);
        profileSection.innerHTML = `<div class="error">Error loading profile: ${error.message}</div>`;
    }
}

async function fetchTweets() {
    const tweetsList = document.getElementById('tweets-list');

    try {
        // Fetch more tweets for better analysis (limit=100 handled in backend)
        const response = await fetch(`${API_BASE}/tweets?limit=50`);
        if (!response.ok) throw new Error('Failed to fetch tweets');

        allTweets = await response.json();
        filterTweets('latest'); // Initial render

    } catch (error) {
        console.error(error);
        tweetsList.innerHTML = `<div class="error">Error loading tweets: ${error.message}</div>`;
    }
}

function filterTweets(criteria) {
    currentFilter = criteria;

    // Update UI buttons
    document.querySelectorAll('.filter-btn').forEach(btn => {
        btn.classList.remove('active');
        if (btn.textContent.toLowerCase() === criteria) btn.classList.add('active');
        // Handle "Impressions" vs "latest" text match
        if (criteria === 'latest' && btn.textContent === 'Latest') btn.classList.add('active');
    });

    let sortedTweets = [...allTweets];

    if (criteria === 'latest') {
        // Already sorted by API mostly, but ensure desc
        sortedTweets.sort((a, b) => new Date(b.created_at) - new Date(a.created_at));
    } else if (criteria === 'impressions') {
        sortedTweets.sort((a, b) => getMetric(b, 'impression_count') - getMetric(a, 'impression_count'));
    } else if (criteria === 'likes') {
        sortedTweets.sort((a, b) => getMetric(b, 'like_count') - getMetric(a, 'like_count'));
    } else if (criteria === 'retweets') {
        sortedTweets.sort((a, b) => getMetric(b, 'retweet_count') - getMetric(a, 'retweet_count'));
    }

    renderTweets(sortedTweets, criteria);
}

function getMetric(tweet, key) {
    // Check non_public_metrics first (impressions), then public_metrics, then organic
    let val = 0;
    if (tweet.non_public_metrics && tweet.non_public_metrics[key] !== undefined) val = tweet.non_public_metrics[key];
    else if (tweet.public_metrics && tweet.public_metrics[key] !== undefined) val = tweet.public_metrics[key];
    else if (tweet.organic_metrics && tweet.organic_metrics[key] !== undefined) val = tweet.organic_metrics[key];

    return val || 0;
}

function renderProfile(user) {
    const template = document.getElementById('profile-template').content.cloneNode(true);

    // Replace high-res image if available (normal -> 400x400)
    const imgUrl = user.profile_image_url ? user.profile_image_url.replace('_normal', '_400x400') : '';

    template.querySelector('.profile-img').src = imgUrl;
    template.querySelector('.name').textContent = user.name;
    template.querySelector('.handle').textContent = `@${user.username}`;
    template.querySelector('.bio').textContent = user.description;

    const date = new Date(user.created_at);
    template.querySelector('.date').textContent = date.toLocaleDateString(undefined, { month: 'long', year: 'numeric' });

    const profileSection = document.getElementById('profile-section');
    profileSection.innerHTML = '';
    profileSection.appendChild(template);
}

function renderStats(metrics) {
    const statsSection = document.getElementById('stats-section');
    statsSection.innerHTML = '';

    const stats = [
        { label: 'Followers', value: metrics.followers_count },
        { label: 'Following', value: metrics.following_count },
        { label: 'Tweets', value: metrics.tweet_count },
        { label: 'Listed', value: metrics.listed_count }
    ];

    stats.forEach(stat => {
        const card = document.createElement('div');
        card.className = 'stat-card';
        card.innerHTML = `
            <div class="stat-value">${formatNumber(stat.value)}</div>
            <div class="stat-label">${stat.label}</div>
        `;
        statsSection.appendChild(card);
    });
}

function renderTweets(tweets, criteria = 'latest') {
    const tweetsList = document.getElementById('tweets-list');
    tweetsList.innerHTML = '';

    if (!tweets || tweets.length === 0) {
        tweetsList.innerHTML = '<p style="text-align:center; color:var(--text-secondary);">No tweets found.</p>';
        return;
    }

    tweets.forEach((tweet, index) => {
        const div = document.createElement('div');
        div.className = 'tweet-item';

        // Highlight top 3 if custom sort
        if (criteria !== 'latest' && index < 3) {
            div.classList.add('top-performer');
            div.innerHTML += `<div style="font-size:0.8rem; color:var(--accent-color); margin-bottom:0.5rem;"><i class="fas fa-trophy"></i> #${index + 1} Best Performer</div>`;
        }

        const metrics = tweet.public_metrics || {};
        const impressionCount = getMetric(tweet, 'impression_count');

        // Highlight the metric being sorted by
        const getStyle = (key) => (criteria === key || (criteria === 'impressions' && key === 'impression_count')) ? 'highlight' : '';

        div.innerHTML += `
            <div class="tweet-text">${linkify(tweet.text)}</div>
            <div class="tweet-metrics">
                <span class="metric ${getStyle('impression_count')}" title="Impressions"><i class="far fa-eye"></i> ${formatNumber(impressionCount)}</span>
                <span class="metric ${getStyle('likes')}" title="Likes"><i class="far fa-heart"></i> ${formatNumber(metrics.like_count || 0)}</span>
                <span class="metric ${getStyle('retweets')}" title="Retweets"><i class="fas fa-retweet"></i> ${formatNumber(metrics.retweet_count || 0)}</span>
                <span class="metric" title="Replies"><i class="far fa-comment"></i> ${formatNumber(metrics.reply_count || 0)}</span>
                <span class="metric" title="Date" style="margin-left:auto; font-size:0.75rem;">${new Date(tweet.created_at).toLocaleDateString()}</span>
            </div>
        `;
        tweetsList.appendChild(div);
    });
}

function formatNumber(num) {
    return new Intl.NumberFormat('en-US', { notation: "compact", compactDisplay: "short" }).format(num);
}

function linkify(text) {
    // Simple linkify for URLs and hashtags
    return text
        .replace(/(https?:\/\/[^\s]+)/g, '<a href="$1" target="_blank" style="color:var(--accent-color);text-decoration:none;">$1</a>')
        .replace(/#(\w+)/g, '<span style="color:var(--accent-color);">#$1</span>')
        .replace(/@(\w+)/g, '<span style="color:var(--accent-color);">@$1</span>');
}

function renderChart(historyData) {
    if (!historyData || historyData.length === 0) return;

    const ctx = document.getElementById('growthChart').getContext('2d');

    // Sort by date just in case
    historyData.sort((a, b) => new Date(a.date) - new Date(b.date));

    // Limit to last 30 entries
    const recentData = historyData.slice(-30);

    const labels = recentData.map(d => d.date);
    const followers = recentData.map(d => d.followers);

    // Gradient fill
    const gradient = ctx.createLinearGradient(0, 0, 0, 400);
    gradient.addColorStop(0, 'rgba(29, 155, 240, 0.5)');
    gradient.addColorStop(1, 'rgba(29, 155, 240, 0.0)');

    new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [{
                label: 'Followers',
                data: followers,
                borderColor: '#1d9bf0',
                backgroundColor: gradient,
                borderWidth: 2,
                fill: true,
                tension: 0.4,
                pointRadius: 4,
                pointHoverRadius: 6,
                pointBackgroundColor: '#1d9bf0'
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    display: false
                },
                tooltip: {
                    mode: 'index',
                    intersect: false,
                    backgroundColor: 'rgba(0,0,0,0.8)',
                    titleColor: '#fff',
                    bodyColor: '#fff',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1
                }
            },
            scales: {
                x: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#9ca3af'
                    }
                },
                y: {
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)'
                    },
                    ticks: {
                        color: '#9ca3af'
                    }
                }
            },
            interaction: {
                mode: 'nearest',
                axis: 'x',
                intersect: false
            }
        }
    });
}
