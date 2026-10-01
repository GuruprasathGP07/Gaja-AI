/* static/app.js - Frontend Application Logic for GajaAlert AI */

document.addEventListener('DOMContentLoaded', () => {
  initDropZone();
  initFormSubmit();
  initMap();
  initChart();
  fetchEvents();
  fetchStats();
});

// Global state variables
let leafletMap = null;
let siteMarkers = {};
let sightingsChart = null;
let currentPredictionData = null;

// State-Wide Surveillance Camera Coordinates across Tamil Nadu
const SITE_COORDS = {
  'maruthamalai': [11.0450, 76.9025],
  'thadagam': [11.0833, 76.8833],
  'gudalur': [11.5000, 76.4900],
  'masinagudi': [11.5722, 76.6439],
  'sanamavu': [12.6350, 77.9250],
  'denkanikottai': [12.5270, 77.7910],
  'valparai': [10.3267, 76.9553],
  'sathyamangalam': [11.5050, 77.2400],
  'hasanur': [11.7580, 77.0650],
  'pennagaram': [12.1333, 77.9000],
  'madukkarai': [10.9050, 76.9550],
  'megamalai': [9.6955, 77.4042]
};

// --- Drop Zone & File Selection ---
function initDropZone() {
  const dropZone = document.getElementById('dropZone');
  const imageInput = document.getElementById('imageInput');

  if (!dropZone || !imageInput) return;

  dropZone.addEventListener('click', () => imageInput.click());

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  ['dragleave', 'dragend'].forEach(evt => {
    dropZone.addEventListener(evt, () => dropZone.classList.remove('dragover'));
  });

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      imageInput.files = e.dataTransfer.files;
      previewLocalImage(e.dataTransfer.files[0]);
    }
  });

  imageInput.addEventListener('change', () => {
    if (imageInput.files && imageInput.files[0]) {
      previewLocalImage(imageInput.files[0]);
    }
  });

  // Grad-CAM Toggle Handler
  const gradcamToggle = document.getElementById('gradcamToggle');
  if (gradcamToggle) {
    gradcamToggle.addEventListener('change', (e) => {
      const previewImg = document.getElementById('previewImg');
      if (!currentPredictionData || !previewImg) return;

      if (e.target.checked && currentPredictionData.heatmap) {
        previewImg.src = currentPredictionData.heatmap;
      } else {
        previewImg.src = currentPredictionData.image_url;
      }
    });
  }
}

function previewLocalImage(file) {
  const previewImg = document.getElementById('previewImg');
  if (!previewImg) return;
  const reader = new FileReader();
  reader.onload = (e) => {
    previewImg.src = e.target.result;
  };
  reader.readAsDataURL(file);
}

// --- Form Submit & REST API Predict ---
function initFormSubmit() {
  const form = document.getElementById('uploadForm');
  const btnCheck = document.getElementById('btnCheck');

  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const imageInput = document.getElementById('imageInput');
    if (!imageInput.files || imageInput.files.length === 0) {
      alert('Please select or drop an image file first.');
      return;
    }

    const formData = new FormData(form);
    btnCheck.disabled = true;
    btnCheck.textContent = 'Executing Corridor Scan...';

    try {
      const res = await fetch('/predict', {
        method: 'POST',
        body: formData
      });

      const data = await res.json();
      if (!res.ok) {
        alert(`Error: ${data.error || 'Failed to process image.'}`);
        return;
      }

      currentPredictionData = data;
      renderPredictionResult(data);
      fetchEvents();
      fetchStats();

    } catch (err) {
      console.error('Prediction API Error:', err);
      alert('Network error connecting to State Surveillance API.');
    } finally {
      btnCheck.disabled = false;
      btnCheck.textContent = 'Execute Corridor Threat Scan';
    }
  });
}

// --- Render Prediction Results ---
function renderPredictionResult(data) {
  // 1. Verdict Band Update
  const verdictBand = document.getElementById('verdictBand');
  const verdictBadge = document.getElementById('verdictBadge');
  const verdictTitle = document.getElementById('verdictTitle');
  const verdictSubtext = document.getElementById('verdictSubtext');
  const verdictTime = document.getElementById('verdictTime');

  verdictBand.className = `verdict-container state-${data.risk}`;
  verdictBadge.textContent = `RISK LEVEL: ${data.risk}`;

  if (data.risk === 'NONE') {
    verdictTitle.textContent = `Clear - No Threat Detected (${data.site.name})`;
    verdictSubtext.textContent = `Predicted class: ${data.label_name} (${data.confidence}% confidence).`;
  } else if (data.risk === 'LOW') {
    verdictTitle.textContent = `ADVISORY: Elephant Detected (${data.site.name})`;
    verdictSubtext.textContent = `Low confidence / daytime detection (${data.confidence}%). Stay vigilant.`;
  } else if (data.risk === 'MEDIUM') {
    verdictTitle.textContent = `WARNING: Elephant Sighting Confirmed (${data.site.name})`;
    verdictSubtext.textContent = `Medium threat alert generated. Forest officials notified.`;
  } else if (data.risk === 'HIGH') {
    verdictTitle.textContent = `CRITICAL ALERT: ELEPHANT INTRUSION (${data.site.name})`;
    verdictSubtext.textContent = `Immediate caution required! Night time or repeat sighting within 30 mins.`;
  }

  // Dynamically update sector & top bar zone
  const verdictSectorText = document.getElementById('verdictSectorText');
  const topBarZone = document.getElementById('topBarZone');
  const sectorName = data.site.sector || data.site.name;
  if (verdictSectorText) verdictSectorText.textContent = sectorName;
  if (topBarZone) topBarZone.textContent = `ZONE: ${sectorName.toUpperCase()}`;

  const dt = new Date(data.ts);
  verdictTime.textContent = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

  // 2. Image Preview & Grad-CAM toggle state
  const previewImg = document.getElementById('previewImg');
  const gradcamToggle = document.getElementById('gradcamToggle');
  const reviewFlag = document.getElementById('reviewFlag');

  previewImg.src = data.image_url;
  if (gradcamToggle) {
    gradcamToggle.checked = false;
    gradcamToggle.disabled = !data.heatmap;
  }

  if (reviewFlag) {
    reviewFlag.style.display = data.review_needed ? 'inline-block' : 'none';
  }

  // 3. Probability Bars
  updateProbBar('probElephant', data.probs['elephant'] || 0);
  updateProbBar('probOther', data.probs['other_animal'] || 0);
  updateProbBar('probNo', data.probs['no_animal'] || 0);

  document.getElementById('repeatStatus').textContent = data.repeat_sighting ? 'YES (Last 30m)' : 'No';
  document.getElementById('nightStatus').textContent = data.night ? 'YES (18:00-06:00)' : 'No';

  // 4. Alert Cards
  document.getElementById('alertEnText').textContent = data.alert_en;
  document.getElementById('alertTaText').textContent = data.alert_ta;

  // 5. Audio Warning Trigger
  const audioToggle = document.getElementById('audioToggle');
  if (audioToggle && audioToggle.checked && (data.risk === 'MEDIUM' || data.risk === 'HIGH')) {
    playSirenSound(data.risk);
  }
}

function updateProbBar(prefix, pct) {
  const pctEl = document.getElementById(`${prefix}Pct`);
  const fillEl = document.getElementById(`${prefix}Fill`);
  if (pctEl && fillEl) {
    pctEl.textContent = `${pct.toFixed(1)}%`;
    fillEl.style.width = `${pct}%`;
  }
}

// --- Web Audio API Synthesizer Siren ---
function playSirenSound(risk) {
  try {
    const AudioContext = window.AudioContext || window.webkitAudioContext;
    if (!AudioContext) return;

    const ctx = new AudioContext();
    const osc = ctx.createOscillator();
    const gain = ctx.createGain();

    osc.type = 'sawtooth';

    // Siren frequency modulation (wailing pattern)
    const now = ctx.currentTime;
    const duration = risk === 'HIGH' ? 2.5 : 1.5;

    osc.frequency.setValueAtTime(440, now);
    osc.frequency.exponentialRampToValueAtTime(880, now + duration * 0.3);
    osc.frequency.exponentialRampToValueAtTime(440, now + duration * 0.6);
    osc.frequency.exponentialRampToValueAtTime(880, now + duration);

    gain.gain.setValueAtTime(0.3, now);
    gain.gain.exponentialRampToValueAtTime(0.01, now + duration);

    osc.connect(gain);
    gain.connect(ctx.destination);

    osc.start(now);
    osc.stop(now + duration);
  } catch (e) {
    console.log('Web Audio play warning:', e);
  }
}

// --- Web Speech API Text to Speech ---
function speakText(elementId, lang) {
  const el = document.getElementById(elementId);
  if (!el || !('speechSynthesis' in window)) {
    alert('Text-to-speech is not supported by your browser.');
    return;
  }

  window.speechSynthesis.cancel();
  const utterance = new SpeechSynthesisUtterance(el.textContent);
  utterance.lang = lang;
  utterance.rate = 0.95;
  window.speechSynthesis.speak(utterance);
}

function copyAlert(elementId) {
  const el = document.getElementById(elementId);
  if (!el) return;
  navigator.clipboard.writeText(el.textContent).then(() => {
    alert('Alert text copied to clipboard!');
  });
}

// --- Leaflet Map ---
function initMap() {
  const mapContainer = document.getElementById('mapContainer');
  if (!mapContainer || typeof L === 'undefined') return;

  try {
    leafletMap = L.map('mapContainer', {
      center: [11.3000, 77.3000],
      zoom: 8,
      zoomControl: true
    });

    // OpenStreetMap tile layer (degrades gracefully offline)
    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
      maxZoom: 18,
      attribution: '&copy; OpenStreetMap contributors'
    }).addTo(leafletMap);

    // Initial markers for 5 Coimbatore sites
    Object.keys(SITE_COORDS).forEach(sk => {
      const coords = SITE_COORDS[sk];
      const marker = L.circleMarker(coords, {
        radius: 10,
        fillColor: '#374151',
        color: '#ffffff',
        weight: 2,
        opacity: 1,
        fillOpacity: 0.8
      }).addTo(leafletMap);

      marker.bindPopup(`<b>${sk.toUpperCase()} Sensor Node</b><br>Risk Status: NONE`);
      siteMarkers[sk] = marker;
    });

  } catch (e) {
    console.log('Leaflet map initialization notice (Offline degrade mode):', e);
  }
}

function updateMapSiteStatus(sitesData) {
  if (!leafletMap || !sitesData) return;

  const colorMap = {
    'NONE': '#10b981',
    'LOW': '#f59e0b',
    'MEDIUM': '#f97316',
    'HIGH': '#ef4444'
  };

  Object.keys(sitesData).forEach(sk => {
    const sinfo = sitesData[sk];
    const marker = siteMarkers[sk];
    if (marker && colorMap[sinfo.latest_risk]) {
      marker.setStyle({
        fillColor: colorMap[sinfo.latest_risk],
        radius: sinfo.latest_risk === 'HIGH' ? 14 : 10
      });
      marker.bindPopup(`
        <strong>${sinfo.name}</strong><br>
        Latest Risk: <b style="color:${colorMap[sinfo.latest_risk]}">${sinfo.latest_risk}</b><br>
        Class: ${sinfo.latest_label} (${sinfo.latest_confidence.toFixed(1)}%)
      `);
    }
  });
}

// --- Chart.js Sightings Bar Chart ---
function initChart() {
  const ctx = document.getElementById('sightingsChart');
  if (!ctx || typeof Chart === 'undefined') return;

  const hoursLabels = Array.from({length: 24}, (_, i) => `${String(i).padStart(2, '0')}:00`);
  const initialData = Array(24).fill(0);

  sightingsChart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: hoursLabels,
      datasets: [{
        label: 'Elephant Sightings',
        data: initialData,
        backgroundColor: '#ef4444',
        borderRadius: 4
      }]
    },
    options: {
      responsive: true,
      maintainAspectRatio: false,
      plugins: {
        legend: { display: false }
      },
      scales: {
        x: {
          ticks: { color: '#9ca3af', font: { size: 10 } },
          grid: { color: '#374151' }
        },
        y: {
          beginAtZero: true,
          ticks: { color: '#9ca3af', stepSize: 1 },
          grid: { color: '#374151' }
        }
      }
    }
  });
}

// --- Fetch Events & Stats ---
async function fetchEvents() {
  try {
    const res = await fetch('/api/events?limit=15');
    if (!res.ok) return;
    const data = await res.json();
    renderEventsTable(data.events || []);
  } catch (e) {
    console.error('Error fetching events:', e);
  }
}

async function fetchStats() {
  try {
    const res = await fetch('/api/stats');
    if (!res.ok) return;
    const stats = await res.json();

    if (sightingsChart && stats.hourly_sightings) {
      sightingsChart.data.datasets[0].data = stats.hourly_sightings;
      sightingsChart.update();
    }

    if (stats.sites) {
      updateMapSiteStatus(stats.sites);
    }
  } catch (e) {
    console.error('Error fetching stats:', e);
  }
}

function renderEventsTable(events) {
  const tbody = document.getElementById('eventsTableBody');
  if (!tbody) return;

  if (events.length === 0) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align: center; color: var(--text-muted); padding: 1.5rem;">No detection events logged yet.</td></tr>`;
    return;
  }

  const riskBadgeColors = {
    'NONE': '#064e3b',
    'LOW': '#78350f',
    'MEDIUM': '#7c2d12',
    'HIGH': '#7f1d1d'
  };

  tbody.innerHTML = events.map(ev => {
    const dt = new Date(ev.timestamp);
    const timeStr = dt.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    const badgeColor = riskBadgeColors[ev.risk] || '#1f2937';

    return `
      <tr>
        <td>${timeStr}</td>
        <td><img src="${ev.image_url}" class="thumb-small" alt="Thumb"></td>
        <td>${ev.site ? ev.site.name : ev.site_key}</td>
        <td><strong>${ev.label}</strong></td>
        <td>${ev.confidence.toFixed(1)}%</td>
        <td><span style="background:${badgeColor}; padding:0.2rem 0.5rem; border-radius:4px; font-weight:700; font-size:0.75rem;">${ev.risk}</span></td>
        <td>${ev.is_night ? 'Night' : 'Day'}</td>
      </tr>
    `;
  }).join('');
}

async function clearEventsLog() {
  if (!confirm('Are you sure you want to clear all logged detection events?')) return;
  try {
    const res = await fetch('/api/clear', { method: 'POST' });
    if (res.ok) {
      fetchEvents();
      fetchStats();
    }
  } catch (e) {
    alert('Could not clear logs.');
  }
}
