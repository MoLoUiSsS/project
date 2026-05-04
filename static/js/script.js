document.addEventListener('DOMContentLoaded', () => {
    const socket = io();

    const realtimeFeed = document.getElementById('realtime-feed');
    const plateDetail = document.getElementById('plate-detail');
    const cameraInput = document.getElementById('camera-input');
    const totalCapturesEl = document.getElementById('total-captures');
    const searchInput = document.getElementById('search-plate');
    const groupBySelect = document.getElementById('group-by-select');

    let capturesData = [];

    fetch('/api/captures')
        .then(r => r.json())
        .then(data => {
            capturesData = data;
            refreshDisplay();
            updateStats();
        })
        .catch(() => {
            realtimeFeed.innerHTML = '<div class="empty-state"><p>Erreur lors du chargement de l\'historique.</p></div>';
        });

    socket.on('new_capture', (data) => {
        capturesData.unshift(data);
        refreshDisplay();
        updateStats();
    });

    cameraInput.addEventListener('change', (e) => {
        const file = e.target.files[0];
        if (!file) return;

        const formData = new FormData();
        formData.append('image', file);

        const statusDiv = document.getElementById('upload-status');
        statusDiv.innerHTML = '<p style="color:var(--primary); margin-top:10px; font-weight:600;"><i class="fa-solid fa-spinner fa-spin"></i> Traitement de l\'image par l\'IA OCR...</p>';

        fetch('/upload', { method: 'POST', body: formData })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    statusDiv.innerHTML = '<p style="color:var(--success); margin-top:10px; font-weight:600;"><i class="fa-solid fa-check"></i> Plaque lue avec succès.</p>';
                    setTimeout(() => statusDiv.innerHTML = '', 3000);
                } else {
                    throw new Error(data.error || 'Erreur inconnue');
                }
            })
            .catch(err => {
                statusDiv.innerHTML = `<p style="color:var(--danger); margin-top:10px;"><i class="fa-solid fa-triangle-exclamation"></i> Erreur: ${err.message}</p>`;
            });

        cameraInput.value = '';
    });

    searchInput.addEventListener('input', () => refreshDisplay());
    groupBySelect.addEventListener('change', () => refreshDisplay());

    function refreshDisplay() {
        const term = searchInput.value.toLowerCase();
        const filtered = capturesData.filter(c => {
            const plate = (c.plaque_immatriculation || c.plate || '').toLowerCase();
            return plate.includes(term);
        });

        const groupMode = groupBySelect.value;
        if (groupMode !== 'none') {
            renderGroupedFeed(filtered, groupMode);
        } else {
            renderFeed(filtered);
        }
    }

    function renderGroupedFeed(dataList, groupMode) {
        if (dataList.length === 0) {
            realtimeFeed.innerHTML = '<div class="empty-state"><p>Aucune capture trouvée.</p></div>';
            return;
        }

        realtimeFeed.innerHTML = '';
        const groups = {};

        dataList.forEach(capture => {
            const plateStr = capture.plaque_immatriculation || capture.plate;
            const parsed = parseAlgerianPlate(plateStr);
            let key = 'Inconnue/Non-Standard';
            if (parsed.isValid) {
                if (groupMode === 'wilaya') key = parsed.wilaya;
                if (groupMode === 'year') key = 'Année ' + parsed.year;
                if (groupMode === 'type') key = parsed.type;
            }
            if (!groups[key]) groups[key] = [];
            groups[key].push(capture);
        });

        for (const [groupName, items] of Object.entries(groups).sort()) {
            const groupHeader = document.createElement('div');
            groupHeader.className = 'group-header';
            groupHeader.style = 'padding: 8px 12px; margin-top: 10px; background: rgba(59, 130, 246, 0.2); border-left: 3px solid var(--primary); font-weight: 600; font-size: 14px; border-radius: 4px;';
            groupHeader.innerHTML = `${groupName} <span style="float: right; opacity: 0.7; font-size: 12px;">${items.length} capture(s)</span>`;
            realtimeFeed.appendChild(groupHeader);
            items.forEach(capture => realtimeFeed.appendChild(createItemElement(capture)));
        }
    }

    function renderFeed(dataList) {
        if (dataList.length === 0) {
            realtimeFeed.innerHTML = '<div class="empty-state"><p>Aucune capture trouvée.</p></div>';
            return;
        }
        realtimeFeed.innerHTML = '';
        dataList.forEach(capture => realtimeFeed.appendChild(createItemElement(capture)));
    }

    function createItemElement(capture) {
        const plateStr = capture.plaque_immatriculation || capture.plate;
        const timeStr = capture.date_heure_capture || capture.timestamp;
        const imgStr = capture.chemin_image || capture.image_url;
        const imgSrc = imgStr.startsWith('/') ? imgStr : (imgStr.startsWith('http') ? imgStr : `/static/${imgStr}`);
        const reliability = capture.fiabilite_lecture || capture.reliability;

        let reliabilityClass = 'high';
        if (reliability < 85) reliabilityClass = 'medium';
        if (reliability < 70) reliabilityClass = 'low';

        const item = document.createElement('div');
        item.className = 'capture-item';
        item.innerHTML = `
            <img src="${imgSrc}" class="capture-img-thumb" alt="Car" onerror="this.src='https://via.placeholder.com/60x40?text=Error'">
            <div class="capture-details">
                <div class="plate-number">${plateStr}</div>
                <div class="capture-meta">
                    <span><i class="fa-regular fa-clock"></i> ${String(timeStr).split(' ')[1] || timeStr}</span>
                    <span class="reliability ${reliabilityClass}">${reliability}%</span>
                </div>
            </div>
        `;

        item.addEventListener('click', () => {
            document.querySelectorAll('.capture-item').forEach(el => el.classList.remove('active'));
            item.classList.add('active');
            showDetail(capture, imgSrc, plateStr, timeStr, reliability, reliabilityClass);
        });

        return item;
    }

    function showDetail(capture, imgSrc, plateStr, timeStr, reliability, reliabilityClass) {
        let extraInfoHtml = '';
        const parsed = parseAlgerianPlate(plateStr);
        if (parsed.isValid) {
            extraInfoHtml = `
                <div class="info-item" style="grid-column: span 2; background: rgba(59, 130, 246, 0.1); border: 1px solid rgba(59, 130, 246, 0.3);">
                    <div class="info-label"><i class="fa-solid fa-map-location-dot"></i> Informations Véhicule (Algérie)</div>
                    <div class="info-val" style="color: #60a5fa; font-size: 14px; margin-top:5px;">
                        <strong>Wilaya :</strong> ${parsed.wilaya} <br>
                        <strong>Type :</strong> ${parsed.type} <br>
                        <strong>Année :</strong> ${parsed.year}
                    </div>
                </div>
            `;
        }

        plateDetail.innerHTML = `
            <div class="detail-card">
                <div class="section-header">
                    <h3>Détails de Capture</h3>
                    <div class="actions">
                        <button class="btn-primary" style="padding: 8px 12px; font-size:12px; margin-right: 5px; background: linear-gradient(135deg, #ef4444, #b91c1c);" onclick="deleteCapture(${capture.id_capture || capture.id})"><i class="fa-solid fa-trash"></i> Supprimer</button>
                        <button class="btn-primary" style="padding: 8px 12px; font-size:12px;" onclick="exportToPDF()"><i class="fa-solid fa-download"></i> Exporter PDF</button>
                    </div>
                </div>
                <div class="detail-image-container">
                    <img src="${imgSrc}" alt="Plaque" onerror="this.src='https://via.placeholder.com/400x250?text=Image+Non+Trouvée'">
                    <div class="scan-line"></div>
                </div>
                <div class="plate-extracted">${plateStr}</div>
                <div class="info-grid">
                    ${extraInfoHtml}
                    <div class="info-item">
                        <div class="info-label"><i class="fa-solid fa-calendar"></i> Date et Heure</div>
                        <div class="info-val">${timeStr}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label"><i class="fa-solid fa-bullseye"></i> Fiabilité LAPI</div>
                        <div class="info-val ${reliabilityClass}">${reliability}%</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label"><i class="fa-solid fa-video"></i> Source</div>
                        <div class="info-val">Appareil Mobile #${capture.id_camera || 1}</div>
                    </div>
                    <div class="info-item">
                        <div class="info-label"><i class="fa-solid fa-hashtag"></i> ID Capture</div>
                        <div class="info-val">#${capture.id_capture || capture.id}</div>
                    </div>
                </div>
            </div>
        `;
    }

    function parseAlgerianPlate(plateStr) {
        if (!plateStr) return { isValid: false };
        const parts = plateStr.trim().split(' ');
        if (parts.length !== 3) return { isValid: false };

        const wilayaCode = parts[2];
        const middleCode = parts[1];
        if (middleCode.length !== 3) return { isValid: false };

        const wilayas = {
            "01": "Adrar", "02": "Chlef", "03": "Laghouat", "04": "Oum El Bouaghi", "05": "Batna",
            "06": "Béjaïa", "07": "Biskra", "08": "Béchar", "09": "Blida", "10": "Bouira",
            "11": "Tamanrasset", "12": "Tébessa", "13": "Tlemcen", "14": "Tiaret", "15": "Tizi Ouzou",
            "16": "Alger", "17": "Djelfa", "18": "Jijel", "19": "Sétif", "20": "Saïda",
            "21": "Skikda", "22": "Sidi Bel Abbès", "23": "Annaba", "24": "Guelma", "25": "Constantine",
            "26": "Médéa", "27": "Mostaganem", "28": "M'Sila", "29": "Mascara", "30": "Ouargla",
            "31": "Oran", "32": "El Bayadh", "33": "Illizi", "34": "Bordj Bou Arreridj", "35": "Boumerdès",
            "36": "El Tarf", "37": "Tindouf", "38": "Tissemsilt", "39": "El Oued", "40": "Khenchela",
            "41": "Souk Ahras", "42": "Tipaza", "43": "Mila", "44": "Aïn Defla", "45": "Naâma",
            "46": "Aïn Témouchent", "47": "Ghardaïa", "48": "Relizane", "49": "Timimoun", "50": "Bordj Badji Mokhtar",
            "51": "Ouled Djellal", "52": "Béni Abbès", "53": "In Salah", "54": "In Guezzam", "55": "Touggourt",
            "56": "Djanet", "57": "El M'Ghair", "58": "El Meniaa"
        };

        let wName = wilayas[wilayaCode];
        if (!wName && parseInt(wilayaCode) > 58 && parseInt(wilayaCode) <= 69) {
            wName = "Nouvelle Wilaya";
        } else if (!wName) {
            wName = "Inconnue";
        }

        const vehTypes = {
            "1": "Véhicule Tourisme", "2": "Camion", "3": "Camionnette", "4": "Autocar",
            "5": "Tracteur Routier", "6": "Tracteur Agricole", "7": "Engin Spécial",
            "8": "Remorque", "9": "Moto"
        };
        const typeName = vehTypes[middleCode.charAt(0)] || "Inconnu";
        const yearCode = middleCode.substring(1, 3);
        const year = parseInt(yearCode) > 50 ? `19${yearCode}` : `20${yearCode}`;

        return {
            isValid: true,
            wilaya: `${wilayaCode} (${wName})`,
            type: typeName,
            year: year
        };
    }

    window.exportToPDF = function () {
        const element = document.querySelector('.detail-card');
        if (!element) return;

        const actionsDiv = element.querySelector('.actions');
        if (actionsDiv) actionsDiv.style.opacity = '0';

        const plateText = element.querySelector('.plate-extracted')?.innerText || 'capture';
        const filename = `LAPI_${plateText.replace(/\s+/g, '_')}.pdf`;

        const opt = {
            margin: 10,
            filename,
            image: { type: 'jpeg', quality: 0.98 },
            html2canvas: { scale: 2, useCORS: true },
            jsPDF: { unit: 'mm', format: 'a4', orientation: 'portrait' }
        };

        const title = document.createElement('h2');
        title.innerHTML = '<i class="fa-solid fa-car-on"></i> LAPISys — Rapport de Capture';
        title.style.cssText = 'text-align:center; color:#3b82f6; margin-bottom:20px;';
        element.prepend(title);

        html2pdf().set(opt).from(element).save().then(() => {
            if (actionsDiv) actionsDiv.style.opacity = '1';
            title.remove();
        });
    };

    window.deleteCapture = function (captureId) {
        if (!confirm('Êtes-vous sûr de vouloir supprimer cette capture ?')) return;

        plateDetail.innerHTML = '<div class="empty-state"><i class="fa-solid fa-spinner fa-spin"></i><p>Suppression en cours...</p></div>';

        fetch(`/api/captures/${captureId}`, { method: 'DELETE' })
            .then(r => r.json())
            .then(data => {
                if (data.success) {
                    capturesData = capturesData.filter(c => (c.id_capture || c.id) !== captureId);
                    refreshDisplay();
                    updateStats();
                    plateDetail.innerHTML = `
                    <div class="empty-state">
                        <i class="fa-solid fa-trash-check" style="color:var(--success)"></i>
                        <p style="color:var(--success)">Capture supprimée avec succès</p>
                    </div>`;
                    setTimeout(() => {
                        plateDetail.innerHTML = `
                        <div class="empty-state">
                            <i class="fa-solid fa-id-card"></i>
                            <p>Sélectionnez une capture pour voir les détails</p>
                        </div>`;
                    }, 2000);
                } else {
                    alert('Erreur: ' + data.error);
                }
            });
    };

    function updateStats() {
        totalCapturesEl.textContent = capturesData.length;
    }
});
