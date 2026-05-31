document.addEventListener('DOMContentLoaded', () => {
    const socket = io();
    let vehiclesData = [];
    let logsData = [];
    let searchTerm = '';

    window.loadVehicles = function () {
        fetch('/api/vehicles')
            .then(r => r.json())
            .then(data => {
                vehiclesData = data;
                renderVehicles(data);
                updateStats(data);
            })
            .catch(() => {
                document.getElementById('vehicles-tbody').innerHTML =
                    `<tr><td colspan="8" class="table-loading" style="color:var(--danger);">
                        <i class="fa-solid fa-triangle-exclamation"></i> Erreur de chargement
                    </td></tr>`;
            });
    };

    function renderVehicles(data) {
        const term = searchTerm.toLowerCase();
        const filtered = data.filter(v =>
            (v.owner_name || '').toLowerCase().includes(term) ||
            (v.plaque_immatriculation || '').toLowerCase().includes(term) ||
            (v.phone || '').toLowerCase().includes(term)
        );

        const tbody = document.getElementById('vehicles-tbody');
        if (filtered.length === 0) {
            tbody.innerHTML = `<tr><td colspan="8" class="table-loading" style="color:var(--text-muted);">
                <i class="fa-solid fa-car-burst"></i> Aucun véhicule trouvé
            </td></tr>`;
            return;
        }

        tbody.innerHTML = '';
        filtered.forEach(v => {
            const isPaid = v.is_paid === 1;
            const tr = document.createElement('tr');
            tr.id = `vehicle-row-${v.id}`;
            tr.innerHTML = `
                <td style="color:var(--text-muted); font-size:12px;">#${v.id}</td>
                <td>
                    <div style="font-weight:600;">${escHtml(v.owner_name)}</div>
                    ${v.phone ? `<div style="font-size:12px; color:var(--text-muted);">${escHtml(v.phone)}</div>` : ''}
                </td>
                <td><span class="plate-badge">${escHtml(v.plaque_immatriculation)}</span></td>
                <td style="color:var(--text-muted);">${escHtml(v.phone || '—')}</td>
                <td>
                    <select class="status-select" onchange="changeStatus(${v.id}, this.value)" style="padding:4px; border-radius:4px; font-size:12px; background:rgba(255,255,255,0.1); color:white; border:none;">
                        <option value="normal" ${v.status === 'normal' ? 'selected' : ''}>Normal</option>
                        <option value="whitelist" ${v.status === 'whitelist' ? 'selected' : ''}>Liste Blanche</option>
                        <option value="blacklist" ${v.status === 'blacklist' ? 'selected' : ''}>Liste Noire</option>
                    </select>
                </td>
                <td>
                    <span class="status-badge ${isPaid ? 'paid' : 'unpaid'}">
                        <i class="fa-solid ${isPaid ? 'fa-circle-check' : 'fa-clock'}"></i>
                        ${isPaid ? 'Payé' : 'En attente'}
                    </span>
                    ${v.payment_date ? `<br><span style="font-size:11px; color:var(--text-muted);">${formatDate(v.payment_date)}</span>` : ''}
                </td>
                <td>
                    <div class="action-btns">
                        ${isPaid
                            ? `<button class="btn-action unpay" title="Marquer impayé" onclick="togglePay(${v.id}, false)">
                                 <i class="fa-solid fa-clock"></i>
                               </button>`
                            : `<button class="btn-action pay" title="Marquer payé" onclick="togglePay(${v.id}, true)">
                                 <i class="fa-solid fa-check"></i>
                               </button>`
                        }
                        <button class="btn-action del" title="Supprimer" onclick="deleteVehicle(${v.id})">
                            <i class="fa-solid fa-trash"></i>
                        </button>
                    </div>
                </td>`;
            tbody.appendChild(tr);
        });
    }

    function updateStats(data) {
        const total = data.length;
        const paid = data.filter(v => v.is_paid === 1).length;
        const unpaid = total - paid;

        document.getElementById('stat-total').textContent = total;
        document.getElementById('stat-paid').textContent = paid;
        document.getElementById('stat-unpaid').textContent = unpaid;
        document.getElementById('sb-total').textContent = total;
        document.getElementById('sb-paid').textContent = paid;
        document.getElementById('sb-unpaid').textContent = unpaid;
    }

    window.togglePay = function (id, pay) {
        const endpoint = pay ? `/api/vehicles/${id}/pay` : `/api/vehicles/${id}/unpay`;
        fetch(endpoint, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ amount: 2500 })
        })
        .then(r => r.json())
        .then(data => {
            if (data.success) {
                showToast(pay ? '✅ Marqué comme payé' : '⏳ Marqué comme non payé', 'success');
                loadVehicles();
            } else {
                showToast(data.error || 'Erreur', 'error');
            }
        });
    };

    window.deleteVehicle = function (id) {
        if (!confirm('Supprimer ce véhicule du parking ?')) return;
        fetch(`/api/vehicles/${id}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    showToast('Véhicule supprimé', 'success');
                    loadVehicles();
                } else {
                    showToast(data.error || 'Erreur', 'error');
                }
            });
    };

    window.changeStatus = function (id, status) {
        fetch(`/api/vehicles/${id}/status`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ status })
        }).then(r => r.json()).then(data => {
            if (data.success) {
                showToast('Statut mis à jour', 'success');
            } else {
                showToast(data.error || 'Erreur', 'error');
            }
        });
    };

    window.controlGate = function(action) {
        const command = action === 'open' ? 'GATE:OPEN' : 'GATE:CLOSE';
        fetch('/api/arduino/command', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ command })
        }).then(r => r.json()).then(data => {
            if (data.success) {
                showToast(action === 'open' ? 'Ouverture...' : 'Fermeture...', 'info');
            }
        });
    };

    window.loadLogs = function () {
        fetch('/api/access-logs')
            .then(r => r.json())
            .then(logs => {
                logsData = logs;
                renderLogs(logs);
                const today = new Date().toISOString().split('T')[0];
                const todayCount = logs.filter(l => (l.timestamp || '').startsWith(today)).length;
                document.getElementById('stat-today').textContent = todayCount;
            });
    };

    function renderLogs(logs) {
        const tbody = document.getElementById('logs-tbody');
        if (logs.length === 0) {
            tbody.innerHTML = `<tr><td colspan="7" class="table-loading" style="color:var(--text-muted);">
                Aucun accès enregistré
            </td></tr>`;
            return;
        }

        tbody.innerHTML = '';
        logs.forEach(log => {
            const granted = log.access_granted === 1;
            const tr = document.createElement('tr');
            const imgSrc = log.chemin_image ? `/static/${log.chemin_image}` : null;
            tr.innerHTML = `
                <td style="color:var(--text-muted); font-size:12px;">#${log.id}</td>
                <td><span class="plate-badge">${escHtml(log.plaque_immatriculation || 'N/A')}</span></td>
                <td style="font-size:13px; color:var(--text-muted);">${formatDate(log.timestamp)}</td>
                <td>
                    <span class="access-badge ${granted ? 'granted' : 'denied'}">
                        <i class="fa-solid ${granted ? 'fa-door-open' : 'fa-ban'}"></i>
                        ${granted ? 'AUTORISÉ' : 'REFUSÉ'}
                    </span>
                </td>
                <td style="font-size:13px;">${escHtml(log.reason || '—')}</td>
                <td style="font-size:13px; color:var(--text-muted);">${log.distance_cm > 0 ? log.distance_cm + ' cm' : '—'}</td>
                <td>
                    ${imgSrc
                        ? `<img src="${imgSrc}" style="width:60px; height:40px; object-fit:cover; border-radius:6px; border:1px solid rgba(255,255,255,0.1);"
                               onerror="this.style.display='none'" alt="capture">`
                        : '<span style="color:var(--text-muted); font-size:12px;">—</span>'
                    }
                </td>`;
            tbody.appendChild(tr);
        });
    }

    window.switchTab = function (tab) {
        document.getElementById('tab-vehicles').classList.toggle('active', tab === 'vehicles');
        document.getElementById('tab-logs').classList.toggle('active', tab === 'logs');
        document.getElementById('tab-analytics').classList.toggle('active', tab === 'analytics');
        
        document.getElementById('panel-vehicles').style.display = tab === 'vehicles' ? 'flex' : 'none';
        document.getElementById('panel-logs').style.display = tab === 'logs' ? 'flex' : 'none';
        document.getElementById('panel-analytics').style.display = tab === 'analytics' ? 'flex' : 'none';
        
        if (tab === 'logs') loadLogs();
        if (tab === 'analytics') loadAnalytics();
    };

    let chartInstance = null;
    window.loadAnalytics = function() {
        fetch('/api/analytics/peak_hours')
            .then(r => r.json())
            .then(data => {
                const ctx = document.getElementById('occupancyChart');
                if(!ctx) return;
                
                if(chartInstance) {
                    chartInstance.destroy();
                }
                
                chartInstance = new Chart(ctx, {
                    type: 'bar',
                    data: {
                        labels: data.labels,
                        datasets: [{
                            label: 'Passages par heure',
                            data: data.data,
                            backgroundColor: 'rgba(59, 130, 246, 0.5)',
                            borderColor: 'rgba(59, 130, 246, 1)',
                            borderWidth: 1,
                            borderRadius: 4
                        }]
                    },
                    options: {
                        responsive: true,
                        maintainAspectRatio: false,
                        plugins: {
                            legend: { labels: { color: 'rgba(255,255,255,0.7)' } }
                        },
                        scales: {
                            y: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: 'rgba(255,255,255,0.7)' }, beginAtZero: true },
                            x: { grid: { color: 'rgba(255,255,255,0.1)' }, ticks: { color: 'rgba(255,255,255,0.7)' } }
                        }
                    }
                });
            });
    };

    document.getElementById('admin-search').addEventListener('input', (e) => {
        searchTerm = e.target.value;
        renderVehicles(vehiclesData);
    });

    // ---- Live Phone Camera Preview ----
    const adminPhoneDot = document.getElementById('admin-phone-dot');
    const adminPhoneStatus = document.getElementById('admin-phone-status');
    const adminCamCanvas = document.getElementById('admin-cam-canvas');
    const adminCamPlaceholder = document.getElementById('admin-cam-placeholder');

    socket.on('camera_status', (data) => {
        if (data.connected) {
            adminPhoneDot.className = 'status-dot connected';
            adminPhoneStatus.textContent = 'Tél. connecté (Live)';
        } else {
            adminPhoneDot.className = 'status-dot';
            adminPhoneStatus.textContent = 'Tél. déconnecté';
            adminCamCanvas.style.display = 'none';
            adminCamPlaceholder.style.display = 'block';
        }
    });

    socket.on('phone_frame', (data) => {
        if (!data.image) return;
        adminCamCanvas.style.display = 'block';
        adminCamPlaceholder.style.display = 'none';
        const img = new Image();
        img.onload = () => {
            adminCamCanvas.width = img.width;
            adminCamCanvas.height = img.height;
            adminCamCanvas.getContext('2d').drawImage(img, 0, 0);
        };
        img.src = data.image;
    });

    // Load initial camera status
    fetch('/api/camera/status').then(r => r.json()).then(d => {
        if (d.connected) {
            adminPhoneDot.className = 'status-dot connected';
            adminPhoneStatus.textContent = 'Tél. connecté (Live)';
        }
    });

    // ---- CSV Export ----
    window.exportCSV = function(type) {
        if (type === 'vehicles') {
            if (!vehiclesData.length) { showToast('Aucune donnée à exporter', 'info'); return; }
            const headers = ['ID', 'Propriétaire', 'Plaque', 'Téléphone', 'Statut', 'Payé', 'Date Paiement'];
            const rows = vehiclesData.map(v => [
                v.id, v.owner_name, v.plaque_immatriculation, v.phone || '',
                v.status, v.is_paid ? 'Oui' : 'Non', v.payment_date || ''
            ]);
            downloadCSV('vehicules_lapi.csv', headers, rows);
        } else if (type === 'logs') {
            if (!logsData.length) { showToast('Aucun journal à exporter', 'info'); return; }
            const headers = ['ID', 'Plaque', 'Horodatage', 'Décision', 'Raison', 'Distance (cm)'];
            const rows = logsData.map(l => [
                l.id, l.plaque_immatriculation, l.timestamp,
                l.access_granted ? 'AUTORISÉ' : 'REFUSÉ',
                l.reason || '', l.distance_cm || ''
            ]);
            downloadCSV('journal_acces_lapi.csv', headers, rows);
        }
    };

    function downloadCSV(filename, headers, rows) {
        const BOM = '\uFEFF';
        const csv = BOM + [headers, ...rows].map(r =>
            r.map(c => `"${String(c).replace(/"/g, '""')}"`).join(',')
        ).join('\n');
        const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' });
        const link = document.createElement('a');
        link.href = URL.createObjectURL(blob);
        link.download = filename;
        link.click();
        showToast(`Exporté : ${filename}`, 'success');
    }

    socket.on('vehicle_registered', () => loadVehicles());
    socket.on('vehicle_updated', () => loadVehicles());
    socket.on('vehicle_deleted', () => loadVehicles());
    socket.on('gate_result', () => {
        if (document.getElementById('tab-logs').classList.contains('active')) loadLogs();
        const cur = parseInt(document.getElementById('stat-today').textContent || '0');
        document.getElementById('stat-today').textContent = cur + 1;
    });

    function escHtml(str) {
        if (!str) return '';
        return String(str).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
    }

    function formatDate(dateStr) {
        if (!dateStr) return '—';
        const d = new Date(dateStr.replace(' ', 'T'));
        if (isNaN(d)) return dateStr;
        return d.toLocaleDateString('fr-DZ', { day: '2-digit', month: '2-digit', year: 'numeric' })
            + ' ' + d.toLocaleTimeString('fr-DZ', { hour: '2-digit', minute: '2-digit' });
    }

    window.showToast = function (msg, type = 'info') {
        const toast = document.getElementById('toast');
        toast.textContent = msg;
        toast.className = `toast ${type} show`;
        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => toast.className = `toast ${type}`, 3000);
    };

    loadVehicles();
    loadLogs();
});
