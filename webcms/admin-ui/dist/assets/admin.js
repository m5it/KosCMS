const API = '/api/v1/admin';

const menuGroups = [
  { title: 'Content', items: [
    { path: 'dashboard', label: 'Dashboard', icon: '📊' },
    { path: 'content', label: 'Pages & Posts', icon: '📝' },
    { path: 'media', label: 'Media', icon: '🖼️' }
  ]},
  { title: 'Design', items: [
    { path: 'templates', label: 'Templates', icon: '📄' },
    { path: 'themes', label: 'Themes', icon: '🎨' },
    { path: 'plugins', label: 'Plugins', icon: '🔌' }
  ]},
  { title: 'Access', items: [
    { path: 'users', label: 'Users', icon: '👤' },
    { path: 'roles', label: 'Roles', icon: '🛡️' },
    { path: 'settings', label: 'Settings', icon: '⚙️' }
  ]},
  { title: 'Operations', items: [
    { path: 'cache', label: 'Cache', icon: '⚡' },
    { path: 'backups', label: 'Backups', icon: '💾' },
    { path: 'workflows', label: 'Workflows', icon: '🔁' },
    { path: 'tenants', label: 'Tenants', icon: '🏢' },
    { path: 'search', label: 'Search', icon: '🔍' },
    { path: 'notifications', label: 'Notifications', icon: '🔔' }
  ]}
];

function currentRoute() { return location.hash.slice(1) || 'dashboard'; }

function escapeHtml(text) {
  return String(text).replace(/[&<>"']/g, function(m) {
    return ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[m]);
  });
}

function renderNav() {
  var html = '';
  for (var gi = 0; gi < menuGroups.length; gi++) {
    var g = menuGroups[gi];
    html += '<div class="nav-group"><h4>' + escapeHtml(g.title) + '</h4><ul>';
    for (var ii = 0; ii < g.items.length; ii++) {
      var i = g.items[ii];
      var active = currentRoute() === i.path ? 'active' : '';
      html += '<li><a href="#' + i.path + '" class="' + active + '" onclick="navigate(\'' + i.path + '\')">';
      html += '<span>' + escapeHtml(i.icon) + '</span> ' + escapeHtml(i.label) + '</a></li>';
    }
    html += '</ul></div>';
  }
  document.getElementById('sidebar-nav').innerHTML = html;
}

function breadcrumb() {
  var r = currentRoute();
  document.getElementById('breadcrumb').innerHTML =
    '<a href="#dashboard" onclick="navigate(\'dashboard\')">Admin</a> / ' +
    r.charAt(0).toUpperCase() + r.slice(1);
}

function navigate(route) { location.hash = route; render(); }

function getJson(url) { return fetch(API + url).then(function(r){ return r.json(); }); }
function postJson(url, body) {
  return fetch(API + url, { method: 'POST', headers: {'Content-Type':'application/json'}, body: JSON.stringify(body || {}) })
    .then(function(r){ return r.json(); });
}

function buildTable(cols, rows) {
  var html = '<table class="data-table"><thead><tr>';
  for (var c = 0; c < cols.length; c++) html += '<th>' + escapeHtml(cols[c].label) + '</th>';
  html += '<th>Actions</th></tr></thead><tbody>';
  for (var r = 0; r < rows.length; r++) {
    var row = rows[r];
    html += '<tr>';
    for (var c = 0; c < cols.length; c++) {
      var val = row[cols[c].key];
      html += '<td>' + escapeHtml(val !== undefined ? val : '') + '</td>';
    }
    html += '<td><button class="btn" onclick="alert(\'Edit ' + row.id + '\')">Edit</button></td></tr>';
  }
  html += '</tbody></table>';
  return html;
}

function card(title, value) {
  return '<div class="card"><h3>' + escapeHtml(title) + '</h3><p>' + escapeHtml(value) + '</p></div>';
}

var screens = {
  dashboard: function() {
    return getJson('/dashboard').then(function(data){
      var html = '<h1>Dashboard</h1><div class="dashboard-grid">';
      var widgets = data.widgets || [];
      for (var i = 0; i < widgets.length; i++) {
        var w = widgets[i];
        html += card(w.title, JSON.stringify(w.data, null, 2));
      }
      html += '</div>';
      return html;
    });
  },
  content: function() {
    return getJson('/content').then(function(data){
      var rows = data.content || [];
      return '<h1>Pages & Posts</h1><div class="toolbar"><button class="btn" onclick="alert(\'New content\')">New</button></div>' +
        buildTable([{key:'title',label:'Title'},{key:'type',label:'Type'},{key:'status',label:'Status'}], rows);
    });
  },
  media: function() {
    return getJson('/media').then(function(data){
      var items = data.media || [];
      var html = '<h1>Media</h1><div class="toolbar"><input type="file" id="file" /><button class="btn" onclick="alert(\'Upload\')">Upload</button></div><div class="media-grid">';
      for (var i = 0; i < items.length; i++) {
        var m = items[i];
        html += '<div class="media-card"><p>' + escapeHtml(m.name || '') + '</p><small>' + escapeHtml(m.mime_type || '') + '</small></div>';
      }
      html += '</div>';
      return html;
    });
  },
  templates: function() {
    return getJson('/templates').then(function(data){
      return '<h1>Templates</h1><div class="toolbar"><button class="btn" onclick="alert(\'New template\')">New</button></div>' +
        buildTable([{key:'name',label:'Name'},{key:'path',label:'Path'}], data.templates || []);
    });
  },
  themes: function() {
    return getJson('/themes').then(function(data){
      var items = data.themes || [];
      var html = '<h1>Themes</h1><div class="theme-grid">';
      for (var i = 0; i < items.length; i++) {
        var t = items[i];
        html += '<div class="theme-card ' + (t.active ? 'active' : '') + '"><h3>' + escapeHtml(t.name || '') + '</h3>' +
          '<p>' + escapeHtml(t.description || '') + '</p>' +
          '<button class="btn" onclick="postJson(\'/themes/' + t.id + '/activate\')">Activate</button></div>';
      }
      html += '</div>';
      return html;
    });
  },
  plugins: function() {
    return getJson('/plugins').then(function(data){
      var items = data.plugins || [];
      var html = '<h1>Plugins</h1>';
      for (var i = 0; i < items.length; i++) {
        var p = items[i];
        html += '<div class="plugin-row"><strong>' + escapeHtml(p.name || '') + '</strong>' +
          '<button class="btn" onclick="postJson(\'/plugins/' + p.id + '/' + (p.active ? 'deactivate' : 'activate') + '\')">' +
          (p.active ? 'Deactivate' : 'Activate') + '</button></div>';
      }
      return html;
    });
  },
  users: function() {
    return getJson('/users').then(function(data){
      return '<h1>Users</h1><div class="toolbar"><button class="btn" onclick="alert(\'New user\')">New User</button></div>' +
        buildTable([{key:'username',label:'Username'},{key:'email',label:'Email'},{key:'role',label:'Role'},{key:'is_active',label:'Active'}], data.users || []);
    });
  },
  roles: function() {
    return getJson('/roles').then(function(data){
      var items = data.roles || [];
      var html = '<h1>Roles</h1>';
      for (var i = 0; i < items.length; i++) {
        var r = items[i];
        var perms = (r.permissions || []).join(', ');
        html += '<div class="plugin-row"><strong>' + escapeHtml(r.name || '') + '</strong><span>' + escapeHtml(perms) + '</span></div>';
      }
      return html;
    });
  },
  settings: function() {
    return getJson('/settings').then(function(data){
      var s = data.settings || {};
      return '<h1>Settings</h1><div class="settings-group"><h3>Site</h3>' +
        '<div class="form-grid"><label>Site Name</label><input value="' + escapeHtml(s.site_name || '') + '" /></div>' +
        '<div class="form-actions"><button class="btn" onclick="alert(\'Saved\')">Save</button></div></div>';
    });
  },
  cache: function() {
    return getJson('/cache/stats').then(function(data){
      return '<h1>Cache</h1><div class="dashboard-grid">' +
        card('Keys', data.keys || 0) + card('Hit Rate', (data.hit_rate || 0) + '%') + card('Memory', data.memory || 0) +
        '</div><div class="form-actions">' +
        '<button class="btn" onclick="postJson(\'/cache/warm\')">Warm</button>' +
        '<button class="btn btn-secondary" onclick="postJson(\'/cache/invalidate\', {pattern:\'*\'})">Flush</button></div>';
    });
  },
  backups: function() {
    return getJson('/backups').then(function(data){
      return '<h1>Backups</h1><div class="form-actions"><button class="btn" onclick="postJson(\'/backups\')">Create</button></div>' +
        buildTable([{key:'id',label:'ID'},{key:'created_at',label:'Created'},{key:'size',label:'Size'}], data.backups || []);
    });
  },
  workflows: function() {
    return getJson('/workflows/instances').then(function(data){
      var items = data.instances || [];
      var html = '<h1>Workflows</h1>';
      for (var i = 0; i < items.length; i++) {
        var inst = items[i];
        html += '<div class="workflow-row"><strong>' + escapeHtml(inst.content_title || '') + '</strong>' +
          '<span class="status-badge">' + escapeHtml(inst.state || '') + '</span></div>';
      }
      return html;
    });
  },
  tenants: function() {
    return getJson('/tenants').then(function(data){
      return '<h1>Tenants</h1><div class="toolbar"><button class="btn" onclick="alert(\'New tenant\')">New</button></div>' +
        buildTable([{key:'name',label:'Name'},{key:'domain',label:'Domain'},{key:'active',label:'Active'}], data.tenants || []);
    });
  },
  search: function() {
    return getJson('/search/analytics').then(function(data){
      return '<h1>Search</h1><div class="dashboard-grid">' +
        card('Queries 24h', data.queries_24h || 0) + card('Top Query', data.top_query || '—') +
        '</div>';
    });
  },
  notifications: function() {
    return getJson('/notifications/queue').then(function(data){
      return '<h1>Notifications</h1><div class="dashboard-grid">' +
        card('Pending', data.pending || 0) + card('Sent 24h', data.sent_24h || 0) +
        '</div><div class="form-actions">' +
        '<button class="btn" onclick="postJson(\'/notifications/send\')">Send Test</button>' +
        '<button class="btn btn-secondary" onclick="postJson(\'/notifications/digest\')">Trigger Digest</button></div>';
    });
  }
};

function render() {
  try {
    renderNav();
    breadcrumb();
    var route = currentRoute();
    var screen = screens[route] || screens.dashboard;
    screen().then(function(html){
      document.getElementById('content').innerHTML = html;
    }).catch(function(err){
      document.getElementById('content').innerHTML = '<div class="error-box">Error loading ' + route + ': ' + escapeHtml(err.message) + '</div>';
    });
  } catch (err) {
    document.getElementById('content').innerHTML = '<div class="error-box">Render error: ' + escapeHtml(err.message) + '</div>';
  }
}

window.addEventListener('hashchange', render);
window.addEventListener('DOMContentLoaded', render);
