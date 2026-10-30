(() => {
'use strict';
let SITE = {};
try { SITE = JSON.parse(document.getElementById('site-data').textContent) || {}; } catch (_) {}
const PAGES = SITE.mode === 'pages';
const ARTIFACT_URL = PAGES ? (SITE.url || location.href.split('#')[0]) : 'https://claude.ai/artifact/7zZixgAnh8J2dPf5MX9Hdq';
const RAW = JSON.parse(document.getElementById('data').textContent);
const SINCE = JSON.parse(document.getElementById('since-data').textContent).sort((a, b) => a.date.localeCompare(b.date));
const DISPUTED = JSON.parse(document.getElementById('disputed-data').textContent);
const THREADS = JSON.parse(document.getElementById('threads-data').textContent);
const CENS = RAW.censures || [];
const QUALITY = RAW.quality || {};
const CURATED = RAW.curated || [];
const BOOKS = RAW.books.map(([name, test, aliases], i) => ({ i, name, test, aliases, refs: new Map(), count: 0 }));
const ERAS = RAW.eras.map((e, i) => ({ i, name: e.n, dates: e.d, sub: e.s, year: e.y, app: !!e.a, sup: !!e.sup, entries: [] }));
const ENTRIES = RAW.entries.map((r, k) => {
  const f = r[6] || {};
  return { k, id: r[0], era: ERAS[r[1]], ses: r[2], topic: r[3], src: r[4], paras: r[5], note: !!f.n, kinds: f.k || [], sc: f.s || [], weight: f.w || 'papal', cens: f.c === undefined ? null : f.c, cur: f.h === undefined ? null : f.h, sup: !!f.sup, links: f.L || [], ds: f.x || [], dsHow: f.xh || '', year: Math.abs(f.y || 0), yearExact: f.y > 0, citedBy: f.cb || [], rc: f.rc || [] };
});
const byId = new Map(), byBase = new Map(), byDS = new Map();
for (const e of ENTRIES) {
  for (const n of e.ds) { if (!byDS.has(+n)) byDS.set(+n, []); byDS.get(+n).push(e); }
  e.era.entries.push(e);
  byId.set(e.id, e);
  const base = parseInt(e.id, 10);
  if (!byBase.has(base)) byBase.set(base, e);
}
const norm = s => s.normalize('NFD').replace(/[̀-ͯ]/g, '').toLowerCase().replace(/[^a-z0-9]+/g, ' ');
for (const e of ENTRIES) {
  e.hay = ' ' + norm(e.paras.join(' ')) + ' ';
  e.meta = ' ' + norm((e.topic || '') + ' ' + (e.src || '') + ' ' + e.era.name) + ' ';
  const seen = new Set();
  for (const [b, c, v] of e.sc) {
    const key = c + ':' + v;
    const bk = BOOKS[b];
    if (!bk.refs.has(c)) bk.refs.set(c, new Map());
    const ch = bk.refs.get(c);
    if (!ch.has(v)) ch.set(v, []);
    if (!seen.has(b + ':' + key)) { ch.get(v).push(e); bk.count++; seen.add(b + ':' + key); }
  }
}
/* which guide items discuss each entry */
const DISCUSSED = new Map();
const addDisc = (id, item) => { if (!DISCUSSED.has(id)) DISCUSSED.set(id, []); DISCUSSED.get(id).push(item); };
for (const d of DISPUTED) for (const r of d.refs) addDisc(r, { href: '#q-' + d.id, label: d.title, kind: 'Disputed question' });
for (const s of SINCE) for (const r of s.refs) addDisc(r, { href: '#since-' + s.id, label: s.title, kind: 'Since 1950' });
for (const t of THREADS) for (const st of t.steps) if (st.ref) addDisc(st.ref, { href: '#thread-' + t.id, label: t.title + ' (thread)', kind: 'Thread' });
const DISP_BY_ID = new Map(DISPUTED.map(d => [d.id, d]));
/* the Roman Catechism, chapter by chapter */
const RC = RAW.rc || { parts: [] };
const RC_CH = new Map();
for (const p of RC.parts) for (const ch of p.chapters) RC_CH.set(ch.id, Object.assign({}, ch, { part: p }));
const RC_YEAR = 1566;
function rcShort(ch) {
  const m = ch.title.match(/^(Article \d+|\w+ and \w+ Commandments|\w+ Commandment|\w+ Petition|Introduction|The seal of the Lord's Prayer)/);
  const part = ch.part.title.replace(/^Part [IVX]+\.\s*/, '');
  return m ? `${part}, ${m[1]}` : `${part}: ${ch.title}`;
}
const SINCE_BY_ID = new Map(SINCE.map(s => [s.id, s]));

const kind = er => /^Creeds/.test(er.name) ? 'Creeds' : /Council|Synod/i.test(er.name) ? 'Council' : 'Pontificate';
const PERIODS = [
  ['All periods', 0, 9999], ['To 600', 0, 599], ['600–1100', 600, 1099], ['1100–1500', 1100, 1499],
  ['1500–1700', 1500, 1699], ['1700–1850', 1700, 1849], ['1850 on', 1850, 9999],
];
const KINDS = [
  ['', 'All kinds'],
  ['creed', 'Creeds'],
  ['definition', 'Defining formulas'],
  ['anathema', 'Anathemas'],
  ['condemned', 'Condemned propositions'],
  ['pbc', 'Biblical Commission'],
  ['curia', 'Holy Office & congregations'],
];
const KIND_LABEL = Object.fromEntries(KINDS);
const LEVELS = {
  dogma: ['Restates dogma', 'Repeats revealed doctrine already defined or held by divine and Catholic faith. Nothing new is defined.'],
  definitive: ['Definitive', 'Teaching to be firmly held as definitive, though not proposed as formally revealed.'],
  authentic: ['Authentic teaching', 'Owed religious submission of mind and will (Lumen Gentium 25), without being infallible.'],
  discipline: ['Discipline', 'Law, liturgy or practice. Binds in obedience and can be changed by competent authority.'],
  prudential: ['Prudential', 'Applications of principle to circumstances. Owed serious respect; reasoned disagreement is possible (Donum Veritatis 24).'],
  dialogue: ['Ecumenical agreement', 'A joint statement with other Christians, not a magisterial definition in itself.'],
  study: ['Study or address', 'A commission study, address or report. Weighty, but not binding in itself.'],
  private: ['Private opinion', 'An interview, press conference or book written as a private person. Not an act of the Magisterium; it carries the weight of its reasons.'],
};
const WEIGHTS = {
  'papal-def': ['Papal definition', 'dogma', 'A pope defining a doctrine of faith or morals to be held by the whole Church, in the form Vatican I describes (ex cathedra).'],
  'conc-def': ['Conciliar definition', 'dogma', 'An ecumenical council\'s creed or defining formula. What is proposed as to be believed is dogma; the reasons given for it are not themselves defined.'],
  'conc-canon': ['Conciliar canon', 'definitive', 'A canon of an ecumenical council, usually with an anathema. Most concern faith; some concern discipline, and theologians weigh each one by its content.'],
  'conc-decree': ['Conciliar decree', 'authentic', 'Doctrinal chapters, reform decrees and letters of an ecumenical council. Authoritative teaching; only what is proposed as defined is infallible.'],
  'papal-teaching': ['Papal teaching', 'authentic', 'Encyclicals, bulls and letters of popes. Owed religious assent; infallible only when the conditions of a definition are met or the teaching is otherwise definitive.'],
  'particular': ['Particular council', 'study', 'A regional council or synod. Its authority comes from its reception and from papal approval; some, like Orange II, became widely normative.'],
  'curia': ['Curial response', 'prudential', 'A reply or decree of the Holy Office or another Roman congregation, approved by the pope. Authoritative and binding in practice, not infallible. After 1958 the doctrinal documents of the Doctrine of the Faith have their own label.'],
  'pbc': ['Biblical Commission', 'prudential', 'A response of the Pontifical Biblical Commission (1902 onward). Binding as a disciplinary safeguard in its time; see the disputed question on these decrees.'],
  'condemned': ['Condemned proposition', 'definitive', 'A proposition the Church censured. What is rejected is the proposition in its condemned sense; its contradictory is not thereby defined, and the weight depends on the censure.'],
  'creed': ['Creed', 'dogma', 'A creed, profession of faith or the early formulas collected at the start of the book.'],
  'note': ['Editorial note', 'study', 'A cross-reference or note by the editors, not a text of the Magisterium.'],
  'cdf': ['Doctrine of the Faith', 'authentic', 'A doctrinal document of the Congregation (since 2022 the Dicastery) for the Doctrine of the Faith, approved by the pope and published by his order. Part of the ordinary Magisterium and owed religious assent; it is the pope\'s own act when he approves it in specific form.'],
  'liturgy': ['Liturgical norm', 'discipline', 'A rite, liturgical book or norm of the Roman congregations for worship. Binds as law and can be changed by competent authority; what it presupposes about the faith keeps its own weight.'],
  'catechism': ['Catechism', 'authentic', 'The Catechism of the Catholic Church (1992, Latin edition 1997), promulgated as "a sure norm for teaching the faith". Each statement keeps the weight of the teaching it presents.'],
  'papal-address': ['Address or homily', 'study', 'A pope\'s address, homily, message, catechesis or letter to a particular group. His ordinary teaching, but its weight depends on the manner of speaking and how often it is repeated (Lumen Gentium 25); less than an encyclical.'],
  'interview': ['Interview', 'private', 'An interview, press conference or book a pope wrote as a private theologian. Not an act of the Magisterium.'],
  'commission': ['Commission or council study', 'study', 'A document of a pontifical council or commission: the Biblical Commission after 1971, the International Theological Commission, Christian Unity, Justice and Peace and the like. Not magisterial in itself.'],
  'synod': ['Synod of Bishops', 'study', 'A document or message of the Synod of Bishops. Consultative unless the pope makes it his own.'],
  'bishops': ['Bishops\' conference', 'study', 'A statement of a national or regional conference of bishops. Teaches with the authority of those bishops for their own territory.'],
  'ecumenical': ['Ecumenical agreement', 'dialogue', 'A joint declaration or agreed statement with other Christians. Binds the Church only so far as it restates Catholic doctrine.'],
  'supplement': ['Not in Denzinger', 'study', 'Added to this site: decrees of Constance and Basel that Denzinger leaves out, mostly because no pope approved them or they came from a schismatic assembly. Mostly summaries; one translation.'],
};
const GRADES = {
  dogma: ['Defined dogma', 'dogma'], definitive: ['Definitive', 'definitive'], authentic: ['Authoritative teaching', 'authentic'],
  discipline: ['Discipline', 'discipline'], condemned: ['Condemned, graded censures', 'definitive'], 'condemned-heresy': ['Condemned as heresy', 'definitive'],
  profession: ['Profession of faith', 'dogma'], disputed: ['Weight disputed', 'prudential'],
  act: ['Juridical act', 'discipline'], void: ['Without authority', 'study'],
  prudential: ['Prudential decision', 'prudential'], witness: ['Historical witness', 'study'], editorial: ['Editorial note', 'study'],
};
const wKey = w => w === 'papal' ? 'papal-teaching' : w;
const levelOf = e => e.cur !== null && CURATED[e.cur] && GRADES[CURATED[e.cur].g] ? GRADES[CURATED[e.cur].g][1] : (WEIGHTS[wKey(e.weight)] || WEIGHTS['papal-teaching'])[1];
const W = w => WEIGHTS[wKey(w)] || WEIGHTS['papal-teaching'];
const CATS = {
  open: ['Open questions', 'Matters the Church has left open, or where definitions leave room for argument.'],
  fact: ['Historical questions', 'What actually happened, and the category of dogmatic facts.'],
  censure: ['Condemned propositions', 'What exactly was condemned, and whether the words can bear an orthodox sense.'],
  formula: ['Formulas with an orthodox sense', 'Wordings once in tension with the Latin formula, accepted in the sense intended.'],
  continuity: ['Contested continuity', 'Where newer teaching and older texts must be read together.'],
  discipline: ['Discipline and prudence', 'Changes of law, liturgy and policy that do not touch doctrine.'],
};

const $ = id => document.getElementById(id);
const view = $('view'), rail = $('rail'), qInput = $('q');
const esc = s => String(s).replace(/[&<>"]/g, c => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
const fmt = n => n.toLocaleString('en-US');
// Ids: 1839 (Denzinger), C1 and B1 (supplement), LG11 (a document after 1958 and its article, shown "LG 11").
const dispId = id => id.replace(/-\d+$/, '').replace(/^([A-Z]{2,})(\d)/, '$1 $2');
const nlab = id => /^[A-Z]{2}/.test(id) ? dispId(id) : /^[A-Z]/.test(id) ? 'Suppl. ' + id : 'n. ' + dispId(id);
const store = {
  get(k) { try { return localStorage.getItem(k); } catch (_) { return null; } },
  set(k, v) { try { localStorage.setItem(k, v); } catch (_) {} },
};

let state = { view: 'home', era: null, query: '', topic: null, kind: '', weight: '', period: 0, limit: 60, sinceLevel: '', dispCat: '', cmpA: null };
const Cite = { open: null };
const pageUrl = e => PAGES && SITE.url ? `${SITE.url}n/${encodeURIComponent(e.id.replace(/\*/g, '_s'))}/` : `${ARTIFACT_URL}#n${e.id}`;
let highlightTerms = [];

/* ---------- saved entries and notes ---------- */
const Marks = {
  map: new Map(), mode: 'local', db: null, col: null, editing: null,
  keyOf: id => id.replace(/\*/g, '_s'),
  idOf: k => k.replace(/_s/g, '*'),
  loadLocal() {
    try { const raw = JSON.parse(store.get('denz:marks') || '{}'); for (const [k, v] of Object.entries(raw)) this.map.set(k, v); } catch (_) {}
  },
  saveLocal() {
    const o = {}; for (const [k, v] of this.map) o[k] = v;
    store.set('denz:marks', JSON.stringify(o));
  },
  get(id) { return this.map.get(id) || null; },
  list() { return [...this.map.entries()].filter(([id]) => byId.has(id)).map(([id, v]) => ({ e: byId.get(id), ...v })).sort((a, b) => a.e.k - b.e.k); },
  async init(db, user) {
    try {
      const uid = user ? await user.id() : null;
      if (!db || !uid) return;
      this.db = db;
      this.col = db.collection('data/users/' + uid);
      let first = true;
      this.col.onSnapshot(snap => {
        const cloud = new Map();
        for (const d of snap.docs) if (d.exists) cloud.set(this.idOf(d.id), d.data());
        if (first) {
          first = false;
          this.mode = 'cloud';
          // carry anything saved in this browser before signing in up to the account
          const pending = [...this.map.entries()].filter(([id]) => !cloud.has(id));
          (async () => { for (const [id, v] of pending) { try { await this.col.doc(this.keyOf(id)).set(v); } catch (_) { break; } } })();
          for (const [id, v] of pending) cloud.set(id, v);
        }
        this.map = cloud;
        this.saveLocal();
        updateSavedCount();
        refreshMarks();
      }, () => { this.mode = 'local'; });
    } catch (_) { /* stays in this browser */ }
  },
  async set(id, patch) {
    const cur = { b: false, note: '', ...(this.map.get(id) || {}), ...patch, t: Date.now() };
    const empty = !cur.b && !(cur.note || '').trim();
    if (empty) this.map.delete(id); else this.map.set(id, cur);
    this.saveLocal();
    updateSavedCount();
    if (this.mode === 'cloud' && this.col) {
      try {
        const ref = this.col.doc(this.keyOf(id));
        if (empty) await ref.delete(); else await ref.set(cur);
      } catch (err) {
        this.mode = 'local';
        toast('Saved in this browser only. Your account could not store it.');
      }
    }
  },
};
/* ---------- reviews ---------- */
const rvKey = k => k.replace(/[^A-Za-z0-9_.~:@+-]/g, '_');
const Reviews = {
  map: new Map(), col: null, user: null, uid: null, canWrite: null, names: {}, ready: false, failed: false, editing: null, open: new Set(),
  async init(db, user) {
    try {
      this.user = user;
      this.uid = user ? await user.id() : null;
      this.canWrite = user ? await user.can('data.write') : null;
      this.col = db.collection('reviews');
      this.col.onSnapshot(async snap => {
        const m = new Map();
        for (const d of snap.docs) if (d.exists) m.set(d.id, d.data());
        this.map = m; this.ready = true;
        await this.resolveNames();
        refreshReviews();
      }, () => { this.failed = true; refreshReviews(); });
    } catch (_) { this.failed = true; refreshReviews(); }
  },
  async resolveNames() {
    if (!this.user) return;
    const ids = new Set();
    for (const v of this.map.values()) { if (v.by) ids.add(v.by); for (const c of v.comments || []) if (c.by) ids.add(c.by); }
    if (!ids.size) return;
    try { const ps = await this.user.profiles([...ids]); for (const id of ids) this.names[id] = (ps[id] && ps[id].name) || ''; } catch (_) {}
  },
  name(id) { return id && id === this.uid ? 'you' : (this.names[id] || 'a reviewer'); },
  get(key) { return this.map.get(rvKey(key)) || null; },
  async save(key, status, text) {
    const k = rvKey(key);
    const cur = this.map.get(k) || {};
    const comments = [...(cur.comments || []), { by: this.uid, t: Date.now(), status, text }].slice(-40);
    await this.col.doc(k).set({ status, by: this.uid, t: Date.now(), comments });
  },
};
const RV_LABEL = { reviewed: ['Reviewed', 'rv-ok'], correction: ['Needs correction', 'rv-fix'], none: ['Not reviewed', 'rv-none'] };
const fmtDate = t => new Date(t).toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' });
function reviewInner(key) {
  if (!Reviews.ready) {
    return `<div class="rvline"><span class="rv rv-none">Not reviewed</span><span>${Reviews.failed || !window.claude ? 'Reviews are shared through Claude and need this page opened there.' : 'Loading reviews…'}</span></div>`;
  }
  const r = Reviews.get(key);
  const st = r && r.status && RV_LABEL[r.status] ? r.status : 'none';
  const who = r && r.status && r.status !== 'none' ? ` by ${esc(Reviews.name(r.by))} on ${fmtDate(r.t)}` : '';
  const comments = (r && r.comments || []).filter(c => c.text).slice().reverse();
  const shown = Reviews.open.has(key) ? comments : comments.slice(0, 2);
  let h = `<div class="rvline"><span class="rv ${RV_LABEL[st][1]}">${RV_LABEL[st][0]}</span><span>${who}</span>
    ${Reviews.canWrite === false ? '' : `<button class="tool" data-rv-open="${esc(key)}">${r ? 'Update review' : 'Review this'}</button>`}</div>`;
  if (Reviews.editing === key) {
    h += `<div class="rvedit"><div><label><input type="radio" name="rvst" value="reviewed" ${st !== 'correction' ? 'checked' : ''}> Reviewed and sound</label><label><input type="radio" name="rvst" value="correction" ${st === 'correction' ? 'checked' : ''}> Needs correction</label></div>
      <textarea id="rvText" aria-label="Review comment" placeholder="What did you check, or what needs correcting?"></textarea>
      <div class="row" style="display:flex;gap:.4rem;flex-wrap:wrap"><button class="btn small primary" data-rv-save="${esc(key)}">Save review</button><button class="btn small" data-rv-cancel="1">Cancel</button></div></div>`;
  }
  if (shown.length) h += `<div class="cm">${shown.map(c => `<div><small>${esc(Reviews.name(c.by))}, ${fmtDate(c.t)}${c.status ? ' · ' + RV_LABEL[c.status][0] : ''}</small><br>${esc(c.text)}</div>`).join('')}${comments.length > shown.length ? `<button class="tool" data-rv-more="${esc(key)}" style="margin-top:.3rem">Show all ${comments.length} comments</button>` : ''}</div>`;
  return h;
}
function issueUrl(title, item, page) {
  const q = new URLSearchParams({ template: 'correction.yml', title, item, page });
  return `https://github.com/${SITE.repo}/issues/new?${q.toString()}`;
}
function reviewRow(key) {
  if (PAGES) {
    if (!SITE.repo) return '';
    const it = reviewItems().find(x => x.key === key);
    const label = it ? it.label : key;
    return `<div class="review"><div class="rvline"><a class="xref" href="${esc(issueUrl('Correction: ' + label, label, ARTIFACT_URL + (it ? it.href : '')))}" target="_blank" rel="noopener">Suggest a correction ↗</a></div></div>`;
  }
  return `<div class="review" data-review-key="${esc(key)}">${reviewInner(key)}</div>`; }
function refreshReviews() {
  document.querySelectorAll('[data-review-key]').forEach(el => { if (Reviews.editing !== el.dataset.reviewKey) el.innerHTML = reviewInner(el.dataset.reviewKey); });
  if (state.view === 'edition') { const el = $('rvProgress'); if (el) el.innerHTML = reviewProgress(); }
}
function reviewItems() {
  return [
    ...SINCE.map(s => ({ key: 'since:' + s.id, label: s.title, href: '#since-' + s.id, group: 'Since 1950' })),
    ...DISPUTED.map(d => ({ key: 'q:' + d.id, label: d.title, href: '#q-' + d.id, group: 'Disputed questions' })),
    ...THREADS.map(t => ({ key: 'thread:' + t.id, label: t.title, href: '#thread-' + t.id, group: 'Doctrinal threads' })),
    ...[...RC_CH.values()].map(c => ({ key: 'rc:' + c.id, label: 'Roman Catechism: ' + c.title, href: '#rc-' + c.id, group: 'Roman Catechism' })),
    ...CURATED.map(c => ({ key: 'w:' + c.from, label: `${nlab(c.from)}${c.to !== c.from ? "–" + dispId(c.to) : ""}: ${GRADES[c.g][0]}`, href: '#n' + c.from, group: 'Hand-checked weights' })),
  ];
}
function reviewProgress() {
  if (!Reviews.ready) return `<p>${Reviews.failed || !window.claude ? 'Review status is stored through Claude and appears when this page is opened there.' : 'Loading reviews…'}</p>`;
  const items = reviewItems();
  const groups = {};
  for (const it of items) {
    const r = Reviews.get(it.key); const st = r && r.status ? r.status : 'none';
    (groups[it.group] = groups[it.group] || { reviewed: 0, correction: 0, none: 0, fix: [] })[st]++;
    if (st === 'correction') groups[it.group].fix.push(it);
  }
  return `<div class="tablewrap"><table class="wtable"><thead><tr><th>Section</th><th>Reviewed</th><th>Needs correction</th><th>Not reviewed</th></tr></thead><tbody>${Object.entries(groups).map(([g, c]) => `<tr><td>${g}</td><td>${c.reviewed}</td><td>${c.correction}</td><td>${c.none}</td></tr>`).join('')}</tbody></table></div>
    ${Object.values(groups).some(c => c.fix.length) ? `<h3 style="font-size:1rem;margin:1rem 0 .3rem">Flagged for correction</h3><div class="tips">${Object.values(groups).flatMap(c => c.fix).map(it => `<div><a class="xref" href="${it.href}">${esc(it.label)}</a></div>`).join('')}</div>` : ''}`;
}

function updateSavedCount() {
  const n = Marks.list().length;
  $('savedCount').textContent = n ? String(n) : '';
}

/* ---------- text rendering ---------- */
function termRegex(terms) {
  if (!terms.length) return null;
  const parts = terms.map(t => t.split(' ').map(w => w.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')).join('[^A-Za-z0-9]+'));
  parts.sort((a, b) => b.length - a.length);
  return new RegExp('\\b(' + parts.join('|') + ')', 'gi');
}
function linkNums(list) {
  return list.replace(/\d{1,4}[a-z]?\*?/g, num => {
    const target = byId.get(num) || byBase.get(parseInt(num, 10));
    return target ? `<a class="xref" href="#n${esc(target.id)}">${num}</a>` : num;
  });
}
function renderText(text, re) {
  let h = esc(text);
  h = h.replace(/\[([^\[\]]{2,80}?\d+\s?:\s?\d+[^\[\]]{0,40}?)\]/g, '<span class="cite">[$1]</span>');
  if (re) h = h.replace(/(<[^>]*>)|([^<]+)/g, (m, tag, txt) => tag ? tag : txt.replace(re, '<mark>$1</mark>'));
  h = h.replace(/(^|[^A-Za-z])((?:Kch|Kirch|R|H|L|M|EP|RS)\.?\s)?(nn?\.\s?)(\d{1,4}[a-z]?(?:\s?(?:,|and|-|–|f\.|ff\.)\s?\d{1,4}[a-z]?)*)/g,
    (m, pre, other, lab, list) => other ? m : pre + lab + linkNums(list));
  // supplement entries cited in parentheses, e.g. (C9) or (B13–B15)
  h = h.replace(/\(((?:[CB]\d{1,2}(?:–[CB]\d{1,2})?)(?:,\s*[CB]\d{1,2}(?:–[CB]\d{1,2})?)*)\)/g, (m, list) =>
    '(' + list.replace(/[CB]\d{1,2}/g, id => byId.has(id) && byId.get(id).sup ? `<a class="xref" href="#n${id}">${id}</a>` : id) + ')');
  h = h.replace(/\b(MG|ML)(\s+)(\d{1,3})(\s*,\s*\d{1,4}(?:\s?[A-D]\b)?)/g, (m, ser, sp, vol, rest) => {
    const host = ser === 'MG' ? 'graeca' : 'latina';
    return `<a class="xref" href="http://${host}.patristica.net/#t${String(vol).padStart(3, '0')}" target="_blank" rel="noopener" title="${ser === 'MG' ? 'Patrologia Graeca' : 'Patrologia Latina'} volume ${vol} at patristica.net">${ser}${sp}${vol}${rest}</a>`;
  });
  return h;
}
function refLinks(refs) {
  return refs.map(r => { const e = byId.get(r); return e ? `<a class="xref" href="#n${esc(r)}">${esc(nlab(r))}</a>` : ''; }).join(' ');
}

/* ---------- contents rail ---------- */
function ordinal(n) { const s = ['th', 'st', 'nd', 'rd'], v = n % 100; return n + (s[(v - 20) % 10] || s[v] || s[0]); }
const GUIDES = [
  ['#home', 'Introduction', ''],
  ['#threads', 'Doctrinal threads', THREADS.length + ' threads'],
  ['#since', 'Since 1950', SINCE.length + ' documents'],
  ['#disputed', 'Disputed questions', DISPUTED.length + ' questions'],
  ['#catechism', 'Roman Catechism', RC_CH.size + ' chapters'],
  ['#timeline', 'Timeline', ''],
  ['#ask', 'Ask or check a statement', ''],
  ['#compare', 'Compare two texts', ''],
  ['#weights', 'Weight and censures', ''],
  ['#reading', 'Reading a condemnation', ''],
  ['#scripture', 'Scripture index', ''],
  ['#concordance', 'Old and new numbers', ''],
  ['#topics', 'Topics', ''],
  ['#saved', 'Saved and notes', ''],
  ['#edition', 'About this edition', ''],
];
function buildRail() {
  let html = '<h2>Guides and indexes</h2>';
  for (const [href, name, ct] of GUIDES) html += `<button class="era-btn guide-btn" data-go="${href}"><span class="nm">${name}</span><span class="ct">${ct}</span></button>`;
  let group = null;
  for (const er of ERAS) {
    const g = er.sup ? 'Supplement · not in Denzinger' : er.app ? 'Appendix · 5000 and following' : er.i === 0 ? 'The Creeds' : ordinal(Math.floor(er.year / 100) + 1) + ' century';
    if (g !== group) { html += `<h2>${g}</h2>`; group = g; }
    const first = dispId(er.entries[0].id), last = dispId(er.entries[er.entries.length - 1].id);
    html += `<button class="era-btn ${kind(er) === 'Council' ? 'council' : ''}" data-era="${er.i}">
      <span class="nm">${esc(er.name)}</span><span class="dt">${esc(er.dates)}</span>
      <span class="ct">${first === last ? first : first + '–' + last}</span></button>`;
  }
  rail.innerHTML = html;
  rail.addEventListener('click', ev => {
    const b = ev.target.closest('.era-btn');
    if (!b) return;
    closeNav();
    go(b.dataset.go || '#e' + b.dataset.era);
  });
}
function markRail() {
  rail.querySelectorAll('.era-btn.active').forEach(b => b.classList.remove('active'));
  let b = null;
  if (state.view === 'read' && state.era) b = rail.querySelector(`[data-era="${state.era.i}"]`);
  else {
    const map = { home: '#home', catechism: '#catechism', timeline: '#timeline', since: '#since', disputed: '#disputed', scripture: '#scripture', book: '#scripture', topics: '#topics', saved: '#saved', threads: '#threads', thread: '#threads', ask: '#ask', compare: '#compare', weights: '#weights', reading: '#reading', edition: '#edition', concordance: '#concordance' };
    if (map[state.view]) b = rail.querySelector(`[data-go="${map[state.view]}"]`);
  }
  if (b) {
    b.classList.add('active');
    const r = b.getBoundingClientRect(), rr = rail.getBoundingClientRect();
    if (r.top < rr.top + 40 || r.bottom > rr.bottom - 40) rail.scrollTop += r.top - rr.top - rr.height / 3;
  }
}

/* ---------- home ---------- */
const NOTABLE = [
  ['39', 'The Athanasian Creed (Quicumque)'], ['54', 'The Nicene Creed'], ['86', 'The Nicene-Constantinopolitan Creed'],
  ['148', 'Chalcedon: the two natures of Christ'], ['783', 'Trent: Scripture and Tradition'], ['793', 'Trent: the Decree on Justification'],
  ['1641', 'The Immaculate Conception'], ['1700', 'The Syllabus of Errors'], ['1792', 'Vatican I: Faith'],
  ['1839', 'Vatican I: Papal infallibility'], ['2071', 'Pascendi: the doctrines of the Modernists'], ['2333', 'The Assumption of Mary'],
];
/* ---------- text for today ---------- */
let TODAY_POOL = null;
function todayEntry() {
  if (!TODAY_POOL) TODAY_POOL = ENTRIES.filter(e => !e.sup && !e.note && e.weight !== 'note' && ['dogma', 'definitive', 'authentic'].includes(levelOf(e)) && (() => { const n = e.paras.join(' ').length; return n > 280 && n < 2600; })());
  const d = new Date();
  const day = Math.floor(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()) / 864e5);
  let h = day * 2654435761 % 4294967296; h = (h ^ (h >>> 15)) >>> 0;
  return TODAY_POOL[h % TODAY_POOL.length];
}
function todayHtml() {
  const e = todayEntry();
  if (!e) return '';
  const text = e.paras.join(' ');
  const ex = text.length > 420 ? text.slice(0, 420).replace(/\s\S*$/, '') + '…' : text;
  return `<h2 class="sect-h">Text for today</h2>
    <a class="today" href="#n${esc(e.id)}">
      <span class="ctx"><b>${esc(nlab(e.id))}</b>${e.ds.length ? ' · ' + esc(dsText(e)) : ''} · ${esc(e.era.name)} · ${e.year}</span>
      ${e.topic ? `<span class="tt">${esc(e.topic)}</span>` : ''}
      <span class="ex">${esc(ex)}</span>
      <span class="go">Read in context →</span>
    </a>`;
}
function renderHome() {
  const last = store.get('denz:last');
  const lastE = last && byId.get(last);
  const nCouncils = ERAS.filter(e => kind(e) === 'Council').length;
  const kindCounts = Object.fromEntries(KINDS.slice(1).map(([k]) => [k, ENTRIES.filter(e => e.kinds.includes(k)).length]));
  view.className = 'col';
  view.innerHTML = `
    <section class="hero">
      <div class="eyebrow">Enchiridion Symbolorum · English translation · older numbering</div>
      <h1>Sources of Catholic Dogma</h1>
      <p>Denzinger's handbook of creeds, conciliar definitions and papal documents, from the Apostles' Creed to Pius XII, with guides to what has been taught since 1950 and to the questions still argued over.</p>
      <div class="stats">
        <div><b>${fmt(ENTRIES.length)}</b>numbered entries</div>
        <div><b>${ERAS.length}</b>pontificates, councils and creeds</div>
        <div><b>${nCouncils}</b>councils and synods</div>
      </div>
      <div class="actions">
        ${lastE ? `<a class="btn primary" href="#n${esc(lastE.id)}">Continue at ${esc(nlab(lastE.id))}</a><a class="btn" href="#n1">Start at n. 1</a>` : `<a class="btn primary" href="#n1">Start reading at n. 1</a>`}
      </div>
    </section>
    ${todayHtml()}
    <h2 class="sect-h">Guides and indexes</h2>
    <div class="guides">
      <a class="guide" href="#catechism"><b>Roman Catechism</b><span>The Catechism of the Council of Trent, chapter by chapter, with the texts in this collection that each chapter explains.</span></a>
      <a class="guide" href="#timeline"><b>Timeline</b><span>Every entry by date and weight: where definitions, canons and condemnations cluster across twenty centuries.</span></a>
      <a class="guide" href="#threads"><b>Doctrinal threads</b><span>One doctrine at a time, traced in order from the early Church to Leo XIV, with a note on each step.</span></a>
      <a class="guide" href="#ask"><b>Ask or check a statement</b><span>Ask a question, or test a statement against the texts; an AI answers from the entries and cites each by number.</span></a>
      <a class="guide" href="#since"><b>Since 1950</b><span>Vatican II to Leo XIV, sorted by weight: restated dogma, definitive teaching, authentic teaching, discipline and prudence.</span></a>
      <a class="guide" href="#disputed"><b>Disputed questions</b><span>Open questions, contested continuity, and condemned propositions that can bear an orthodox sense.</span></a>
      <a class="guide" href="#concordance"><b>Old and new numbers</b><span>Every entry's older number beside its DS number, with the Latin text under any entry.</span></a>
      <a class="guide" href="#scripture"><b>Scripture index</b><span>Every bracketed Scripture reference, by book, chapter and verse.</span></a>
      <a class="guide" href="#topics"><b>Topics</b><span>The section headings of the whole collection, A to Z.</span></a>
      <a class="guide" href="#weights"><b>Weight and censures</b><span>What each kind of text binds, the theological notes, and the grades of censure.</span></a>
      <a class="guide" href="#reading"><b>Reading a condemnation</b><span>Why a condemned proposition is read in the sense condemned, how that sense is established, and the case of Unigenitus.</span></a>
      <a class="guide" href="#e${ERAS.find(x => x.sup).i}"><b>Constance and Basel</b><span>The conciliar decrees Denzinger leaves out, from Haec Sancta to Basel's "three truths," with their standing.</span></a>
      <a class="guide" href="#compare"><b>Compare two texts</b><span>Read two entries side by side, with the guides that discuss them together.</span></a>
    </div>
    <h2 class="sect-h">Browse by kind of text</h2>
    <div class="chips">${KINDS.slice(1).map(([k, label]) => `<a class="chip" href="#kind-${k}" style="text-decoration:none">${label}<span>${fmt(kindCounts[k])}</span></a>`).join('')}</div>
    <h2 class="sect-h">Frequently cited</h2>
    <div class="notable">${NOTABLE.map(([n, t]) => { const e = byId.get(n); return e ? `<a href="#n${n}"><span class="n">${n}</span><span class="t">${t}<span class="s">${esc(e.era.name)}${e.era.dates ? ' · ' + esc(e.era.dates) : ''}</span></span></a>` : ''; }).join('')}</div>
    <h2 class="sect-h">Searching</h2>
    <div class="tips">
      <div>Type words to find entries that contain all of them: <code>grace merit</code></div>
      <div>Put an exact phrase in quotes: <code>"ex cathedra"</code></div>
      <div>Type a number to jump straight to it: <code>1839</code> or <code>n. 2333</code></div>
      <div>Or a new number, after DS or DH: <code>DS 3074</code></div>
      <div>Type a Scripture reference: <code>Matt 16:18</code> or <code>John 6</code></div>
      <div>Narrow by pope, council or date: <code>pope:"Pius IX"</code> <code>council:trent</code> <code>year:1850-1900</code> <code>before:800</code></div>
      <div>By weight or kind: <code>weight:dogma</code> <code>weight:condemned</code> <code>kind:anathema</code>, or leave a word out with <code>-word</code></div>
      <div>In the Latin text, accents ignored: <code>latin:"ex cathedra"</code></div>
      <div>Press <code>/</code> anywhere to start a search, and <code>Esc</code> to clear it.</div>
    </div>
    <p class="colophon">Text of the English translation as published on patristica.net (archived from catecheticsonline.com), with the older Denzinger numbering used before the 32nd edition of 1963, lightly corrected for scanning errors. Numbers linked in red point to other entries in this collection; references to Rouët de Journel (R) and Kirch (Kch) are left as printed. The Since 1950 and Disputed questions guides are summaries written for this site, read according to the hermeneutic of continuity, with links to the official texts.</p>`;
}

/* ---------- reader ---------- */
function markHtml(e) {
  const m = Marks.get(e.id);
  let h = '';
  if (Marks.editing === e.id) {
    h += `<div class="noteedit"><textarea id="noteText" aria-label="Your note on ${esc(nlab(e.id))}" placeholder="Your note on ${esc(nlab(e.id))}">${esc(m && m.note || '')}</textarea>
      <div class="row"><button class="btn small primary" data-note-save="${esc(e.id)}">Save note</button><button class="btn small" data-note-cancel="1">Cancel</button>${m && m.note ? `<button class="btn small" data-note-del="${esc(e.id)}">Delete note</button>` : ''}</div></div>`;
  } else if (m && m.note) {
    h += `<div class="mynote">${esc(m.note)}</div>`;
  }
  return h;
}
function weightPill(w) { const x = W(w); return `<a class="pill lv-${x[1]}" href="#weights" style="text-decoration:none" title="${esc(x[2])}">${x[0]}</a>`; }
function censHtml(e) {
  if (e.cens === null || !CENS[e.cens]) return '';
  const c = CENS[e.cens];
  const at = c.at && c.at !== e.id ? ` <span>(verdict at <a class="xref" href="#n${esc(c.at)}">${esc(nlab(c.at))}</a>)</span>` : '';
  return `<span>Censured as ${esc(c.w.join(', '))}${c.r ? ', respectively' : ''}</span>${at}`;
}
function curPill(e) {
  if (e.cur === null || !CURATED[e.cur]) return '';
  const g = GRADES[CURATED[e.cur].g];
  return `<span class="pill lv-${g[1]}" title="Checked by hand: ${esc(CURATED[e.cur].n)}">Checked · ${g[0]}</span>`;
}
function curNote(e) {
  const c = CURATED[e.cur];
  return `<div class="curnote"><b>Checked by hand · ${GRADES[c.g][0]}${c.to !== c.from ? ` (${esc(nlab(c.from))}–${esc(dispId(c.to))})` : ''}.</b> ${renderText(c.n, null)}${reviewRow('w:' + c.from)}</div>`;
}
function entryHtml(e, re, showCur) {
  const m = Marks.get(e.id);
  const tags = `<div class="wline">${dsTag(e)}${e.sup ? weightPill(e.weight) : ''}${curPill(e) || weightPill(e.weight)}${censHtml(e)}${e.kinds.filter(k => k === 'definition' || k === 'anathema').map(k => `<span class="tag">${KIND_LABEL[k]}</span>`).join('')}</div>`;
  const disc = DISCUSSED.get(e.id);
  const side = Latin.mode === 'side' && !e.sup;
  const body = `<div class="body">${tags}${e.paras.map(p => `<p>${renderText(p, re)}</p>`).join('')}</div>`;
  return `<section class="entry${e.note ? ' note' : ''}${m ? ' has-mark' : ''}" id="n${esc(e.id)}">
    <a class="num" href="#n${esc(e.id)}" aria-label="Entry ${esc(e.id)}">${esc(dispId(e.id))}${m && m.b ? '<span class="saved-dot" title="Saved">●</span>' : ''}</a>
    ${side ? `<div class="pair">${body}${latinHtml(e)}</div>` : body}
    ${!side && !e.sup && latinShown(e.id) ? latinHtml(e) : ''}
    ${e.links.length ? `<div class="discussed">Full text: ${e.links.map(l => `<a href="${esc(l.url)}" target="_blank" rel="noopener">${esc(l.label)} ↗</a>`).join(' · ')}</div>` : ''}
    ${e.cur !== null && CURATED[e.cur] && (showCur || CURATED[e.cur].from === e.id) ? curNote(e) : ''}
    ${e.cens !== null && CENS[e.cens] || e.weight === 'condemned' ? `<div class="discussed">Condemned in a determinate sense: <a href="#reading">how to read a condemnation</a></div>` : ''}
    ${disc ? `<div class="discussed">Discussed in ${disc.slice(0, 4).map(d => `<a href="${d.href}">${esc(d.label)}</a>`).join(', ')}</div>` : ''}
    ${e.citedBy.length ? `<div class="discussed">Cited by ${e.citedBy.map(id => `<a href="#n${esc(id)}">${esc(nlab(id))}</a>`).join(', ')}</div>` : ''}
    ${e.rc.length ? `<div class="discussed">Roman Catechism: ${e.rc.map(id => { const c = RC_CH.get(id); return c ? `<a href="#rc-${esc(id)}" title="${esc(c.title)}">${esc(rcShort(c))}</a>` : ''; }).join('; ')}</div>` : ''}
    ${Cite.open === e.id ? citePanel(e) : ''}
    <div class="slot-note" style="display:contents">${markHtml(e)}</div>
    <div class="tools">
      <button class="tool" data-save="${esc(e.id)}" aria-pressed="${!!(m && m.b)}">${m && m.b ? 'Saved' : 'Save'}</button>
      <button class="tool" data-note="${esc(e.id)}">${m && m.note ? 'Edit note' : 'Add note'}</button>
      ${e.sup || Latin.mode === 'side' ? '' : `<button class="tool" data-latin="${esc(e.id)}" aria-pressed="${latinShown(e.id)}">Latin</button>`}
      <button class="tool" data-cmp="${esc(e.id)}">${state.cmpA === e.id ? 'Picked for compare' : 'Compare'}</button>
      <button class="tool" data-link="${esc(e.id)}">Copy link</button>
      <button class="tool" data-citep="${esc(e.id)}" aria-pressed="${Cite.open === e.id}">Cite</button>
      <button class="tool" data-copy="${esc(e.id)}">Copy text</button>
      ${PAGES && SITE.repo ? `<a class="tool" style="text-decoration:none" href="${esc(issueUrl('Correction: ' + nlab(e.id), nlab(e.id), pageUrl(e)))}" target="_blank" rel="noopener">Report a problem ↗</a>` : ''}
    </div>
  </section>`;
}
function refreshEntry(id) {
  const el = document.getElementById('n' + id);
  if (!el) return;
  const e = byId.get(id);
  const tmp = document.createElement('div');
  tmp.innerHTML = entryHtml(e, termRegex(highlightTerms));
  el.replaceWith(tmp.firstElementChild);
  if (Marks.editing === id) { const t = $('noteText'); if (t) { t.focus(); t.setSelectionRange(t.value.length, t.value.length); } }
}
function refreshMarks() {
  if (state.view === 'read') document.querySelectorAll('.entry').forEach(el => { if (Marks.editing !== el.id.slice(1)) refreshEntry(el.id.slice(1)); });
  if (state.view === 'saved') renderSaved();
}
function seeAlso(er) {
  const sups = ERAS.filter(x => x.sup);
  const link = (x, t) => x ? `<p class="checked" style="margin:.2rem 0 .4rem">${t} <a class="xref" href="#e${x.i}">${esc(x.name)}</a></p>` : '';
  if (/Constance/.test(er.name) && !er.sup) return link(sups.find(x => /Constance/.test(x.name)), 'See also the decrees this collection leaves out:');
  if (/Florence/.test(er.name) && !er.sup) return link(sups.find(x => /Basel/.test(x.name)), 'For the Council of Basel, which this collection leaves out, see');
  if (er.sup) return `<p class="checked" style="margin:.2rem 0 .4rem">Added to this site. Denzinger leaves these texts out, mostly because no pope approved them or they came from a schismatic assembly. Except for Haec Sancta, which is translated, the entries summarize the decrees and link to the full texts.</p>`;
  return '';
}
function latinSeg() {
  const b = (m, label) => `<button data-latin-mode="${m}" aria-pressed="${Latin.mode === m}">${label}</button>`;
  return `<span class="seg" role="group" aria-label="Latin text"><span class="lbl">Latin</span>${b('off', 'Off')}${b('under', 'Below')}${b('side', 'Side by side')}</span>`;
}
function renderEra(er, focusId) {
  const re = termRegex(highlightTerms);
  view.className = Latin.mode === 'side' && !er.sup ? 'col side' : 'col';
  const first = dispId(er.entries[0].id), last = dispId(er.entries[er.entries.length - 1].id);
  let html = `<header class="era-head">
    <div class="eyebrow">${er.sup ? 'Supplement · not in Denzinger' : kind(er)}${er.app ? ' · Appendix' : ''}</div>
    <h1>${esc(er.name)}</h1>
    ${seeAlso(er)}
    <div class="meta">${er.dates ? `<span>${esc(er.dates)}</span>` : ''}${er.sub ? `<span>${esc(er.sub)}</span>` : ''}<span>${/^\d/.test(first) ? 'n. ' : ''}${first === last ? first : first + '–' + last}</span><span>${er.entries.length} ${er.entries.length === 1 ? 'entry' : 'entries'}</span></div>
    <div class="era-tools">${er.sup ? '' : latinSeg()}${PAGES ? '<button class="btn small" data-print="1">Print</button>' : ''}</div>
  </header>`;
  let ses = null, topic, src;
  for (const e of er.entries) {
    if (e.ses && e.ses !== ses) { html += `<div class="session">${esc(e.ses)}</div>`; ses = e.ses; topic = undefined; }
    if (e.topic !== topic || (e.src && e.src !== src)) {
      if (e.topic && e.topic !== topic) html += `<h2 class="topic">${renderText(e.topic, re)}</h2>`;
      if (e.src && e.src !== src) html += `<p class="src">${renderText(e.src, re)}</p>`;
      topic = e.topic; src = e.src;
    }
    html += entryHtml(e, re);
  }
  const prev = ERAS[er.i - 1], next = ERAS[er.i + 1];
  html += `<nav class="pager">
    ${prev ? `<button data-go="#e${prev.i}"><small>Previous</small><span>${esc(prev.name)}</span></button>` : '<span></span>'}
    ${next ? `<button class="next" data-go="#e${next.i}"><small>Next</small><span>${esc(next.name)}</span></button>` : ''}
  </nav>`;
  view.innerHTML = html;
  if (focusId) {
    const el = document.getElementById('n' + focusId);
    if (el) {
      el.scrollIntoView({ block: 'start' });
      window.scrollBy(0, -(document.querySelector('.top').offsetHeight + 12));
      el.classList.add('flash');
      store.set('denz:last', focusId);
    }
  } else {
    window.scrollTo(0, 0);
    store.set('denz:last', er.entries[0].id);
  }
}
const MONTHS = ['January', 'February', 'March', 'April', 'May', 'June', 'July', 'August', 'September', 'October', 'November', 'December'];
function citeFormats(e) {
  const d = new Date(), acc = `${MONTHS[d.getMonth()]} ${d.getDate()}, ${d.getFullYear()}`;
  const url = pageUrl(e);
  const dsp = e.ds.length ? ` (${dsText(e)})` : '';
  const short = e.sup ? `Suppl. ${e.id}` : `D ${dispId(e.id)}${e.ds.length ? '; ' + dsText(e) : ''}`;
  const where = `${e.era.name}${e.ses ? ', ' + e.ses.replace(/\s*\(.*\)$/, '') : ''}`;
  const site = `“${e.sup ? 'Supplement ' + e.id : nlab(e.id)}${e.topic ? ': ' + e.topic.replace(/\s+/g, ' ') : ''},” <i>Sources of Catholic Dogma</i> (online reader), ${where}, accessed ${acc}, ${url}.`;
  const f = [];
  f.push({ label: 'Short reference', html: esc(short) });
  if (!e.sup) {
    f.push({ label: 'Chicago note', html: `Henry Denzinger, <i>The Sources of Catholic Dogma</i>, trans. Roy J. Deferrari (St. Louis: B. Herder, 1957), no. ${esc(dispId(e.id))}${esc(dsp)}.` });
    f.push({ label: 'Chicago bibliography', html: `Denzinger, Henry. <i>The Sources of Catholic Dogma</i>. Translated by Roy J. Deferrari from the thirtieth edition of <i>Enchiridion Symbolorum</i>. St. Louis: B. Herder, 1957.` });
    f.push({ label: 'Turabian author-date', html: `(Denzinger 1957, no. ${esc(dispId(e.id))})<br>Denzinger, Henry. 1957. <i>The Sources of Catholic Dogma</i>. Translated by Roy J. Deferrari. St. Louis: B. Herder.` });
  }
  f.push({ label: 'This site', html: site.replace(/&(?!amp;|lt;|gt;|quot;)/g, '&amp;') });
  return f;
}
function citePanel(e) {
  const f = citeFormats(e);
  return `<div class="citep"><div class="cph">Cite ${esc(nlab(e.id))}${e.sup ? '' : ' · the print citations assume the 1957 Herder printing of this translation; check the number there before citing'}</div>
    ${f.map((x, i) => `<div class="cpr"><b>${x.label}</b><span class="cpt" id="cpt-${i}">${x.html}</span><button class="tool" data-copycite="${i}" data-for="${esc(e.id)}">Copy</button></div>`).join('')}</div>`;
}
async function copyRich(htmlStr, okMsg, el) {
  const tmp = document.createElement('div'); tmp.innerHTML = htmlStr.replace(/<br>/g, '\n');
  const plain = tmp.textContent;
  try {
    if (window.ClipboardItem && navigator.clipboard && navigator.clipboard.write) {
      await navigator.clipboard.write([new ClipboardItem({ 'text/html': new Blob([htmlStr], { type: 'text/html' }), 'text/plain': new Blob([plain], { type: 'text/plain' }) })]);
      toast(okMsg); return;
    }
  } catch (_) { /* fall back to plain text */ }
  copy(plain, okMsg, el);
}
function citation(e) {
  if (e.sup) return `${e.topic} (${e.era.name.replace(/:.*$/, '')}, ${e.ses}); Sources of Catholic Dogma reader, supplement ${e.id}.`;
  const where = [e.era.name, e.ses ? e.ses.replace(/\s*\(.*\)$/, '') : null].filter(Boolean).join(', ');
  return `Denzinger, Sources of Catholic Dogma, ${nlab(e.id)}${e.ds.length ? ` [${dsText(e)}]` : ''} (${where}${e.era.dates ? ', ' + e.era.dates : ''}).`;
}

/* ---------- old and new numbers ---------- */
let LATIN = null;
const latinText = n => { if (!LATIN) { try { LATIN = JSON.parse(document.getElementById('latin-data').textContent); } catch (_) { LATIN = {}; } } return LATIN[n]; };
const DS_HOW = {
  series: ['inferred', 'Inferred from the numbering of the neighboring entries; the Latin page does not print the old number here.'],
  checked: ['matched by hand', 'The Latin page prints this pair confusingly; matched by reading both texts.'],
};
function dsRange(list) {
  const out = []; let i = 0;
  while (i < list.length) {
    let j = i;
    while (j + 1 < list.length && +list[j + 1] === +list[j] + 1) j++;
    out.push(j > i ? `${list[i]}–${list[j]}` : list[i]); i = j + 1;
  }
  return out.join(', ');
}
const dsText = e => e.ds.length ? (e.dsHow === 'series' ? 'cf. DS ' : 'DS ') + dsRange(e.ds) : '';
function dsTag(e) {
  if (!e.ds.length) return '';
  const h = DS_HOW[e.dsHow];
  return `<a class="dsno${h ? ' inf' : ''}" href="#concordance" title="${h ? esc(h[1]) : 'Number in Denzinger-Schönmetzer (1963), kept by Denzinger-Hünermann'}">DS ${esc(dsRange(e.ds))}${h ? ` · ${h[0]}` : ''}</a>`;
}
function dsNeighbors(e) {
  let before = null, after = null;
  for (let k = e.k - 1; k >= 0 && !before; k--) if (ENTRIES[k].ds.length && !ENTRIES[k].sup) before = ENTRIES[k];
  for (let k = e.k + 1; k < ENTRIES.length && !after; k++) if (ENTRIES[k].ds.length && !ENTRIES[k].sup) after = ENTRIES[k];
  return [before, after].filter(Boolean);
}
const nbLink = x => `<a class="xref" href="#n${esc(x.id)}">${esc(nlab(x.id))}</a> = DS ${esc(dsRange(x.ds))}`;
function latinHtml(e) {
  if (!e.ds.length) {
    const nb = dsNeighbors(e);
    return `<div class="latin none">This entry has no number on the Latin page${e.weight === 'note' ? ' (it is an editorial note)' : ''}.${nb.length ? ` Nearest numbered entries: ${nb.map(nbLink).join('; ')}.` : ''}</div>`;
  }
  const h = DS_HOW[e.dsHow];
  return `<div class="latin" lang="la"><div class="lh">Latin · ${esc(dsText(e))}${h ? ` · ${h[0]}` : ''}</div>${e.ds.map(n => { const t = latinText(n); return `<p><span class="dsn">${esc(n)}</span>${t ? esc(t) : '<i>The Latin page gives no text under this number.</i>'}</p>`; }).join('')}</div>`;
}
const Latin = { mode: 'off', flip: new Set(), get all() { return this.mode !== 'off'; } };
try { const v = localStorage.getItem('dz-latin'); Latin.mode = v === '2' ? 'side' : v === '1' ? 'under' : 'off'; } catch (_) {}
const latinShown = id => Latin.mode === 'side' || ((Latin.mode === 'under') !== Latin.flip.has(id));
function setLatinMode(m) { Latin.mode = m; Latin.flip.clear(); try { localStorage.setItem('dz-latin', m === 'side' ? '2' : m === 'under' ? '1' : '0'); } catch (_) {} }
function setLatinAll(on) { setLatinMode(on ? 'under' : 'off'); }
function dsQuery(q) { const m = q.trim().match(/^(?:ds|dh|dz?s|denz\.?-?sch\.?)\s*\.?\s*(\d{1,4})$/i); return m ? +m[1] : null; }
function dsNearest(n) {
  let lo = null, hi = null;
  for (const e of ENTRIES) for (const d of e.ds) { const v = +d; if (v < n && (!lo || v > lo[0])) lo = [v, e]; if (v > n && (!hi || v < hi[0])) hi = [v, e]; }
  return [lo, hi].filter(Boolean).map(x => x[1]);
}

/* ---------- Scripture lookup ---------- */
const ALIAS = [];
for (const b of BOOKS) for (const a of [b.name, ...b.aliases]) ALIAS.push([norm(a).trim(), b]);
ALIAS.sort((a, b) => b[0].length - a[0].length);
function scriptureQuery(q) {
  const n = norm(q).trim();
  for (const [a, b] of ALIAS) {
    if (n === a || n.startsWith(a + ' ')) {
      const rest = n.slice(a.length).trim().split(' ').filter(Boolean);
      if (!rest.length || rest.length > 2 || rest.some(x => !/^\d{1,3}$/.test(x))) continue;
      return { book: b, ch: +rest[0], v: rest[1] ? +rest[1] : null };
    }
  }
  return null;
}

/* ---------- search ---------- */
/* Trent's later sessions are printed under Julius III and Pius IV; count them as Trent */
const assembly = e => kind(e.era) === 'Council' ? e.era.name : (e.ses && /^Session [IVXLC]+/i.test(e.ses) && e.year >= 1545 && e.year <= 1563 ? 'Council of Trent' : null);
const FILTER_KEYS = new Set(['pope', 'council', 'era', 'weight', 'grade', 'level', 'kind', 'year', 'before', 'after', 'latin', 'topic', 'ds']);
function splitQuery(q) {
  const terms = [], neg = [], filters = [];
  q.replace(/(-?)(?:([A-Za-z]+):)?(?:"([^"]*)"?|(\S+))/g, (m, minus, key, ph, w) => {
    const val = ph !== undefined ? ph : (w || '');
    if (key && FILTER_KEYS.has(key.toLowerCase()) && val.trim()) { filters.push({ key: key.toLowerCase(), val: val.trim() }); return ''; }
    const t = norm((key ? key + ' ' : '') + val).trim();
    if (!t) return '';
    if (minus && !key) neg.push(t); else terms.push(t);
    return '';
  });
  return { terms, neg, filters };
}
function parseQuery(q) { return splitQuery(q).terms; }
const startsWord = (hay, needle) => (' ' + norm(hay) + ' ').includes(' ' + norm(needle).trim());
function yearRange(v) {
  const m = v.match(/^(\d{1,4})\s*(?:-|–|to|\.\.)\s*(\d{1,4})$/); if (m) return [+m[1], +m[2]];
  const c = v.match(/^(\d{1,2})(?:(?:st|nd|rd|th)?\s*c(?:ent(?:ury)?)?\.?|st|nd|rd|th)$/i); if (c) return [(+c[1] - 1) * 100, +c[1] * 100 - 1];
  const s = v.match(/^(\d{3,4})s$/); if (s) { const y = +s[1]; return [y, y + (y % 100 === 0 ? 99 : 9)]; }
  const y = v.match(/^\d{1,4}$/); if (y) return [+v, +v];
  return null;
}
let LAT_HAY = null;
function latinHay(e) {
  if (!LAT_HAY) LAT_HAY = new Map();
  if (!LAT_HAY.has(e.id)) LAT_HAY.set(e.id, ' ' + norm(e.ds.map(n => latinText(n) || '').join(' ')) + ' ');
  return LAT_HAY.get(e.id);
}
/* one test per filter; returns null if the value means nothing, with a message */
function filterTest(f) {
  const v = f.val, nv = norm(v).trim();
  switch (f.key) {
    case 'pope': return e => kind(e.era) === 'Pontificate' && startsWord(e.era.name, v);
    case 'council': return e => { const a = assembly(e); return !!a && startsWord(a, v); };
    case 'era': return e => startsWord(e.era.name, v) || (assembly(e) && startsWord(assembly(e), v));
    case 'topic': return e => e.topic && startsWord(e.topic, v);
    case 'weight': case 'grade': case 'level': {
      const wk = Object.entries(WEIGHTS).filter(([k, x]) => norm(k).startsWith(nv) || startsWord(x[0], v)).map(([k]) => k);
      const gk = Object.entries(GRADES).filter(([k, x]) => norm(k).startsWith(nv) || startsWord(x[0], v)).map(([k]) => k);
      const lk = Object.entries(LEVELS).filter(([k, x]) => norm(k).startsWith(nv) || startsWord(x[0], v)).map(([k]) => k);
      if (!wk.length && !gk.length && !lk.length) return { error: `No weight called “${v}”. Try dogma, definitive, authentic, discipline, prudential, condemned or creed.` };
      return e => lk.includes(levelOf(e)) || (e.cur !== null && CURATED[e.cur] ? gk.includes(CURATED[e.cur].g) : wk.includes(wKey(e.weight)));
    }
    case 'kind': {
      const ks = KINDS.filter(([k, label]) => k && (k.startsWith(nv) || startsWord(label, v))).map(([k]) => k);
      if (!ks.length) return { error: `No kind of text called “${v}”. Try creed, definition, anathema, condemned, pbc or curia.` };
      return e => ks.some(k => e.kinds.includes(k));
    }
    case 'year': { const r = yearRange(v); if (!r) return { error: `Give a year or a span, like year:1854 or year:1850-1900.` }; return e => e.year >= r[0] && e.year <= r[1]; }
    case 'before': { const r = yearRange(v); if (!r) return { error: 'Give a year, like before:800.' }; return e => e.year < r[0]; }
    case 'after': { const r = yearRange(v); if (!r) return { error: 'Give a year, like after:1800.' }; return e => e.year > r[1]; }
    case 'ds': { const r = yearRange(v); if (!r) return { error: 'Give a DS number or span, like ds:3000-3075.' }; return e => e.ds.some(n => +n >= r[0] && +n <= r[1]); }
    case 'latin': {
      const words = nv.split(' ').filter(Boolean);
      const phrase = /\s/.test(v.trim()) ? ' ' + nv : null;
      return e => { if (!e.ds.length) return false; const h = latinHay(e); return phrase ? h.includes(phrase) : words.every(w => h.includes(' ' + w)); };
    }
  }
  return null;
}
const FILTER_LABEL = { pope: 'Pope', council: 'Council', era: 'Pope or council', weight: 'Weight', grade: 'Weight', level: 'Weight', kind: 'Kind', year: 'Year', before: 'Before', after: 'After', latin: 'Latin', topic: 'Heading', ds: 'DS' };
function numberQuery(q) {
  const d = dsQuery(q);
  if (d !== null) return (byDS.get(d) || [])[0] || null;
  const doc = q.trim().match(/^([a-z]{2,3})\s*(\d{1,3})$/i);
  if (doc && byId.has(doc[1].toUpperCase() + doc[2])) return byId.get(doc[1].toUpperCase() + doc[2]);
  const m = q.trim().match(/^(?:d\.?|dz\.?|n\.?|no\.?|#)?\s*(\d{1,4}[a-z]?)$/i);
  if (!m) return null;
  return byId.get(m[1].toLowerCase()) || byBase.get(parseInt(m[1], 10)) || null;
}
function runSearch() {
  if (state.topic) {
    const t = state.topic.toLowerCase();
    return { hits: ENTRIES.filter(e => e.topic && e.topic.toLowerCase() === t).map(e => ({ e, score: 0 })), terms: [], filters: [], errors: [] };
  }
  const { terms, neg, filters } = splitQuery(state.query);
  const tests = [], errors = [];
  for (const f of filters) { const t = filterTest(f); if (t && t.error) errors.push(t.error); else if (t) tests.push(t); }
  const pass = e => tests.every(t => t(e)) && !neg.some(n => e.hay.includes(' ' + n) || e.meta.includes(' ' + n));
  if (!terms.length) {
    if (tests.length || neg.length) return { hits: ENTRIES.filter(pass).map(e => ({ e, score: 0 })), terms, filters, errors };
    if (state.weight) return { hits: ENTRIES.filter(e => wKey(e.weight) === state.weight).map(e => ({ e, score: 0 })), terms, filters, errors };
    return { hits: state.kind ? ENTRIES.filter(e => e.kinds.includes(state.kind)).map(e => ({ e, score: 0 })) : [], terms, filters, errors };
  }
  const hits = [];
  for (const e of ENTRIES) {
    if (!pass(e)) continue;
    let score = 0, ok = true;
    for (const t of terms) {
      const needle = ' ' + t;
      let c = 0, i = e.hay.indexOf(needle);
      while (i !== -1 && c < 50) { c++; i = e.hay.indexOf(needle, i + needle.length); }
      const inMeta = e.meta.indexOf(needle) !== -1;
      if (!c && !inMeta) { ok = false; break; }
      score += c + (inMeta ? 6 : 0) + (e.hay.indexOf(needle + ' ') !== -1 ? 1 : 0);
    }
    if (ok) hits.push({ e, score: score / Math.sqrt(30 + e.hay.length / 60) });
  }
  hits.sort((a, b) => b.score - a.score || a.e.k - b.e.k);
  return { hits, terms, filters, errors };
}
function snippet(e, re) {
  const text = e.paras.join(' ');
  let start = 0;
  if (re) { re.lastIndex = 0; const m = re.exec(text); if (m) start = Math.max(0, m.index - 90); }
  let s = text.slice(start, start + 300);
  if (start > 0) s = '…' + s.replace(/^\S*\s/, '');
  if (start + 300 < text.length) s = s.replace(/\s\S*$/, '') + '…';
  let h = esc(s);
  if (re) h = h.replace(re, '<mark>$1</mark>');
  return h;
}
function hitHtml(e, re) {
  const m = Marks.get(e.id);
  return `<a class="hit" href="#n${esc(e.id)}">
    <span class="n">${esc(dispId(e.id))}</span>
    <span><span class="ctx">${W(e.weight)[0]} · ${esc(e.era.name)}${e.era.dates ? ' · ' + esc(e.era.dates) : ''}${e.ses ? ' · ' + esc(e.ses.replace(/\s*\(.*\)$/, '')) : ''}</span>
    ${e.topic ? `<div class="ht">${re ? esc(e.topic).replace(re, '<mark>$1</mark>') : esc(e.topic)}</div>` : ''}
    <div class="snip">${snippet(e, re)}</div>${m && m.note ? `<div class="nt">${esc(m.note)}</div>` : ''}</span></a>`;
}
function renderResults() {
  let { hits, terms, filters, errors } = runSearch();
  if (state.weight && terms.length) hits = hits.filter(h => wKey(h.e.weight) === state.weight);
  highlightTerms = terms;
  const re = termRegex(terms);
  view.className = 'col';
  const inKind = state.kind ? hits.filter(h => h.e.kinds.includes(state.kind)) : hits;
  const periodCounts = PERIODS.map(([, lo, hi]) => inKind.filter(h => h.e.era.year >= lo && h.e.era.year <= hi).length);
  const [, lo, hi] = PERIODS[state.period];
  const inPeriod = hits.filter(h => h.e.era.year >= lo && h.e.era.year <= hi);
  const kindCounts = KINDS.map(([k]) => k ? inPeriod.filter(h => h.e.kinds.includes(k)).length : inPeriod.length);
  const shown = state.kind ? inPeriod.filter(h => h.e.kinds.includes(state.kind)) : inPeriod;
  let title;
  if (state.topic) title = `<em>${esc(state.topic)}</em>`;
  else if (!terms.length && state.weight) title = `<em>${W(state.weight)[0]}</em>`;
  else if (!terms.length && state.kind) title = `<em>${KIND_LABEL[state.kind]}</em>`;
  else if (!terms.length && filters.length) title = `${fmt(shown.length)} ${shown.length === 1 ? 'entry' : 'entries'}`;
  else title = `${fmt(shown.length)} ${shown.length === 1 ? 'entry' : 'entries'} for <em>${esc(terms.join(' '))}</em>`;
  let html = `<div class="res-head"><h1>${title}</h1>${state.topic || (!terms.length && !filters.length) ? `<span class="count">${fmt(shown.length)} ${shown.length === 1 ? 'entry' : 'entries'}</span>` : ''}</div>`;
  if (filters.length) html += `<div class="chips fl"><span class="lbl">Filters</span>${filters.map(f => `<span class="chip on">${FILTER_LABEL[f.key]}: ${esc(f.val)}</span>`).join('')}</div>`;
  if (errors.length) html += `<div class="jump">${errors.map(esc).join('<br>')}</div>`;
  const plain = !filters.length;
  const num = !state.topic && plain ? numberQuery(state.query) : null;
  const dq = !state.topic && plain ? dsQuery(state.query) : null;
  if (dq !== null && num) html += `<div class="jump">DS ${dq} is <a class="xref" href="#n${esc(num.id)}"><b>${esc(nlab(num.id))}</b></a> in the older numbering${(byDS.get(dq) || []).length > 1 ? ` (also ${byDS.get(dq).slice(1).map(x => `<a class="xref" href="#n${esc(x.id)}">${esc(nlab(x.id))}</a>`).join(', ')})` : ''} · ${esc(num.era.name)}${num.dsHow ? ` · ${DS_HOW[num.dsHow][0]}` : ''}</div>`;
  else if (dq !== null) { const nb = dsNearest(dq); html += `<div class="jump">DS ${dq} has no counterpart in this collection${nb.length ? `. Nearest: ${nb.map(nbLink).join('; ')}` : ''}. <a class="xref" href="#concordance">Old and new numbers</a></div>`; }
  else if (num) html += `<div class="jump">Go to <a class="xref" href="#n${esc(num.id)}"><b>${esc(nlab(num.id))}</b></a>${num.ds.length ? ' (' + esc(dsText(num)) + ')' : ''} · ${esc(num.era.name)}${num.topic ? ' · ' + esc(num.topic) : ''}</div>`;
  const sq = !state.topic && plain && scriptureQuery(state.query);
  if (sq) {
    const ch = sq.book.refs.get(sq.ch);
    let list = [];
    if (ch) for (const [v, es] of ch) if (!sq.v || v === sq.v) list.push(...es.map(e => [v, e]));
    list.sort((a, b) => a[0] - b[0] || a[1].k - b[1].k);
    html += `<div class="jump">${esc(sq.book.name)} ${sq.ch}${sq.v ? ':' + sq.v : ''} is cited in ${list.length ? list.map(([v, e]) => `<a class="xref" href="#n${esc(e.id)}">${esc(nlab(e.id))}</a>${sq.v ? '' : ` <span class="count">(${sq.ch}:${v})</span>`}`).join(', ') : 'no entries'} · <a class="xref" href="#book-${sq.book.i}">all of ${esc(sq.book.name)}</a></div>`;
  }
  if (!state.topic) {
    html += `<div class="chips" role="group" aria-label="Filter by period"><span class="lbl">Period</span>${PERIODS.map(([name], i) =>
      `<button class="chip" data-period="${i}" aria-pressed="${state.period === i}" ${periodCounts[i] || i === 0 ? '' : 'disabled'}>${name}<span>${fmt(periodCounts[i])}</span></button>`).join('')}</div>`;
    html += `<div class="chips" role="group" aria-label="Filter by kind of text"><span class="lbl">Kind</span>${KINDS.map(([k, name], i) =>
      `<button class="chip" data-kind="${k}" aria-pressed="${state.kind === k}" ${kindCounts[i] || !k ? '' : 'disabled'}>${name}<span>${fmt(kindCounts[i])}</span></button>`).join('')}</div>`;
    html += `<div class="chips"><span class="lbl">Weight</span><select class="wsel" id="wsel" aria-label="Filter by weight"><option value="">All weights</option>${Object.entries(WEIGHTS).map(([k, x]) => `<option value="${k}" ${state.weight === k ? 'selected' : ''}>${x[0]}</option>`).join('')}</select></div>`;
  }
  if (!shown.length) {
    if (!terms.length && filters.length) html += `<div class="empty">No entries match these filters. Check the spelling of a name (this collection writes <b>Pius IX</b>, <b>Trent</b>, <b>Vatican Council</b>), or widen the years.</div>`;
    if (terms.length) html += `<div class="empty">No entries contain ${terms.length > 1 ? 'all of these words' : 'this word'}${state.period || state.kind ? ' with these filters' : ''}. Try fewer words, a shorter stem such as <b>justif</b>, or another spelling (this translation uses older forms like <b>Machabees</b> and <b>Isaias</b>).</div>`;
  } else {
    html += shown.slice(0, state.topic ? shown.length : state.limit).map(({ e }) => hitHtml(e, re)).join('');
    if (!state.topic && shown.length > state.limit) html += `<button class="btn more" id="more">Show more (${fmt(shown.length - state.limit)} left)</button>`;
  }
  view.innerHTML = html;
  const more = $('more');
  if (more) more.onclick = () => { state.limit += 100; renderResults(); };
}

/* ---------- Since 1950 ---------- */
function levelPill(l) { return `<span class="pill lv-${l}">${LEVELS[l][0]}</span>`; }
function renderSince(focus) {
  view.className = 'col wide';
  const counts = {}; for (const s of SINCE) counts[s.level] = (counts[s.level] || 0) + 1;
  const shown = SINCE.filter(s => !state.sinceLevel || s.level === state.sinceLevel);
  let html = `<div class="eyebrow">Guide</div><h1 class="page-h">Since 1950</h1>
    <p class="lede">No dogma has been defined since the Assumption in 1950 (n. 2333). This guide lists the main documents from Vatican II to Leo XIV, says how much weight each carries, and links each to the older texts in this collection that it continues. Summaries are written for this site; follow the title to the official text.</p>
    <div class="legend">${Object.entries(LEVELS).map(([k, [, d]]) => `<div>${levelPill(k)}<span>${d}</span></div>`).join('')}</div>
    <div class="chips" role="group" aria-label="Filter by weight"><button class="chip" data-level="" aria-pressed="${!state.sinceLevel}">All<span>${SINCE.length}</span></button>${Object.keys(LEVELS).filter(k => counts[k]).map(k => `<button class="chip" data-level="${k}" aria-pressed="${state.sinceLevel === k}">${LEVELS[k][0]}<span>${counts[k]}</span></button>`).join('')}</div>`;
  for (const s of shown) {
    const disp = (s.disputed || []).map(id => DISP_BY_ID.get(id)).filter(Boolean);
    html += `<article class="doc" id="since-${s.id}">
      <div class="meta">${levelPill(s.level)}<span>${esc(s.date.length > 7 ? new Date(s.date + 'T12:00:00').toLocaleDateString('en-US', { year: 'numeric', month: 'short', day: 'numeric' }) : s.date.slice(0, 4))}</span><span>${esc(s.pope)}</span><span>${esc(s.kind)}</span></div>
      <h2><a href="${esc(s.url)}" target="_blank" rel="noopener">${esc(s.title)}<span class="ext">Official text ↗</span></a></h2>
      <p>${esc(s.summary)}</p>
      <div class="blk"><b>Continuity</b><div>${esc(s.continuity)}</div></div>
      <div class="links">
        ${s.refs.length ? `<div>Older texts: ${refLinks(s.refs)}</div>` : ''}
        ${disp.length ? `<div>Debated: ${disp.map(d => `<a href="#q-${d.id}">${esc(d.title)}</a>`).join(' · ')}</div>` : ''}
        ${s.extra ? `<div class="extra"><a href="${esc(s.extra.url)}" target="_blank" rel="noopener">${esc(s.extra.label)} ↗</a></div>` : ''}
      </div>
      <div class="checked">${s.checked === 'text' ? 'Link, date and summary checked against the official text.' : 'Link and date checked against the official page; summary not re-checked line by line.'}</div>
      ${reviewRow('since:' + s.id)}
    </article>`;
  }
  view.innerHTML = html;
  scrollToTarget(focus ? 'since-' + focus : null);
}

/* ---------- Disputed questions ---------- */
function renderDisputed(focus) {
  view.className = 'col wide';
  const counts = {}; for (const d of DISPUTED) counts[d.cat] = (counts[d.cat] || 0) + 1;
  const order = Object.keys(CATS);
  const shown = DISPUTED.filter(d => !state.dispCat || d.cat === state.dispCat).map((d, i) => [d, i]).sort((a, b) => order.indexOf(a[0].cat) - order.indexOf(b[0].cat) || a[1] - b[1]).map(x => x[0]);
  let html = `<div class="eyebrow">Guide</div><h1 class="page-h">Disputed questions</h1>
    <p class="lede">Questions the Church leaves open, cases where older and newer teaching must be read together, and condemned propositions whose words can bear an orthodox sense. A condemnation always attaches to a sense: the one its author intended, or the one the words have as they stand. Each entry gives what is settled, what remains argued, and the reading that keeps both in continuity. Where others see a real break, the entry says so.</p>
    <div class="chips" role="group" aria-label="Filter by category"><button class="chip" data-cat="" aria-pressed="${!state.dispCat}">All<span>${DISPUTED.length}</span></button>${Object.keys(CATS).filter(k => counts[k]).map(k => `<button class="chip" data-cat="${k}" aria-pressed="${state.dispCat === k}">${CATS[k][0]}<span>${counts[k]}</span></button>`).join('')}</div>`;
  let cat = null;
  for (const d of shown) {
    if (d.cat !== cat) { cat = d.cat; html += `<h2 class="sect-h">${CATS[cat][0]}</h2><p class="lede" style="font-size:.95rem;margin-top:-.3rem">${CATS[cat][1]}</p>`; }
    const rel = (d.related || []).map(id => SINCE_BY_ID.get(id)).filter(Boolean);
    html += `<article class="doc" id="q-${d.id}">
      <div class="meta"><span class="pill lv-${d.cat === 'continuity' ? 'authentic' : d.cat === 'censure' ? 'definitive' : d.cat === 'formula' ? 'dogma' : d.cat === 'discipline' ? 'discipline' : d.cat === 'open' ? 'prudential' : 'study'}">${esc(d.status)}</span></div>
      <h2>${esc(d.title)}</h2>
      <p class="q">${esc(d.question)}</p>
      <div class="blk"><b>Settled</b><div>${renderText(d.settled, null)}</div></div>
      <div class="blk"><b>Still open</b><div>${renderText(d.open, null)}</div></div>
      <div class="blk"><b>Continuity</b><div>${renderText(d.reading, null)}</div></div>
      <div class="links">
        ${d.refs.length ? `<div>Texts: ${refLinks(d.refs)}</div>` : ''}
        ${rel.length ? `<div>Since 1950: ${rel.map(s => `<a href="#since-${s.id}">${esc(s.title)}</a>`).join(' · ')}</div>` : ''}
        ${d.refs.length >= 2 ? `<div><a href="#cmp-${encId(d.refs[0])}~${encId(d.refs[d.refs.length - 1])}">Compare ${esc(nlab(d.refs[0]))} with ${esc(nlab(d.refs[d.refs.length - 1]))}</a></div>` : ''}
      </div>
      ${reviewRow('q:' + d.id)}
    </article>`;
  }
  view.innerHTML = html;
  scrollToTarget(focus ? 'q-' + focus : null);
}
function scrollToTarget(id) {
  if (!id) { window.scrollTo(0, 0); return; }
  const el = document.getElementById(id);
  if (!el) { window.scrollTo(0, 0); return; }
  el.scrollIntoView({ block: 'start' });
  el.classList.add('target');
}

/* ---------- Roman Catechism ---------- */
function refGroups(ids) {
  // group a chapter's entries by council or pope and session, and join runs of consecutive entries
  const es = ids.map(id => byId.get(id)).filter(Boolean).sort((a, b) => a.k - b.k);
  const groups = [];
  for (const e of es) {
    const key = e.era.name + (e.ses ? ' · ' + e.ses.replace(/\s*\(.*\)$/, '') : '');
    let g = groups[groups.length - 1];
    if (!g || g.key !== key) { g = { key, era: e.era, year: e.year, runs: [] }; groups.push(g); }
    const r = g.runs[g.runs.length - 1];
    if (r && r[r.length - 1].k === e.k - 1) r.push(e); else g.runs.push([e]);
  }
  return groups;
}
function groupHtml(g) {
  const runs = g.runs.map(r => r.length === 1 ? `<a class="xref" href="#n${esc(r[0].id)}">${esc(dispId(r[0].id))}</a>`
    : `<a class="xref" href="#n${esc(r[0].id)}">${esc(dispId(r[0].id))}–${esc(dispId(r[r.length - 1].id))}</a>`).join(', ');
  const t = g.runs.length === 1 && g.runs[0].length === 1 && g.runs[0][0].topic ? ` <span class="rct">${esc(g.runs[0][0].topic)}</span>` : '';
  return `<div class="rcg"><span class="rcw">${esc(g.key)}</span><span>n. ${runs}${t}</span></div>`;
}
function renderCatechism(focus) {
  view.className = 'col wide';
  let html = `<div class="eyebrow">Guide</div><h1 class="page-h">${esc(RC.title || 'The Roman Catechism')}</h1>
    <p class="lede">${esc(RC.about || '')}</p>
    <div class="links" style="font-family:var(--sans);font-size:.92rem">${(RC.texts || []).map(t => `<div><a class="xref" href="${esc(t.url)}" target="_blank" rel="noopener">${esc(t.label)} ↗</a></div>`).join('')}</div>
    <div class="chips" style="margin-top:1rem">${RC.parts.map(p => `<a class="chip" style="text-decoration:none" href="#rc-${esc(p.chapters[0].id)}">${esc(p.title)}<span>${p.chapters.length}</span></a>`).join('')}</div>`;
  for (const p of RC.parts) {
    html += `<h2 class="sect-h">${esc(p.title)}</h2>`;
    for (const ch of p.chapters) {
      const before = ch.refs.filter(id => { const e = byId.get(id); return e && e.year <= RC_YEAR; });
      const later = ch.refs.filter(id => { const e = byId.get(id); return e && e.year > RC_YEAR; });
      html += `<article class="doc" id="rc-${esc(ch.id)}">
        <h2>${esc(ch.title)}</h2>
        <p>${esc(ch.summary)}</p>
        ${ch.refs.length ? '' : '<p class="checked">No text in this collection bears directly on this chapter.</p>'}
        ${before.length ? `<div class="blk"><b>Texts it explains</b><div class="rcl">${refGroups(before).map(groupHtml).join('')}</div></div>` : ''}
        ${later.length ? `<div class="blk"><b>Later texts</b><div class="rcl">${refGroups(later).map(groupHtml).join('')}</div></div>` : ''}
        ${reviewRow('rc:' + ch.id)}
      </article>`;
    }
  }
  view.innerHTML = html;
  scrollToTarget(focus ? 'rc-' + focus : null);
}

/* ---------- timeline ---------- */
const TL_ROWS = [
  ['dogma', 'Defined dogma and creeds'], ['definitive', 'Definitive teaching and condemnations'], ['authentic', 'Authoritative teaching'],
  ['discipline', 'Discipline'], ['prudential', 'Prudential decisions'], ['study', 'Particular councils, notes and witnesses'],
];
const TL_BIN = 25, TL_FROM = 75, TL_TO = 2000;
function tlData() {
  const nb = Math.ceil((TL_TO - TL_FROM) / TL_BIN);
  const rows = TL_ROWS.map(([k, label]) => ({ k, label, bins: new Array(nb).fill(0), total: 0 }));
  const sup = { k: 'sup', label: 'Added to this site: Constance and Basel', bins: new Array(nb).fill(0), total: 0 };
  for (const e of ENTRIES) {
    if (e.note) continue;
    const b = Math.min(nb - 1, Math.max(0, Math.floor((e.year - TL_FROM) / TL_BIN)));
    let row = e.sup ? sup : rows.find(r => r.k === levelOf(e)) || rows[rows.length - 1];
    if (levelOf(e) === 'dialogue') row = rows[rows.length - 1];
    row.bins[b]++; row.total++;
  }
  return { rows: [...rows, sup], nb };
}
let tlResize = null;
window.addEventListener('resize', () => { clearTimeout(tlResize); tlResize = setTimeout(() => { if (state.view === 'timeline') { const y = window.scrollY; renderTimeline(); window.scrollTo(0, y); } }, 200); });
function renderTimeline() {
  view.className = 'col wide';
  const { rows, nb } = tlData();
  const max = Math.max(...rows.flatMap(r => r.bins));
  const W = Math.max(320, Math.round(view.clientWidth || 820)), L = 2, R = 2, labH = 26, barMax = W < 600 ? 30 : 38, rowH = labH + barMax + 14, top = labH;
  const slot = (W - L - R) / nb, bw = Math.max(2, Math.min(24, slot - 2));
  const x = i => L + i * slot + (slot - bw) / 2;
  let svg = `<svg class="tl" width="${W}" height="${rows.length * rowH + 22}" viewBox="0 0 ${W} ${rows.length * rowH + 22}" role="img" aria-label="Entries per quarter century, by weight">`;
  rows.forEach((r, ri) => {
    const base = top + ri * rowH + barMax + 4;
    svg += `<line class="tl-base" x1="${L}" x2="${W - R}" y1="${base + .5}" y2="${base + .5}"/>`;
    r.bins.forEach((c, i) => {
      const y0 = TL_FROM + i * TL_BIN, y1 = y0 + TL_BIN - 1;
      if (c) {
        const h = Math.max(2, c / max * barMax);
        const rr = Math.min(4, h / 2, bw / 2);
        svg += `<path class="tl-bar lv-${r.k === 'sup' ? 'sup' : r.k}" d="M${x(i)},${base} v${-(h - rr)} q0,${-rr} ${rr},${-rr} h${bw - 2 * rr} q${rr},0 ${rr},${rr} v${h - rr} z"/>`;
      }
      if (c) svg += `<rect class="tl-hit" x="${L + i * slot}" y="${base - barMax - 4}" width="${slot}" height="${barMax + 8}" tabindex="0" data-tl="${r.k}|${y0}|${y1}|${c}"><title>${y0}–${y1}: ${c} ${c === 1 ? 'entry' : 'entries'}</title></rect>`;
    });
  });
  const axY = rows.length * rowH + 14;
  for (let y = 200; y < TL_TO; y += W < 600 ? 400 : 200) svg += `<text class="tl-ax" x="${L + (y - TL_FROM) / TL_BIN * slot}" y="${axY}" text-anchor="middle">${y}</text>`;
  svg += '</svg>';
  const labels = rows.map((r, ri) => `<div class="tl-lab" style="top:${ri * rowH}px"><span class="pill ${r.k === 'sup' ? 'lv-study' : 'lv-' + r.k}">${esc(r.label)}</span><span class="count">${fmt(r.total)}</span></div>`).join('');
  // the definitions, in order
  const defs = [];
  for (const e of ENTRIES) {
    if (e.note || e.sup || levelOf(e) !== 'dogma') continue;
    const last = defs[defs.length - 1];
    if (last && last.era === e.era && (last.topic || '') === (e.topic || '') && last.ids[last.ids.length - 1].k === e.k - 1) last.ids.push(e);
    else defs.push({ era: e.era, topic: e.topic, year: e.year, ids: [e] });
  }
  const cent = c => Math.floor(c / 100) + 1;
  let list = '', cur = null;
  for (const d of defs) {
    const c = cent(d.year);
    if (c !== cur) { list += `<div class="tl-cent">${ordinal(c)} century</div>`; cur = c; }
    const a = d.ids[0], b = d.ids[d.ids.length - 1];
    list += `<a class="tl-def" href="#n${esc(a.id)}"><span class="y">${d.year}</span><span class="n">${esc(dispId(a.id))}${a !== b ? '–' + esc(dispId(b.id)) : ''}</span><span class="t">${esc(d.topic || d.era.name)}<small>${esc(d.era.name)}</small></span></a>`;
  }
  // table view: counts by century
  const cents = [];
  for (let c = 1; c <= 20; c++) cents.push(c);
  const byC = rows.map(r => cents.map(c => r.bins.reduce((s, n, i) => { const y = TL_FROM + i * TL_BIN; return s + (cent(y) === c ? n : 0); }, 0)));
  const table = `<div class="tablewrap"><table class="wtable tl-table"><thead><tr><th>Century</th>${rows.map(r => `<th>${esc(r.label)}</th>`).join('')}</tr></thead><tbody>${cents.map((c, ci) => rows.some((_, ri) => byC[ri][ci]) ? `<tr><td>${ordinal(c)}</td>${rows.map((_, ri) => `<td>${byC[ri][ci] || ''}</td>`).join('')}</tr>` : '').join('')}</tbody></table></div>`;
  view.innerHTML = `<div class="eyebrow">Guide</div><h1 class="page-h">Timeline</h1>
    <p class="lede">Every entry placed by date and grouped by weight, in quarter centuries. Dates come from the heading of each text where it gives one, and otherwise from the start of the pontificate or council. Select a column to list its entries.</p>
    <div class="tl-wrap"><div class="tl-labs">${labels}</div>${svg}<div class="tl-tip" id="tlTip" hidden></div></div>
    <details class="tl-more"><summary>Show the counts as a table</summary>${table}</details>
    <h2 class="sect-h">Definitions and creeds, in order</h2>
    <p class="lede" style="font-size:.95rem">Texts graded as defined dogma or a creed, joined where several entries carry one text.</p>
    <div class="tl-defs">${list}</div>`;
  const tip = $('tlTip'), wrap = view.querySelector('.tl-wrap');
  const show = el => {
    const [k, y0, y1, c] = el.dataset.tl.split('|');
    const row = rows.find(r => r.k === k);
    tip.innerHTML = ''; const b = document.createElement('b'); b.textContent = `${c} ${+c === 1 ? 'entry' : 'entries'}`;
    const s = document.createElement('span'); s.textContent = `${row.label} · ${y0}–${y1}`;
    tip.append(b, s); tip.hidden = false;
    const r = el.getBoundingClientRect(), w = wrap.getBoundingClientRect();
    tip.style.left = Math.min(w.width - 200, Math.max(0, r.left - w.left + r.width / 2 - 100)) + 'px';
    tip.style.top = (r.top - w.top - 52) + 'px';
  };
  view.querySelectorAll('.tl-hit').forEach(el => {
    el.addEventListener('pointerenter', () => show(el)); el.addEventListener('focus', () => show(el));
    el.addEventListener('pointerleave', () => { tip.hidden = true; }); el.addEventListener('blur', () => { tip.hidden = true; });
    const open = () => { const [k, y0, y1] = el.dataset.tl.split('|'); const q = k === 'sup' ? `year:${y0}-${y1} era:supplement` : `year:${y0}-${y1} weight:${k}`; qInput.value = q; state.query = q; state.topic = null; state.kind = ''; state.weight = ''; state.period = 0; state.limit = 60; go('#results'); };
    el.addEventListener('click', open);
    el.addEventListener('keydown', ev => { if (ev.key === 'Enter' || ev.key === ' ') { ev.preventDefault(); open(); } });
  });
  window.scrollTo(0, 0);
}

/* ---------- Scripture index ---------- */
function renderScripture() {
  view.className = 'col wide';
  const total = BOOKS.reduce((a, b) => a + b.count, 0);
  const part = t => BOOKS.filter(b => b.test === t).map(b => b.count
    ? `<a href="#book-${b.i}"><b>${esc(b.name)}</b><span>${b.count}</span></a>`
    : `<a class="none"><b>${esc(b.name)}</b><span>–</span></a>`).join('');
  view.innerHTML = `<div class="eyebrow">Index</div><h1 class="page-h">Scripture index</h1>
    <p class="lede">${fmt(total)} references to Scripture in square brackets, by book. The translation follows the Vulgate, so most Psalms are numbered one lower than in modern Bibles (Psalm 32 here is Psalm 33).</p>
    <h2 class="sect-h">Old Testament</h2><div class="books">${part('OT')}</div>
    <h2 class="sect-h">New Testament</h2><div class="books">${part('NT')}</div>`;
  window.scrollTo(0, 0);
}
function renderBook(b) {
  view.className = 'col';
  const chs = [...b.refs.keys()].sort((x, y) => x - y);
  let html = `<div class="eyebrow"><a href="#scripture" style="text-decoration:none">Scripture index</a></div><h1 class="page-h">${esc(b.name)}</h1>
    <p class="lede">${b.count} ${b.count === 1 ? 'citation' : 'citations'} across ${chs.length} ${chs.length === 1 ? 'chapter' : 'chapters'}.</p><div class="vlist">`;
  for (const c of chs) {
    html += `<div class="ch">Chapter ${c}</div>`;
    const vs = [...b.refs.get(c).entries()].sort((x, y) => x[0] - y[0]);
    for (const [v, es] of vs) html += `<div class="v"><b>${c}:${v}</b><span>${es.map(e => `<a href="#n${esc(e.id)}">${esc(nlab(e.id))}</a>`).join('')}</span></div>`;
  }
  view.innerHTML = html + '</div>';
  window.scrollTo(0, 0);
}

/* ---------- topics ---------- */
let TOPICS = null;
function topicIndex() {
  if (TOPICS) return TOPICS;
  const m = new Map();
  for (const e of ENTRIES) {
    if (!e.topic || (e.topic.match(/[A-Za-z]/g) || []).length < 3) continue;
    const key = e.topic.toLowerCase();
    if (!m.has(key)) m.set(key, { name: e.topic, count: 0, first: e });
    m.get(key).count++;
  }
  const sortKey = t => {
    let k = t.name, prev;
    do { prev = k; k = k.replace(/^(?:(?:The|An?)\s+|(?:Chap|Can|Sec|Art|Ch)\.?\s*[\dIVXL]+\s*\.?\s*|[A-Z]\.\s+|\d+\s*\.\s*|["'(\[\s]+)/i, ''); } while (k !== prev);
    return k;
  };
  TOPICS = [...m.values()].map(t => ({ ...t, sort: sortKey(t) })).sort((a, b) => a.sort.localeCompare(b.sort));
  return TOPICS;
}
function renderTopics(filter = '') {
  view.className = 'col';
  const list = topicIndex();
  const f = norm(filter).trim();
  const shown = f ? list.filter(t => (' ' + norm(t.name)).includes(' ' + f)) : list;
  let html = `<div class="res-head"><h1>Topics</h1><span class="count">${fmt(shown.length)} of ${fmt(list.length)} headings</span></div>
    <input class="tfilter" id="tfilter" type="search" placeholder="Filter headings, e.g. primacy, baptism, errors" value="${esc(filter)}" aria-label="Filter topics">
    <div class="tlist">`;
  let letter = null;
  for (const t of shown) {
    const L = (t.sort[0] || '#').toUpperCase();
    if (L !== letter && !f) { html += `<div class="tletter">${esc(L)}</div>`; letter = L; }
    html += `<button data-topic="${esc(t.name)}"><span class="tn">${esc(t.name)}</span><span class="tc">${t.count > 1 ? t.count + ' entries' : esc(nlab(t.first.id))}</span></button>`;
  }
  view.innerHTML = html + '</div>';
  const inp = $('tfilter');
  inp.oninput = () => { const pos = inp.selectionStart; renderTopics(inp.value); const n = $('tfilter'); n.focus(); n.setSelectionRange(pos, pos); };
}

/* ---------- saved ---------- */
function renderSaved() {
  view.className = 'col';
  const list = Marks.list();
  const where = Marks.mode === 'cloud' ? 'Kept with your account, visible only to you, on any device where you open this page.' : 'Kept in this browser only.';
  let html = `<div class="res-head"><h1>Saved and notes</h1><span class="count">${fmt(list.length)} ${list.length === 1 ? 'entry' : 'entries'}</span></div><p class="lede">${where}</p>`;
  if (list.length) html += `<div class="actions" style="margin-bottom:1rem"><button class="btn small primary" data-dl-saved="1">Download study packet</button><span class="count" style="align-self:center">Full texts, your notes and citations, in the order of the collection.</span></div>`;
  if (!list.length) html += `<div class="empty">Nothing saved yet. Open any entry and use <b>Save</b> or <b>Add note</b> under its text.</div>`;
  else html += list.map(x => hitHtml(x.e, null)).join('');
  view.innerHTML = html;
}


/* ---------- weight and censures ---------- */
const NOTES = [
  ['De fide divina et catholica', 'Revealed and proposed as such by a solemn definition or by the ordinary universal magisterium. Denial is heresy.'],
  ['De fide ecclesiastica / definitive', 'Not formally revealed but proposed definitively, such as dogmatic facts or truths closely connected with revelation. To be held firmly.'],
  ['Sententia fidei proxima', 'Generally held to be revealed but not yet finally proposed as such.'],
  ['Theologice certa', 'A conclusion that follows certainly from revealed truth. Denial is called erroneous.'],
  ['Sententia communis', 'The common teaching of theologians in a field left open by the Church.'],
  ['Sententia probabilis', 'A well-founded opinion that can be held, among others.'],
];
const CENSURE_GRADES = [
  ['Heretical', 'Contradicts a truth of divine and Catholic faith.'],
  ['Proximate to heresy', 'Contradicts a truth close to faith (sententia fidei proxima).'],
  ['Erroneous', 'Contradicts a theologically certain conclusion.'],
  ['Suspect of heresy', 'Gives good reason to think heresy lies behind it.'],
  ['False', 'Contrary to fact or to sound teaching, without a stronger note specified.'],
  ['Rash', 'Departs from the common teaching without sufficient grounds.'],
  ['Evil-sounding / ill-sounding', 'Expressed in a way that suggests a wrong sense, though it may be explained correctly.'],
  ['Offensive to pious ears', 'Wounds the sense of the faithful in how it is put.'],
  ['Scandalous', 'Likely to lead others into sin or error.'],
  ['Captious', 'Ambiguous in a way that ensnares.'],
  ['Schismatic, seditious', 'Undermines the unity or order of the Church.'],
];
function renderWeights() {
  view.className = 'col wide';
  const counts = {}; for (const e of ENTRIES) { const k = wKey(e.weight); counts[k] = (counts[k] || 0) + 1; }
  view.innerHTML = `<div class="eyebrow">Guide</div><h1 class="page-h">Weight and censures</h1>
    <p class="lede">Not every text in Denzinger binds in the same way. Each entry here is labeled by the form of the text, which is what its weight follows from. The labels are assigned by rules (the kind of council, the presence of a defining formula, an anathema or a censure) and a short list of papal definitions chosen by hand; treat them as a guide, and weigh each text by what it actually proposes.</p>
    <h2 class="sect-h">Labels used on each entry</h2>
    <div class="tablewrap"><table class="wtable"><thead><tr><th>Label</th><th>What it means</th><th>Entries</th></tr></thead><tbody>
    ${Object.entries(WEIGHTS).map(([k, x]) => `<tr><td><span class="pill lv-${x[1]}">${x[0]}</span></td><td>${esc(x[2])}</td><td><a class="xref" href="#weight-${k}">${fmt(counts[k] || 0)}</a></td></tr>`).join('')}
    </tbody></table></div>
    <h2 class="sect-h">Four cautions</h2>
    <div class="tips" style="font-size:.95rem">
      <div>In a definition, only what is proposed to be held is defined; arguments, historical remarks and reasons are not.</div>
      <div>A canon with an anathema usually concerns faith, but Trent also attached anathemas to disciplinary matters, so each canon is weighed by its content.</div>
      <div>Condemning a proposition does not define its contradictory. When propositions are condemned "respectively," each carries at least one of the listed censures, not all of them.</div>
      <div>Ordinary papal and curial teaching is authoritative and owed assent, but can be refined; Donum Veritatis §24 says some prudential interventions may have deficiencies.</div>
    </div>
    <h2 class="sect-h">Theological notes</h2>
    <p class="lede" style="font-size:.95rem">The classical grades by which theologians rate a proposition's certainty, highest first.</p>
    <div class="tablewrap"><table class="wtable"><tbody>${NOTES.map(([a, b]) => `<tr><td><b>${a}</b></td><td>${b}</td></tr>`).join('')}</tbody></table></div>
    <h2 class="sect-h">Censures</h2>
    <p class="lede" style="font-size:.95rem">The grades the Church used when condemning propositions, roughly from gravest to lightest.</p>
    <div class="tablewrap"><table class="wtable"><tbody>${CENSURE_GRADES.map(([a, b]) => `<tr><td><b>${a}</b></td><td>${b}</td></tr>`).join('')}</tbody></table></div>`;
  window.scrollTo(0, 0);
}

/* ---------- reading a condemnation ---------- */
const refl = ids => refLinks(ids.map(String));
function renderReading() {
  view.className = 'col';
  const qs = DISPUTED.filter(d => d.cat === 'censure');
  view.innerHTML = `<div class="eyebrow">Guide</div><h1 class="page-h">Reading a condemnation</h1>
    <p class="lede">Condemned propositions and controversial bulls are the texts most easily misread. A common shortcut runs: read the bare words of a condemned proposition; notice that, taken as written, they seem to clash with Scripture, a Father or earlier teaching; conclude that Catholic teaching contradicts itself. Each step skips the question the condemnation itself raises: in what sense was this proposition condemned?</p>
    <p>Magisterial texts are written against something: an error in view, an adversary's terms, the argument they answer. Reading them without that setting is reading them wrongly. But the setting has to be shown from evidence, not supplied by assumption.</p>
    <h2 class="sect-h">What a condemnation targets</h2>
    <div class="tips" style="font-size:.95rem">
      <div><b>A proposition in a determinate sense, not every meaning its words could bear.</b> Pius V condemned the propositions of Baius in the strict and proper sense their authors intended, granting that some could be held in some sense (${refl([1080])}). Pius VI often names the sense outright: a proposition on the power given to the Church is heretical "if thus understood" that the power comes from the community (${refl([1502])}); the Church as "one mystical body", language the Church herself uses, is censured only "understood in this sense" that no one belongs to the Church but the perfect (${refl([1515])}).</div>
      <div><b>The condemned sense is established, not assumed.</b> The evidence is the source the proposition was taken from and the argument it served there; the wording of the condemnation, with its clauses, conditions and censures; and authoritative explanations or later acts. An intention that none of these shows is not evidence, whether it is used to accuse or to excuse.</div>
      <div><b>Condemned is not the same as declared heretical.</b> When propositions are condemned "respectively" or in globo, a list of censures covers the whole set, and each proposition deserves at least one of them, not necessarily the gravest. Exsurge Domine (${refl([781])}) and Unigenitus (${refl([1451])}) assign none individually.</div>
      <div><b>Rejecting a sense does not affirm its unrestricted opposite.</b> The contradictory of a condemned proposition is not thereby defined.</div>
      <div><b>The same words can carry different doctrines.</b> Agreement in vocabulary, above all Augustinian vocabulary on grace, freedom and necessity, can hide real disagreement. A sentence that repeats a Father almost word for word can be condemned for the sense it has in its new setting, and that sense has to be found in the argument around it.</div>
      <div><b>A definition is not its reasoning.</b> What is defined is what is proposed to be held; the arguments, illustrations and history around it are not (see the disputed question on Unam Sanctam).</div>
    </div>
    <h2 class="sect-h">A hard case: Unigenitus</h2>
    <p>Clement XI's bull Unigenitus (1713) condemned 101 propositions taken from Quesnel's Réflexions morales (${refl([1351, 1451])}). Jacques M. Gres-Gayer's study of its Roman preparation, drawing on Lucien Ceyssens's edition of the documents, shows why reading it well takes work:</p>
    <div class="tips" style="font-size:.95rem">
      <div>The examiners judged the 155 propositions first submitted as excerpts from a book presumed suspect, "in the sense of Jansenius", and at times reasoned: "Even though he did not say it, I understood what he meant" (p. 267).</div>
      <div>Some propositions are near-quotations of the Fathers. Proposition 13 (${refl([1363])}) is almost Augustine's De correptione et gratia: Clement suspended judgment because "it could be interpreted in a Catholic sense," yet it remained in the bull. He hesitated over proposition 23 (${refl([1373])}), a patristic reference, and noted "posse omitti" on proposition 33 (${refl([1383])}) before it was kept. On proposition 12 (${refl([1362])}) he qualified his own verdict: "unless these are the very words of St. Prosper, which remains to be seen" (pp. 268–69).</div>
      <div>Proposition 90 (${refl([1440])}), on excommunication with the consent of the whole body, was kept despite the Pope's fear that it would provoke a Gallican rejection (p. 269).</div>
      <div>Against Fénelon's advice, the censures were given in globo, so the bull never says which note fits which proposition; the book as a whole was condemned (pp. 269–70).</div>
    </div>
    <p>Two conclusions follow, and they pull against each other. The bare words of proposition 13 cannot show that the Church condemned Augustine: what was condemned is the sense the propositions had in Quesnel's work and system, under censures not all of which fit each one. But that sense is not self-evident either. It has to be shown from Quesnel's text and argument, and the record shows that the Pope himself found some cases close. An apparent contradiction is a question to examine, not a refutation, and not something to dissolve by assuming whatever intention is convenient.</p>
    <p style="font-size:.9rem;color:var(--muted)">Source: Jacques M. Gres-Gayer, "The Unigenitus of Clement XI: A Fresh Look at the Issues," Theological Studies 49 (1988) 259–82. See also the disputed question on Quesnel.</p>
    <h2 class="sect-h">Before concluding that a text contradicts earlier teaching</h2>
    <ol style="font-size:.95rem">
      <li>Read the condemnation's own wording. Is a sense named ("if thus understood", "in the sense of", "as they lie")? Are the censures one per proposition, respective, or in globo?</li>
      <li>Find the source: the book, sermon, synod or system the proposition came from, and the argument it served there.</li>
      <li>Establish what the words meant in that argument, from the source, not by guessing at hidden intentions.</li>
      <li>Look for authoritative explanations: the bull's preamble, its documents of preparation, later papal acts.</li>
      <li>Ask what is actually affirmed by rejecting the proposition, and what is not.</li>
      <li>Weigh it: a definition, a censure of heresy, a lighter note, or a disciplinary measure.</li>
      <li>If a tension remains after all this, name it as an open question rather than a conclusion.</li>
    </ol>
    <h2 class="sect-h">Condemned propositions discussed on this site</h2>
    <div class="tips" style="font-size:.95rem">${qs.map(d => `<div><a class="xref" href="#q-${esc(d.id)}">${esc(d.title)}</a> · ${esc(d.status)}</div>`).join('')}</div>`;
  window.scrollTo(0, 0);
}

/* ---------- threads ---------- */
function stepWhen(st) {
  if (st.since) { const s = SINCE_BY_ID.get(st.since); return s ? s.date.slice(0, 4) : ''; }
  const e = byId.get(st.ref); if (!e) return '';
  const m = ((e.sup ? e.ses : '') || e.era.dates || '').match(/\d{4}/) || (e.era.dates || '').match(/\d{2,4}/); return m ? m[0] : '';
}
function renderThreads() {
  view.className = 'col wide';
  view.innerHTML = `<div class="eyebrow">Guide</div><h1 class="page-h">Doctrinal threads</h1>
    <p class="lede">Each thread follows one doctrine in order through the collection and on into the documents since 1950, with a note on what each step adds. Read together they show development in the same sense and meaning, which is the claim of the hermeneutic of continuity.</p>
    <div class="threads">${THREADS.map(t => `<a class="guide" href="#thread-${t.id}"><b>${esc(t.title)}</b><span>${esc(t.summary)}</span><span>${t.steps.length} steps</span></a>`).join('')}</div>`;
  window.scrollTo(0, 0);
}
function renderThread(t) {
  view.className = 'col';
  let html = `<div class="eyebrow"><a href="#threads" style="text-decoration:none">Doctrinal threads</a></div><h1 class="page-h">${esc(t.title)}</h1>
    <p class="lede">${esc(t.summary)}</p>
    <div class="actions"><button class="btn small" data-dl-thread="${t.id}">Download this thread</button></div>
    ${reviewRow('thread:' + t.id)}
    <div class="timeline">`;
  for (const st of t.steps) {
    if (st.since) {
      const s = SINCE_BY_ID.get(st.since); if (!s) continue;
      html += `<div class="step since"><span class="when">${stepWhen(st)}</span><span class="dot"></span><div class="what">
        <div class="hd"><a href="#since-${s.id}">${esc(s.title)}</a>${levelPill(s.level)}<span>${esc(s.pope)}</span></div>
        <p>${esc(st.note)}</p></div></div>`;
    } else {
      const e = byId.get(st.ref); if (!e) continue;
      const text = e.paras.join(' ');
      html += `<div class="step"><span class="when">${stepWhen(st)}</span><span class="dot"></span><div class="what">
        <div class="hd"><a href="#n${esc(e.id)}">${esc(nlab(e.id))}</a>${e.cur !== null && CURATED[e.cur] ? curPill(e) : weightPill(e.weight)}<span>${esc(e.era.name)}</span></div>
        <p>${esc(st.note)}</p>
        <details><summary>Show the text</summary><p>${renderText(text.length > 900 ? text.slice(0, 900).replace(/\s\S*$/, '') + '…' : text, null)}</p></details></div></div>`;
    }
  }
  view.innerHTML = html + '</div>';
  window.scrollTo(0, 0);
}

/* ---------- study packets ---------- */
let Downloads = null;
function entryMd(e, note) {
  const lines = [`## ${nlab(e.id)}${e.ds.length ? ' (' + dsText(e) + ')' : ''} · ${e.era.name}${e.era.dates ? ' (' + e.era.dates + ')' : ''}`, ''];
  lines.push(`*${W(e.weight)[0]}${e.ses ? ' · ' + e.ses : ''}${e.topic ? ' · ' + e.topic : ''}*`, '');
  if (e.src) lines.push(`${e.src}`, '');
  for (const p of e.paras) lines.push(p, '');
  if (note) lines.push(`> **My note:** ${note.replace(/\n/g, '\n> ')}`, '');
  lines.push(`— ${citation(e)}`, '', '---', '');
  return lines.join('\n');
}
function savedPacket() {
  const list = Marks.list();
  const head = `# Study packet: Sources of Catholic Dogma\n\nSaved entries in the order of the collection, ${new Date().toLocaleDateString('en-US', { year: 'numeric', month: 'long', day: 'numeric' })}. Text: Denzinger, English translation, older numbering.\n\n---\n\n`;
  return head + list.map(x => entryMd(x.e, x.note)).join('\n');
}
function threadPacket(t) {
  let md = `# ${t.title}\n\n${t.summary}\n\nA doctrinal thread from the Sources of Catholic Dogma reader. Notes are summaries; the texts are Denzinger's English translation, older numbering.\n\n---\n\n`;
  for (const st of t.steps) {
    if (st.since) { const s = SINCE_BY_ID.get(st.since); if (s) md += `## ${s.title} (${s.date.slice(0, 4)}, ${s.pope})\n\n*${LEVELS[s.level][0]} · ${s.kind}*\n\n**Step:** ${st.note}\n\n${s.summary}\n\nOfficial text: ${s.url}\n\n---\n\n`; }
    else { const e = byId.get(st.ref); if (e) md += `**Step:** ${st.note}\n\n` + entryMd(e, (Marks.get(e.id) || {}).note) + '\n'; }
  }
  return md;
}
async function offerFile(filename, text) {
  if (PAGES) {
    try {
      const a = document.createElement('a');
      a.href = URL.createObjectURL(new Blob([text], { type: 'text/markdown;charset=utf-8' }));
      a.download = filename; document.body.appendChild(a); a.click(); a.remove();
      setTimeout(() => URL.revokeObjectURL(a.href), 4000); toast('Downloaded'); return;
    } catch (_) { /* fall through to copy */ }
  }
  if (Downloads) {
    try { await Downloads.save({ filename, data: text }); toast('Saved'); return; }
    catch (err) { if (err && err.code === 'declined') return; }
  }
  // fallback: show the text to copy
  const wrap = document.createElement('div');
  wrap.innerHTML = `<h2 class="sect-h">Your packet</h2><p class="lede" style="font-size:.95rem">Downloads aren't available in this view. Copy the text below into a file named ${esc(filename)}.</p><textarea class="packet" readonly aria-label="Packet text"></textarea><div class="actions" style="margin-top:.5rem"><button class="btn small" id="copyPacket">Copy</button></div>`;
  wrap.querySelector('textarea').value = text;
  view.appendChild(wrap);
  wrap.scrollIntoView({ block: 'start' });
  $('copyPacket').onclick = () => copy(text, 'Copied', wrap.querySelector('textarea'));
}

/* ---------- compare ---------- */
const encId = id => id.replace(/\*/g, '_s');
const decId = s => s.replace(/_s/g, '*');
function cmpCol(e) {
  if (!e) return `<div><p class="empty">Enter an entry number above.</p></div>`;
  return `<div><div class="hd"><a href="#n${esc(e.id)}">${esc(nlab(e.id))}</a> · ${esc(e.era.name)}${e.era.dates ? ' · ' + esc(e.era.dates) : ''}</div>
    <div class="wline">${dsTag(e)}${curPill(e) || weightPill(e.weight)}${censHtml(e)}</div>
    ${e.cur !== null && CURATED[e.cur] ? `<p class="checked">${esc(CURATED[e.cur].n)}</p>` : ''}
    ${e.topic ? `<h3>${esc(e.topic)}</h3>` : ''}${e.src ? `<p class="src">${renderText(e.src, null)}</p>` : ''}
    ${e.paras.map(p => `<p>${renderText(p, null)}</p>`).join('')}${Latin.all && !e.sup ? latinHtml(e) : ''}</div>`;
}
function renderCompare(a, b) {
  view.className = 'col wide';
  const A = a && byId.get(a), B = b && byId.get(b);
  let between = '';
  if (A && B) {
    const ds = DISPUTED.filter(d => d.refs.includes(A.id) && d.refs.includes(B.id));
    const ts = THREADS.filter(t => t.steps.some(s => s.ref === A.id) && t.steps.some(s => s.ref === B.id));
    if (ds.length || ts.length) between = `<div class="between">${ds.map(d => `Discussed together in <a href="#q-${d.id}">${esc(d.title)}</a>: ${esc(d.reading)}`).join('<br>')}${ts.length ? `${ds.length ? '<br>' : ''}Both appear in the thread ${ts.map(t => `<a href="#thread-${t.id}">${esc(t.title)}</a>`).join(', ')}.` : ''}</div>`;
  }
  const presets = DISPUTED.filter(d => d.refs.length >= 2).slice(0, 10).map(d => `<a class="chip" style="text-decoration:none" href="#cmp-${encId(d.refs[0])}~${encId(d.refs[d.refs.length - 1])}">${esc(d.title)}</a>`).join('');
  view.innerHTML = `<div class="eyebrow">Tool</div><h1 class="page-h">Compare two texts</h1>
    <p class="lede">Read two entries side by side. Use Compare under any entry to pick one, then Compare under a second, or type numbers here.</p>
    <form class="cmpbar" id="cmpForm"><input id="cmpA" value="${esc(A ? dispId(A.id) : (a || ''))}" aria-label="First entry number" placeholder="e.g. 714 or DS 1351"><span>with</span><input id="cmpB" value="${esc(B ? dispId(B.id) : (b || ''))}" aria-label="Second entry number" placeholder="e.g. 1677"><button class="btn small primary" type="submit">Compare</button><button class="btn small" type="button" data-latin-all="1" aria-pressed="${Latin.all}">${Latin.all ? 'Hide Latin' : 'Show Latin'}</button>${A && B ? `<button class="btn small" type="button" data-go="#cmp-${encId(B.id)}~${encId(A.id)}">Swap</button>` : ''}</form>
    ${between}
    <div class="cmp">${cmpCol(A)}${cmpCol(B)}</div>
    <h2 class="sect-h">Pairs from the disputed questions</h2><div class="chips">${presets}</div>`;
  $('cmpForm').onsubmit = ev => {
    ev.preventDefault();
    const x = numberQuery($('cmpA').value), y = numberQuery($('cmpB').value);
    if (!x || !y) { toast('Enter two entry numbers from the collection (old numbers, or DS before a new one)'); return; }
    go(`#cmp-${encId(x.id)}~${encId(y.id)}`);
  };
  window.scrollTo(0, 0);
}

/* ---------- ask ---------- */
let Sample = null, askCtl = null, askLast = null;
const STOP = new Set('a an the of and or to in on for by with is are was were be been what which who whom whose how why when where did does do can could should would may might about from as at that this these those it its into than then there their they them we our you your i me my not no yes all any each more most some such only also over under after before between church catholic teach teaching taught say said says'.split(' '));
function retrieve(question, k = 22) {
  const words = norm(question).split(' ').filter(w => w.length > 2 && !STOP.has(w));
  const uniq = [...new Set(words)];
  if (!uniq.length) return [];
  const df = uniq.map(w => ENTRIES.reduce((a, e) => a + (e.hay.includes(' ' + w) || e.meta.includes(' ' + w) ? 1 : 0), 0));
  const scored = [];
  for (const e of ENTRIES) {
    let sc = 0;
    uniq.forEach((w, i) => {
      if (!df[i]) return;
      const idf = Math.log(1 + ENTRIES.length / df[i]);
      const inBody = e.hay.includes(' ' + w), inMeta = e.meta.includes(' ' + w);
      if (inBody) sc += idf; if (inMeta) sc += idf * 1.5;
    });
    if (sc > 0) scored.push([sc / Math.sqrt(1 + e.hay.length / 2500), e]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  return scored.slice(0, k).map(x => x[1]);
}
function guideContext(question) {
  const words = new Set(norm(question).split(' ').filter(w => w.length > 3 && !STOP.has(w)));
  const score = t => { let n = 0; for (const w of norm(t).split(' ')) if (words.has(w)) n++; return n; };
  const ds = DISPUTED.map(d => [score(d.title + ' ' + d.question + ' ' + d.settled + ' ' + d.open), d]).filter(x => x[0] > 0).sort((a, b) => b[0] - a[0]).slice(0, 3).map(x => x[1]);
  const ss = SINCE.map(s => [score(s.title + ' ' + s.summary), s]).filter(x => x[0] > 0).sort((a, b) => b[0] - a[0]).slice(0, 4).map(x => x[1]);
  const ts = THREADS.map(t => [score(t.title + ' ' + t.summary), t]).filter(x => x[0] > 0).sort((a, b) => b[0] - a[0]).slice(0, 1).map(x => x[1]);
  return { ds, ss, ts };
}
function entryHeader(e) {
  const g = e.cur !== null && CURATED[e.cur] ? ` · checked by hand: ${GRADES[CURATED[e.cur].g][0]} (${CURATED[e.cur].n})` : '';
  const c = e.cens !== null && CENS[e.cens] ? ` · censured as ${CENS[e.cens].w.join(', ')}${CENS[e.cens].r ? ', respectively' : ''}` : '';
  return `[${nlab(e.id)}] ${e.era.name}${e.era.dates ? ' (' + e.era.dates + ')' : ''} · ${W(e.weight)[0]}${g}${c}${e.topic ? ' · ' + e.topic : ''}${e.src ? ' ' + e.src : ''}`;
}
const READING_RULES = `How to read condemned propositions and controversial bulls:
- A condemnation targets a proposition in a determinate doctrinal sense, not every meaning its words could bear. Establish that sense from the source the proposition was taken from, the wording of the condemnation (named senses such as "if thus understood"; censures), and authoritative explanations. Never supply an intention the evidence does not show, whether to accuse or to excuse.
- "Condemned" is not "declared heretical": with censures given respectively or in globo, each proposition deserves at least one of the listed censures, not necessarily the gravest.
- Rejecting a proposition in a sense does not affirm its unrestricted opposite.
- The same words can express different doctrines; agreement in vocabulary (for example Augustinian language on grace) can hide disagreement, and the reverse.
- A definition is what is proposed to be held, not the reasoning around it.
- If a text seems to contradict earlier teaching, treat it as a question to examine with these distinctions, not as a refutation; where a tension remains, say so plainly.`;
function buildPrompt(question, ents, ctx, mode) {
  const texts = ents.map(e => {
    const t = e.paras.join(' ');
    return `${entryHeader(e)}\n${t.length > 1400 ? t.slice(0, 1400) + ' …' : t}`;
  }).join('\n\n');
  const guides = [
    ...ctx.ss.map(s => `[${s.title}, ${s.date.slice(0, 4)}] ${LEVELS[s.level][0]}. ${s.summary} Continuity: ${s.continuity}`),
    ...ctx.ds.map(d => `[Disputed question: ${d.title}] Settled: ${d.settled} Open: ${d.open} Continuity reading: ${d.reading}`),
  ].join('\n\n');
  const intro = `The texts below come from an online edition of Denzinger's Sources of Catholic Dogma (older numbering, cited "n. 1234") and of the documents after 1958 (cited by document and article, such as "LG 25" or "EV 62"). Each text is labelled with the kind of document, and some with a grade checked by hand and the censure it received.`;
  const common = `- Use ONLY the texts below. If they do not settle the matter, say so plainly and say what is missing.
- Cite every claim by the number given in brackets, such as (n. 1839) or (LG 25).
- Distinguish defined dogma, definitive teaching, authoritative teaching, discipline, prudential judgment, and texts that are not magisterial (addresses, commission studies, interviews), using the labels given.
- Read later teaching in continuity with earlier binding texts. Where others see a break, say so briefly and fairly.

${READING_RULES}`;
  const task = mode === 'check'
    ? `Task: the reader is studying how a statement stands with the Church's teaching, for formation. Assess the statement, never a person: do not judge anyone's faith, standing or intention, and say that your assessment is not an act of the Church's authority.
1. Restate what the statement claims. Note any ambiguity and the different senses it could bear.
2. For each sense, say which texts bear on it, and whether that sense agrees with them, goes beyond them, or contradicts them. Give the weight of the teaching involved: contradicting a defined dogma is not the same as disagreeing with a prudential judgment.
3. If a relevant text is a condemned proposition, apply the reading rules: show the sense that was condemned before comparing.
4. End with one line: consonant with the texts; consonant in one sense and not in another; contrary to the teaching cited (name its weight); or not settled by these texts.
Write plain prose, at most about 450 words.

Statement: ${question}`
    : `Task: answer the question in plain prose in short paragraphs, at most about 350 words, without headings.

Question: ${question}`;
  return `${intro}

Rules:
${common}

${task}

Texts:
${texts || '(none found)'}

${guides ? 'Guide summaries (written for this site, not magisterial texts):\n' + guides : ''}`;
}
function mdLite(text) {
  const blocks = esc(text).split(/\n{2,}/);
  return blocks.map(b => {
    if (/^\s*[-*] /m.test(b)) return '<ul>' + b.split(/\n/).filter(l => l.trim()).map(l => `<li>${l.replace(/^\s*[-*]\s+/, '')}</li>`).join('') + '</ul>';
    return `<p>${b.replace(/\n/g, '<br>')}</p>`;
  }).join('').replace(/\*\*([^*]+)\*\*/g, '<b>$1</b>').replace(/\(n\.\s?(\d{1,4}[a-z]?)\)|\bn\.\s?(\d{1,4}[a-z]?)\b/g, (m, a, b) => {
    const num = a || b; const e = byId.get(num) || byBase.get(parseInt(num, 10));
    return e ? m.replace(num, `<a class="xref" href="#n${esc(e.id)}">${num}</a>`) : m;
  });
}
const EXAMPLES = ['What did the Church teach about baptism of desire before 1950?', 'How is the primacy of the Pope taught from the early centuries to Vatican I?', 'What does the Church teach about purgatory?', 'Did Unigenitus condemn Augustine on grace?'];
const CHECKS = ['Anyone who dies outside the visible Church is damned.', 'Grace is irresistible: when God moves the will, it cannot refuse.', 'Every pope who changed a discipline contradicted his predecessors.', 'Women could be ordained priests if the Church chose.'];
let askMode = 'ask';
function askSources(q) {
  const ctx = guideContext(q);
  const fromGuides = [];
  for (const d of ctx.ds) for (const r of d.refs) fromGuides.push(r);
  for (const t of ctx.ts) for (const st of t.steps) if (st.ref) fromGuides.push(st.ref);
  const seen = new Set(), ents = [];
  for (const e of [...fromGuides.map(r => byId.get(r)).filter(Boolean), ...retrieve(q)]) { if (!seen.has(e.id) && ents.length < 30) { seen.add(e.id); ents.push(e); } }
  return { ctx, ents };
}
function sourcesHtml(ents, ctx, who) {
  return `<h2 class="sect-h">Texts given to ${who}</h2><div class="numgrid">${ents.map(e => `<a href="#n${esc(e.id)}">${esc(nlab(e.id))}</a>`).join('')}${ctx.ss.map(s => `<a href="#since-${s.id}">${esc(s.title)}</a>`).join('')}${ctx.ds.map(d => `<a href="#q-${d.id}">${esc(d.title)}</a>`).join('')}</div>`;
}
function renderAsk() {
  view.className = 'col';
  const check = askMode === 'check';
  view.innerHTML = `<div class="eyebrow">Tool</div><h1 class="page-h">${check ? 'Check a statement' : 'Ask the collection'}</h1>
    <div class="chips" role="group" aria-label="Mode"><button class="chip" data-askmode="ask" aria-pressed="${!check}">Ask a question</button><button class="chip" data-askmode="check" aria-pressed="${check}">Check a statement</button></div>
    <p class="lede">${check
      ? 'For formation: write a statement, and an AI tests it against the most relevant texts in this collection. It distinguishes the senses the statement could bear, weighs the teaching each sense meets, and reads condemned propositions in the sense they were condemned (<a href="#reading">how</a>). It assesses statements, never persons, and is not a judgment of the Church.'
      : 'Ask a question, and an AI answers from the most relevant entries in this collection, citing each by number, and reading later teaching in continuity with earlier binding texts.'} Answers are written by AI; check every claim against the entries it cites.</p>
    <div class="askbox"><textarea id="askQ" aria-label="${check ? 'Statement to check' : 'Your question'}" placeholder="${check ? 'Write a statement to test, for example a claim about grace, the Church or a condemned proposition…' : 'Ask about a doctrine, a council, a condemned proposition…'}">${esc(askLast && askLast.mode === askMode ? askLast.q : '')}</textarea>
      <div class="row">${Sample ? `<button class="btn primary" id="askGo">${check ? 'Check' : 'Ask'}</button><button class="btn" id="askStop" hidden>Stop</button>` : ''}<button class="btn${Sample ? '' : ' primary'}" id="askCopy">Copy prompt for any AI</button><span class="count" id="askNote"></span></div></div>
    <div class="examples" style="margin-top:.8rem">${(check ? CHECKS : EXAMPLES).map(x => `<button class="chip" data-example="${esc(x)}">${esc(x)}</button>`).join('')}</div>
    ${Sample ? '' : `<p style="font-size:.9rem;color:var(--muted)">Opened in Claude, this page answers here. Anywhere else, "Copy prompt for any AI" copies the instructions, the reading rules and the selected texts, so you can paste them into the AI client you use. The data is also published for programs: <a class="xref" href="${esc((SITE.url || '') + 'llms.txt')}">llms.txt</a>.</p>`}
    <div id="askOut">${askLast && askLast.mode === askMode && askLast.html ? askLast.html : ''}</div>`;
  view.querySelectorAll('[data-askmode]').forEach(b => b.onclick = () => { askMode = b.dataset.askmode; renderAsk(); });
  if (Sample) { $('askGo').onclick = runAsk; $('askStop').onclick = () => { if (askCtl) askCtl.abort(); }; }
  $('askCopy').onclick = copyAskPrompt;
  window.scrollTo(0, 0);
}
async function copyAskPrompt() {
  const q = $('askQ').value.trim();
  if (!q) { $('askQ').focus(); return; }
  const { ctx, ents } = askSources(q);
  $('askOut').innerHTML = sourcesHtml(ents, ctx, 'the prompt');
  try { await navigator.clipboard.writeText(buildPrompt(q, ents, ctx, askMode)); $('askNote').textContent = `Copied, with ${ents.length} texts. Paste it into your AI client.`; }
  catch (err) { $('askNote').textContent = 'Copying was blocked by the browser.'; }
}
async function runAsk() {
  const q = $('askQ').value.trim();
  if (!q) { $('askQ').focus(); return; }
  if (!Sample) { $('askNote').textContent = 'Answering here needs this page opened in Claude; copy the prompt instead.'; return; }
  const { ctx, ents } = askSources(q);
  const mode = askMode;
  const srcHtml = sourcesHtml(ents, ctx, 'Claude');
  const out = $('askOut');
  out.innerHTML = `<div class="answer"><div class="aiflag">Answer written by Claude from the texts listed below</div><div id="askText"><p class="status">Thinking…</p></div></div>${srcHtml}`;
  $('askGo').disabled = true; $('askStop').hidden = false; $('askNote').textContent = '';
  askCtl = new AbortController();
  const setText = t => { const el = $('askText'); if (el) el.innerHTML = mdLite(t); };
  try {
    const { text, truncated } = await Sample(buildPrompt(q, ents, ctx, mode), { signal: askCtl.signal, onText: ({ text }) => setText(text) });
    setText(text);
    if (truncated) $('askNote').textContent = 'The answer was cut short. Try a narrower question.';
  } catch (err) {
    const code = err && err.code;
    if (err && err.text) setText(err.text); else if (code !== 'cancelled') { const el = $('askText'); if (el) el.innerHTML = ''; }
    const msg = { not_granted: 'Asking was not allowed for this page.', sampling_disabled: 'Claude isn\'t available for this account.', rate_limited: 'Too many questions at once. Try again in a little while.', session_expired: 'Sign in to Claude again, then retry.', refused: 'Claude declined this question. Try rephrasing it.', prompt_too_large: 'The question pulled in too much text. Try a narrower question.' }[code];
    if (code !== 'cancelled') $('askNote').textContent = msg || 'Something went wrong. Try again.';
  } finally {
    $('askGo').disabled = false; $('askStop').hidden = true;
    askLast = { q, mode, html: $('askOut') ? $('askOut').innerHTML : '' };
  }
}

/* ---------- feature check ---------- */
const sysResult = {};
function sysRows() {
  const has = !!(window.claude && typeof window.claude.use === 'function');
  const row = (name, ok, text, btn) => `<div><b>${name}</b><span><span class="${ok ? 'ok' : 'no'}">${ok ? 'Working' : 'Not available'}</span> · ${text}${sysResult[name] ? ` <br><small>${esc(sysResult[name])}</small>` : ''}</span>${btn || '<span></span>'}</div>`;
  return [
    row('Notes and saved', Marks.mode === 'cloud', Marks.mode === 'cloud' ? 'kept with your account and synced across devices' : (has ? 'kept in this browser only' : 'kept in this browser only; open the page in Claude to sync'), Marks.mode === 'cloud' ? '<button class="btn small" data-sys="notes">Test sync</button>' : ''),
    row('Ask', !!Sample, Sample ? 'answers use your Claude usage and ask permission the first time' : 'needs this page opened in Claude', ''),
    row('Downloads', !!Downloads, Downloads ? 'study packets download as files after you confirm' : 'packets are shown as text to copy instead', Downloads ? '<button class="btn small" data-sys="dl">Test download</button>' : ''),
    row('Reviews', Reviews.ready && Reviews.canWrite !== false, Reviews.ready ? (Reviews.canWrite === false ? 'you can read reviews but not add them' : 'you can mark items reviewed and comment') : (Reviews.failed || !has ? 'need this page opened in Claude' : 'loading'), ''),
  ].join('');
}
async function runSysCheck(which) {
  if (which === 'notes') {
    sysResult['Notes and saved'] = 'Testing…'; $('sysPanel').innerHTML = sysRows();
    try {
      const ref = Marks.col.doc('_sync-test');
      const stamp = Date.now();
      await ref.set({ b: false, note: 'sync test', t: stamp });
      const back = await ref.get();
      const val = back.exists ? back.data() : null;
      await ref.delete();
      sysResult['Notes and saved'] = val && val.t === stamp ? `Wrote, read back and removed a test note at ${new Date().toLocaleTimeString()}. Open this page on another device to see your notes there.` : 'The test note did not read back. Notes are kept in this browser.';
    } catch (err) { sysResult['Notes and saved'] = 'Your account refused the test write, so notes are kept in this browser only.'; Marks.mode = 'local'; }
  }
  if (which === 'dl') {
    try { await Downloads.save({ filename: 'denzinger-download-test.txt', data: 'This file confirms that downloads work from the Sources of Catholic Dogma reader.\n' }); sysResult['Downloads'] = 'Download accepted.'; }
    catch (err) { sysResult['Downloads'] = err && err.code === 'declined' ? 'You declined the test download.' : 'The download did not go through (' + (err && err.code || 'unknown') + ').'; }
  }
  const p = $('sysPanel'); if (p) p.innerHTML = sysRows();
}

/* ---------- about this edition ---------- */
function renderEdition() {
  view.className = 'col';
  const q = QUALITY;
  const nlink = n => { const e = byBase.get(n); return e ? `<a href="#n${esc(e.id)}">${n}</a>` : `<span>${n}</span>`; };
  const nb = n => { const prev = [...Array(5)].map((_, i) => byBase.get(n - 1 - i)).find(Boolean); return prev ? `<a href="#n${esc(prev.id)}" title="Nearest entry before">${n}</a>` : `<span>${n}</span>`; };
  view.innerHTML = `<div class="eyebrow">Notes</div><h1 class="page-h">About this edition</h1>
    <p class="lede">What this text is, how it was prepared, and what has and has not been checked.</p>
    ${PAGES ? `<h2 class="sect-h">This site</h2>
    <p>A static site with no accounts: nothing you save or write here leaves your browser. Saved entries and notes are kept in this browser only; use Saved and notes to download them as a study packet.${SITE.repo ? ` The source, the data files and the build scripts are on <a class="xref" href="https://github.com/${esc(SITE.repo)}" target="_blank" rel="noopener">GitHub</a>.` : ''}</p>
    <h2 class="sect-h">Corrections</h2>
    <p>Every Since 1950 item, disputed question, thread and hand-checked weight has a "Suggest a correction" link that opens an issue on GitHub with the item filled in.${SITE.repo ? ` You can also <a class="xref" href="https://github.com/${esc(SITE.repo)}/issues" target="_blank" rel="noopener">see the open issues</a>.` : ''}</p>` : `<h2 class="sect-h">Account features on this page</h2>
    <p style="font-size:.95rem;color:var(--muted)">These features use your Claude account. This panel shows whether each one is working for you right now.</p>
    <div class="sys" id="sysPanel">${sysRows()}</div>
    <h2 class="sect-h">Review progress</h2>
    <p style="font-size:.95rem;color:var(--muted)">Every Since 1950 item, disputed question, thread and hand-checked weight can be marked reviewed or flagged for correction, with comments. Reviews are shared with everyone who can open this page.</p>
    <div id="rvProgress">${reviewProgress()}</div>`}
    ${SITE.url ? `<h2 class="sect-h">Open data</h2>
    <p>Everything on this site can be downloaded as data, rebuilt with each change${SITE.built ? ` (last built ${esc(SITE.built)})` : ''}:</p>
    <div class="tips" style="font-size:.95rem">
      <div><a class="xref" href="${esc(SITE.url)}data/entries.json">entries.json</a> · every entry with its text, DS numbers, year, weight, grade, censure, cross-references and Roman Catechism chapters</div>
      <div><a class="xref" href="${esc(SITE.url)}data/crosswalk.csv">crosswalk.csv</a> · old and DS numbers, with how each pair was matched</div>
      <div><a class="xref" href="${esc(SITE.url)}data/weights.csv">weights.csv</a> · the hand-checked weight ranges and their notes</div>
      <div><a class="xref" href="${esc(SITE.url)}data/latin.json">latin.json</a> · the Latin text by DS number, not proofread</div>
      <div><a class="xref" href="${esc(SITE.url)}data/roman-catechism.json">roman-catechism.json</a> and <a class="xref" href="${esc(SITE.url)}data/guides.json">guides.json</a> · the Roman Catechism map and the guides</div>
    </div>
    <p style="font-size:.95rem;color:var(--muted)">The English translation's copyright status is uncertain; the data files carry the same text as the site.</p>` : ''}
    <h2 class="sect-h">The text</h2>
    <p>The English translation of Denzinger's Enchiridion with the older numbering (before the 32nd edition of 1963), as published on patristica.net and archived from catecheticsonline.com. It covers ${fmt(ENTRIES.length)} entries from the creeds to Pius XII, with an appendix numbered from 5000.</p>
    <h2 class="sect-h">Supplement</h2>
    <p>${ENTRIES.filter(e => e.sup).length} entries were added for decrees of Constance and Basel that the collection leaves out. Haec Sancta is translated for this site from the Latin; the others are summaries written for this site, with links to full texts. Each carries a hand-checked grade explaining its standing.</p>
    <h2 class="sect-h">Numbers not found</h2>
    <p>${(q.missing || []).length} numbers in the main sequence have no entry of their own. Some are gaps in the printed edition, where one entry covers several numbers; others may have been merged with a neighbor when the text was scanned. Each link opens the nearest entry before it.</p>
    <div class="numgrid">${(q.missing || []).map(nb).join('')}</div>
    <h2 class="sect-h">Numbers printed twice</h2>
    <p>These numbers appear twice, usually because the edition gives two versions of the same text (for example a Latin and a Greek version of a canon). Both are kept; the second is linked as the same number.</p>
    <div class="numgrid">${(q.dups || []).map(n => nlink(parseInt(n, 10))).join('')}</div>
    <h2 class="sect-h">Greek passages left out</h2>
    <p>The source marks ${(q.greek || []).length} places where Greek text was deleted. The Latin page of the same site leaves the Greek out as well, so these gaps remain; the Latin version is shown where the edition prints one.</p>
    <div class="numgrid">${(q.greek || []).map(id => `<a href="#n${esc(id)}">${esc(dispId(id))}</a>`).join('')}</div>
    <h2 class="sect-h">Corrections</h2>
    <p>${fmt(q.fixes || 0)} scanning errors were corrected automatically and conservatively (words split or run together, broken hyphenation). Examples: ${(q.fixSamples || []).slice(0, 6).map(esc).join('; ')}. Spelling, archaic forms and the translator's bracketed insertions are left as printed.</p>
    <p>Two errors in the source's headings were corrected by hand: entries 899–929 (Trent on penance and extreme unction) were labeled Session XIII and belong to Session XIV of 25 November 1551; and the heading for Julius III, printed twice, is shown once.</p>
    <h2 class="sect-h">Labels and indexes</h2>
    <p>Kinds of text, censure grades and Scripture references are detected by rules from the wording and structure of each entry. Weights were first assigned the same way, then checked by hand: ${(() => { const n = ENTRIES.filter(e => !e.sup && e.cur !== null).length, t = ENTRIES.filter(e => !e.sup).length; return `${fmt(n)} of ${fmt(t)} entries (${Math.round(100 * n / t)}%) now carry a grade set by hand, range by range (${fmt(CURATED.length)} ranges, each with a short note on why)${n < t ? '; the rule-based label remains elsewhere' : ''}`; })()}. A grade covers a whole range, so a single entry inside it can deserve a finer note; flag one in the review panel if so. They are a reading aid, not an official classification.</p>
    <h2 class="sect-h">Cross-references and dates</h2>
    <p>"Cited by" lists the entries whose text points to an entry by number (${fmt(ENTRIES.filter(e => e.citedBy.length).length)} entries are cited this way). Dates on the timeline and in <code>year:</code> searches come from the heading of each text where it prints a year (${fmt(ENTRIES.filter(e => e.yearExact).length)} entries), and otherwise from the first year of the pontificate or council. The Roman Catechism chapters are matched to entries by topic for this site.</p>
    <h2 class="sect-h">What was checked in the guides</h2>
    <div class="tips" style="font-size:.95rem">
      <div>Every Denzinger number cited in the doctrinal threads, Since 1950 and the disputed questions was checked against the text of this collection, and several notes were corrected against it.</div>
      <div>Every official-text link in Since 1950 was opened and its title and date confirmed on 13 October 2026. For five items (Donum Veritatis, the Rosmini note, the 1998 commentary, the 1974 declaration and the 2025 diaconate report) the summary was also checked against the text. The other summaries are condensed readings that have not been re-checked line by line.</div>
      <div>The guides follow the hermeneutic of continuity, and say where others see a break. Use the official texts before citing.</div>
    </div>
    <h2 class="sect-h">Old and new numbering</h2>
    <p>Every entry shows its Denzinger-Schönmetzer (DS) number where one could be found, read from the Latin page of the same site, which prints both numbers. ${(() => { const st = cwStats(); return `${fmt(st.exact)} pairs are printed there; ${st.series} are inferred from the neighboring entries and marked as inferred; ${st.checked} were matched by hand; ${fmt(st.none)} entries have no number on that page.`; })()} The Latin text shown under entries is that page's text, unchecked. <a class="xref" href="#concordance">Open the table</a>.</p>
    <h2 class="sect-h">Migne references</h2>
    <p>Citations of Migne's Patrologia (MG and ML) link to the volume on patristica.net's Greek and Latin indexes. The Greek index's volume addresses were confirmed; the Latin ones follow the same pattern but were not checked.</p>`;
  window.scrollTo(0, 0);
}


/* ---------- concordance ---------- */
const CW = { f: '', sort: 'old' };
function cwStats() {
  const main = ENTRIES.filter(e => !e.sup);
  return { total: main.length, exact: main.filter(e => e.ds.length && !e.dsHow).length, series: main.filter(e => e.dsHow === 'series').length, checked: main.filter(e => e.dsHow === 'checked').length, none: main.filter(e => !e.ds.length).length, notes: main.filter(e => !e.ds.length && e.weight === 'note').length };
}
function cwRow(e, d) {
  const h = DS_HOW[e.dsHow];
  return `<a class="cwr${e.ds.length ? '' : ' no'}" href="#n${esc(e.id)}"><span class="o">${esc(dispId(e.id))}</span><span class="d">${e.ds.length ? esc(d !== undefined ? d : dsRange(e.ds)) : '—'}</span><span class="t">${h ? `<em>${h[0]}</em> · ` : ''}${esc((e.topic || e.src || e.paras[0] || '').replace(/\s+/g, ' ').slice(0, 90))}</span></a>`;
}
function cwLookup(q) {
  q = q.trim(); if (!q) return '';
  const d = dsQuery(q) ?? (/^\d{1,4}$/.test(q) && +q > 2400 && +q < 5000 ? +q : null);
  if (d !== null) {
    const hits = byDS.get(d) || [];
    if (hits.length) return `DS ${d} = ${hits.map(e => `<a class="xref" href="#n${esc(e.id)}"><b>${esc(nlab(e.id))}</b></a>${e.dsHow ? ` (${DS_HOW[e.dsHow][0]})` : ''}`).join(', ')} in the older numbering.`;
    const nb = dsNearest(d);
    return `DS ${d} has no counterpart in this collection; it is a text the 1963 edition added, or one this translation leaves out.${nb.length ? ` Nearest: ${nb.map(nbLink).join('; ')}.` : ''}`;
  }
  const e = numberQuery(q);
  if (!e) return 'Not a number in this collection. Type an old number (1839) or a new one after DS (DS 3074).';
  if (e.sup) return `<a class="xref" href="#n${esc(e.id)}">${esc(nlab(e.id))}</a> is a supplement entry and has no Denzinger number.`;
  if (!e.ds.length) { const nb = dsNeighbors(e); return `<a class="xref" href="#n${esc(e.id)}"><b>${esc(nlab(e.id))}</b></a> has no number on the Latin page.${nb.length ? ` Nearest: ${nb.map(nbLink).join('; ')}.` : ''}`; }
  return `<a class="xref" href="#n${esc(e.id)}"><b>${esc(nlab(e.id))}</b></a> = <b>${esc(dsText(e))}</b>${e.dsHow ? ` (${DS_HOW[e.dsHow][0]})` : ''}.`;
}
function cwTable() {
  const keep = e => !e.sup && (!CW.f || (CW.f === 'none' ? !e.ds.length : e.dsHow === CW.f));
  let html = '';
  if (CW.sort === 'ds') {
    const rows = [];
    for (const e of ENTRIES) if (keep(e)) for (const d of e.ds) rows.push([+d, e, d]);
    rows.sort((a, b) => a[0] - b[0] || a[1].k - b[1].k);
    let band = -1;
    for (const [v, e, d] of rows) {
      const b = Math.floor(v / 500);
      if (b !== band) { html += `<div class="cwh">DS ${b * 500 || 1}–${b * 500 + 499}</div>`; band = b; }
      html += cwRow(e, d);
    }
  } else {
    let er = null;
    for (const e of ENTRIES) {
      if (!keep(e)) continue;
      if (e.era !== er) { er = e.era; html += `<div class="cwh">${esc(er.name)}${er.dates ? ` <span>${esc(er.dates)}</span>` : ''}</div>`; }
      html += cwRow(e);
    }
  }
  return html || '<p class="empty">Nothing to show.</p>';
}
function renderConcordance() {
  view.className = 'col';
  const st = cwStats();
  const chip = (f, label, n) => `<button class="chip" data-cwf="${f}" aria-pressed="${CW.f === f}">${label}<span>${fmt(n)}</span></button>`;
  view.innerHTML = `<div class="eyebrow">Index</div><h1 class="page-h">Old and new numbers</h1>
    <p class="lede">This site uses the older Denzinger numbers, from before the 32nd edition of 1963. Most books now cite the numbers of Denzinger-Schönmetzer (DS), which Denzinger-Hünermann (DH) keeps for the same texts. Each entry below is paired with its DS number, and the Latin text can be shown under any entry.</p>
    <form class="cmpbar" id="cwForm"><input id="cwQ" aria-label="Look up a number" placeholder="1839, or DS 3074"><button class="btn small primary" type="submit">Look up</button></form>
    <div class="jump" id="cwOut" hidden></div>
    <div class="tips" style="font-size:.92rem">
      <div><b>${fmt(st.exact)}</b> of ${fmt(st.total)} entries are paired exactly as the Latin page of patristica.net prints them.</div>
      <div><b>${fmt(st.series)}</b> are inferred: the Latin page gives the text without the old number, so the pair follows from the entries on either side. <b>${st.checked}</b> were matched by hand where the page is confusing.</div>
      <div><b>${fmt(st.none)}</b> have no number on the Latin page${st.notes ? `, ${st.notes} of them editorial notes` : ''}. The page leaves some texts out, and gives no Greek. Each such entry shows its nearest numbered neighbors.</div>
      <div>Numbers DS added in 1963, mostly texts this translation does not contain, have no counterpart here.</div>
    </div>
    <h2 class="sect-h">The table</h2>
    <div class="chips" style="margin-bottom:.6rem">${chip('', 'All', st.total)}${chip('series', 'Inferred', st.series)}${chip('checked', 'Matched by hand', st.checked)}${chip('none', 'No DS number', st.none)}</div>
    <div class="chips" style="margin-bottom:1rem"><button class="chip" data-cws="old" aria-pressed="${CW.sort === 'old'}">In the order of this collection</button><button class="chip" data-cws="ds" aria-pressed="${CW.sort === 'ds'}">In DS order</button></div>
    <div class="cwt"><div class="cwr hd"><span class="o">Old</span><span class="d">DS</span><span class="t">Topic</span></div><div id="cwBody">${cwTable()}</div></div>`;
  $('cwForm').onsubmit = ev => { ev.preventDefault(); const o = $('cwOut'); o.innerHTML = cwLookup($('cwQ').value); o.hidden = !o.innerHTML; };
  window.scrollTo(0, 0);
}

/* ---------- routing ---------- */
function go(hash) { if (location.hash === hash) route(); else location.hash = hash; }
function setView(v) {
  state.view = v;
  $('savedBtn').setAttribute('aria-pressed', v === 'saved');
}
function route() {
  const h = decodeURIComponent(location.hash.slice(1));
  let m;
  Marks.editing = null; Cite.open = null;
  if ((m = h.match(/^n(.+)$/)) && byId.has(m[1])) {
    const e = byId.get(m[1]); state.era = e.era; setView('read'); renderEra(e.era, e.id);
  } else if ((m = h.match(/^e(\d+)$/)) && ERAS[+m[1]]) {
    state.era = ERAS[+m[1]]; setView('read'); renderEra(state.era, null);
  } else if (h === 'since' || h.startsWith('since-')) {
    setView('since'); highlightTerms = []; renderSince(h.startsWith('since-') ? h.slice(6) : null);
  } else if (h === 'disputed' || h.startsWith('q-')) {
    setView('disputed'); highlightTerms = []; if (h.startsWith('q-')) state.dispCat = ''; renderDisputed(h.startsWith('q-') ? h.slice(2) : null);
  } else if (h === 'threads') {
    setView('threads'); highlightTerms = []; renderThreads();
  } else if ((m = h.match(/^thread-([a-z-]+)$/)) && THREADS.find(t => t.id === m[1])) {
    setView('thread'); highlightTerms = []; renderThread(THREADS.find(t => t.id === m[1]));
  } else if (h === 'weights') {
    setView('weights'); renderWeights();
  } else if ((m = h.match(/^weight-([a-z-]+)$/)) && WEIGHTS[m[1]]) {
    state.weight = m[1]; state.kind = ''; state.query = ''; state.topic = null; state.limit = 60; qInput.value = '';
    setView('search'); renderResults(); window.scrollTo(0, 0);
  } else if (h === 'reading') {
    setView('reading'); highlightTerms = []; renderReading();
  } else if (h === 'ask') {
    setView('ask'); highlightTerms = []; renderAsk();
  } else if (h === 'compare' || h.startsWith('cmp-')) {
    setView('compare'); highlightTerms = [];
    const parts = h.startsWith('cmp-') ? h.slice(4).split('~').map(decId) : [state.cmpA, null];
    renderCompare(parts[0] || null, parts[1] || null);
  } else if (h === 'edition') {
    setView('edition'); renderEdition();
  } else if (h === 'concordance') {
    setView('concordance'); highlightTerms = []; renderConcordance();
  } else if (h === 'scripture') {
    setView('scripture'); renderScripture();
  } else if ((m = h.match(/^book-(\d+)$/)) && BOOKS[+m[1]]) {
    setView('book'); renderBook(BOOKS[+m[1]]);
  } else if (h === 'topics') {
    state.topic = null; setView('topics'); highlightTerms = []; renderTopics(''); window.scrollTo(0, 0);
  } else if (h === 'saved') {
    setView('saved'); highlightTerms = []; renderSaved(); window.scrollTo(0, 0);
  } else if ((m = h.match(/^kind-([a-z]+)$/)) && KIND_LABEL[m[1]]) {
    state.weight = '';
    state.kind = m[1]; state.query = ''; state.topic = null; state.limit = 60; qInput.value = '';
    setView('search'); renderResults(); window.scrollTo(0, 0);
  } else if (h === 'catechism' || h.startsWith('rc-')) {
    setView('catechism'); highlightTerms = []; renderCatechism(h.startsWith('rc-') ? h.slice(3) : null);
  } else if (h === 'timeline') {
    setView('timeline'); highlightTerms = []; renderTimeline();
  } else if (h === 'results' && (state.query.trim() || state.topic || state.kind || state.weight)) {
    setView('search'); renderResults(); window.scrollTo(0, 0);
  } else {
    setView('home'); state.era = null; highlightTerms = []; renderHome(); window.scrollTo(0, 0);
  }
  markRail();
}

let tmr = null;
qInput.addEventListener('input', () => {
  clearTimeout(tmr);
  tmr = setTimeout(() => {
    state.query = qInput.value; state.topic = null; state.limit = 60;
    if (!state.query.trim()) { highlightTerms = []; if (state.view === 'search' && !state.kind && !state.weight) go('#home'); else if (state.view === 'search') route(); return; }
    if (location.hash !== '#results') location.hash = '#results'; else route();
  }, 140);
});
qInput.addEventListener('keydown', ev => {
  if (ev.key === 'Enter') {
    const e = numberQuery(qInput.value);
    if (e) { ev.preventDefault(); clearTimeout(tmr); qInput.blur(); go('#n' + e.id); }
  } else if (ev.key === 'Escape') {
    qInput.value = ''; state.query = ''; state.kind = ''; state.weight = ''; highlightTerms = []; qInput.blur();
    if (state.view === 'search') go('#home');
  }
});
document.addEventListener('keydown', ev => {
  if (ev.key === '/' && document.activeElement !== qInput && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
    ev.preventDefault(); qInput.focus(); qInput.select();
  }
});

async function copy(text, okMsg, fallbackEl) {
  try { await navigator.clipboard.writeText(text); toast(okMsg); }
  catch (_) {
    if (fallbackEl) {
      const sel = window.getSelection(), r = document.createRange();
      r.selectNodeContents(fallbackEl); sel.removeAllRanges(); sel.addRange(r);
      toast('Selected. Press Ctrl+C to copy');
    } else toast(text);
  }
}
view.addEventListener('click', async ev => {
  const t = ev.target;
  let el;
  if ((el = t.closest('[data-period]'))) { state.period = +el.dataset.period; state.limit = 60; renderResults(); return; }
  if ((el = t.closest('[data-kind]'))) { state.kind = el.dataset.kind; state.limit = 60; if (!state.query.trim() && !state.kind) { go('#home'); return; } renderResults(); return; }
  if ((el = t.closest('[data-rv-open]'))) { const k = el.dataset.rvOpen; const prev = Reviews.editing; Reviews.editing = k; if (prev && prev !== k) { const pe = document.querySelector(`[data-review-key="${CSS.escape(prev)}"]`); if (pe) pe.innerHTML = reviewInner(prev); } const box = el.closest('[data-review-key]'); box.innerHTML = reviewInner(k); const ta = $('rvText'); if (ta) ta.focus(); return; }
  if ((el = t.closest('[data-rv-cancel]'))) { const k = Reviews.editing; Reviews.editing = null; const box = el.closest('[data-review-key]'); if (box && k) box.innerHTML = reviewInner(k); return; }
  if ((el = t.closest('[data-rv-more]'))) { Reviews.open.add(el.dataset.rvMore); el.closest('[data-review-key]').innerHTML = reviewInner(el.dataset.rvMore); return; }
  if ((el = t.closest('[data-rv-save]'))) {
    const k = el.dataset.rvSave, box = el.closest('[data-review-key]');
    const st = (box.querySelector('input[name="rvst"]:checked') || {}).value || 'reviewed';
    const txt = ($('rvText') || {}).value || '';
    el.disabled = true;
    try { await Reviews.save(k, st, txt.trim()); Reviews.editing = null; toast(st === 'correction' ? 'Flagged for correction' : 'Marked as reviewed'); }
    catch (err) { el.disabled = false; Reviews.canWrite = false; toast('You can read reviews here but not add them.'); }
    box.innerHTML = reviewInner(k);
    return;
  }
  if ((el = t.closest('[data-sys]'))) { runSysCheck(el.dataset.sys); return; }
  if ((el = t.closest('[data-example]'))) { $('askQ').value = el.dataset.example; runAsk(); return; }
  if ((el = t.closest('[data-dl-thread]'))) { const th = THREADS.find(x => x.id === el.dataset.dlThread); offerFile(`${th.title.replace(/[^A-Za-z0-9]+/g, '-').replace(/-+$/, '')}-thread.md`, threadPacket(th)); return; }
  if ((el = t.closest('[data-dl-saved]'))) { offerFile('denzinger-study-packet.md', savedPacket()); return; }
  if ((el = t.closest('[data-latin]'))) {
    const id = el.dataset.latin;
    if (Latin.flip.has(id)) Latin.flip.delete(id); else Latin.flip.add(id);
    refreshEntry(id); return;
  }
  if ((el = t.closest('[data-cwf],[data-cws]'))) {
    if (el.dataset.cwf !== undefined) CW.f = el.dataset.cwf; else CW.sort = el.dataset.cws;
    const y = window.scrollY; renderConcordance(); window.scrollTo(0, y); return;
  }
  if ((el = t.closest('[data-latin-mode]'))) {
    const anchor = [...document.querySelectorAll('.entry')].find(x => x.getBoundingClientRect().bottom > 80);
    setLatinMode(el.dataset.latinMode);
    if (state.view === 'read' && state.era) {
      renderEra(state.era, null);
      if (anchor) { const n = document.getElementById(anchor.id); if (n) { n.scrollIntoView({ block: 'start' }); window.scrollBy(0, -(document.querySelector('.top').offsetHeight + 12)); } }
    }
    markRail();
    toast({ off: 'Latin hidden', under: 'Latin shown below each entry', side: 'Latin shown side by side' }[Latin.mode]); return;
  }
  if ((el = t.closest('[data-print]'))) { window.print(); return; }
  if ((el = t.closest('[data-citep]'))) { const id = el.dataset.citep; const prev = Cite.open; Cite.open = prev === id ? null : id; if (prev && prev !== id) refreshEntry(prev); refreshEntry(id); return; }
  if ((el = t.closest('[data-copycite]'))) { const span = el.parentElement.querySelector('.cpt'); copyRich(span.innerHTML, 'Citation copied', span); return; }
  if ((el = t.closest('[data-latin-all]'))) {
    setLatinAll(!Latin.all);
    if (state.view === 'compare') route();
    else if (state.view === 'read') { document.querySelectorAll('.entry').forEach(x => refreshEntry(x.id.slice(1))); el.setAttribute('aria-pressed', Latin.all); el.textContent = Latin.all ? 'Hide Latin' : 'Show Latin'; }
    toast(Latin.all ? 'Latin shown under each entry' : 'Latin hidden'); return;
  }
  if ((el = t.closest('[data-cmp]'))) {
    const id = el.dataset.cmp;
    if (!state.cmpA || state.cmpA === id) { state.cmpA = state.cmpA === id ? null : id; refreshEntry(id); toast(state.cmpA ? `Picked ${nlab(id)}. Choose Compare on a second entry.` : 'Compare cleared'); return; }
    const a = state.cmpA; state.cmpA = null; go(`#cmp-${encId(a)}~${encId(id)}`); return;
  }
  if ((el = t.closest('[data-level]'))) { state.sinceLevel = el.dataset.level; renderSince(null); return; }
  if ((el = t.closest('[data-cat]'))) { state.dispCat = el.dataset.cat; renderDisputed(null); return; }
  if ((el = t.closest('[data-topic]'))) { state.topic = el.dataset.topic; state.query = ''; state.kind = ''; qInput.value = ''; highlightTerms = []; go('#results'); return; }
  if ((el = t.closest('[data-go]'))) { go(el.dataset.go); return; }
  if ((el = t.closest('[data-save]'))) { const id = el.dataset.save; const m = Marks.get(id); await Marks.set(id, { b: !(m && m.b) }); refreshEntry(id); toast(m && m.b ? 'Removed from saved' : 'Saved'); return; }
  if ((el = t.closest('[data-note]'))) { const id = el.dataset.note; Marks.editing = id; refreshEntry(id); return; }
  if ((el = t.closest('[data-note-cancel]'))) { const id = Marks.editing; Marks.editing = null; if (id) refreshEntry(id); return; }
  if ((el = t.closest('[data-note-save]'))) { const id = el.dataset.noteSave; const txt = ($('noteText') || {}).value || ''; Marks.editing = null; await Marks.set(id, { note: txt.trim() }); refreshEntry(id); toast(txt.trim() ? 'Note saved' : 'Note removed'); return; }
  if ((el = t.closest('[data-note-del]'))) { const id = el.dataset.noteDel; Marks.editing = null; await Marks.set(id, { note: '' }); refreshEntry(id); toast('Note deleted'); return; }
  if ((el = t.closest('[data-link]'))) { const e = byId.get(el.dataset.link); copy(pageUrl(e), 'Link copied'); return; }
  if ((el = t.closest('[data-cite],[data-copy]'))) {
    const e = byId.get(el.dataset.cite || el.dataset.copy);
    const text = el.dataset.cite ? citation(e) : `${e.paras.join('\n\n')}\n\n— ${citation(e)}`;
    copy(text, el.dataset.cite ? 'Citation copied' : 'Text copied', el.closest('.entry').querySelector('.body'));
  }
});
view.addEventListener('change', ev => {
  if (ev.target.id === 'wsel') { state.weight = ev.target.value; state.limit = 60; if (!state.query.trim() && !state.weight && !state.kind) { go('#home'); return; } renderResults(); }
});
$('savedBtn').onclick = () => { closeNav(); go('#saved'); };
$('brand').onclick = ev => { ev.preventDefault(); qInput.value = ''; state.query = ''; state.kind = ''; closeNav(); go('#home'); };

function openNav() { document.body.classList.add('nav-open'); $('menuBtn').setAttribute('aria-expanded', 'true'); }
function closeNav() { document.body.classList.remove('nav-open'); $('menuBtn').setAttribute('aria-expanded', 'false'); }
$('menuBtn').onclick = () => document.body.classList.contains('nav-open') ? closeNav() : openNav();
$('scrim').onclick = closeNav;

let toastT = null;
function toast(msg) { const el = $('toast'); el.textContent = msg; el.hidden = false; clearTimeout(toastT); toastT = setTimeout(() => { el.hidden = true; }, 2000); }

window.addEventListener('hashchange', route);
buildRail();
Marks.loadLocal();
updateSavedCount();
try {
  const sp = new URLSearchParams(location.search);
  const q0 = sp.get('q');
  if (q0 && q0.trim()) {
    history.replaceState(null, '', location.pathname + '#results');
    qInput.value = q0; state.query = q0;
    const e0 = numberQuery(q0); if (e0) history.replaceState(null, '', location.pathname + '#n' + e0.id);
  }
} catch (_) {}
route();
if (PAGES && 'serviceWorker' in navigator && location.protocol === 'https:') {
  window.addEventListener('load', () => navigator.serviceWorker.register('sw.js').catch(() => {}));
}
(async () => {
  try {
    if (!window.claude || typeof window.claude.use !== 'function') return;
    const [db, user, smp, dl] = await Promise.all(['db', 'user', 'sample', 'downloads'].map(n => window.claude.use(n).catch(() => null)));
    Sample = smp; Downloads = dl;
    if (db) { Marks.init(db, user); Reviews.init(db, user); } else { Reviews.failed = true; refreshReviews(); }
    if (state.view === 'edition') renderEdition();
    if (state.view === 'ask' && $('askNote')) $('askNote').textContent = Sample ? '' : 'Asking isn\'t available in this view.';
  } catch (_) {}
})();
})();
