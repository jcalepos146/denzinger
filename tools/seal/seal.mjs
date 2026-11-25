#!/usr/bin/env node
// Seal, open or check the encrypted research (see "Sealed research" in the README).
//
//   node tools/seal/seal.mjs seal          private/ -> src/data/sealed.json (asks for the password twice)
//   node tools/seal/seal.mjs open [--force] src/data/sealed.json -> private/ (on a new machine)
//   node tools/seal/seal.mjs check         does the password open the file, and does it match private/?
//
// The plaintext lives only in private/, which git ignores: private/sealed-research.json and private/docs/*.md.
// The sealed file holds no password, hash or key: AES-256-GCM, with the key derived from the password by
// PBKDF2-SHA-256 and a random salt. Anyone with the file can only guess passwords, one slow guess at a time,
// so use the long random password you generated. The browser decrypts the same file with the Web Crypto API.
//
// The password is asked for at a hidden prompt. EODEM_SEAL_PASSWORD is read only when there is no terminal
// (automated tests); do not type it on a command line, where shell history would keep it.
import { createCipheriv, createDecipheriv, pbkdf2Sync, randomBytes } from 'node:crypto';
import { gzipSync, gunzipSync } from 'node:zlib';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const ROOT = path.resolve(path.dirname(fileURLToPath(import.meta.url)), '..', '..');
const PRIVATE = path.join(ROOT, 'private');
const PLAIN = path.join(PRIVATE, 'sealed-research.json');
const DOCS = path.join(PRIVATE, 'docs');
const SEALED = path.join(ROOT, 'src', 'data', 'sealed.json');
export const ITERATIONS = 600000; // PBKDF2-HMAC-SHA256, as OWASP recommends (2023)
const MIN_LENGTH = 16;

function die(msg) { console.error(msg); process.exit(1); }

// ---------------------------------------------------------------- the bundle
export function readBundle() {
  if (!fs.existsSync(PLAIN)) die(`Nothing to seal: ${path.relative(ROOT, PLAIN)} is missing.`);
  const research = JSON.parse(fs.readFileSync(PLAIN, 'utf8'));
  const docs = {};
  if (fs.existsSync(DOCS)) for (const f of fs.readdirSync(DOCS).sort()) if (f.endsWith('.md')) docs[f] = fs.readFileSync(path.join(DOCS, f), 'utf8');
  return { ...research, docs };
}

function writeBundle(bundle, force) {
  const { docs = {}, ...research } = bundle;
  const targets = [PLAIN, ...Object.keys(docs).map(f => path.join(DOCS, path.basename(f)))];
  const existing = targets.filter(p => fs.existsSync(p));
  if (existing.length && !force) die(`Refusing to overwrite ${existing.map(p => path.relative(ROOT, p)).join(', ')}. Use --force.`);
  fs.mkdirSync(DOCS, { recursive: true });
  fs.writeFileSync(PLAIN, JSON.stringify(research, null, 1) + '\n');
  for (const [f, text] of Object.entries(docs)) fs.writeFileSync(path.join(DOCS, path.basename(f)), text);
  return targets;
}

// ---------------------------------------------------------------- encryption
export function seal(bundle, password, iterations = ITERATIONS) {
  const salt = randomBytes(16), iv = randomBytes(12);
  const key = pbkdf2Sync(Buffer.from(password.normalize('NFC'), 'utf8'), salt, iterations, 32, 'sha256');
  const c = createCipheriv('aes-256-gcm', key, iv);
  const body = Buffer.concat([c.update(gzipSync(Buffer.from(JSON.stringify(bundle), 'utf8'))), c.final(), c.getAuthTag()]);
  return {
    format: 'eodem-sealed', version: 1,
    kdf: { name: 'PBKDF2', hash: 'SHA-256', iterations, salt: salt.toString('base64') },
    cipher: { name: 'AES-GCM', iv: iv.toString('base64'), tagLength: 128 },
    compression: 'gzip',
    sealed: new Date().toISOString().slice(0, 10),
    data: body.toString('base64'),
  };
}

export function open(file, password) {
  if (file.format !== 'eodem-sealed' || file.version !== 1) throw new Error('not a sealed research file');
  const key = pbkdf2Sync(Buffer.from(password.normalize('NFC'), 'utf8'), Buffer.from(file.kdf.salt, 'base64'), file.kdf.iterations, 32, 'sha256');
  const body = Buffer.from(file.data, 'base64');
  const d = createDecipheriv('aes-256-gcm', key, Buffer.from(file.cipher.iv, 'base64'));
  d.setAuthTag(body.subarray(body.length - 16));
  let plain;
  try { plain = Buffer.concat([d.update(body.subarray(0, body.length - 16)), d.final()]); } catch (_) { throw new Error('wrong password'); }
  return JSON.parse(gunzipSync(plain).toString('utf8'));
}

// ---------------------------------------------------------------- the password
function ask(prompt) {
  if (!process.stdin.isTTY) {
    const p = process.env.EODEM_SEAL_PASSWORD;
    if (!p) die('No terminal to ask for the password (EODEM_SEAL_PASSWORD is not set).');
    return Promise.resolve(p);
  }
  return new Promise(resolve => {
    process.stdout.write(prompt);
    const stdin = process.stdin;
    stdin.setRawMode(true); stdin.resume(); stdin.setEncoding('utf8');
    let s = '';
    const onData = ch => {
      for (const c of ch) {
        if (c === '\r' || c === '\n') { stdin.setRawMode(false); stdin.pause(); stdin.off('data', onData); process.stdout.write('\n'); return resolve(s); }
        if (c === '\u0003') { process.stdout.write('\n'); process.exit(130); }
        if (c === '\u007f' || c === '\b') { s = s.slice(0, -1); continue; }
        s += c;
      }
    };
    stdin.on('data', onData);
  });
}

function sameBundle(a, b) { return JSON.stringify(a) === JSON.stringify(b); }

// ---------------------------------------------------------------- commands
async function main() {
  const [cmd, ...flags] = process.argv.slice(2);
  if (cmd === 'seal') {
    const bundle = readBundle();
    const pw = await ask('Password: ');
    if (pw.length < MIN_LENGTH) die(`Use the long generated password (at least ${MIN_LENGTH} characters).`);
    if (process.stdin.isTTY && (await ask('Again: ')) !== pw) die('The passwords differ; nothing was written.');
    if (fs.existsSync(SEALED)) {
      try { open(JSON.parse(fs.readFileSync(SEALED, 'utf8')), pw); } catch (_) {
        if (!flags.includes('--new-password')) die('This password does not open the current sealed file. To change the password, run again with --new-password.');
      }
    }
    const file = seal(bundle, pw);
    if (!sameBundle(open(file, pw), bundle)) die('Self-check failed; nothing was written.');
    fs.writeFileSync(SEALED, JSON.stringify(file, null, 1) + '\n');
    console.log(`Sealed ${Object.keys(bundle.docs).length} documents and the research data into ${path.relative(ROOT, SEALED)} (${fs.statSync(SEALED).size.toLocaleString('en-US')} bytes).`);
  } else if (cmd === 'open') {
    const pw = await ask('Password: ');
    let bundle;
    try { bundle = open(JSON.parse(fs.readFileSync(SEALED, 'utf8')), pw); } catch (e) { die(e.message); }
    const written = writeBundle(bundle, flags.includes('--force'));
    console.log('Opened into ' + written.map(p => path.relative(ROOT, p)).join(', '));
  } else if (cmd === 'check') {
    const pw = await ask('Password: ');
    let bundle;
    try { bundle = open(JSON.parse(fs.readFileSync(SEALED, 'utf8')), pw); } catch (e) { die(e.message); }
    if (!fs.existsSync(PLAIN)) return console.log('The password opens the sealed file. There is no private copy to compare.');
    console.log(sameBundle(bundle, readBundle()) ? 'The password opens the sealed file, and it matches private/.'
      : 'The password opens the sealed file, but private/ has changed since it was sealed: run seal.');
  } else {
    die('Usage: node tools/seal/seal.mjs seal [--new-password] | open [--force] | check');
  }
}

if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
