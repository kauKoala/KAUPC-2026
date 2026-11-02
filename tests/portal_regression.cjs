const {readFileSync} = require('node:fs');
const {resolve} = require('node:path');
const {test} = require('node:test');
const assert = require('node:assert/strict');
const {JSDOM} = require('jsdom');
const source = readFileSync(resolve(__dirname, '../custom/js/contest-portal.js'), 'utf8');

function page(html, path = '/contest/problems') {
  const dom = new JSDOM(html, {url: 'https://kaupc2026.me' + path, runScripts: 'outside-only'});
  dom.window.eval(source.slice(0, source.lastIndexOf('  document.addEventListener("DOMContentLoaded"')) +
    'window.portalTest = {buildProblemTable, appendCurrentContestCard, currentContestFromMenu, buildStatementChrome};})();');
  return dom.window;
}

test('missing statement keeps all problems and submit buttons visible', () => {
  const card = (label, statement) => `<div><div class="card"><b class="card-title">${label}</b>` +
    `<span class="card-subtitle">Problem ${label}</span><span class="card-subtitle">1s</span>` +
    (statement ? `<a href="/contest/problems/${label}/statement">Statement</a>` : '') +
    `<a href="/contest/submit/${label}">Submit</a></div></div>`;
  const w = page('<h1>Contest</h1><div class="problem-list">' + card('A', true) + card('C', false) + '</div>');
  w.portalTest.buildProblemTable();
  assert.equal(w.document.querySelectorAll('.problem-table tbody tr').length, 2);
  assert.equal(w.document.querySelectorAll('.problem-table__submit').length, 2);
  assert.equal(w.document.querySelectorAll('.problem-app__open').length, 1);
  assert.match(w.document.querySelectorAll('.problem-table tbody tr')[1].textContent, /Problem C/);
});

test('current card explicitly selects its server contest id even after menu removal', () => {
  const w = page('<nav><li><a id="navbarDropdownContests">test</a>' +
    '<div data-current-contest="3"></div></li></nav><div id="grid"></div>', '/contest');
  w.portalTest.currentContestFromMenu();
  w.document.querySelector('nav').remove();
  w.portalTest.appendCurrentContestCard(w.document.querySelector('#grid'), 'test');
  assert.equal(w.document.querySelector('.contest-card').getAttribute('href'), '/contest/change-contest/3');
});

test('shared statement uses the viewing contest and label', () => {
  const w = page('<a id="navbarDropdownContests">kaupc</a>' +
    '<article><p class="problem-eyebrow">KAUPC2026 TEST · K</p></article>');
  w.portalTest.buildStatementChrome(w.document.querySelector('article'), 'L');
  assert.equal(w.document.querySelector('.problem-eyebrow').textContent, 'KAUPC2026 · L');
});
