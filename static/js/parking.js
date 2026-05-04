document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const gateArm = document.getElementById('gate-arm');
    const gateBadge = document.getElementById('gate-badge');
    const gateResultPanel = document.getElementById('gate-result-panel');
    const gateFlash = document.getElementById('gate-flash');
    const carIcon = document.getElementById('car-icon');
    const distanceValue = document.getElementById('distance-value');
    const distanceBar = document.getElementById('distance-bar');
    const gaugeArc = document.getElementById('gauge-arc');
    const gaugeNumber = document.getElementById('gauge-number');
    const accessLogList = document.getElementById('access-log-list');
    const arduinoDot = document.getElementById('arduino-dot');
    const arduinoStatusText = document.getElementById('arduino-status-text');
    const portSelect = document.getElementById('port-select');
    const statGranted = document.getElementById('stat-granted');
    const statDenied = document.getElementById('stat-denied');

    let grantedCount = 0;
    let deniedCount = 0;

    document.getElementById('btn-connect').addEventListener('click', () => {
        const port = portSelect.value || null;
        const btn = document.getElementById('btn-connect');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i>';
        btn.disabled = true;

        fetch('/api/arduino/connect', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ port })
        })
        .then(r => r.json())
        .then(data => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-plug"></i> Connecter';
            showToast(data.success ? 'Arduino connecté !' : 'Erreur: ' + data.message, data.success ? 'success' : 'error');
        })
        .catch(() => {
            btn.disabled = false;
            btn.innerHTML = '<i class="fa-solid fa-plug"></i> Connecter';
            showToast('Erreur de connexion', 'error');
        });
    });

    function loadPorts() {
        fetch('/api/arduino/ports')
            .then(r => r.json())
            .then(ports => {
                while (portSelect.options.length > 1) portSelect.remove(1);
                ports.forEach(p => {
                    const opt = document.createElement('option');
                    opt.value = p.device;
                    opt.textContent = `${p.device} — ${p.description}`;
                    portSelect.appendChild(opt);
                });
            });
    }

    fetch('/api/arduino/status')
        .then(r => r.json())
        .then(data => {
            if (data.connected) {
                setArduinoConnected(true, data.port);
                if (data.last_distance > 0) updateDistance(data.last_distance);
            }
        });

    loadPorts();
    setInterval(loadPorts, 10000);

    socket.on('arduino_status', (data) => {
        setArduinoConnected(data.connected, data.port);
        if (data.message) showToast(data.message, data.connected ? 'success' : 'info');
    });

    socket.on('distance_update', (data) => updateDistance(data.distance));

    socket.on('gate_triggered', () => {
        carIcon.classList.add('approaching');
        showProcessing();
        showToast('🚗 Véhicule détecté ! Analyse en cours...', 'info');
    });

    socket.on('gate_result', (data) => {
        carIcon.classList.remove('approaching');
        showGateResult(data);
        addLogEntry(data);
    });

    socket.on('gate_status', (data) => {
        if (data.status === 'open') openGate();
        else closeGate();
    });

    function openGate() {
        gateArm.classList.add('open');
        gateBadge.textContent = 'OUVERTE';
        gateBadge.classList.add('open');
        flashScreen('green');
    }

    function closeGate() {
        gateArm.classList.remove('open');
        gateBadge.textContent = 'FERMÉE';
        gateBadge.classList.remove('open');
    }

    function flashScreen(color) {
        gateFlash.className = `gate-flash flash-${color}`;
        setTimeout(() => gateFlash.className = 'gate-flash', 600);
    }

    function showProcessing() {
        gateResultPanel.innerHTML = `
            <div class="waiting-state">
                <i class="fa-solid fa-spinner fa-spin" style="color:var(--primary); font-size:32px;"></i>
                <p>Analyse de la plaque en cours...</p>
            </div>`;
    }

    function showGateResult(data) {
        const isGranted = data.access;
        const icon = isGranted ? 'fa-door-open' : 'fa-ban';
        const title = isGranted ? 'ACCÈS AUTORISÉ' : 'ACCÈS REFUSÉ';
        const imgSrc = data.image ? `/static/${data.image}` : '';

        gateResultPanel.innerHTML = `
            <div class="result-granted">
                <div class="result-icon-wrap ${isGranted ? 'green' : 'red'}">
                    <i class="fa-solid ${icon}"></i>
                </div>
                <div class="result-info">
                    <h4 style="color: ${isGranted ? 'var(--success)' : 'var(--danger)'};">${title}</h4>
                    <div class="result-plate">${data.plate || 'N/A'}</div>
                    <p>${data.reason || ''}</p>
                    <p style="margin-top:4px; font-size:12px; color:var(--text-muted);">
                        Fiabilité OCR: ${data.reliability || '--'}% &nbsp;|&nbsp; ${data.timestamp || ''}
                    </p>
                </div>
                ${imgSrc ? `<img src="${imgSrc}" class="result-image" alt="capture" onerror="this.style.display='none'">` : ''}
            </div>`;

        if (isGranted) {
            openGate();
            grantedCount++;
            statGranted.textContent = grantedCount;
            setTimeout(closeGate, 8000);
        } else {
            closeGate();
            flashScreen('red');
            deniedCount++;
            statDenied.textContent = deniedCount;
        }
    }

    function updateDistance(distance) {
        if (distance < 0) return;

        distanceValue.textContent = distance + ' cm';
        gaugeNumber.textContent = distance;

        const pct = Math.min(distance / 200, 1) * 100;
        distanceBar.style.width = pct + '%';

        const arcLen = Math.min(distance / 200, 1) * 251;
        gaugeArc.setAttribute('stroke-dasharray', `${arcLen} 251`);

        if (distance < 30) {
            gaugeArc.style.stroke = 'var(--danger)';
            gaugeNumber.style.color = 'var(--danger)';
        } else if (distance < 80) {
            gaugeArc.style.stroke = '#fbbf24';
            gaugeNumber.style.color = '#fbbf24';
        } else {
            gaugeArc.style.stroke = 'var(--primary)';
            gaugeNumber.style.color = 'var(--primary)';
        }
    }

    function addLogEntry(data) {
        if (accessLogList.querySelector('.loading-state')) {
            accessLogList.innerHTML = '';
        }

        const isGranted = data.access;
        const item = document.createElement('div');
        item.className = `log-item ${isGranted ? 'granted' : 'denied'}`;
        const time = data.timestamp ? data.timestamp.split(' ')[1] || data.timestamp : '--:--';
        item.innerHTML = `
            <div class="log-icon">
                <i class="fa-solid ${isGranted ? 'fa-check' : 'fa-xmark'}"></i>
            </div>
            <div>
                <div class="log-plate">${data.plate || 'N/A'}</div>
                <div class="log-reason">${data.reason || ''}</div>
            </div>
            <div class="log-time">${time}</div>`;

        accessLogList.insertBefore(item, accessLogList.firstChild);
        while (accessLogList.children.length > 20) {
            accessLogList.removeChild(accessLogList.lastChild);
        }
    }

    function loadAccessLogs() {
        fetch('/api/access-logs')
            .then(r => r.json())
            .then(logs => {
                if (logs.length === 0) {
                    accessLogList.innerHTML = '<div class="loading-state" style="color:var(--text-muted)">Aucun accès enregistré</div>';
                    return;
                }
                accessLogList.innerHTML = '';
                let granted = 0, denied = 0;
                logs.slice(0, 20).forEach(log => {
                    if (log.access_granted) granted++; else denied++;
                    addLogEntry({
                        access: !!log.access_granted,
                        plate: log.plaque_immatriculation,
                        reason: log.reason,
                        timestamp: log.timestamp
                    });
                });
                grantedCount = granted;
                deniedCount = denied;
                statGranted.textContent = granted;
                statDenied.textContent = denied;
            });
    }
    loadAccessLogs();

    function setArduinoConnected(connected, port) {
        if (connected) {
            arduinoDot.className = 'status-dot connected';
            arduinoStatusText.textContent = `Connecté — ${port || ''}`;
        } else {
            arduinoDot.className = 'status-dot';
            arduinoStatusText.textContent = 'Déconnecté';
        }
    }

    document.getElementById('btn-manual-capture').addEventListener('click', () => {
        const btn = document.getElementById('btn-manual-capture');
        btn.innerHTML = '<i class="fa-solid fa-spinner fa-spin"></i> Capture en cours...';
        btn.disabled = true;
        carIcon.classList.add('approaching');
        showProcessing();

        fetch('/api/gate/capture', { method: 'POST' })
            .then(r => r.json())
            .then(data => {
                carIcon.classList.remove('approaching');
                btn.innerHTML = '<i class="fa-solid fa-camera"></i> Test Manuel (Webcam)';
                btn.disabled = false;

                if (data.success) {
                    showGateResult(data);
                    addLogEntry(data);
                } else {
                    gateResultPanel.innerHTML = `
                        <div class="waiting-state">
                            <i class="fa-solid fa-triangle-exclamation" style="color:var(--danger);"></i>
                            <p style="color:var(--danger);">Erreur: ${data.error || 'Capture échouée'}</p>
                        </div>`;
                    showToast('Erreur de capture: ' + (data.error || ''), 'error');
                }
            })
            .catch(() => {
                carIcon.classList.remove('approaching');
                btn.innerHTML = '<i class="fa-solid fa-camera"></i> Test Manuel (Webcam)';
                btn.disabled = false;
                showToast('Erreur réseau', 'error');
            });
    });

    function showToast(msg, type = 'info') {
        let toast = document.getElementById('toast-notif');
        if (!toast) {
            toast = document.createElement('div');
            toast.id = 'toast-notif';
            toast.className = 'toast';
            document.body.appendChild(toast);
        }
        toast.textContent = msg;
        toast.className = `toast ${type} show`;
        clearTimeout(toast._timer);
        toast._timer = setTimeout(() => toast.className = `toast ${type}`, 3500);
    }
});
