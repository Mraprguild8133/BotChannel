// Bot Admin Panel JavaScript
class BotAdmin {
    constructor() {
        this.init();
        this.setupEventListeners();
        this.startAutoRefresh();
    }

    init() {
        console.log('Bot Admin Panel initialized');
        this.loadInitialData();
        this.animateCounters();
    }

    setupEventListeners() {
        // Refresh buttons
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('refresh-btn')) {
                this.refreshData();
            }

            if (e.target.classList.contains('btn-action')) {
                this.handleAction(e.target.dataset.action, e.target.dataset.id);
            }
        });

        // Auto-refresh toggle
        const autoRefreshToggle = document.getElementById('autoRefresh');
        if (autoRefreshToggle) {
            autoRefreshToggle.addEventListener('change', (e) => {
                if (e.target.checked) {
                    this.startAutoRefresh();
                } else {
                    this.stopAutoRefresh();
                }
            });
        }

        // Search functionality
        const searchInput = document.getElementById('searchInput');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => {
                this.filterTable(e.target.value);
            });
        }
    }

    async loadInitialData() {
        try {
            await this.fetchBotStats();
            await this.fetchChannels();
            await this.fetchAdmins();
            await this.fetchKeywords();
        } catch (error) {
            console.error('Error loading initial data:', error);
            this.showNotification('Error loading data', 'error');
        }
    }

    async fetchBotStats() {
        try {
            const response = await fetch('/api/stats');
            if (response.ok) {
                const stats = await response.json();
                this.updateStats(stats);
            }
        } catch (error) {
            console.error('Error fetching stats:', error);
        }
    }

    async fetchChannels() {
        try {
            const response = await fetch('/api/channels');
            if (response.ok) {
                const channels = await response.json();
                this.updateChannelsTable(channels);
            }
        } catch (error) {
            console.error('Error fetching channels:', error);
        }
    }

    async fetchAdmins() {
        try {
            const response = await fetch('/api/admins');
            if (response.ok) {
                const admins = await response.json();
                this.updateAdminsTable(admins);
            }
        } catch (error) {
            console.error('Error fetching admins:', error);
        }
    }

    async fetchKeywords() {
        try {
            const response = await fetch('/api/keywords');
            if (response.ok) {
                const keywords = await response.json();
                this.updateKeywordsTable(keywords);
            }
        } catch (error) {
            console.error('Error fetching keywords:', error);
        }
    }

    updateStats(stats) {
        const elements = {
            'total-admins': stats.total_admins || 0,
            'total-channels': stats.total_channels || 0,
            'total-keywords': stats.total_keywords || 0,
            'total-members': this.formatNumber(stats.total_members || 0),
            'avg-members': Math.round(stats.avg_members_per_channel || 0)
        };

        Object.entries(elements).forEach(([id, value]) => {
            const element = document.getElementById(id);
            if (element) {
                element.textContent = value;
            }
        });

        // Update progress bars
        this.updateProgressBar('channels-progress', stats.total_channels, 100);
        this.updateProgressBar('keywords-progress', stats.total_keywords, 50);
    }

    updateProgressBar(id, value, max) {
        const progressBar = document.getElementById(id);
        if (progressBar) {
            const percentage = Math.min((value / max) * 100, 100);
            progressBar.style.width = `${percentage}%`;
        }
    }

    updateChannelsTable(channels) {
        const tbody = document.getElementById('channels-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        channels.forEach(channel => {
            const row = document.createElement('tr');
            row.className = 'fade-in';
            row.innerHTML = `
                <td>${this.escapeHtml(channel.channel_name || 'Unknown')}</td>
                <td>@${this.escapeHtml(channel.channel_username || 'N/A')}</td>
                <td>${this.formatNumber(channel.member_count || 0)}</td>
                <td>
                    <span class="status-badge ${channel.is_active ? 'status-active' : 'status-inactive'}">
                        ${channel.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>${this.formatDate(channel.added_at)}</td>
                <td>
                    <button class="btn btn-sm btn-danger btn-action" 
                            data-action="remove-channel" 
                            data-id="${channel.channel_id}">
                        Remove
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateAdminsTable(admins) {
        const tbody = document.getElementById('admins-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        admins.forEach(admin => {
            const row = document.createElement('tr');
            row.className = 'fade-in';
            row.innerHTML = `
                <td>${this.escapeHtml(admin.first_name || 'Unknown')}</td>
                <td>@${this.escapeHtml(admin.username || 'N/A')}</td>
                <td><code>${admin.user_id}</code></td>
                <td>
                    <span class="status-badge ${admin.is_active ? 'status-active' : 'status-inactive'}">
                        ${admin.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>${this.formatDate(admin.added_at)}</td>
                <td>
                    <button class="btn btn-sm btn-danger btn-action" 
                            data-action="remove-admin" 
                            data-id="${admin.user_id}">
                        Remove
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    updateKeywordsTable(keywords) {
        const tbody = document.getElementById('keywords-tbody');
        if (!tbody) return;

        tbody.innerHTML = '';

        keywords.forEach(keyword => {
            const row = document.createElement('tr');
            row.className = 'fade-in';
            row.innerHTML = `
                <td><code>${this.escapeHtml(keyword.keyword)}</code></td>
                <td>${keyword.detection_count || 0}</td>
                <td>
                    <span class="status-badge ${keyword.is_active ? 'status-active' : 'status-inactive'}">
                        ${keyword.is_active ? 'Active' : 'Inactive'}
                    </span>
                </td>
                <td>${this.formatDate(keyword.added_at)}</td>
                <td>
                    <button class="btn btn-sm btn-danger btn-action" 
                            data-action="remove-keyword" 
                            data-id="${keyword.keyword}">
                        Remove
                    </button>
                </td>
            `;
            tbody.appendChild(row);
        });
    }

    async handleAction(action, id) {
        if (!confirm(`Are you sure you want to ${action.replace('-', ' ')}?`)) {
            return;
        }

        try {
            const response = await fetch(`/api/${action}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ id: id })
            });

            if (response.ok) {
                this.showNotification(`Successfully ${action.replace('-', ' ')}ed`, 'success');
                await this.refreshData();
            } else {
                throw new Error(`Failed to ${action}`);
            }
        } catch (error) {
            console.error(`Error ${action}:`, error);
            this.showNotification(`Error: ${error.message}`, 'error');
        }
    }

    async refreshData() {
        const refreshBtn = document.querySelector('.refresh-btn');
        if (refreshBtn) {
            refreshBtn.innerHTML = '<span class="loading"></span> Refreshing...';
            refreshBtn.disabled = true;
        }

        try {
            await this.loadInitialData();
            this.showNotification('Data refreshed successfully', 'success');
        } catch (error) {
            this.showNotification('Error refreshing data', 'error');
        } finally {
            if (refreshBtn) {
                refreshBtn.innerHTML = '🔄 Refresh';
                refreshBtn.disabled = false;
            }
        }
    }

    startAutoRefresh() {
        this.stopAutoRefresh(); // Clear any existing interval
        this.refreshInterval = setInterval(() => {
            this.refreshData();
        }, 30000); // Refresh every 30 seconds
    }

    stopAutoRefresh() {
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
            this.refreshInterval = null;
        }
    }

    filterTable(searchTerm) {
        const tables = document.querySelectorAll('table tbody tr');
        
        tables.forEach(row => {
            const text = row.textContent.toLowerCase();
            const matches = text.includes(searchTerm.toLowerCase());
            row.style.display = matches ? '' : 'none';
        });
    }

    animateCounters() {
        const counters = document.querySelectorAll('.stat-value');
        
        counters.forEach(counter => {
            const target = parseInt(counter.textContent.replace(/,/g, ''));
            if (isNaN(target)) return;
            
            let current = 0;
            const increment = target / 50;
            const timer = setInterval(() => {
                current += increment;
                if (current >= target) {
                    counter.textContent = this.formatNumber(target);
                    clearInterval(timer);
                } else {
                    counter.textContent = this.formatNumber(Math.floor(current));
                }
            }, 20);
        });
    }

    showNotification(message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `alert alert-${type} fade-in`;
        notification.textContent = message;
        
        const container = document.querySelector('.container');
        if (container) {
            container.insertBefore(notification, container.firstChild);
            
            setTimeout(() => {
                notification.remove();
            }, 5000);
        }
    }

    formatNumber(num) {
        return new Intl.NumberFormat().format(num);
    }

    formatDate(dateString) {
        if (!dateString) return 'N/A';
        
        try {
            const date = new Date(dateString);
            return date.toLocaleDateString();
        } catch (error) {
            return 'Invalid Date';
        }
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
}

// Health check functionality
class HealthCheck {
    constructor() {
        this.checkInterval = null;
        this.startHealthCheck();
    }

    async startHealthCheck() {
        await this.performHealthCheck();
        this.checkInterval = setInterval(() => {
            this.performHealthCheck();
        }, 60000); // Check every minute
    }

    async performHealthCheck() {
        try {
            const response = await fetch('/health');
            const isHealthy = response.ok;
            
            this.updateHealthStatus(isHealthy);
        } catch (error) {
            console.error('Health check failed:', error);
            this.updateHealthStatus(false);
        }
    }

    updateHealthStatus(isHealthy) {
        const statusElement = document.getElementById('health-status');
        const iconElement = document.getElementById('health-icon');
        const messageElement = document.getElementById('health-message');
        
        if (isHealthy) {
            if (statusElement) statusElement.className = 'health-status status-healthy';
            if (iconElement) iconElement.textContent = '✅';
            if (messageElement) messageElement.textContent = 'Bot is Running Smoothly';
        } else {
            if (statusElement) statusElement.className = 'health-status status-unhealthy';
            if (iconElement) iconElement.textContent = '❌';
            if (messageElement) messageElement.textContent = 'Bot Health Check Failed';
        }
    }

    stopHealthCheck() {
        if (this.checkInterval) {
            clearInterval(this.checkInterval);
            this.checkInterval = null;
        }
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Initialize admin panel if on admin page
    if (document.querySelector('.dashboard')) {
        new BotAdmin();
    }
    
    // Initialize health check if on health page
    if (document.querySelector('.health-status')) {
        new HealthCheck();
    }
    
    // Add smooth scrolling to anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function (e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth'
                });
            }
        });
    });
    
    // Add loading states to buttons
    document.addEventListener('click', (e) => {
        if (e.target.classList.contains('btn') && !e.target.disabled) {
            const originalText = e.target.innerHTML;
            e.target.innerHTML = '<span class="loading"></span> Loading...';
            e.target.disabled = true;
            
            setTimeout(() => {
                e.target.innerHTML = originalText;
                e.target.disabled = false;
            }, 2000);
        }
    });
});

// Export for module use
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { BotAdmin, HealthCheck };
}
