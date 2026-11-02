(function (root, factory) {
  var api = factory();
  if (typeof module === "object" && module.exports) module.exports = api;
  else { root.KaupcResolver = api; if (root.document) { if (root.document.readyState === 'loading') root.document.addEventListener('DOMContentLoaded',api.mount,{once:true}); else api.mount(); } }
})(typeof window === "undefined" ? globalThis : window, function () {
  "use strict";
  function seconds(value) {
    if (typeof value === "number" && Number.isFinite(value)) return value;
    var m = String(value).match(/^(-?)(\d+):([0-5]\d):([0-5]\d(?:\.\d+)?)$/);
    if (!m) throw new Error("대회 시간 형식을 확인할 수 없습니다: " + value);
    return (m[1] ? -1 : 1) * (+m[2] * 3600 + +m[3] * 60 + +m[4]);
  }
  function create(data) {
    var contest = data.contest;
    if (contest.scoreboard_type !== "pass-fail" || contest.runtime_as_score_tiebreaker) throw new Error("이 결과 발표 화면은 ICPC 점수 방식에서 사용할 수 있습니다.");
    var duration = seconds(contest.duration), freezeLength = seconds(contest.scoreboard_freeze_duration || "0:00:00");
    if (freezeLength <= 0 || freezeLength > duration) throw new Error("먼저 이 대회의 순위표 프리즈를 설정해 주세요.");
    var cutoff = duration - freezeLength, history = [], total = 0;
    var problems = data.problems.slice().sort(function (a, b) { return a.label.localeCompare(b.label, undefined, {numeric:true}); });
    var official = new Map(data.scoreboard.rows.map(function (r) { return [String(r.team_id), r]; }));
    var types = new Map(data.judgementTypes.map(function (j) { return [j.id, j]; }));
    var teams = data.teams.filter(function (t) { return official.has(String(t.id)); }).map(function (t) {
      var cells = {};
      problems.forEach(function (p) { cells[p.id] = {attempts:0, bad:0, accepted:false, time:0, shown:0, events:[]}; });
      return {id:String(t.id), name:t.display_name || t.name, cells:cells};
    });
    if (teams.length !== official.size) throw new Error("참가자 목록과 공식 순위표가 다릅니다. 다시 불러와 주세요.");
    var teamMap = new Map(teams.map(function (t) { return [t.id, t]; })), judgements = new Map();
    function stamp(j) { return Date.parse(j.start_time || j.end_time || "") || 0; }
    data.judgements.filter(function (j) { return j.valid !== false; }).forEach(function (j) {
      var id = String(j.submission_id), previous = judgements.get(id);
      if (!previous || stamp(j) >= stamp(previous)) judgements.set(id, j);
    });
    function apply(cell, event) {
      cell.attempts++;
      if (event.solved) { cell.accepted = true; cell.time = Math.floor(event.seconds / 60); }
      else if (event.penalty) cell.bad++;
    }
    data.submissions.map(function (s) {
      var time = s.contest_time != null ? seconds(s.contest_time) : (Date.parse(s.time) - Date.parse(contest.start_time)) / 1000;
      return {source:s, time:time};
    }).filter(function (s) { return s.source.valid !== false && Number.isFinite(s.time) && s.time >= 0 && s.time < duration; })
      .sort(function (a, b) { return a.time - b.time || String(a.source.id).localeCompare(String(b.source.id), undefined, {numeric:true}); })
      .forEach(function (item) {
        var s = item.source, team = teamMap.get(String(s.team_id)), cell = team && team.cells[s.problem_id];
        if (!cell) return;
        var j = judgements.get(String(s.id));
        if (!j || !j.end_time || !j.judgement_type_id) throw new Error("채점 중인 제출이 있습니다. 채점 완료 후 다시 불러와 주세요.");
        var type = types.get(j.judgement_type_id);
        if (!type) throw new Error("알 수 없는 판정: " + j.judgement_type_id);
        if (cell.accepted || cell.futureAccepted) return;
        var event = {id:s.id, seconds:item.time, verdict:type.id, solved:!!type.solved, penalty:!!type.penalty};
        if (item.time < cutoff) apply(cell, event);
        else { cell.events.push(event); total++; if (event.solved) cell.futureAccepted = true; }
      });
    function score(t) {
      var result = {solved:0, total:0, last:0};
      problems.forEach(function (p) { var c = t.cells[p.id]; if (c.accepted) { result.solved++; result.total += c.time + c.bad * Number(contest.penalty_time || 20); result.last = Math.max(result.last, c.time); } });
      return result;
    }
    function compare(a, b) { var x = score(a), y = score(b); return y.solved - x.solved || x.total - y.total || x.last - y.last; }
    function ranking() {
      var result = teams.slice().sort(function (a, b) { return compare(a, b) || a.name.localeCompare(b.name) || a.id.localeCompare(b.id); });
      var rank = 0;
      return result.map(function (t, index) { if (!index || compare(result[index - 1], t) !== 0) rank = index + 1; return {team:t, score:score(t), rank:rank}; });
    }
    function next() {
      var rows = ranking();
      for (var i = rows.length - 1; i >= 0; i--) {
        for (var p of problems) { var c = rows[i].team.cells[p.id]; if (!c.accepted && c.shown < c.events.length) return {team:rows[i].team, problem:p, cell:c, rank:rows[i].rank, position:i+1}; }
      }
      return null;
    }
    function step(remember) {
      var target = next(); if (!target) return null;
      var c = target.cell, event = c.events[c.shown];
      if (remember !== false) history.push({cell:c, state:{attempts:c.attempts,bad:c.bad,accepted:c.accepted,time:c.time,shown:c.shown}});
      c.shown++; apply(c, event);
      var afterRows = ranking(), afterPosition = afterRows.findIndex(function (r) { return r.team.id === target.team.id; });
      return {team:target.team, problem:target.problem, attempt:c.attempts, accepted:event.solved, verdict:event.verdict, before:target.rank, after:afterRows[afterPosition].rank, beforePosition:target.position, afterPosition:afterPosition+1};
    }
    function validate() {
      var copy = create(data); while (copy.next()) copy.step(false);
      var differences = [];
      copy.ranking().forEach(function (row) { var expected = official.get(row.team.id); if (row.score.solved !== expected.score.num_solved || row.score.total !== expected.score.total_time || row.rank !== expected.rank) differences.push(row.team.name); });
      return {ok:!differences.length, differences:differences};
    }
    return {problems:problems, teams:teams, contest:contest, total:total, cutoff:cutoff, ranking:ranking, next:next, step:step, validate:validate, undo:function () { var h = history.pop(); if (h) Object.assign(h.cell, h.state); return !!h; }, history:history,
      revealed:function () { return teams.reduce(function (sum, t) { return sum + problems.reduce(function (n, p) { return n + t.cells[p.id].shown; }, 0); }, 0); }};
  }
  function announcements(engine) {
    var confirmed = new Set(), visited = new Set(), history = [];
    function next() {
      var rows = engine.ranking();
      for (var i = rows.length - 1; i >= 0; i--) {
        var row = rows[i]; if (confirmed.has(row.team.id)) continue;
        for (var p of engine.problems) {
          var c = row.team.cells[p.id];
          if (!c.accepted && c.shown < c.events.length) return {kind:'reveal',team:row.team,problem:p,cell:c,rank:row.rank,position:i+1};
        }
        return {kind:'confirm',team:row.team,problem:null,rank:row.rank,position:i+1};
      }
      return null;
    }
    return {next:next,isConfirmed:function (id) { return confirmed.has(id); },isVisited:function (id) { return visited.has(id); },step:function () {
      var target = next(); if (!target) return null;
      var wasVisited = visited.has(target.team.id); visited.add(target.team.id);
      if (target.kind === 'confirm') { confirmed.add(target.team.id); target.wasVisited = wasVisited; history.push(target); return target; }
      var event = engine.step(); event.kind = 'reveal'; event.wasVisited = wasVisited; history.push(event); return event;
    },undo:function () {
      var event = history.pop(); if (!event) return false;
      if (event.kind === 'confirm') confirmed.delete(event.team.id); else engine.undo();
      if (!event.wasVisited) visited.delete(event.team.id);
      return true;
    }};
  }
  function escape(value) { return String(value == null ? "" : value).replace(/[&<>"']/g, function (c) { return {"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]; }); }
  function presentation(c) {
    return {state:c.accepted ? 'accepted' : c.shown ? 'wrong' : c.events.length ? 'pending' : c.attempts ? 'wrong' : 'blank',
      label:c.accepted ? '+' + c.attempts : c.shown ? (c.shown < c.events.length ? '+' : '−') + c.attempts : c.attempts ? '−' + c.attempts : c.events.length ? '?' : '',
      detail:c.accepted ? c.time + '분' : ''};
  }
  function frame() { return '<h1>스코어보드</h1><div id="kr-error" role="alert" hidden></div><div class="kr-table-wrap"><table class="scoreboard desktop-scoreboard center scoreboard_jury"><thead id="kr-head"></thead><tbody id="kr-body"></tbody></table></div>'; }
  function totals(score) { return '<td class="scorenc kr-total-solved">' + score.solved + '</td><td class="scorett kr-total-time">' + score.total + '</td>'; }
  function rankLabel(rank, position, confirmed) { return String(confirmed ? rank : position); }
  async function mount() {
    if (location.pathname !== "/jury/scoreboard" || new URLSearchParams(location.search).get("resolver") !== "1") return;
    if (document.getElementById("kaupc-resolver")) return;
    document.body.classList.add("kaupc-results-mode");
    var style = document.createElement("link"); style.rel = "stylesheet"; style.href = "/css/custom/scoreboard-resolver.css"; document.head.append(style);
    var scoreboard = document.querySelector("table.desktop-scoreboard"), container = scoreboard && scoreboard.closest(".container-fluid");
    var host = document.createElement("main"); host.id = "kaupc-resolver";
    if (container) { container.hidden = true; container.after(host); } else { document.body.append(host); }
    host.innerHTML = frame(); document.title = '스코어보드';
    var $ = function (id) { return host.querySelector("#kr-" + id); }, engine, announcement, snapshot, busy = false, active, epoch = 0, selectedContest;
    function selectCurrent() { var next = announcement.next(); active = next ? {team:next.team.id,problem:next.problem && next.problem.id} : null; return next; }
    async function get(path) { var r = await fetch("/api/v4/" + path, {credentials:"same-origin",cache:"no-store"}); if (!r.ok) throw new Error("운영자 데이터 접근 실패 (" + r.status + ")"); return r.json(); }
    function failure(error) { $("error").textContent = error.message; $("error").hidden = false; }
    function cellHTML(c, selected) {
      var shown = presentation(c);
      var scoreClass = shown.state === 'accepted' ? 'score_correct' : shown.state === 'wrong' ? 'score_incorrect' : shown.state === 'pending' ? 'score_pending' : '';
      return '<div class="kr-cell ' + scoreClass + ' ' + shown.state + (selected ? ' selected' : '') + '"><b>' + shown.label + '</b><small>' + shown.detail + '</small></div>';
    }
    function render(animate) {
      if (!engine) return;
      var previous = new Map(Array.from($("body").children).map(function (r) { return [r.dataset.id, r.getBoundingClientRect().top]; }));
      $("head").innerHTML = '<tr><th class="kr-rank">순위</th><th class="kr-name">이름</th>' + engine.problems.map(function (p) {
        var color = /^#[0-9a-f]{6}$/i.test(p.rgb || '') ? p.rgb : '#4682b4';
        var text = parseInt(color.slice(1,3),16)*.299 + parseInt(color.slice(3,5),16)*.587 + parseInt(color.slice(5,7),16)*.114 > 140 ? '#111' : '#fff';
        return '<th title="' + escape(p.name) + '"><span class="badge problem-badge" style="background:' + color + ';color:' + text + '">' + escape(p.label) + '</span></th>';
      }).join("") + '<th colspan="2" class="kr-total-heading">총계</th></tr>';
      $("body").innerHTML = engine.ranking().map(function (r, index) { var state = announcement.isConfirmed(r.team.id) ? 'confirmed' : active && active.team === r.team.id ? 'current' : announcement.isVisited(r.team.id) ? 'visited' : 'pending'; return '<tr data-id="' + escape(r.team.id) + '" data-announcement-status="' + state + '"' + (state === 'pending' ? ' aria-hidden="true"' : '') + ' class="' + (state === 'current' ? 'kr-active' : state === 'confirmed' ? 'kr-confirmed' : state === 'pending' ? 'kr-unrevealed' : '') + '"><td class="scorepl rank">' + rankLabel(r.rank,index + 1,state === 'confirmed') + '</td><td class="kr-name scoretn">' + escape(r.team.name) + '</td>' + engine.problems.map(function (p) { return '<td class="score_cell">' + cellHTML(r.team.cells[p.id], active && active.team === r.team.id && active.problem === p.id) + '</td>'; }).join("") + totals(r.score) + '</tr>'; }).join("");
      if (animate && !matchMedia('(prefers-reduced-motion: reduce)').matches) Array.from($("body").children).forEach(function (r) { var old = previous.get(r.dataset.id), now = r.getBoundingClientRect().top; if (old != null && old !== now) r.animate([{transform:'translateY(' + (old - now) + 'px)'},{transform:'translateY(0)'}],{duration:650,easing:'cubic-bezier(.22,.7,.2,1)'}); });
      host.setAttribute('aria-busy',String(busy));
    }
    function rowFor(id) { return Array.from($("body").children).find(function (r) { return r.dataset.id === id; }); }
    function center(id, problemId) {
      var row = rowFor(id), wrap = host.querySelector('.kr-table-wrap'); if (!row) return;
      var bounds = wrap.getBoundingClientRect(), left = wrap.scrollLeft;
      var index = engine.problems.findIndex(function (p) { return p.id === problemId; });
      var cell = row.querySelectorAll('td.score_cell')[index];
      if (cell) {
        var rect = cell.getBoundingClientRect(), right = bounds.left + wrap.clientWidth - host.querySelector('.kr-total-heading').getBoundingClientRect().width;
        var visibleLeft = bounds.left + row.querySelector('.rank').getBoundingClientRect().width + row.querySelector('.kr-name').getBoundingClientRect().width;
        if (rect.right > right) left += rect.right - right;
        else if (rect.left < visibleLeft) left += rect.left - visibleLeft;
      }
      wrap.scrollTo({top:wrap.scrollTop + row.getBoundingClientRect().top - bounds.top - (wrap.clientHeight - row.offsetHeight) / 2,left:left,behavior:'smooth'});
    }
    async function load() {
      var version = ++epoch; engine = null; busy = true; $("body").replaceChildren(); host.setAttribute('aria-busy','true'); $("error").hidden = true;
      try {
        var prefix = 'contests/' + encodeURIComponent(selectedContest) + '/';
        var includeHidden = new URLSearchParams(location.search).get('allteams') === '1';
        var parts = await Promise.all([get(prefix.slice(0,-1)),get(prefix+'problems'),get(prefix+'teams'),get(prefix+'submissions'),get(prefix+'judgements'),get(prefix+'judgement-types'),get(prefix+'scoreboard?public=false' + (includeHidden ? '&allteams=true' : ''))]);
        if (version !== epoch) return;
        snapshot = {contest:parts[0],problems:parts[1],teams:parts[2],submissions:parts[3],judgements:parts[4],judgementTypes:parts[5],scoreboard:parts[6]};
        var candidate = create(snapshot), checked = candidate.validate();
        if (!checked.ok) throw new Error("공식 순위표와 점수가 일치하지 않습니다: " + checked.differences.join(", ") + ". 진행하지 말고 운영자에게 확인해 주세요.");
        engine = candidate; announcement = announcements(engine); busy = false; var next = selectCurrent(); render(false);
        if (next) { var wrap = host.querySelector('.kr-table-wrap'); wrap.scrollTop = wrap.scrollHeight; }
      } catch (e) { busy = false; engine = null; host.setAttribute('aria-busy','false'); failure(e); }
    }
    function advance() {
      if (busy || !engine || !announcement.next()) return;
      var next = selectCurrent(); render(false); center(next.team.id,next.problem && next.problem.id);
      if (next.kind === 'confirm') {
        announcement.step(); next = selectCurrent(); render(false);
        if (next) center(next.team.id,next.problem && next.problem.id);
        return;
      }
      var row = rowFor(next.team.id), index = engine.problems.findIndex(function (p) { return p.id === next.problem.id; }), card = row.querySelectorAll('td.score_cell')[index].firstElementChild;
      var event = announcement.step(), version = epoch, flipDuration = 900; busy = true; host.setAttribute('aria-busy','true');
      if (!matchMedia('(prefers-reduced-motion: reduce)').matches) card.animate([{transform:'perspective(450px) rotateX(0)'},{transform:'perspective(450px) rotateX(-90deg)',offset:.5},{transform:'perspective(450px) rotateX(0)'}],{duration:flipDuration,easing:'cubic-bezier(.4,0,.2,1)'});
      setTimeout(function () { if (version !== epoch) return; card.className = 'kr-cell selected ' + (event.accepted ? 'accepted score_correct' : 'wrong score_incorrect'); card.querySelector('b').textContent = '+' + event.attempt; card.querySelector('small').textContent = ''; },flipDuration / 2);
      setTimeout(function () {
        if (version !== epoch) return; render(true);
        setTimeout(function () { if (version !== epoch) return; busy = false; var next = selectCurrent(); render(false); if (next) center(next.team.id,next.problem && next.problem.id); },event.accepted && event.afterPosition < event.beforePosition ? 700 : 0);
      },flipDuration);
    }
    function undo() { if (busy || !engine || !announcement.undo()) return; busy = true; var version = epoch, next = selectCurrent(); render(true); if (next) center(next.team.id,next.problem && next.problem.id); setTimeout(function () { if (version !== epoch) return; busy = false; render(false); },700); }
    function reset() { if (busy || !snapshot) return; engine = create(snapshot); announcement = announcements(engine); var next = selectCurrent(); render(false); if (next) center(next.team.id,next.problem && next.problem.id); }
    document.addEventListener('keydown',function (e) { if (e.target.matches('input,textarea,select') || e.target.isContentEditable || e.ctrlKey || e.altKey || e.metaKey) return; if (['Space','Enter','NumpadEnter'].includes(e.code)) { e.preventDefault(); if (!e.repeat) advance(); } else if (e.code === 'ArrowLeft') { e.preventDefault(); if (!e.repeat) undo(); } else if (e.code === 'Home') { e.preventDefault(); if (!e.repeat) reset(); } });
    try {
      var user = await get('user'); if (!(user.roles || []).some(function (r) { return /^(admin|jury)$/.test(r); })) throw new Error("운영자만 결과 발표를 열 수 있습니다.");
      var contests = await get('contests'), query = new URLSearchParams(location.search), cid = query.get('cid');
      var selectedNode = document.querySelector('[data-current-contest]'), selectedCid = selectedNode && selectedNode.getAttribute('data-current-contest');
      var menu = document.querySelector('#navbarDropdownContests'), menuName = menu ? menu.textContent.trim().replace(/^[^\p{L}\p{N}]+/u,'').trim() : '';
      var selected = contests.find(function (c) { return cid ? c.id === cid || String(c.cid) === cid : String(c.cid) === selectedCid || c.id === menuName || c.name === menuName; }) || contests.find(function (c) { return c.id === 'kaupc'; }) || contests[0];
      if (!selected) throw new Error("접근 가능한 대회가 없습니다."); selectedContest = selected.id; await load();
    } catch (e) { failure(e); }
  }
  return {seconds:seconds, create:create, announcements:announcements, presentation:presentation, frame:frame, totals:totals, rankLabel:rankLabel, mount:mount};
});
