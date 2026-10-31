/* PixelMath Studio: a no-dependency front end for the PixelMath HTTP API (same origin). */
(() => {
'use strict';

const $ = (sel, root = document) => root.querySelector(sel);
const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
const store = {
  get(k, d) { try { const v = localStorage.getItem(k); return v === null ? d : v; } catch (e) { return d; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (e) { /* private mode: fine */ } },
};
function h(tag, attrs, ...kids) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (k === 'class') el.className = v; else if (k === 'text') el.textContent = v;
    else if (k.startsWith('on')) el.addEventListener(k.slice(2), v); else el.setAttribute(k, v);
  }
  for (const kid of kids.flat()) if (kid != null) el.append(kid.nodeType ? kid : document.createTextNode(String(kid)));
  return el;
}
const clear = (el) => { while (el.firstChild) el.removeChild(el.firstChild); };

const state = {
  key: store.get('pm_key', ''), health: null, mode: store.get('pm_mode', 'plain'), busy: false, ctrl: null,
  last: null, history: [], items: [], zip: null, trainBusy: false,
};

// ------------------------------------------------------------------------------------------------ API
async function api(path, opt = {}) {
  const headers = Object.assign({}, opt.headers || {});
  if (state.key) headers['X-API-Key'] = state.key;
  let body = opt.body;
  if (opt.json !== undefined) { body = JSON.stringify(opt.json); headers['Content-Type'] = 'application/json'; }
  let res;
  try {
    res = await fetch(path, { method: opt.method || 'GET', headers, body, signal: opt.signal });
  } catch (e) {
    if (e.name === 'AbortError') throw e;
    throw new Error('Cannot reach the server. Is it still running?');
  }
  let data = null;
  if ((res.headers.get('content-type') || '').includes('json')) { try { data = await res.json(); } catch (e) { data = null; } }
  if (!res.ok) {
    if (res.status === 401) askKey();
    const msg = data && data.error ? data.error.message : 'The server answered HTTP ' + res.status;
    const err = new Error(msg);
    err.status = res.status;
    throw err;
  }
  return data;
}

function banner(msg, isErr) {
  const b = $('#banner');
  if (!msg) { b.hidden = true; return; }
  b.textContent = msg; b.className = 'banner' + (isErr ? ' err' : ''); b.hidden = false;
}

// ------------------------------------------------------------------------------------------------ status / key
async function refreshHealth() {
  const pill = $('#status-pill');
  try {
    const hres = await fetch('/health');
    state.health = await hres.json();
    const m = state.health.model_loaded;
    pill.textContent = 'ready · ' + (m ? 'trained model loaded' : 'no trained model');
    pill.className = 'pill ok';
    $('#key-btn').hidden = !state.health.auth_required;
    $('#learned-wrap').hidden = !m;
    $('#save-wrap').hidden = !state.health.database;
    $('#gallery-off').hidden = !!state.health.database; $('#gallery-tools').hidden = !state.health.database;
    $('#train-go').disabled = !state.health.training_enabled || state.trainBusy || !(state.items.length || state.zip);
    if (!state.health.training_enabled) banner('Training is switched off on this server: start it with a model file (python3 app.py does this for you).', false);
  } catch (e) {
    pill.textContent = 'server not reachable'; pill.className = 'pill bad';
  }
}
function askKey() {
  const d = $('#key-dialog');
  if (typeof d.showModal !== 'function' || d.open) return;
  $('#key-input').value = state.key;
  d.showModal();
}
$('#key-btn').addEventListener('click', askKey);
$('#key-dialog').addEventListener('close', (e) => {
  if (e.target.returnValue === 'ok') { state.key = $('#key-input').value.trim(); store.set('pm_key', state.key); refreshHealth(); }
});

// ------------------------------------------------------------------------------------------------ tabs
function showTab(name) {
  $$('.tab').forEach((t) => { const on = t.dataset.tab === name; t.classList.toggle('active', on); t.setAttribute('aria-selected', on); });
  $$('.panel').forEach((p) => p.classList.toggle('active', p.id === 'tab-' + name));
  if (name === 'model') loadModel();
  if (name === 'studio') initStudio();
  if (name === 'gallery') loadGallery(true);
  if (name === 'dataset') loadDataset(true);
  if (name === 'train') loadJobHistory();
}
$$('.tab').forEach((t) => t.addEventListener('click', () => showTab(t.dataset.tab)));

// ------------------------------------------------------------------------------------------------ create
const EXAMPLES = ['laptop and coffee cup', 'red tractor and dog', 'doctor and stethoscope', 'tea shop "CHAI"', 'cat in space',
  'red house near a lake at sunset', 'mandelbrot complementary', 'fractal tree', 'flow field triadic', 'snowflake', 'fern', 'marble'];
const MODE_HELP = {
  plain: 'Draws exactly what the prompt says. The same prompt and seed always give the same picture.',
  creative: 'Adds related props, settings and colours, lets a critic reject variations that break your request, and keeps the best. It never scores below the plain picture.',
  imagine: 'Mashes two ideas together (your prompt is kept as one of them; leave it empty for fully random). The critic rejects mash-ups that do not work.',
};
EXAMPLES.forEach((t) => $('#chips').append(h('button', { class: 'chip', type: 'button', text: t, onclick: () => { $('#prompt').value = t; $('#prompt').focus(); } })));

function setMode(m) {
  state.mode = m; store.set('pm_mode', m);
  $$('#mode-seg button').forEach((b) => { const on = b.dataset.mode === m; b.classList.toggle('on', on); b.setAttribute('aria-checked', on); });
  $('#mode-help').textContent = MODE_HELP[m];
  $('#creative-opts').hidden = m === 'plain';
  $('#explore').closest('label').hidden = m === 'imagine';
  $('#go').textContent = m === 'plain' ? 'Generate' : m === 'creative' ? 'Create' : 'Imagine';
}
$$('#mode-seg button').forEach((b) => b.addEventListener('click', () => setMode(b.dataset.mode)));
$('#temp').addEventListener('input', () => { $('#temp-out').textContent = (+$('#temp').value).toFixed(2); });
$('#dice').addEventListener('click', () => { $('#seed').value = Math.floor(Math.random() * 2147483647); });
$('#prompt').addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); generate(); } });
$('#go').addEventListener('click', () => generate());
$('#cancel').addEventListener('click', () => { if (state.ctrl) state.ctrl.abort(); });

function numv(sel, d) { const v = parseInt($(sel).value, 10); return Number.isFinite(v) ? v : d; }

function buildRequest() {
  const prompt = $('#prompt').value.trim();
  const size = numv('#size', 512);
  const base = { size, seed: Math.max(0, numv('#seed', 0)), response: 'base64' };
  if (state.health && state.health.database && $('#save').checked) base.save = true;
  if (!$('#learned-wrap').hidden) base.learned = $('#learned').value;
  if (state.mode === 'plain') return { path: '/generate', body: Object.assign({ prompt }, base) };
  const common = Object.assign({}, base, { temperature: +$('#temp').value, population: numv('#pop', 8), generations: numv('#gen', 3), max_seconds: 40 });
  if (state.mode === 'creative') return { path: '/create', body: Object.assign({ prompt, alternatives: 4, explore: numv('#explore', 0) }, common) };
  const body = Object.assign({ attempts: 12 }, common);
  if (prompt) body.anchor = prompt;
  return { path: '/imagine', body };
}

async function generate() {
  if (state.busy) return;
  const prompt = $('#prompt').value.trim();
  if (!prompt && state.mode !== 'imagine') { banner('Type what you want drawn first.', true); $('#prompt').focus(); return; }
  banner('');
  const req = buildRequest();
  await run(req, prompt);
}

async function run(req, label) {
  state.busy = true; state.ctrl = new AbortController();
  $('#go').disabled = true; $('#cancel').hidden = false;
  const t0 = Date.now();
  const tick = () => { $('#busy').replaceChildren(h('span', { class: 'spin' }), ((Date.now() - t0) / 1000).toFixed(1) + ' s'); };
  tick(); const timer = setInterval(tick, 200);
  try {
    const data = await api(req.path, { method: 'POST', json: req.body, signal: state.ctrl.signal });
    show(data, req, label);
  } catch (e) {
    if (e.name === 'AbortError') banner('Cancelled.', false);
    else banner(e.status === 503 ? 'The server is busy. Try again in a moment.' : e.message, true);
  } finally {
    clearInterval(timer); state.busy = false; state.ctrl = null;
    $('#go').disabled = false; $('#cancel').hidden = true; $('#busy').textContent = '';
  }
}

function show(data, req, label) {
  const src = 'data:' + data.mime + ';base64,' + data.image_base64;
  const used = data.creation ? data.creation.prompt_used : req.body.prompt || label || '';
  state.last = { src, prompt: used, seed: data.seed, req, data };
  $('#out').src = src;
  const dl = $('#download'); dl.href = src; dl.download = 'pixelmath-' + data.seed + '.png';
  $('#empty').hidden = true; $('#figure').hidden = false; $('#result-actions').hidden = false;
  const bits = [data.mode, data.width + '×' + data.height, 'seed ' + data.seed, data.render_seconds + ' s'];
  if (data.gallery_id) bits.push('saved to gallery');
  $('#meta').replaceChildren(h('div', { text: bits.join(' · ') }), used ? h('div', { text: '“' + used + '”' }) : null);
  const w = $('#warnings'); clear(w);
  (data.warnings || []).forEach((t) => w.append(h('li', { text: t })));
  renderCreation(data.creation, req);
  pushHistory(src, used, data.seed);
  if (used) explain(used);
}

function renderCreation(c, req) {
  const box = $('#creation');
  if (!c) { box.hidden = true; return; }
  box.hidden = false;
  const ul = $('#thinking'); clear(ul);
  c.thinking.forEach((line) => ul.append(h('li', { class: line.startsWith('  ') ? 'sub' : '', text: line.trim() })));
  const sc = $('#scores'); clear(sc);
  Object.entries(c.scores).forEach(([k, v]) => {
    const bar = h('div', { class: 'meter' }, h('span', {}));
    bar.firstChild.style.width = Math.round(Math.max(0, Math.min(1, v)) * 100) + '%';
    sc.append(h('div', { class: 'row' }, h('span', { text: k }), bar, h('span', { class: 'muted', text: v.toFixed(2) })));
  });
  sc.append(h('div', { class: 'hint', text: 'overall ' + c.score.toFixed(3) + ' vs plain picture ' + c.baseline_score.toFixed(3) }));
  const g = $('#gens'); clear(g);
  c.generations.forEach((x) => {
    if (x.best == null) return;
    const grp = h('div', { class: 'gen', title: 'generation ' + x.generation + ': best ' + x.best.toFixed(2) + ', average ' + x.mean.toFixed(2) });
    [['best', x.best], ['avg', x.mean]].forEach(([k, v]) => { const bar = h('span', { class: k }); bar.style.height = Math.max(4, Math.round(Math.min(1, v) * 56)) + 'px'; grp.append(bar); });
    grp.append(h('em', { text: x.generation === 0 ? 'start' : 'gen ' + x.generation }));
    g.append(grp);
  });
  const alts = $('#alts'); clear(alts);
  $('#alts-wrap').hidden = !c.alternatives.length;
  c.alternatives.forEach((a) => alts.append(h('button', { class: 'alt', type: 'button', onclick: () => {
    if (state.busy) return;
    run({ path: '/generate', body: { prompt: a.prompt, seed: a.seed, size: req.body.size, learned: req.body.learned, response: 'base64' } }, a.prompt);
  } }, h('span', { text: a.prompt }), h('b', { text: a.score.toFixed(2) }))));
}

async function explain(prompt) {
  const box = $('#parse-box'), body = $('#parse-body');
  try {
    const p = await api('/parse', { method: 'POST', json: { prompt } });
    clear(body);
    const chips = h('div', { class: 'chips' });
    chips.append(h('span', { class: 'chip static', text: 'type: ' + p.mode }));
    if (p.time) chips.append(h('span', { class: 'chip static', text: 'time: ' + p.time }));
    p.flags.forEach((f) => chips.append(h('span', { class: 'chip static', text: f })));
    p.entities.forEach((e) => {
      const chip = h('span', { class: 'chip static' });
      if (e.color) { const sw = h('span', { class: 'sw' }); sw.style.background = e.color; chip.append(sw); }
      chip.append((e.count > 1 ? e.count + '× ' : '') + e.name);
      chips.append(chip);
    });
    body.append(chips);
    if (p.not_in_lexicon.length) body.append(h('p', { class: 'hint', text: 'Not understood (ignored): ' + p.not_in_lexicon.join(', ') }));
    if (p.model_knows.length) body.append(h('p', { class: 'hint', text: 'Words from your training that apply: ' + p.model_knows.join(', ') }));
    box.hidden = false;
  } catch (e) { box.hidden = true; }
}

function pushHistory(src, prompt, seed) {
  state.history.unshift({ src, prompt, seed });
  state.history = state.history.slice(0, 12);
  const hs = $('#history'); clear(hs);
  state.history.forEach((x, i) => {
    const img = h('img', { src: x.src, alt: x.prompt, title: x.prompt + ' (seed ' + x.seed + ')', loading: 'lazy' });
    if (i === 0) img.classList.add('cur');
    img.addEventListener('click', () => { $('#out').src = x.src; $('#download').href = x.src; $$('img', hs).forEach((n) => n.classList.remove('cur')); img.classList.add('cur'); });
    hs.append(img);
  });
  $('#history-wrap').hidden = false;
}

$('#reuse').addEventListener('click', () => {
  if (!state.last) return;
  $('#prompt').value = state.last.prompt; $('#seed').value = state.last.seed; setMode('plain'); window.scrollTo({ top: 0, behavior: 'smooth' });
});
$('#copy-curl').addEventListener('click', async () => {
  if (!state.last) return;
  const { path, body } = state.last.req;
  const b = Object.assign({}, body); delete b.response;
  const cmd = 'curl -X POST ' + location.origin + path + ' -H "Content-Type: application/json"' +
    (state.key ? ' -H "X-API-Key: YOUR_KEY"' : '') + " -d '" + JSON.stringify(b).replace(/'/g, "'\\''") + "' -o out.png";
  try { await navigator.clipboard.writeText(cmd); banner('API call copied.', false); setTimeout(() => banner(''), 1800); }
  catch (e) { window.prompt('Copy this command', cmd); }
});

// ------------------------------------------------------------------------------------------------ training: choosing data
const IMG_RE = /\.(png|jpe?g|bmp)$/i;
const MAX_ITEMS = 2000;

function nameToCaption(name) {
  return name.replace(/\.[^.]+$/, '').replace(/[_\-.]+/g, ' ').split(/\s+/).filter((w) => w && !/^\d+$/.test(w)).join(' ').trim();
}
function parseCsv(text) {
  const rows = []; let row = [], cur = '', q = false;
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (q) { if (c === '"') { if (text[i + 1] === '"') { cur += '"'; i++; } else q = false; } else cur += c; }
    else if (c === '"') q = true;
    else if (c === ',') { row.push(cur); cur = ''; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; row.push(cur); rows.push(row); row = []; cur = ''; }
    else cur += c;
  }
  if (cur !== '' || row.length) { row.push(cur); rows.push(row); }
  return rows.filter((r) => r.some((x) => x.trim() !== ''));
}
async function readCaptionTables(files) {
  const byName = new Map();
  for (const f of files) {
    const base = f.name.toLowerCase();
    try {
      if (base.endsWith('.csv')) {
        const rows = parseCsv(await f.text());
        if (!rows.length) continue;
        const head = rows[0].map((x) => x.trim().toLowerCase());
        const fi = head.findIndex((x) => ['file', 'filename', 'image', 'name', 'path'].includes(x));
        const ci = head.findIndex((x) => ['caption', 'text', 'prompt', 'description', 'label'].includes(x));
        const useHead = fi >= 0 && ci >= 0;
        for (const r of rows.slice(useHead ? 1 : 0)) {
          const fn = (r[useHead ? fi : 0] || '').trim().split(/[\\/]/).pop().toLowerCase();
          const cap = (r[useHead ? ci : 1] || '').trim();
          if (fn && cap) byName.set(fn, cap);
        }
      } else if (base.endsWith('.txt')) {
        const t = (await f.text()).trim();
        if (t) byName.set(base.replace(/\.txt$/, ''), t.split(/\r?\n/)[0].trim());
      }
    } catch (e) { /* unreadable table: ignore */ }
  }
  return byName;
}
async function addFiles(fileList) {
  const all = Array.from(fileList);
  const imgs = all.filter((f) => IMG_RE.test(f.name));
  if (!imgs.length) { banner('No png / jpg / bmp images in that selection.', true); return; }
  banner('');
  const tables = await readCaptionTables(all.filter((f) => /\.(csv|txt)$/i.test(f.name)));
  state.zip = null; $('#zip-note').hidden = true;
  for (const f of imgs) {
    if (state.items.length >= MAX_ITEMS) { banner('Only the first ' + MAX_ITEMS + ' images are used.', false); break; }
    const stem = f.name.toLowerCase();
    const cap = tables.get(stem) || tables.get(stem.replace(/\.[^.]+$/, '')) || nameToCaption(f.name);
    state.items.push({ file: f, caption: cap, url: URL.createObjectURL(f) });
  }
  renderItems();
}
function renderItems() {
  const box = $('#items'); clear(box);
  state.items.forEach((it, i) => {
    const input = h('input', { type: 'text', value: it.caption, maxlength: '200', placeholder: 'what does this show?', 'aria-label': 'caption for ' + it.file.name });
    input.addEventListener('input', () => { it.caption = input.value; updateTrainButton(); });
    box.append(h('div', { class: 'item' }, h('img', { src: it.url, alt: '', loading: 'lazy' }),
      h('div', { class: 'col' }, h('div', { class: 'fn', text: it.file.name }), input),
      h('button', { type: 'button', title: 'Remove', 'aria-label': 'Remove ' + it.file.name, text: '×', onclick: () => { URL.revokeObjectURL(it.url); state.items.splice(i, 1); renderItems(); } })));
  });
  $('#bulk').hidden = !state.items.length; $('#clear-items').hidden = !(state.items.length || state.zip);
  updateTrainButton();
}
function updateTrainButton() {
  const missing = state.items.filter((i) => !i.caption.trim()).length;
  $('#train-go').disabled = state.trainBusy || !(state.health && state.health.training_enabled) || !(state.items.length || state.zip);
  if (!state.trainBusy) $('#train-busy').textContent = state.items.length
    ? state.items.length + ' image(s)' + (missing ? ', ' + missing + ' without a caption (the file name will be used)' : '') : '';
}
$('#pick-images').addEventListener('change', (e) => { addFiles(e.target.files); e.target.value = ''; });
$('#pick-folder').addEventListener('change', (e) => { addFiles(e.target.files); e.target.value = ''; });
$('#pick-zip').addEventListener('change', (e) => {
  const f = e.target.files[0]; e.target.value = '';
  if (!f) return;
  state.items.forEach((i) => URL.revokeObjectURL(i.url)); state.items = []; state.zip = f;
  const note = $('#zip-note'); note.hidden = false;
  note.textContent = 'Using ' + f.name + ' (' + (f.size / 1048576).toFixed(1) + ' MB). It should contain images plus captions.csv (file,caption), captions.json or a .txt next to each image.';
  renderItems();
});
$('#clear-items').addEventListener('click', () => { state.items.forEach((i) => URL.revokeObjectURL(i.url)); state.items = []; state.zip = null; $('#zip-note').hidden = true; renderItems(); });
$('#bulk-go').addEventListener('click', () => {
  const t = $('#bulk-text').value.trim(); if (!t) return;
  state.items.forEach((it) => { if (!it.caption.trim()) it.caption = t; }); renderItems();
});

// ------------------------------------------------------------------------------------------------ training: zip in the browser
const CRC = (() => { const t = new Uint32Array(256); for (let n = 0; n < 256; n++) { let c = n; for (let k = 0; k < 8; k++) c = c & 1 ? 0xEDB88320 ^ (c >>> 1) : c >>> 1; t[n] = c >>> 0; } return t; })();
function crc32(u8) { let c = 0xFFFFFFFF; for (let i = 0; i < u8.length; i++) c = CRC[(c ^ u8[i]) & 255] ^ (c >>> 8); return (c ^ 0xFFFFFFFF) >>> 0; }
function makeZip(entries) {          // entries: [{name, data: Uint8Array}] -> Blob (stored, UTF-8 names)
  const enc = new TextEncoder(), parts = [], central = [];
  let offset = 0;
  for (const e of entries) {
    const nm = enc.encode(e.name), crc = crc32(e.data), size = e.data.length;
    const lh = new DataView(new ArrayBuffer(30));
    lh.setUint32(0, 0x04034b50, true); lh.setUint16(4, 20, true); lh.setUint16(6, 0x0800, true); lh.setUint16(8, 0, true);
    lh.setUint16(10, 0, true); lh.setUint16(12, 0x21, true); lh.setUint32(14, crc, true); lh.setUint32(18, size, true);
    lh.setUint32(22, size, true); lh.setUint16(26, nm.length, true); lh.setUint16(28, 0, true);
    parts.push(lh.buffer, nm, e.data);
    const ch = new DataView(new ArrayBuffer(46));
    ch.setUint32(0, 0x02014b50, true); ch.setUint16(4, 20, true); ch.setUint16(6, 20, true); ch.setUint16(8, 0x0800, true);
    ch.setUint16(10, 0, true); ch.setUint16(12, 0, true); ch.setUint16(14, 0x21, true); ch.setUint32(16, crc, true);
    ch.setUint32(20, size, true); ch.setUint32(24, size, true); ch.setUint16(28, nm.length, true); ch.setUint32(42, offset, true);
    central.push(ch.buffer, nm);
    offset += 30 + nm.length + size;
  }
  const csize = central.reduce((a, b) => a + b.byteLength, 0);
  const end = new DataView(new ArrayBuffer(22));
  end.setUint32(0, 0x06054b50, true); end.setUint16(8, entries.length, true); end.setUint16(10, entries.length, true);
  end.setUint32(12, csize, true); end.setUint32(16, offset, true);
  return new Blob([...parts, ...central, end.buffer], { type: 'application/zip' });
}
function csvCell(s) { return /[",\n\r]/.test(s) ? '"' + s.replace(/"/g, '""') + '"' : s; }
async function buildZip(items) {
  const used = new Set(), entries = [], rows = ['file,caption'];
  for (const it of items) {
    let name = it.file.name.replace(/[\\/:*?"<>|]+/g, '_'), n = 2;
    const dot = name.lastIndexOf('.'), stem = dot > 0 ? name.slice(0, dot) : name, ext = dot > 0 ? name.slice(dot) : '';
    while (used.has(name.toLowerCase())) name = stem + '-' + (n++) + ext;
    used.add(name.toLowerCase());
    entries.push({ name, data: new Uint8Array(await it.file.arrayBuffer()) });
    if (it.caption.trim()) rows.push(csvCell(name) + ',' + csvCell(it.caption.trim()));
  }
  entries.push({ name: 'captions.csv', data: new TextEncoder().encode(rows.join('\n') + '\n') });
  return makeZip(entries);
}

// ------------------------------------------------------------------------------------------------ training: run + poll
$('#train-go').addEventListener('click', async () => {
  if (state.trainBusy) return;
  banner('');
  state.trainBusy = true; updateTrainButton();
  const job = $('#job'); job.hidden = false; $('#job-result').replaceChildren(); setJob(3, 'Packing your images…');
  try {
    const blob = state.zip || await buildZip(state.items);
    const q = new URLSearchParams({
      epochs: String(numv('#epochs', 80)), fresh: $('#fresh').checked, refit: $('#refit').checked,
      lr: $('#lr').value || '0.3', val_frac: $('#valfrac').value || '0.15', grid: String(numv('#grid', 16)),
    });
    setJob(6, 'Uploading ' + (blob.size / 1048576).toFixed(1) + ' MB…');
    const acc = await api('/train?' + q, { method: 'POST', body: blob, headers: { 'Content-Type': 'application/zip' } });
    finishJob(await poll(acc.job_id));
    loadJobHistory();
  } catch (e) {
    setJob(0, ''); job.hidden = true;
    banner(e.status === 409 ? 'A training job is already running. Wait for it to finish.' : e.message, true);
  } finally {
    state.trainBusy = false; updateTrainButton(); refreshHealth();
  }
});
function setJob(pct, text) { $('#job-bar').style.width = pct + '%'; $('#job-text').textContent = text; }
async function poll(id, setter = setJob) {
  for (;;) {
    const j = await api('/jobs/' + encodeURIComponent(id));
    const pct = { queued: 8, extracting: 12, reading: 25, training: 25 + 70 * (j.epoch || 0) / Math.max(1, j.epochs || 1), done: 100, error: 100 }[j.status] ?? 10;
    let msg = j.message || j.status;
    if (j.status === 'training' && j.train_rmse != null) msg += ' · train error ' + j.train_rmse.toFixed(4) + (j.val_rmse != null ? ' · validation error ' + j.val_rmse.toFixed(4) : '');
    setter(pct, msg);
    if (j.status === 'done') return j;
    if (j.status === 'error') { throw new Error(j.error && j.error.message ? j.error.message : 'Training failed'); }
    await new Promise((r) => setTimeout(r, 700));
  }
}
function finishJob(j) {
  const out = $('#job-result'); clear(out);
  const m = j.metrics || {};
  out.append(h('p', { class: 'ok', text: 'Training finished. ' + (m.samples != null ? m.samples + ' images in the model' : '') + (m.added != null ? ' (' + m.added + ' new)' : '') + '.' }));
  if (m.val_rmse != null) {
    out.append(h('p', { class: 'hint', text: 'Error on images it did not train on: ' + m.val_rmse + (m.baseline_rmse != null ? ' (a model that knew nothing would score ' + m.baseline_rmse + (m.improvement_percent != null ? ', so ' + m.improvement_percent + '% lower' : '') + ')' : '') + '. Lower is better.' }));
  } else if (m.samples != null && m.samples < 10) {
    out.append(h('p', { class: 'hint', text: 'With fewer than 10 images there is nothing to test on; add more images to see an error figure.' }));
  }
  if (j.skipped_count) {
    const d = h('details', {}, h('summary', { text: j.skipped_count + ' file(s) were skipped' }));
    (j.skipped || []).slice(0, 50).forEach((s) => d.append(h('div', { class: 'hint', text: (s.file || s.name || '') + ': ' + (s.reason || '') })));
    out.append(d);
  }
  out.append(h('div', { class: 'actions' },
    h('button', { class: 'primary', type: 'button', text: 'Try it on the Create tab', onclick: () => { showTab('create'); $('#learned').value = 'always'; $('#prompt').focus(); } }),
    h('button', { class: 'ghost', type: 'button', text: 'See what it learned', onclick: () => showTab('model') })));
}

// ------------------------------------------------------------------------------------------------ model tab
async function loadModel() {
  try {
    const m = await api('/model');
    $('#model-empty').hidden = m.loaded; $('#model-body').hidden = !m.loaded;
    if (!m.loaded) return;
    const stats = $('#model-stats'); clear(stats);
    const meta = m.meta || {};
    const cells = [['images', m.samples], ['words', m.vocabulary], ['grid', m.grid + '×' + m.grid], ['epochs', meta.epochs],
      ['better than knowing nothing', meta.val_mse != null && meta.baseline_val ? Math.round(100 * (1 - meta.val_mse / meta.baseline_val)) + '%' : null]].filter((c) => c[1] != null);
    cells.forEach(([k, v]) => stats.append(h('div', { class: 'stat' }, h('b', { text: typeof v === 'number' && !Number.isInteger(v) ? v.toFixed(4) : String(v) }), h('span', { text: k }))));
    const tw = $('#top-words'); clear(tw);
    m.top_words.forEach((w) => { const sw = h('span', { class: 'sw' }); sw.style.background = w.color; tw.append(h('span', { class: 'chip static', title: w.captions + ' caption(s)' }, sw, w.word)); });
  } catch (e) { banner(e.message, true); }
}
$('#probe-go').addEventListener('click', async () => {
  const text = $('#probe').value.trim(); if (!text) return;
  const out = $('#probe-out'); clear(out);
  try {
    const p = await api('/parse', { method: 'POST', json: { prompt: text } });
    if (p.model_knows.length) p.model_knows.forEach((w) => out.append(h('span', { class: 'chip static ok', text: '✓ ' + w })));
    else out.append(h('span', { class: 'hint', text: 'None of these words appear in your training captions.' }));
    p.not_in_lexicon.filter((w) => !p.model_knows.includes(w)).forEach((w) => out.append(h('span', { class: 'chip static bad', text: '✗ ' + w })));
  } catch (e) { banner(e.message, true); }
});
$('#probe').addEventListener('keydown', (e) => { if (e.key === 'Enter') $('#probe-go').click(); });
$('#curl-sample').textContent = 'curl -X POST ' + location.origin + '/generate -H "Content-Type: application/json" \\\n  -d \'{"prompt":"red house near a lake","size":512}\' -o out.png\n\n' +
  'curl -X POST ' + location.origin + '/create -H "Content-Type: application/json" \\\n  -d \'{"prompt":"laptop and coffee cup","temperature":0.8}\' -o creative.png';


// ------------------------------------------------------------------------------------------------ images that need the API key
async function loadImg(img, url) {
  if (!state.key) { img.src = url; return; }
  const u = await fetchBlobUrl(url);
  if (u) img.src = u;
}
async function fetchBlobUrl(url) {
  try {
    const r = await fetch(url, { headers: state.key ? { 'X-API-Key': state.key } : {} });
    return r.ok ? URL.createObjectURL(await r.blob()) : null;
  } catch (e) { return null; }
}
const when = (t) => (t ? new Date(t * 1000).toLocaleString() : '');

// ------------------------------------------------------------------------------------------------ gallery
const gal = { offset: 0, total: 0, fav: false, q: '', cur: null, timer: null };
async function loadGallery(reset) {
  if (!state.health || !state.health.database) return;
  if (reset) { gal.offset = 0; clear($('#gal-grid')); }
  try {
    const q = new URLSearchParams({ limit: '48', offset: String(gal.offset), favourites: String(gal.fav) });
    if (gal.q) q.set('q', gal.q);
    const d = await api('/gallery?' + q);
    gal.total = d.total;
    d.items.forEach((it) => $('#gal-grid').append(galleryTile(it)));
    gal.offset += d.items.length;
    $('#gal-more').hidden = gal.offset >= d.total;
    $('#gal-count').textContent = d.total + ' picture' + (d.total === 1 ? '' : 's');
    $('#gal-empty').hidden = d.total > 0;
  } catch (e) { banner(e.message, true); }
}
function galleryTile(it) {
  const img = h('img', { alt: it.prompt_used || it.prompt, loading: 'lazy' });
  loadImg(img, '/gallery/' + it.id + '/thumb');
  const t = h('button', { class: 'tile', type: 'button', title: (it.prompt_used || it.prompt) + ' (seed ' + it.seed + ')', onclick: () => openGallery(it.id) },
    img, h('span', { class: 'badge', text: it.kind === 'plain' ? it.mode : it.kind }), it.favourite ? h('span', { class: 'star', text: '★' }) : null,
    h('div', { class: 'cap', text: it.prompt_used || it.prompt || '(random mash-up)' }));
  t.dataset.id = it.id;
  return t;
}
$$('#gal-filter button').forEach((b) => b.addEventListener('click', () => {
  gal.fav = b.dataset.fav === '1';
  $$('#gal-filter button').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-checked', x === b); });
  loadGallery(true);
}));
$('#gal-q').addEventListener('input', () => { clearTimeout(gal.timer); gal.timer = setTimeout(() => { gal.q = $('#gal-q').value.trim(); loadGallery(true); }, 300); });
$('#gal-more').addEventListener('click', () => loadGallery(false));
$('#gal-clear').addEventListener('click', async () => {
  if (!confirm('Delete every picture that is not a favourite? This cannot be undone.')) return;
  try {
    const r = await api('/gallery?keep_favourites=true', { method: 'DELETE' });
    banner(r.deleted + ' picture(s) deleted.', false); setTimeout(() => banner(''), 2500); loadGallery(true);
  } catch (e) { banner(e.message, true); }
});
async function openGallery(id) {
  try {
    const it = await api('/gallery/' + id);
    gal.cur = it;
    const dlg = $('#gal-dialog');
    $('#gd-img').removeAttribute('src'); loadImg($('#gd-img'), '/gallery/' + id + '/image');
    $('#gd-title').textContent = it.prompt_used || it.prompt || '(random mash-up)';
    $('#gd-meta').textContent = [it.kind === 'plain' ? it.mode : it.kind, it.width + 'x' + it.height, 'seed ' + it.seed, when(it.created)].join(' · ') +
      (it.prompt && it.prompt_used && it.prompt !== it.prompt_used ? ' · you typed: ' + it.prompt : '');
    const ul = $('#gd-think'); clear(ul);
    ((it.creation && it.creation.thinking) || []).forEach((l) => ul.append(h('li', { class: l.startsWith('  ') ? 'sub' : '', text: l.trim() })));
    setFavButton(it.favourite);
    const dl = $('#gd-dl'); dl.removeAttribute('href'); dl.download = 'pixelmath-' + id + '.png';
    fetchBlobUrl('/gallery/' + id + '/image').then((u) => { if (u) dl.href = u; });
    if (typeof dlg.showModal === 'function' && !dlg.open) dlg.showModal();
  } catch (e) { banner(e.message, true); }
}
function setFavButton(on) { $('#gd-fav').textContent = on ? '★ Favourite' : '☆ Favourite'; }
$('#gd-close').addEventListener('click', () => $('#gal-dialog').close());
$('#gd-fav').addEventListener('click', async () => {
  if (!gal.cur) return;
  try {
    const r = await api('/gallery/' + gal.cur.id + '/favourite', { method: 'POST', json: { favourite: !gal.cur.favourite } });
    gal.cur.favourite = r.favourite; setFavButton(r.favourite);
    const tile = $('#gal-grid .tile[data-id="' + gal.cur.id + '"]');
    if (tile) { const old = $('.star', tile); if (old) old.remove(); if (r.favourite) tile.append(h('span', { class: 'star', text: '★' })); }
  } catch (e) { banner(e.message, true); }
});
$('#gd-del').addEventListener('click', async () => {
  if (!gal.cur || !confirm('Delete this picture?')) return;
  try { await api('/gallery/' + gal.cur.id, { method: 'DELETE' }); $('#gal-dialog').close(); loadGallery(true); }
  catch (e) { banner(e.message, true); }
});
$('#gd-use').addEventListener('click', () => {
  if (!gal.cur) return;
  $('#prompt').value = gal.cur.prompt_used || gal.cur.prompt; $('#seed').value = gal.cur.seed;
  if (gal.cur.params && gal.cur.params.size) $('#size').value = String(gal.cur.params.size);
  setMode('plain'); $('#gal-dialog').close(); showTab('create'); $('#prompt').focus();
});

// ------------------------------------------------------------------------------------------------ dataset manager
const ds = { offset: 0, total: 0, q: '', sel: new Set(), timer: null, busy: false };
async function loadDataset(reset) {
  if (reset) { ds.offset = 0; clear($('#ds-grid')); ds.sel.clear(); updateDsButtons(); }
  try {
    const q = new URLSearchParams({ limit: '60', offset: String(ds.offset) });
    if (ds.q) q.set('q', ds.q);
    const d = await api('/dataset?' + q);
    ds.total = d.total;
    d.items.forEach((it) => $('#ds-grid').append(datasetTile(it)));
    ds.offset += d.items.length;
    $('#ds-more').hidden = ds.offset >= d.total;
    $('#ds-count').textContent = d.total + ' image' + (d.total === 1 ? '' : 's');
    $('#ds-empty').hidden = d.total > 0 || !!ds.q;
  } catch (e) { banner(e.message, true); }
}
function datasetTile(it) {
  const img = h('img', { alt: it.caption, loading: 'lazy' });
  loadImg(img, '/dataset/' + it.id + '/image');
  const pick = h('input', { type: 'checkbox', class: 'pick', 'aria-label': 'select ' + it.caption });
  const capText = h('span', { text: it.caption });
  const editBtn = h('button', { class: 'edit', type: 'button', text: 'edit caption' });
  const note = it.file ? h('span', { class: 'file', title: it.file, text: it.file }) : h('span', { class: 'file', text: it.original_preview ? '' : 'colour preview only' });
  const tile = h('div', { class: 'tile' }, img, pick, h('div', { class: 'cap' }, capText, note, editBtn));
  pick.addEventListener('change', () => { pick.checked ? ds.sel.add(it.id) : ds.sel.delete(it.id); tile.classList.toggle('sel', pick.checked); updateDsButtons(); });
  editBtn.addEventListener('click', () => {
    const input = h('input', { type: 'text', value: it.caption, maxlength: '200', 'aria-label': 'new caption' });
    capText.replaceWith(input); editBtn.hidden = true; input.focus(); input.select();
    const finish = async (save) => {
      const v = input.value.trim();
      if (!save || !v || v === it.caption) { input.replaceWith(capText); editBtn.hidden = false; return; }
      input.disabled = true;
      try { const acc = await api('/dataset/' + it.id + '/caption', { method: 'POST', json: { caption: v } }); await trackRebuild(acc.job_id); }
      catch (e) { banner(e.status === 409 ? 'Training is busy. Try again in a moment.' : e.message, true); input.replaceWith(capText); editBtn.hidden = false; }
    };
    input.addEventListener('keydown', (e) => { if (e.key === 'Enter') finish(true); else if (e.key === 'Escape') finish(false); });
    input.addEventListener('blur', () => { if (!input.disabled) finish(false); });
  });
  return tile;
}
function updateDsButtons() {
  $('#ds-delete').disabled = ds.busy || !ds.sel.size;
  $('#ds-delete').textContent = ds.sel.size ? 'Delete selected (' + ds.sel.size + ')' : 'Delete selected';
}
async function trackRebuild(jobId) {
  ds.busy = true; updateDsButtons();
  const box = $('#ds-job'); box.hidden = false;
  const setter = (pct, text) => { $('#ds-bar').style.width = pct + '%'; $('#ds-text').textContent = text; };
  try {
    await poll(jobId, setter);
    setter(100, 'Done. The model was retrained.');
    setTimeout(() => { box.hidden = true; }, 2500);
    await refreshHealth(); loadDataset(true); loadJobHistory();
  } catch (e) { box.hidden = true; banner(e.message, true); }
  finally { ds.busy = false; updateDsButtons(); }
}
$('#ds-q').addEventListener('input', () => { clearTimeout(ds.timer); ds.timer = setTimeout(() => { ds.q = $('#ds-q').value.trim(); loadDataset(true); }, 300); });
$('#ds-more').addEventListener('click', () => loadDataset(false));
$('#ds-all').addEventListener('click', () => $$('#ds-grid .pick').forEach((c) => { if (!c.checked) c.click(); }));
$('#ds-delete').addEventListener('click', async () => {
  const ids = Array.from(ds.sel);
  if (!ids.length) return;
  const all = ids.length >= ds.total && !ds.q;
  if (!confirm(all ? 'This removes ALL trained images and resets the model (the old model file is kept as .bak). Continue?'
    : 'Remove ' + ids.length + ' image(s) from the training data and retrain the model?')) return;
  try { const acc = await api('/dataset/delete', { method: 'POST', json: { ids } }); await trackRebuild(acc.job_id); }
  catch (e) { banner(e.status === 409 ? 'Training is busy. Try again in a moment.' : e.message, true); }
});

// ------------------------------------------------------------------------------------------------ training history
async function loadJobHistory() {
  try {
    const d = await api('/jobs');
    const box = $('#job-history'); clear(box);
    $('#history-card').hidden = !d.jobs.length;
    d.jobs.slice(0, 15).forEach((j) => {
      const m = j.metrics || {};
      const detail = j.status === 'done'
        ? (j.kind === 'rebuild' ? 'retrained after editing the dataset' : (m.added != null ? m.added + ' new image(s)' : '')) +
          (m.samples != null ? ' · ' + m.samples + ' in model' : '') +
          (m.improvement_percent != null ? ' · ' + m.improvement_percent + '% better than knowing nothing' : '')
        : (j.error && j.error.message) || j.message || '';
      box.append(h('div', { class: 'jobrow' }, h('span', { class: 'st ' + j.status, text: j.status }),
        h('span', { text: (j.kind === 'rebuild' ? 'edit' : 'train') + ' · ' + detail }), h('span', { class: 'muted', text: when(j.created) })));
    });
  } catch (e) { /* history is a convenience */ }
}


// ------------------------------------------------------------------------------------------------ studio: website pictures
const st = { ready: false, kind: 'one', images: [], cur: 0, ctrl: null, busy: false, zone: null, textColor: null };
const ST_EXAMPLES = ['wood fired pizza on a board', 'gym with dumbbells in red light', 'dental clinic reception, calm blue', 'kurti store, ethnic wear',
  'B2B SaaS analytics dashboard', 'bakery with sourdough and croissants', 'yoga and meditation studio', 'luxury real estate apartments', 'school with smart classrooms',
  'मिठाई की दुकान', 'daant ka doctor', 'submarine under the sea'];
const ZONE_BOX = { left: [0.05, 0.14, 0.50, 0.86], center: [0.14, 0.20, 0.86, 0.56], bottom: [0.05, 0.64, 0.95, 0.94] };

async function initStudio() {
  if (st.ready) return;
  st.ready = true;
  ST_EXAMPLES.forEach((t) => $('#st-chips').append(h('button', { class: 'chip', type: 'button', text: t, onclick: () => { $('#st-prompt').value = t; $('#st-prompt').focus(); } })));
  try {
    const d = await api('/niches');
    d.niches.sort((a, b) => a.title.localeCompare(b.title)).forEach((n) => $('#st-niche').append(h('option', { value: n.id, text: n.title })));
  } catch (e) { banner(e.message, true); }
}
$$('#st-kind button').forEach((b) => b.addEventListener('click', () => {
  st.kind = b.dataset.kind;
  $$('#st-kind button').forEach((x) => { x.classList.toggle('on', x === b); x.setAttribute('aria-checked', x === b); });
  $('#st-size-wrap').hidden = st.kind === 'set'; $('#st-count-wrap').hidden = st.kind !== 'set';
  $('#st-go').textContent = st.kind === 'set' ? 'Create site set' : 'Create';
}));
$('#st-go').addEventListener('click', () => studioGo());
$('#st-prompt').addEventListener('keydown', (e) => { if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) { e.preventDefault(); studioGo(); } });
$('#st-cancel').addEventListener('click', () => { if (st.ctrl) st.ctrl.abort(); });
$('#st-toggle').addEventListener('click', () => { const o = $('#st-overlay'); o.hidden = !o.hidden; $('#st-toggle').textContent = o.hidden ? 'Show sample text' : 'Hide sample text'; });

function studioBody() {
  const body = { prompt: $('#st-prompt').value.trim(), seed: Math.max(0, numv('#st-seed', 1)), response: 'base64' };
  const zone = $('#st-zone').value;
  body.text_zone = zone;
  if ($('#st-niche').value) body.niche = $('#st-niche').value;
  if ($('#st-mood').value) body.mood = $('#st-mood').value;
  if ($('#st-accent-on').checked) body.accent = $('#st-accent').value;
  if (st.kind === 'set') body.count = numv('#st-count', 6);
  else { const [w, hh] = $('#st-size').value.split('x').map(Number); body.width = w; body.height = hh; }
  return body;
}

async function studioGo() {
  if (st.busy) return;
  const body = studioBody();
  if (!body.prompt && !body.niche) { banner('Describe the business first.', true); return; }
  if (!body.prompt) body.prompt = $('#st-niche').selectedOptions[0].textContent;
  banner('');
  st.busy = true; st.ctrl = new AbortController();
  $('#st-go').disabled = true; $('#st-cancel').hidden = false;
  const t0 = Date.now();
  const tick = () => { $('#st-busy').replaceChildren(h('span', { class: 'spin' }), ((Date.now() - t0) / 1000).toFixed(1) + ' s'); };
  tick(); const timer = setInterval(tick, 200);
  try {
    const data = await api(st.kind === 'set' ? '/set' : '/scene', { method: 'POST', json: body, signal: st.ctrl.signal });
    st.kind === 'set' ? showStudioSet(data, body) : showStudioOne(data, body);
  } catch (e) {
    if (e.name === 'AbortError') banner('Cancelled.', false); else banner(e.status === 503 ? 'The server is busy. Try again in a moment.' : e.message, true);
  } finally {
    clearInterval(timer); st.busy = false; st.ctrl = null; $('#st-go').disabled = false; $('#st-cancel').hidden = true; $('#st-busy').textContent = '';
  }
}

function showStudioOne(data, body) {
  const item = { src: 'data:' + data.mime + ';base64,' + data.image_base64, report: data.report, file: 'picture.jpg', w: data.width, h: data.height, bytes: atob(data.image_base64).length };
  st.images = [item]; st.cur = 0;
  $('#st-set').hidden = true; $('#st-zip').hidden = true;
  renderStudioMain(item, data.render_seconds);
}

function showStudioSet(data, body) {
  st.images = data.images.map((im) => ({ src: 'data:' + im.mime + ';base64,' + im.image_base64, file: im.file, role: im.role, w: im.width, h: im.height,
    report: data.report.images.find((r) => r.file === im.file) || {}, bytes: atob(im.image_base64).length }));
  st.setReport = data.report; st.cur = 0;
  const grid = $('#st-set'); clear(grid); grid.hidden = false;
  st.images.forEach((im, i) => {
    const fig = h('figure', { class: i === 0 ? 'cur' : '', title: im.file }, h('img', { src: im.src, alt: im.file }),
      h('figcaption', { text: im.file + ' · ' + im.w + '×' + im.h + ' · ' + Math.round(im.bytes / 1024) + ' KB' }));
    fig.addEventListener('click', () => { st.cur = i; $$('figure', grid).forEach((f, k) => f.classList.toggle('cur', k === i)); renderStudioMain(im, null); });
    grid.append(fig);
  });
  $('#st-zip').hidden = false;
  renderStudioMain(st.images[0], data.report.seconds);
  const r = data.report;
  const note = $('#st-banner'); note.hidden = false; note.className = 'notice ok';
  note.textContent = r.fallback ? '' : 'Set judged: smallest difference between two pictures ' + r.min_distance + ' bits (needs 14), palette family ' + r.palette_family +
    ', hero text contrast ' + r.hero_contrast + ' (needs 4.5), ' + r.redrawn + ' redraw(s), ' + r.seconds + ' s.';
  if (r.fallback) fallbackNote(r.images[0]);
}

function fallbackNote(rep) {
  const note = $('#st-banner'); note.hidden = false; note.className = 'notice';
  note.textContent = 'No business type fits these words (' + (rep.fallback_reason || 'not recognised') + '), so this is a neutral abstract in the accent colour instead of a wrong picture. Try adding the kind of business or choose a niche.';
}

function renderStudioMain(item, secs) {
  $('#st-empty').hidden = true; $('#st-out').hidden = false;
  $('#st-img').src = item.src;
  const dl = $('#st-dl'); dl.href = item.src; dl.download = item.file;
  const r = item.report || {};
  const banner_ = $('#st-banner');
  if (st.kind === 'one') { banner_.hidden = true; if (r.fallback) fallbackNote(r); }
  $('#st-meta').textContent = [r.title || '', item.w + '×' + item.h, Math.round(item.bytes / 1024) + ' KB', 'mood ' + (r.mood || ''), 'accent ' + (r.accent || ''), secs ? secs + ' s' : ''].filter(Boolean).join(' · ');
  // sample headline on the text zone, in the colour the judge recommends: the quickest way to see the contrast with your own eyes
  const o = $('#st-overlay');
  const zone = r.text_zone && ZONE_BOX[r.text_zone];
  if (zone && r.text_color) {
    o.hidden = false; $('#st-toggle').hidden = false; $('#st-toggle').textContent = 'Hide sample text';
    o.style.left = zone[0] * 100 + '%'; o.style.top = zone[1] * 100 + '%'; o.style.width = (zone[2] - zone[0]) * 100 + '%'; o.style.height = (zone[3] - zone[1]) * 100 + '%';
    o.style.color = r.text_color;
  } else { o.hidden = true; $('#st-toggle').hidden = true; }
  const rep = $('#st-report'); clear(rep);
  const cell = (k, v, sub) => h('div', {}, h('b', { text: String(v) }), h('span', { text: k + (sub ? ' · ' + sub : '') }));
  const box = h('div', { class: 'rep' });
  box.append(cell('niche', r.niche || 'none (fallback)'), cell('fallback', r.fallback ? 'yes' : 'no'));
  if (r.contrast) {
    const sw = h('span', { class: 'sw' }); sw.style.background = r.text_color;
    box.append(h('div', {}, h('b', {}, sw, r.text_color), h('span', { text: 'text colour for the ' + r.text_zone + ' area' })), cell('text contrast', r.contrast + ':1', 'needs 4.5'));
  }
  box.append(cell('redrawn by the judge', r.redrawn == null ? '' : r.redrawn));
  Object.entries(r.scores || {}).forEach(([k, v]) => box.append(cell('score ' + k.replace('_', ' '), typeof v === 'number' ? v.toFixed(2) : v)));
  rep.append(box);
}

$('#st-zip').addEventListener('click', async () => {
  if (!st.images.length) return;
  const entries = st.images.map((im) => ({ name: im.file, data: Uint8Array.from(atob(im.src.split(',')[1]), (c) => c.charCodeAt(0)) }));
  entries.push({ name: 'report.json', data: new TextEncoder().encode(JSON.stringify(st.setReport || {}, null, 2)) });
  const url = URL.createObjectURL(makeZip(entries));
  const a = h('a', { href: url, download: 'site-pictures.zip' }); document.body.append(a); a.click(); a.remove();
  setTimeout(() => URL.revokeObjectURL(url), 5000);
});

// ------------------------------------------------------------------------------------------------ boot
$('#prompt').value = store.get('pm_prompt', $('#prompt').value);
$('#prompt').addEventListener('input', () => store.set('pm_prompt', $('#prompt').value));
setMode(['plain', 'creative', 'imagine'].includes(state.mode) ? state.mode : 'plain');
refreshHealth();
setInterval(() => { if (!state.busy && !state.trainBusy) refreshHealth(); }, 15000);
})();
