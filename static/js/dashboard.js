/**
 * Dashboard functionality
 */

// Chart instances for later updating
let activeUsersChart;
let trafficSourcesChart;
let campaignPerformanceChart;

// Initialize charts when page loads
document.addEventListener('DOMContentLoaded', async function() {
    // Check authentication status first
    const authenticated = await checkAuthStatus();
    
    if (authenticated) {
        initializeCharts();
    }
});

/**
 * Initialize all dashboard charts
 */
async function initializeCharts() {
    // Default to 30 days
    const days = 30;
    
    // Initialize charts in parallel
    await Promise.all([
        initActiveUsersChart(days),
        initTrafficSourcesChart(days),
        initCampaignPerformanceChart(days)
    ]);
}

/**
 * Update all charts when date range changes
 */
async function updateCharts(days) {
    // Update all charts with new data
    await Promise.all([
        updateActiveUsersChart(days),
        updateTrafficSourcesChart(days),
        updateCampaignPerformanceChart(days)
    ]);
}

/**
 * Initialize Active Users chart
 */
async function initActiveUsersChart(days) {
    try {
        // Fetch active users data
        const response = await fetch(`/api/analytics/active-users?days=${days}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }
        
        // Format the data
        const data = result.data;
        
        // Sort data by date
        data.sort((a, b) => {
            return new Date(formatDateString(a.date)) - new Date(formatDateString(b.date));
        });
        
        // Extract data for chart
        const dates = data.map(item => formatDate(item.date));
        const activeUsers = data.map(item => item.activeUsers);
        const newUsers = data.map(item => item.newUsers);
        
        // Get canvas context
        const ctx = document.getElementById('active-users-chart').getContext('2d');
        
        // Create chart
        activeUsersChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: dates,
                datasets: [
                    {
                        label: 'Active Users',
                        data: activeUsers,
                        borderColor: '#4a6bef',
                        backgroundColor: 'rgba(74, 107, 239, 0.1)',
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'New Users',
                        data: newUsers,
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    },
                    title: {
                        display: false
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize active users chart:', error);
        const container = document.getElementById('active-users-chart').parentNode;
        container.innerHTML = `<div class="error-message">Failed to load chart: ${error.message}</div>`;
    }
}

/**
 * Initialize Traffic Sources chart
 */
async function initTrafficSourcesChart(days) {
    try {
        // Fetch traffic sources data
        const response = await fetch(`/api/analytics/traffic-sources?days=${days}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }
        
        // Format the data
        const data = result.data;
        
        // Sort data by sessions (descending)
        data.sort((a, b) => b.sessions - a.sessions);
        
        // Get top 8 sources
        const topSources = data.slice(0, 8);
        
        // Extract data for chart
        const sources = topSources.map(item => item.sessionSource || 'Direct');
        const sessions = topSources.map(item => item.sessions);
        
        // Get canvas context
        const ctx = document.getElementById('traffic-sources-chart').getContext('2d');
        
        // Colors for chart
        const colors = [
            '#4a6bef', '#28a745', '#dc3545', '#ffc107',
            '#17a2b8', '#6c757d', '#6f42c1', '#fd7e14'
        ];
        
        // Create chart
        trafficSourcesChart = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: sources,
                datasets: [{
                    data: sessions,
                    backgroundColor: colors,
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'right',
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize traffic sources chart:', error);
        const container = document.getElementById('traffic-sources-chart').parentNode;
        container.innerHTML = `<div class="error-message">Failed to load chart: ${error.message}</div>`;
    }
}

/**
 * Initialize Campaign Performance chart
 */
async function initCampaignPerformanceChart(days) {
    try {
        // Fetch campaign data
        const response = await fetch(`/api/analytics/ads/campaigns?days=${days}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }
        
        // Format the data
        const data = result.data;
        
        // Sort data by impressions (descending)
        data.sort((a, b) => b.impressions - a.impressions);
        
        // Get top 10 campaigns
        const topCampaigns = data.slice(0, 10);
        
        // Extract data for chart
        const campaigns = topCampaigns.map(item => item.campaign_name);
        const impressions = topCampaigns.map(item => item.impressions);
        const clicks = topCampaigns.map(item => item.clicks);
        const conversions = topCampaigns.map(item => item.conversions);
        
        // Get canvas context
        const ctx = document.getElementById('campaign-performance-chart').getContext('2d');
        
        // Create chart
        campaignPerformanceChart = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: campaigns,
                datasets: [
                    {
                        label: 'Impressions',
                        data: impressions,
                        backgroundColor: 'rgba(74, 107, 239, 0.7)',
                        order: 3
                    },
                    {
                        label: 'Clicks',
                        data: clicks,
                        backgroundColor: 'rgba(40, 167, 69, 0.7)',
                        order: 2
                    },
                    {
                        label: 'Conversions',
                        data: conversions,
                        backgroundColor: 'rgba(220, 53, 69, 0.7)',
                        order: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top',
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        grid: {
                            drawBorder: false
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Failed to initialize campaign performance chart:', error);
        const container = document.getElementById('campaign-performance-chart').parentNode;
        container.innerHTML = `<div class="error-message">Failed to load chart: ${error.message}</div>`;
    }
}

/**
 * Update Active Users chart
 */
async function updateActiveUsersChart(days) {
    try {
        // Fetch new data
        const response = await fetch(`/api/analytics/active-users?days=${days}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }
        
        // Format the data
        const data = result.data;
        
        // Sort data by date
        data.sort((a, b) => {
            return new Date(formatDateString(a.date)) - new Date(formatDateString(b.date));
        });
        
        // Extract data for chart
        const dates = data.map(item => formatDate(item.date));
        const activeUsers = data.map(item => item.activeUsers);
        const newUsers = data.map(item => item.newUsers);
        
        // Update chart data
        activeUsersChart.data.labels = dates;
        activeUsersChart.data.datasets[0].data = activeUsers;
        activeUsersChart.data.datasets[1].data = newUsers;
        
        // Update chart
        activeUsersChart.update();
    } catch (error) {
        console.error('Failed to update active users chart:', error);
    }
}

/**
 * Update Traffic Sources chart
 */
async function updateTrafficSourcesChart(days) {
    try {
        // Fetch new data
        const response = await fetch(`/api/analytics/traffic-sources?days=${days}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }
        
        // Format the data
        const data = result.data;
        
        // Sort data by sessions (descending)
        data.sort((a, b) => b.sessions - a.sessions);
        
        // Get top 8 sources
        const topSources = data.slice(0, 8);
        
        // Extract data for chart
        const sources = topSources.map(item => item.sessionSource || 'Direct');
        const sessions = topSources.map(item => item.sessions);
        
        // Update chart data
        trafficSourcesChart.data.labels = sources;
        trafficSourcesChart.data.datasets[0].data = sessions;
        
        // Update chart
        trafficSourcesChart.update();
    } catch (error) {
        console.error('Failed to update traffic sources chart:', error);
    }
}

/**
 * Update Campaign Performance chart
 */
async function updateCampaignPerformanceChart(days) {
    try {
        // Fetch new data
        const response = await fetch(`/api/analytics/ads/campaigns?days=${days}`);
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error);
        }
        
        // Format the data
        const data = result.data;
        
        // Sort data by impressions (descending)
        data.sort((a, b) => b.impressions - a.impressions);
        
        // Get top 10 campaigns
        const topCampaigns = data.slice(0, 10);
        
        // Extract data for chart
        const campaigns = topCampaigns.map(item => item.campaign_name);
        const impressions = topCampaigns.map(item => item.impressions);
        const clicks = topCampaigns.map(item => item.clicks);
        const conversions = topCampaigns.map(item => item.conversions);
        
        // Update chart data
        campaignPerformanceChart.data.labels = campaigns;
        campaignPerformanceChart.data.datasets[0].data = impressions;
        campaignPerformanceChart.data.datasets[1].data = clicks;
        campaignPerformanceChart.data.datasets[2].data = conversions;
        
        // Update chart
        campaignPerformanceChart.update();
    } catch (error) {
        console.error('Failed to update campaign performance chart:', error);
    }
}

/**
 * Helper function to format date from YYYYmmdd to readable format
 */
function formatDate(dateString) {
    // Convert from YYYYmmdd to YYYY-mm-dd
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    
    // Create date object
    const date = new Date(`${year}-${month}-${day}`);
    
    // Format to readable string
    return date.toLocaleDateString('en-US', { 
        month: 'short', 
        day: 'numeric'
    });
}

/**
 * Helper function to format date from YYYYmmdd to YYYY-mm-dd
 */
function formatDateString(dateString) {
    const year = dateString.substring(0, 4);
    const month = dateString.substring(4, 6);
    const day = dateString.substring(6, 8);
    
    return `${year}-${month}-${day}`;
}