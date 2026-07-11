
/**
 * Widget Loader
 * 
 * Loads and renders dashboard widgets for admin panel.
 */

class WidgetLoader {
    constructor(apiBaseUrl = '/api/v1') {
        this.apiUrl = apiBaseUrl;
        this.widgets = new Map();
        this.refreshIntervals = new Map();
    }

    /**
     * Initialize widget loader
     */
    async init() {
        await this.loadWidgets();
        this.setupAutoRefresh();
    }

    /**
     * Load widgets from API
     */
    async loadWidgets() {
        try {
            const response = await fetch(`${this.apiUrl}/admin/widgets`);
            const data = await response.json();
            
            if (data.widgets) {
                this.renderWidgets(data.widgets);
            }
        } catch (error) {
            console.error('Failed to load widgets:', error);
            this.showError('Failed to load widgets');
        }
    }

    /**
     * Render widgets to DOM
     */
    renderWidgets(widgets) {
        const container = document.getElementById('widget-container');
        if (!container) return;

        container.innerHTML = '';
        
        widgets.forEach(widget => {
            const element = this.createWidgetElement(widget);
            container.appendChild(element);
            
            // Store widget reference
            this.widgets.set(widget.config.id, widget);
            
            // Setup refresh if interval set
            if (widget.config.refresh_interval > 0) {
                this.setupWidgetRefresh(widget.config.id, widget.config.refresh_interval);
            }
        });
    }

    /**
     * Create widget DOM element
     */
    createWidgetElement(widget) {
        const div = document.createElement('div');
        div.className = `widget widget-${widget.config.type} widget-position-${widget.config.position}`;
        div.id = `widget-${widget.config.id}`;
        
        div.innerHTML = `
            <div class="widget-header">
                <h3 class="widget-title">${this.escapeHtml(widget.config.title)}</h3>
                <div class="widget-actions">
                    <button class="widget-refresh" data-widget="${widget.config.id}">
                        ↻
                    </button>
                    <button class="widget-collapse" data-widget="${widget.config.id}">
                        −
                    </button>
                </div>
            </div>
            <div class="widget-content">
                ${this.renderWidgetContent(widget)}
            </div>
            <div class="widget-footer">
                <span class="widget-timestamp"></span>
            </div>
        `;

        // Add event listeners
        div.querySelector('.widget-refresh').addEventListener('click', () => {
            this.refreshWidget(widget.config.id);
        });

        div.querySelector('.widget-collapse').addEventListener('click', () => {
            this.toggleWidget(widget.config.id);
        });

        return div;
    }

    /**
     * Render widget content based on type
     */
    renderWidgetContent(widget) {
        const { type, data } = widget;

        switch (type) {
            case 'stats':
                return this.renderStatsWidget(data);
            case 'activity':
                return this.renderActivityWidget(data);
            case 'health':
                return this.renderHealthWidget(data);
            default:
                return `<pre>${JSON.stringify(data, null, 2)}</pre>`;
        }
    }

    /**
     * Render stats widget
     */
    renderStatsWidget(data) {
        if (!data.stats) return '<p>No data</p>';

        const { posts, pages, users, media } = data.stats;
        
        return `
            <div class="stats-grid">
                <div class="stat-item">
                    <span class="stat-value">${posts.total}</span>
                    <span class="stat-label">Posts</span>
                    <span class="stat-sublabel">${posts.published} published</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${pages}</span>
                    <span class="stat-label">Pages</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${users}</span>
                    <span class="stat-label">Users</span>
                </div>
                <div class="stat-item">
                    <span class="stat-value">${media}</span>
                    <span class="stat-label">Media</span>
                </div>
            </div>
        `;
    }

    /**
     * Render activity widget
     */
    renderActivityWidget(data) {
        if (!data.activities || data.activities.length === 0) {
            return '<p>No recent activity</p>';
        }

        const items = data.activities.map(activity => `
            <div class="activity-item">
                <span class="activity-type">${activity.type}</span>
                <span class="activity-action">${activity.action}</span>
                <span class="activity-title">${this.escapeHtml(activity.title)}</span>
                <span class="activity-time">${this.formatTime(activity.time)}</span>
            </div>
        `).join('');

        return `<div class="activity-list">${items}</div>`;
    }

    /**
     * Render health widget
     */
    renderHealthWidget(data) {
        const status = data.status || 'unknown';
        const checks = data.checks || {};
        
        const checkItems = Object.entries(checks).map(([name, check]) => `
            <div class="health-check health-${check.status}">
                <span class="check-name">${name}</span>
                <span class="check-status">${check.status}</span>
                ${check.used_percent !== undefined ? 
                    `<span class="check-value">${check.used_percent}%</span>` : ''}
            </div>
        `).join('');

        return `
            <div class="health-status health-${status}">
                <span class="status-indicator"></span>
                <span class="status-text">${status.toUpperCase()}</span>
            </div>
            <div class="health-checks">${checkItems}</div>
        `;
    }

    /**
     * Refresh single widget
     */
    async refreshWidget(widgetId) {
        const widget = this.widgets.get(widgetId);
        if (!widget) return;

        try {
            const response = await fetch(`${this.apiUrl}/admin/widgets/${widgetId}`);
            const data = await response.json();
            
            const element = document.getElementById(`widget-${widgetId}`);
            if (element) {
                const content = element.querySelector('.widget-content');
                content.innerHTML = this.renderWidgetContent(data);
                
                // Update timestamp
                const timestamp = element.querySelector('.widget-timestamp');
                timestamp.textContent = new Date().toLocaleTimeString();
            }
        } catch (error) {
            console.error(`Failed to refresh widget ${widgetId}:`, error);
        }
    }

    /**
     * Toggle widget collapse
     */
    toggleWidget(widgetId) {
        const element = document.getElementById(`widget-${widgetId}`);
        if (element) {
            element.classList.toggle('collapsed');
        }
    }

    /**
     * Setup auto-refresh for all widgets
     */
    setupAutoRefresh() {
        // Clear existing intervals
        this.refreshIntervals.forEach(interval => clearInterval(interval));
        this.refreshIntervals.clear();
        
        // Setup new intervals
        this.widgets.forEach((widget, id) => {
            if (widget.config.refresh_interval > 0) {
                this.setupWidgetRefresh(id, widget.config.refresh_interval);
            }
        });
    }

    /**
     * Setup refresh for single widget
     */
    setupWidgetRefresh(widgetId, intervalSeconds) {
        const interval = setInterval(() => {
            this.refreshWidget(widgetId);
        }, intervalSeconds * 1000);
        
        this.refreshIntervals.set(widgetId, interval);
    }

    /**
     * Format timestamp
     */
    formatTime(isoTime) {
        const date = new Date(isoTime);
        const now = new Date();
        const diff = (now - date) / 1000; // seconds

        if (diff < 60) return 'just now';
        if (diff < 3600) return `${Math.floor(diff / 60)}m ago`;
        if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
        return date.toLocaleDateString();
    }

    /**
     * Escape HTML
     */
    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }

    /**
     * Show error message
     */
    showError(message) {
        const container = document.getElementById('widget-container');
        if (container) {
            container.innerHTML = `<div class="widget-error">${message}</div>`;
        }
    }

    /**
     * Cleanup
     */
    destroy() {
        this.refreshIntervals.forEach(interval => clearInterval(interval));
        this.refreshIntervals.clear();
        this.widgets.clear();
    }
}

// Export for module systems
if (typeof module !== 'undefined' && module.exports) {
    module.exports = WidgetLoader;
}
