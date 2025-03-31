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
    
    // Initialize charts in parallel with proper error handling
    try {
        await Promise.all([
            initActiveUsersChart(days).catch(handleChartError('active-users-chart')),
            initTrafficSourcesChart(days).catch(handleChartError('traffic-sources-chart')),
            initCampaignPerformanceChart(days).catch(handleChartError('campaign-performance-chart'))
        ]);
    } catch (error) {
        console.error('Error initializing charts:', error);
    }
}

/**
 * Handle chart loading errors
 */
function handleChartError(chartId) {
    return function(error) {
        console.error(`Failed to load ${chartId}:`, error);
        const container = document.getElementById(chartId).parentNode;
        container.innerHTML = `<div class="error-message">Failed to load chart: ${error.message || 'Unknown error'}</div>`;
    };
}

/**
 * Update all charts when date range changes
 */
async function updateCharts(days) {
    // Update all charts with new data
    try {
        await Promise.all([
            updateActiveUsersChart(days).catch(handleChartError('active-users-chart')),
            updateTrafficSourcesChart(days).catch(handleChartError('traffic-sources-chart')),
            updateCampaignPerformanceChart(days).catch(handleChartError('campaign-performance-chart'))
        ]);
    } catch (error) {
        console.error('Error updating charts:', error);
    }
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
            throw new Error(result.error || 'Failed to load active users data');
        }
        
        // Format the data
        const data = result.data || [];
        
        if (data.length === 0) {
            throw new Error('No active users data available');
        }
        
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
        throw error;
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
            throw new Error(result.error || 'Failed to load traffic sources data');
        }
        
        // Format the data
        const data = result.data || [];
        
        if (data.length === 0) {
            throw new Error('No traffic sources data available');
        }
        
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
        throw error;
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
            throw new Error(result.error || 'Failed to load campaign data');
        }
        
        // Format the data
        const data = result.data || [];
        
        if (data.length === 0) {
            throw new Error('No campaign data available');
        }
        
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
        throw error;
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
            throw new Error(result.error || 'Failed to update active users data');
        }
        
        // Format the data
        const data = result.data || [];
        
        if (data.length === 0) {
            throw new Error('No active users data available');
        }
        
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
        throw error;
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
            throw new Error(result.error || 'Failed to update traffic sources data');
        }
        
        // Format the data
        const data = result.data || [];
        
        if (data.length === 0) {
            throw new Error('No traffic sources data available');
        }
        
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
        throw error;
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
            throw new Error(result.error || 'Failed to update campaign data');
        }
        
        // Format the data
        const data = result.data || [];
        
        if (data.length === 0) {
            throw new Error('No campaign data available');
        }
        
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
        throw error;
    }
}

/**
 * Helper function to format date from YYYYmmdd to readable format
 */
function formatDate(dateString) {
    if (!dateString) return '';
    
    try {
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
    } catch (e) {
        console.error('Error formatting date:', dateString, e);
        return dateString; // Return original string if parsing fails
    }
}

/**
 * Helper function to format date from YYYYmmdd to YYYY-mm-dd
 */
function formatDateString(dateString) {
    if (!dateString) return '';
    
    try {
        const year = dateString.substring(0, 4);
        const month = dateString.substring(4, 6);
        const day = dateString.substring(6, 8);
        
        return `${year}-${month}-${day}`;
    } catch (e) {
        console.error('Error formatting date string:', dateString, e);
        return dateString; // Return original string if parsing fails
    }
}
