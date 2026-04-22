const dropZone    = document.getElementById('dropZone');
const fileInput   = document.getElementById('fileInput');
const previewWrap = document.getElementById('previewWrap');
const previewImg  = document.getElementById('previewImg');
const clearBtn    = document.getElementById('clearBtn');
const analyzeBtn  = document.getElementById('analyzeBtn');

const uploadCard      = document.getElementById('uploadCard');
const loaderCard      = document.getElementById('loaderCard');
const resultsWrap     = document.getElementById('resultsWrap');
const notCannabisCard = document.getElementById('notCannabisCard');

let selectedFile = null;

// ── File selection ────────────────────────────────────────────────────────────

function setFile(file) {
  if (!file || !file.type.startsWith('image/')) return;
  selectedFile = file;
  previewImg.src = URL.createObjectURL(file);
  dropZone.classList.add('hidden');
  previewWrap.classList.remove('hidden');
  analyzeBtn.disabled = false;
}

function clearFile() {
  selectedFile = null;
  fileInput.value = '';
  previewImg.src = '';
  previewWrap.classList.add('hidden');
  dropZone.classList.remove('hidden');
  analyzeBtn.disabled = true;
}

fileInput.addEventListener('change', () => { if (fileInput.files[0]) setFile(fileInput.files[0]); });
clearBtn.addEventListener('click', clearFile);

dropZone.addEventListener('dragover', e => { e.preventDefault(); dropZone.classList.add('drag-over'); });
dropZone.addEventListener('dragleave', () => dropZone.classList.remove('drag-over'));
dropZone.addEventListener('drop', e => {
  e.preventDefault();
  dropZone.classList.remove('drag-over');
  if (e.dataTransfer.files[0]) setFile(e.dataTransfer.files[0]);
});
dropZone.addEventListener('click', () => fileInput.click());

// ── Analyze ───────────────────────────────────────────────────────────────────

analyzeBtn.addEventListener('click', async () => {
  if (!selectedFile) return;
  uploadCard.classList.add('hidden');
  loaderCard.classList.remove('hidden');
  resultsWrap.classList.add('hidden');
  notCannabisCard.classList.add('hidden');

  const fd = new FormData();
  fd.append('image', selectedFile);

  try {
    const res  = await fetch('/analyze', { method: 'POST', body: fd });
    const data = await res.json();
    loaderCard.classList.add('hidden');

    if (data.error) {
      alert('Error: ' + data.error);
      uploadCard.classList.remove('hidden');
      return;
    }
    if (!data.is_cannabis) {
      notCannabisCard.classList.remove('hidden');
      return;
    }

    renderQuality(data);
    renderDiseases(data);
    renderStrains(data);
    renderAnalytes(data);
    resultsWrap.classList.remove('hidden');

  } catch (err) {
    loaderCard.classList.add('hidden');
    uploadCard.classList.remove('hidden');
    alert('Request failed: ' + err.message);
  }
});

// ── Quality render ────────────────────────────────────────────────────────────

const CRITERIA_META = {
  color:      { label: 'Color',         icon: '🎨' },
  trichomes:  { label: 'Trichomes',     icon: '✨' },
  structure:  { label: 'Bud Structure', icon: '🌸' },
  moisture:   { label: 'Moisture',      icon: '💧' },
  appearance: { label: 'Appearance',    icon: '👁️' },
};

function barClass(score) {
  return score >= 7 ? 'bar-high' : score >= 4 ? 'bar-medium' : 'bar-low';
}

function renderQuality(data) {
  const grade = (data.grade || 'C').toUpperCase();
  const banner = document.getElementById('gradeBanner');
  banner.className = 'grade-banner grade-' + grade.toLowerCase();
  document.getElementById('gradeLetter').textContent = grade;
  document.getElementById('overallScore').textContent = data.overall_score + ' / 100';
  document.getElementById('summaryText').textContent = data.summary || '';

  const grid = document.getElementById('criteriaGrid');
  grid.innerHTML = '';
  for (const [key, meta] of Object.entries(CRITERIA_META)) {
    const c = data.criteria?.[key];
    if (!c) continue;
    const score = c.score ?? 0;
    const div = document.createElement('div');
    div.className = 'criterion';
    div.innerHTML = `
      <div class="criterion-header">
        <span class="criterion-name">${meta.icon} ${meta.label}</span>
        <span class="criterion-score">${score}/10</span>
      </div>
      <div class="criterion-bar-bg">
        <div class="criterion-bar ${barClass(score)}" style="width:${score * 10}%"></div>
      </div>
      <div class="criterion-note">${c.note || ''}</div>
    `;
    grid.appendChild(div);
  }

  const prosUl = document.getElementById('prosUl');
  prosUl.innerHTML = '';
  (data.positives || []).forEach(p => {
    const li = document.createElement('li'); li.textContent = p; prosUl.appendChild(li);
  });

  const consUl = document.getElementById('consUl');
  consUl.innerHTML = '';
  (data.negatives || []).forEach(n => {
    const li = document.createElement('li'); li.textContent = n; consUl.appendChild(li);
  });
}

// ── Disease render ────────────────────────────────────────────────────────────

function renderDiseases(data) {
  const container = document.getElementById('diseaseContent');
  container.innerHTML = '';

  const diseases = data.detected_diseases || [];

  if (diseases.length === 0) {
    container.innerHTML = `<div class="disease-healthy">✅ No diseases or deficiencies detected — sample appears healthy.</div>`;
    return;
  }

  const list = document.createElement('div');
  list.className = 'disease-list';

  diseases.forEach(d => {
    const sevClass = 'severity-' + (d.severity || 'medium');
    const sevLabel = 'sev-' + (d.severity || 'medium');
    const pct = Math.round((d.confidence || 0) * 100);

    const item = document.createElement('div');
    item.className = `disease-item ${sevClass}`;

    const catIcon = { fungal: '🍄', pest: '🐛', nutrient: '🌱', environmental: '🌡️', unknown: '⚠️' };
    const icon = catIcon[d.category] || '⚠️';

    item.innerHTML = `
      <div class="disease-header">
        <span class="disease-severity ${sevLabel}">${d.severity}</span>
        <span class="disease-name">${icon} ${d.name}</span>
        <span class="disease-confidence">${pct}% confidence</span>
      </div>
      <div class="disease-body">
        ${d.evidence ? `<div class="disease-evidence">"${d.evidence}"</div>` : ''}
        ${d.causes    ? `<div class="disease-row"><strong>Cause:</strong> ${d.causes}</div>` : ''}
        ${d.treatment ? `<div class="disease-row"><strong>Treatment:</strong> ${d.treatment}</div>` : ''}
        ${d.risk_to_consumer ? `<div class="disease-risk">⚠️ ${d.risk_to_consumer}</div>` : ''}
      </div>
    `;
    list.appendChild(item);
  });

  container.appendChild(list);
}

// ── Strain render ─────────────────────────────────────────────────────────────

function renderStrains(data) {
  const type = data.strain_type || 'Unknown';

  // Type badge
  const badge = document.getElementById('strainTypeBadge');
  badge.textContent = type;
  badge.className = 'strain-type-badge ' + type.toLowerCase();

  // Effect / flavor tags
  const tagsEl = document.getElementById('strainTags');
  tagsEl.innerHTML = '';
  const tags = [...(data.likely_effects || []), ...(data.likely_flavors || [])];
  tags.forEach(t => {
    const span = document.createElement('span');
    span.className = 'strain-tag';
    span.textContent = t;
    tagsEl.appendChild(span);
  });

  // Dataset size
  document.getElementById('dbSize').textContent =
    (data.dataset_size || 0).toLocaleString();

  // Strain list
  const list = document.getElementById('strainList');
  list.innerHTML = '';

  const matches = data.matched_strains || [];
  if (matches.length === 0) {
    list.innerHTML = '<p style="color:var(--text-muted);font-size:.85rem">No close matches found in the dataset.</p>';
    return;
  }

  matches.forEach(s => {
    const item = document.createElement('div');
    item.className = 'strain-item';

    const typeClass = 'badge-type-' + (s.type || 'hybrid').toLowerCase();
    const thcBadge  = s.thc  ? `<span class="badge badge-thc">THC ${s.thc}%</span>` : '';
    const cbdBadge  = s.cbd  ? `<span class="badge badge-cbd">CBD ${s.cbd}%</span>` : '';
    const descHtml  = s.description ? `<div class="strain-desc">${s.description}</div>` : '';

    const metaTags = [...(s.effects || []), ...(s.flavors || []), ...(s.terpenes || [])]
      .slice(0, 8)
      .map(t => `<span class="strain-meta-tag">${t}</span>`)
      .join('');

    item.innerHTML = `
      <div class="strain-item-header">
        <span class="strain-name">${s.name}</span>
        <div class="strain-badges">
          <span class="badge ${typeClass}">${s.type}</span>
          ${thcBadge}${cbdBadge}
        </div>
      </div>
      ${descHtml}
      <div class="strain-meta">${metaTags}</div>
    `;
    list.appendChild(item);
  });
}

// ── Analyte render ────────────────────────────────────────────────────────────

function renderAnalyteItem(a) {
  const item = document.createElement('div');
  item.className = 'analyte-item';

  const formula = a.chemical_formula
    ? `<span class="analyte-formula">${a.chemical_formula}</span>` : '';
  const sci = a.scientific_name
    ? `<div class="analyte-sci">${a.scientific_name}</div>` : '';
  const subtype = a.subtype
    ? `<span class="analyte-subtype">${a.subtype}</span>` : '';
  const desc = a.description
    ? `<div class="analyte-desc">${a.description}</div>` : '';

  const chains = [];
  if (a.degrades_to?.length)
    chains.push('Degrades to: ' + a.degrades_to.join(', '));
  if (a.precursors?.length)
    chains.push('Precursor of: ' + a.precursors.join(', '));
  const chainHtml = chains.length
    ? `<div class="analyte-chain">${chains.join(' · ')}</div>` : '';

  const wikiLink = a.wikipedia_url
    ? ` <a href="${a.wikipedia_url}" target="_blank" rel="noopener">Wikipedia ↗</a>` : '';

  item.innerHTML = `
    <div class="analyte-name">${a.name}</div>
    ${formula}
    ${sci}
    ${subtype}
    ${desc}
    ${chainHtml}
    ${wikiLink ? `<div class="analyte-chain">${wikiLink}</div>` : ''}
  `;
  return item;
}

function renderAnalytes(data) {
  // THC / CBD estimates
  const estEl = document.getElementById('analyteEstimates');
  estEl.innerHTML = '';
  if (data.thc_estimate) {
    estEl.innerHTML += `<div class="estimate-chip"><span>Est. THC</span><strong>${data.thc_estimate}</strong></div>`;
  }
  if (data.cbd_estimate) {
    estEl.innerHTML += `<div class="estimate-chip"><span>Est. CBD</span><strong>${data.cbd_estimate}</strong></div>`;
  }

  // Terpenes
  const terpList = document.getElementById('terpeneList');
  terpList.innerHTML = '';
  (data.analyte_terpenes || []).forEach(a => terpList.appendChild(renderAnalyteItem(a)));
  if (!data.analyte_terpenes?.length) {
    terpList.innerHTML = '<p style="font-size:.82rem;color:var(--text-muted)">No terpene data matched.</p>';
  }

  // Cannabinoids
  const cbList = document.getElementById('cannabinoidList');
  cbList.innerHTML = '';
  (data.analyte_cannabinoids || []).forEach(a => cbList.appendChild(renderAnalyteItem(a)));
  if (!data.analyte_cannabinoids?.length) {
    cbList.innerHTML = '<p style="font-size:.82rem;color:var(--text-muted)">No cannabinoid data matched.</p>';
  }
}

// ── Retry ─────────────────────────────────────────────────────────────────────

function resetToUpload() {
  clearFile();
  resultsWrap.classList.add('hidden');
  notCannabisCard.classList.add('hidden');
  uploadCard.classList.remove('hidden');
}

document.getElementById('retryBtn').addEventListener('click', resetToUpload);
document.getElementById('retryBtn2').addEventListener('click', resetToUpload);
