(function () {
  "use strict";

  var INTERNAL_ROOT = "/team";
  var CONTEST_ROOT = "/contest";

  function contestPath(path) {
    return CONTEST_ROOT + (path || "");
  }

  function isContestPath() {
    return location.pathname === CONTEST_ROOT || location.pathname.indexOf(CONTEST_ROOT + "/") === 0;
  }

  function isContestPage() {
    return location.pathname.indexOf(CONTEST_ROOT + "/") === 0;
  }

  function isClarificationsPage() {
    return location.pathname === contestPath("/clarifications");
  }

  function isStatusPage() {
    return /^\/contest\/status(\/[0-9]+)?$/.test(location.pathname);
  }

  function isStatementPage() {
    return location.pathname === contestPath("/problems");
  }

  function clarificationsPath() {
    return contestPath("/clarifications");
  }

  function contestUrl(value) {
    var url = new URL(value, location.origin);
    if (url.pathname === INTERNAL_ROOT || url.pathname.indexOf(INTERNAL_ROOT + "/") === 0) {
      url.pathname = CONTEST_ROOT + url.pathname.slice(INTERNAL_ROOT.length);
    }
    return url.pathname + url.search + url.hash;
  }

  function rewriteParticipantLinks(root) {
    if (!isContestPath()) return;
    (root || document).querySelectorAll("a[href], form[action]").forEach(function (element) {
      var attribute = element.tagName === "FORM" ? "action" : "href";
      var value = element.getAttribute(attribute);
      if (value && (value === INTERNAL_ROOT || value.indexOf(INTERNAL_ROOT + "/") === 0)) {
        element.setAttribute(attribute, contestUrl(value));
      }
    });
  }

  function contestLinks() {
    return Array.from(document.querySelectorAll('a[href*="/team/change-contest/"], a[href*="/contest/change-contest/"]'));
  }

  function contestName(link) {
    return link.textContent.replace(/\s+/g, " ").trim() || "대회";
  }

  function displayContestName(name) {
    var normalized = String(name || "").toLowerCase();
    if (normalized === "kaupc" || normalized === "kaupc2026") return "KAUPC2026";
    if (normalized === "test" || normalized === "kaupc2026 test") return "KAUPC2026 TEST";
    if (normalized === "kaupcopen" || normalized === "kaupc2026 open") return "KAUPC2026 Open";
    return name;
  }

  function pageTarget() {
    return document.querySelector("[data-ajax-refresh-target]");
  }

  function rememberContest(name) {
    try {
      sessionStorage.setItem("kaupc_contest", name);
    } catch (e) {
      /* ignore */
    }
  }

  function rememberPendingContest(name) {
    try {
      sessionStorage.setItem("kaupc_pending_contest", name);
    } catch (e) {
      /* The DOMjudge redirect remains usable without storage. */
    }
  }

  function returnToSelectedContest() {
    if (location.pathname !== CONTEST_ROOT) return false;
    try {
      var pending = sessionStorage.getItem("kaupc_pending_contest");
      var selected = currentContestFromMenu();
      if (!pending || !selected || displayContestName(pending) !== displayContestName(selected)) return false;
      sessionStorage.removeItem("kaupc_pending_contest");
    } catch (e) {
      return false;
    }
    location.replace(contestPath("/problems"));
    return true;
  }

  // DOMjudge 상단의 대회 변경 메뉴에는 지금 선택된 대회가 적혀 있다. 메뉴는 곧 지우므로 먼저 읽어 둔다.
  // 브라우저에 기억해 둔 이름은 지운 대회(예: FIVEMIN)를 가리킬 수 있어, 이 값을 먼저 믿는다.
  var menuContest;
  var menuContestId;

  function currentContestFromMenu() {
    if (menuContest === undefined) {
      var toggle = document.getElementById("navbarDropdownContests");
      menuContest = toggle ? toggle.textContent.replace(/\s+/g, " ").trim() : "";
      var menu = document.querySelector("[data-current-contest]");
      menuContestId = menu ? menu.dataset.currentContest : "";
    }
    return menuContest;
  }

  function resolveContestName(callback) {
    var fromMenu = currentContestFromMenu();
    if (fromMenu) {
      rememberContest(fromMenu);
      callback(fromMenu);
      return;
    }
    var cleanName = function (raw) {
      return (raw || "").trim().replace(/\s+problems$/, "").trim();
    };
    if (location.pathname === contestPath("/problems") && document.querySelector("h1")) {
      var name = cleanName(document.querySelector("h1").textContent);
      if (name) rememberContest(name);
      callback(name);
      return;
    }
    fetch(contestPath("/problems"), { credentials: "same-origin" })
      .then(function (response) {
        return response.ok ? response.text() : "";
      })
      .then(function (html) {
        var parsed = new DOMParser().parseFromString(html, "text/html");
        var heading = parsed.querySelector("h1");
        var name = cleanName(heading ? heading.textContent : "");
        if (name) rememberContest(name);
        callback(name);
      })
      .catch(function () {
        callback("");
      });
  }

  function recalledContest() {
    try {
      return sessionStorage.getItem("kaupc_contest") || "";
    } catch (e) {
      return "";
    }
  }

  function rememberSubmitReturn() {
    var form = document.querySelector(".submitform");
    if (!form || form.dataset.returnToContest === "true") return;
    form.dataset.returnToContest = "true";
    form.addEventListener("submit", function () {
      try {
        sessionStorage.setItem("kaupc_return_to_contest", "1");
      } catch (e) {
        /* A normal DOMjudge redirect is still safe if storage is unavailable. */
      }
    });
  }

  function addPastedCodeSubmission() {
    var form = document.querySelector(".submitform");
    if (!form || form.dataset.pasteSubmit === "true") return;
    var fileInput = form.querySelector('input[type="file"][name="submit_problem[code][]"]');
    var language = form.querySelector('select[name="submit_problem[language]"]');
    if (!fileInput || !language) return;
    form.dataset.pasteSubmit = "true";
    // 브라우저 기본 required 검증은 submit 이벤트보다 먼저 실행된다.
    // 붙여넣은 코드를 File로 바꾸려면 여기서 파일 필수 검증을 대체해야 한다.
    fileInput.required = false;

    var section = document.createElement("section");
    section.className = "paste-submit";
    section.innerHTML =
      '<label for="paste-submit-source">코드 붙여넣기</label>' +
      '<textarea id="paste-submit-source" class="form-control" rows="16" spellcheck="false" placeholder="여기에 제출할 소스 코드를 붙여넣으세요."></textarea>' +
      '<p class="paste-submit__hint">소스 파일을 선택하거나 코드를 붙여넣을 수 있습니다.</p>' +
      '<p class="paste-submit__error" role="alert" hidden></p>';
    var fileRow = fileInput.closest(".mb-3, .form-group") || fileInput.parentElement;
    fileRow.after(section);

    var textarea = section.querySelector("textarea");
    var error = section.querySelector(".paste-submit__error");
    var filenames = {
      c: "solution.c",
      cpp: "solution.cpp",
      java: "Main.java",
      py3: "solution.py"
    };

    function showError(message) {
      error.textContent = message;
      error.hidden = false;
    }

    textarea.addEventListener("input", function () {
      error.hidden = true;
    });

    // 붙여넣은 코드로 만든 파일은 DOMjudge 확인창에서 취소해도 파일 칸에 남는다.
    // 참가자가 고른 파일과 구분해 두었다가 다음 제출 때 지우고 다시 만든다.
    var generated = false;
    fileInput.addEventListener("change", function () {
      generated = false;
    });

    form.addEventListener("submit", function (event) {
      var source = textarea.value.trim();
      if (generated) {
        fileInput.value = "";
        generated = false;
      }
      if (!source) {
        if (fileInput.files && fileInput.files.length) return;
        event.preventDefault();
        showError("소스 파일이나 붙여넣은 코드를 입력하세요.");
        return;
      }
      if (fileInput.files && fileInput.files.length) {
        event.preventDefault();
        showError("파일과 붙여넣은 코드 중 하나만 제출할 수 있습니다.");
        return;
      }
      var filename = filenames[language.value];
      if (!filename) {
        event.preventDefault();
        showError("제출할 언어를 선택하세요.");
        return;
      }
      var transfer = new DataTransfer();
      transfer.items.add(new File([source], filename, { type: "text/plain" }));
      fileInput.files = transfer.files;
      generated = true;
    });
  }

  // 처음 로그인한 참가자는 스코어보드에 보일 이름부터 정한다. 정하기 전에는 닫을 수 없다.
  function askForNickname() {
    var path = location.pathname;
    var participantPage = path === INTERNAL_ROOT || path.indexOf(INTERNAL_ROOT + "/") === 0 || isContestPath();
    if (!participantPage || document.querySelector(".nickname-gate")) return;
    fetch("/participant/nickname", { credentials: "same-origin", cache: "no-store" })
      .then(function (response) { return response.ok ? response.json() : null; })
      .then(function (state) {
        if (state && state.needs_nickname) showNicknameGate();
        if (state && state.guest) offerGuestLogin();
        if (state && state.guest) hideScoreboardFromGuest();
      })
      .catch(function () {});
  }

  // 공개 대회 순위표에는 게스트 이름뿐이고 입장만 해도 0문제 줄이 생겨 의미가 없다. 게스트에게는 채점 현황만 보인다.
  // KAUPC 계정은 이 탭으로 자기 대회 결과를 보므로 그대로 둔다.
  function hideScoreboardFromGuest() {
    if (location.pathname === contestPath("/scoreboard")) {
      location.replace("/contest/status");
      return;
    }
    document.querySelectorAll('a[href="/contest/scoreboard"]').forEach(function (link) { link.remove(); });
    document.querySelectorAll("p").forEach(function (paragraph) {
      if (!paragraph.children.length && paragraph.textContent.indexOf("순위표") >= 0) {
        paragraph.textContent = paragraph.textContent.replace("순위표", "채점 현황");
      }
    });
  }

  // 게스트는 로그아웃해도 같은 게스트로 돌아온다. 그 자리에서 운영진과 KAUPC 계정으로 로그인하게 한다.
  function offerGuestLogin() {
    var button = document.querySelector('a[href="/logout"]');
    if (!button) return;
    button.href = "/login?account=1";
    button.removeAttribute("onclick");
    button.innerHTML = '<i class="fas fa-sign-in-alt"></i> 로그인';
  }

  function showNicknameGate() {
    var gate = document.createElement("div");
    gate.className = "nickname-gate";
    gate.setAttribute("role", "dialog");
    gate.setAttribute("aria-modal", "true");
    gate.setAttribute("aria-labelledby", "nickname-gate-title");
    gate.innerHTML =
      '<form class="nickname-gate__panel">' +
      '<h2 id="nickname-gate-title">스코어보드에 보일 이름을 정하세요</h2>' +
      '<p class="nickname-gate__hint">한 번 정하면 직접 바꿀 수 없습니다. 바꾸려면 운영진에게 말해 주세요.</p>' +
      '<input class="form-control" name="nickname" maxlength="20" autocomplete="off" required placeholder="이름 (20자 이하)">' +
      '<p class="nickname-gate__error" role="alert" hidden></p>' +
      '<button class="btn btn-primary" type="submit">이름 정하기</button>' +
      "</form>";
    document.body.appendChild(gate);
    var form = gate.querySelector("form");
    var input = gate.querySelector("input");
    var error = gate.querySelector(".nickname-gate__error");
    var button = gate.querySelector("button");
    input.focus();

    form.addEventListener("submit", function (event) {
      event.preventDefault();
      error.hidden = true;
      button.disabled = true;
      fetch("/participant/nickname", {
        method: "POST",
        credentials: "same-origin",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nickname: input.value })
      })
        .then(function (response) {
          return response.json().then(function (body) { return { ok: response.ok, body: body }; });
        })
        .then(function (result) {
          if (result.ok) {
            location.reload();
            return;
          }
          error.textContent = result.body.error || "이름을 저장하지 못했습니다.";
          error.hidden = false;
          button.disabled = false;
        })
        .catch(function () {
          error.textContent = "이름을 저장하지 못했습니다. 잠시 후 다시 시도하세요.";
          error.hidden = false;
          button.disabled = false;
        });
    });
  }

  function returnToContestAfterSubmit() {
    if (location.pathname !== CONTEST_ROOT) return false;
    try {
      if (sessionStorage.getItem("kaupc_return_to_contest") !== "1") return false;
      sessionStorage.removeItem("kaupc_return_to_contest");
    } catch (e) {
      return false;
    }
    location.replace(contestPath("/problems"));
    return true;
  }

  function enterContest(event) {
    event.preventDefault();
    var card = event.currentTarget;
    if (!/\/change-contest\//.test(card.href)) {
      location.assign(card.href);
      return;
    }
    rememberContest(card.dataset.contestName);
    rememberPendingContest(card.dataset.contestName);
    // 대회 선택은 DOMjudge 세션을 바꾸는 리다이렉트다. fetch 후 별도 이동하면
    // 세션 반영 전의 대회를 읽을 수 있어, 원래 리다이렉트를 그대로 따른다.
    location.assign(card.href);
  }

  function appendCurrentContestCard(grid, currentContest) {
    if (!currentContest) return;
    var alreadyVisible = Array.from(grid.querySelectorAll("h2")).some(function (heading) {
      return heading.textContent.trim().toLowerCase() === displayContestName(currentContest).toLowerCase();
    });
    if (alreadyVisible) return;
    var card = document.createElement("a");
    card.className = "contest-card";
    card.href = contestPath("/problems");
    card.dataset.contestName = currentContest;
    card.innerHTML = '<span class="contest-card__status">현재 대회</span><h2></h2><p>문제 풀기 · 제출하기 · 순위표 보기</p><span class="contest-card__action">대회로 돌아가기 <span aria-hidden="true">→</span></span>';
    card.querySelector("h2").textContent = displayContestName(currentContest);
    card.addEventListener("click", enterContest);
    grid.prepend(card);
  }

  function splitDashboardMeta(target) {
    var heading = Array.from(target.querySelectorAll(".teamoverview")).find(function (h) {
      return /^(Submissions|제출 현황)$/.test(h.textContent.trim());
    });
    if (!heading) return null;
    var row = heading.closest(".row");
    if (!row) return null;
    var cols = row.querySelectorAll(":scope > .col");
    if (cols.length < 2) return { submissions: cols[0] || null, clarifications: null };
    return { submissions: cols[0], clarifications: cols[1] };
  }

  function escHtml(s) {
    return String(s == null ? "" : s).replace(/[&<>"]/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;" }[c];
    });
  }

  // 질의응답은 공지·답변 목록과 내 질문 목록을 합쳐 게시판 한 장으로 보여 준다.
  // DOMjudge 표의 열 순서: time, from, to, subject, text (subject는 빠질 수 있다).
  var CLAR_KINDS = { notice: "공지", answer: "답변", mine: "내 질문" };

  function readClarificationRows(table, isRequest) {
    return Array.from(table.querySelectorAll("tbody tr")).map(function (tr) {
      var cells = tr.querySelectorAll("td");
      if (cells.length < 4) return null;
      var text = function (i) { return cells[i] ? cells[i].textContent.replace(/\s+/g, " ").trim() : ""; };
      var link = tr.querySelector("a[href]");
      var href = link ? link.getAttribute("href") : "";
      var id = Number((href.match(/clarifications\/(\d+)/) || [])[1] || 0);
      var to = text(2);
      var subject = cells.length >= 5 ? text(3) : "";
      subject = subject.replace(/^problem\s+/i, "");
      if (!subject || /^general$/i.test(subject)) subject = "일반";
      var kind = isRequest ? "mine" : (/^(All|전체)$/i.test(to) ? "notice" : "answer");
      return {
        id: id,
        href: href,
        time: text(0),
        subject: subject,
        body: text(cells.length >= 5 ? 4 : 3),
        kind: kind,
        unseen: tr.classList.contains("unseen")
      };
    }).filter(Boolean);
  }

  function buildClarificationBoard(root) {
    if (root.querySelector(".clar-board")) return;
    var rows = [];
    var isRequest = false;
    var addLink = root.querySelector('a[href$="/clarifications/add"]');
    Array.from(root.children).forEach(function (child) {
      if (child.matches("h1.teamoverview")) {
        isRequest = /Requests|내 질문/.test(child.textContent);
        return;
      }
      var table = child.matches("table") ? child : child.querySelector("table.data-table");
      if (table) rows = rows.concat(readClarificationRows(table, isRequest));
    });
    rows.sort(function (x, y) { return y.id - x.id; });

    var counts = { all: rows.length, notice: 0, answer: 0, mine: 0 };
    rows.forEach(function (row) { counts[row.kind] += 1; });

    var board = document.createElement("div");
    board.className = "clar-board";
    var filters = [["all", "전체"], ["notice", CLAR_KINDS.notice], ["answer", CLAR_KINDS.answer], ["mine", CLAR_KINDS.mine]]
      .map(function (f, i) {
        return '<button type="button" class="clar-board__filter' + (i === 0 ? " active" : "") + '" data-kind="' + f[0] + '">' +
          f[1] + ' <span class="clar-board__count">' + counts[f[0]] + "</span></button>";
      }).join("");
    var body = rows.map(function (row, index) {
      return '<tr class="clar-row' + (row.unseen ? " unseen" : "") + '" data-kind="' + row.kind + '">' +
        '<td class="clar-row__num">' + (rows.length - index) + "</td>" +
        '<td><span class="clar-kind clar-kind--' + row.kind + '">' + CLAR_KINDS[row.kind] + "</span></td>" +
        '<td class="clar-row__subject' + (row.subject === "일반" ? " clar-row__subject--general" : "") + '">' + escHtml(row.subject) + "</td>" +
        '<td class="clar-row__title"><a data-ajax-modal data-ajax-modal-after="markSeen" href="' + escHtml(row.href) + '">' +
        escHtml(row.body || "(내용 없음)") + "</a>" + (row.unseen ? '<span class="clar-row__new" aria-label="읽지 않음">N</span>' : "") + "</td>" +
        '<td class="clar-row__time">' + escHtml(row.time) + "</td></tr>";
    }).join("");
    board.innerHTML =
      '<div class="clar-board__toolbar"><div class="clar-board__filters" role="group" aria-label="글 분류">' + filters + "</div></div>" +
      '<table class="clar-board__table"><thead><tr><th class="clar-row__num">번호</th><th>분류</th><th>문제</th><th>내용</th><th class="clar-row__time">시간</th></tr></thead>' +
      "<tbody>" + (body || '<tr><td colspan="5" class="contest-clarifications__empty">등록된 글이 없습니다.</td></tr>') + "</tbody></table>";

    if (addLink) {
      addLink.className = "clar-board__write";
      addLink.textContent = "질문하기";
      board.querySelector(".clar-board__toolbar").appendChild(addLink);
    }

    board.addEventListener("click", function (event) {
      var filter = event.target.closest(".clar-board__filter");
      if (filter) {
        board.querySelectorAll(".clar-board__filter").forEach(function (b) { b.classList.toggle("active", b === filter); });
        var kind = filter.dataset.kind;
        board.querySelectorAll("tr.clar-row").forEach(function (tr) {
          tr.hidden = kind !== "all" && tr.dataset.kind !== kind;
        });
        return;
      }
      var row = event.target.closest("tr.clar-row");
      if (row && !event.target.closest("a")) {
        var anchor = row.querySelector("a[data-ajax-modal]");
        if (anchor) anchor.click();
      }
    });

    root.innerHTML = "";
    root.appendChild(board);
  }

  function beautifyClarifications(root) {
    buildClarificationBoard(root);
  }

  function buildContestDashboard(target, name) {
    rememberContest(name);
    document.body.classList.add("participant-portal");
    var meta = splitDashboardMeta(target);
    if (meta && meta.submissions) meta.submissions.remove();
    if (!meta || !meta.clarifications) {
      target.innerHTML = '<p class="contest-clarifications">해당 대회를 찾을 수 없습니다. <a href="/contest/problems">문제 목록으로</a></p>';
      return;
    }
    meta.clarifications.hidden = false;
    meta.clarifications.classList.add("contest-clarifications");
    beautifyClarifications(meta.clarifications);
    meta.clarifications.remove();
    target.innerHTML = "";
    target.appendChild(meta.clarifications);
    rewriteParticipantLinks(target);
    applyPageChrome();
    ensureContestPageTitle();
    injectContestTabs();
  }

  // 채점 현황: 운영자 화면의 제출 목록을 모두에게 보여 준다. 공개 대회의 제출만 보이고, 제출을 누르면 운영자 제출 상세와 같은 화면에서 코드와 테스트별 결과가 보인다.
  // 서버(Caddy)가 참가자 첫 화면을 빌려 주고, 그 위에 목록을 그린다. 몇 초마다 새로 불러온다.
  var VERDICTS = {
    AC: ["맞았습니다", "correct"], WA: ["틀렸습니다", "wrong"], TLE: ["시간 초과", "wrong"],
    RTE: ["런타임 에러", "wrong"], MLE: ["메모리 초과", "wrong"], OLE: ["출력 초과", "wrong"],
    CE: ["컴파일 에러", "compile"], NO: ["출력 없음", "wrong"]
  };

  function formatSubmissionTime(value) {
    var date = new Date(value);
    if (isNaN(date.getTime())) return value || "";
    // 대회 시각은 한국 시간이다. 보는 사람의 기기 시간대와 상관없이 같은 시각으로 보인다.
    var parts = {};
    new Intl.DateTimeFormat("en-US", {
      timeZone: "Asia/Seoul", month: "numeric", day: "numeric", hour: "2-digit", minute: "2-digit", second: "2-digit", hourCycle: "h23"
    }).formatToParts(date).forEach(function (part) { parts[part.type] = part.value; });
    return parts.month + "/" + parts.day + " " + parts.hour + ":" + parts.minute + ":" + parts.second;
  }

  function verdictLabel(verdict) {
    return (VERDICTS[verdict] || [verdict || "채점 중", verdict ? "wrong" : "pending"]);
  }

  // 운영자 제출 상세와 같은 표기.
  var CASE_LABELS = { AC: "정답", WA: "오답", TLE: "시간 초과", RTE: "실행 오류", MLE: "메모리 초과", OLE: "출력 초과", NO: "출력 없음" };

  var RUN_SECTIONS = [["diff", "채점기 메시지"], ["input", "입력"], ["answer", "정답"], ["output", "프로그램 출력"], ["error", "에러 출력"]];

  function renderRunData(container, id, ordinal, data) {
    container.replaceChildren();
    RUN_SECTIONS.forEach(function (entry) {
      var kind = entry[0];
      var value = data[kind] || {};
      if ((kind === "diff" || kind === "error") && !value.text) return;
      var head = document.createElement("h4");
      head.textContent = entry[1];
      if (kind === "input" || kind === "answer" || kind === "output") {
        var link = document.createElement("a");
        link.href = "/participant/submissions/" + encodeURIComponent(id) + "/runs/" + ordinal + "/" + kind;
        link.textContent = "내려받기";
        head.appendChild(link);
      }
      var pre = document.createElement("pre");
      pre.textContent = value.text || "(비어 있음)";
      container.append(head, pre);
      if (value.truncated) {
        var note = document.createElement("p");
        note.className = "contest-status__cut";
        note.textContent = "앞 64KB만 보입니다. 전체 " + value.size + "바이트는 내려받으세요.";
        container.appendChild(note);
      }
    });
  }

  function renderRunPanel(id, run, open) {
    var panel = document.createElement("details");
    panel.className = "contest-status__run-panel";
    var title = document.createElement("summary");
    var kind = verdictLabel(run.verdict)[1];
    title.className = "contest-status__verdict--" + kind;
    title.textContent = "테스트 #" + run.ordinal + " · " + (CASE_LABELS[run.verdict] || run.verdict) +
      (typeof run.runtime === "number" ? " · " + Math.round(run.runtime * 1000) + " ms" : "");
    var body = document.createElement("div");
    body.textContent = "불러오는 중…";
    panel.append(title, body);
    var loaded = false;
    panel.addEventListener("toggle", function () {
      if (!panel.open || loaded) return;
      loaded = true;
      fetch("/participant/submissions/" + encodeURIComponent(id) + "/runs/" + run.ordinal, { credentials: "same-origin", cache: "no-store" })
        .then(function (response) { if (!response.ok) throw new Error(); return response.json(); })
        .then(function (data) { renderRunData(body, id, run.ordinal, data); })
        .catch(function () { loaded = false; body.textContent = "입출력을 불러오지 못했습니다. 다시 열어 보세요."; });
    });
    panel.open = open;
    return panel;
  }

  function renderSubmissionDetail(detail, parts) {
    parts.title.textContent = "제출 #" + detail.id;
    parts.summary.replaceChildren();
    [
      "참가자 " + detail.team,
      "문제 " + detail.problem + (detail.problem_name ? " - " + detail.problem_name : ""),
      "언어 " + detail.language,
      "제출 시각 " + formatSubmissionTime(detail.time)
    ].forEach(function (text) {
      var item = document.createElement("span");
      item.textContent = text;
      parts.summary.appendChild(item);
    });
    var label = verdictLabel(detail.verdict);
    var result = document.createElement("span");
    result.className = "contest-status__verdict contest-status__verdict--" + label[1];
    result.textContent = label[0];
    parts.summary.appendChild(result);

    parts.heading.textContent = "제출 코드 · #" + detail.id;
    parts.source.replaceChildren();
    (detail.sources || []).forEach(function (source) {
      var filename = document.createElement("h3");
      filename.textContent = source.filename || "";
      var pre = document.createElement("pre");
      pre.textContent = source.source || "(빈 소스 파일)";
      parts.source.append(filename, pre);
    });

    parts.compileText.textContent = detail.compile_output || "";
    parts.compile.hidden = !detail.compile_output;

    var runs = detail.runs || [];
    var total = Math.max(typeof detail.tests === "number" ? detail.tests : 0, runs.length);
    if (detail.verdict === "CE") {
      parts.status.textContent = "컴파일 에러로 테스트를 실행하지 않았습니다.";
      total = 0;
    } else if (!total) {
      parts.status.textContent = "채점 대기 중입니다.";
    } else {
      parts.status.textContent = (detail.verdict ? "테스트 결과 · " : "채점 중 · ") + runs.length + "/" + total + " 처리 (나머지는 대기 또는 미실행)";
    }
    parts.cases.replaceChildren();
    parts.times.replaceChildren();
    var firstFailureShown = false;
    for (var index = 0; index < total; index++) {
      var run = runs[index];
      var badge = document.createElement("span");
      var kind = run ? verdictLabel(run.verdict)[1] : "pending";
      badge.className = "badge jury-case-badge " + (kind === "correct" ? "text-bg-success" : kind === "pending" ? "text-bg-secondary" : "text-bg-danger");
      badge.textContent = "#" + (index + 1) + " " + (run ? CASE_LABELS[run.verdict] || run.verdict : "대기");
      parts.cases.appendChild(badge);
      if (!run) continue;
      // 틀린 테스트 하나는 처음부터 열어 둔다.
      var openThis = run.verdict !== "AC" && !firstFailureShown;
      if (openThis) firstFailureShown = true;
      parts.times.appendChild(renderRunPanel(detail.id, run, openThis));
    }
    parts.diagnostics.hidden = !runs.length;
  }

  function buildSubmissionPage(section, id) {
    section.innerHTML =
      '<p class="contest-status__back"><a href="/contest/status">← 채점 현황</a></p>' +
      '<h1 class="contest-page-title"></h1>' +
      '<div class="contest-status__meta" role="status">불러오는 중…</div>' +
      '<section class="jury-code-first"><h2></h2><div class="contest-status__sources"></div>' +
      '<section class="contest-status__compile" hidden><h3>컴파일 결과</h3><pre></pre></section>' +
      '<section class="jury-live-results"><p class="contest-status__progress"></p><div class="jury-case-results"></div>' +
      '<button type="button" class="btn btn-outline-secondary btn-sm"></button></section></section>' +
      '<details class="contest-status__diagnostics" open hidden><summary>상세 진단 · 테스트별 입출력</summary>' +
      '<div class="contest-status__run-panels"></div></details>';
    var parts = {
      title: section.querySelector("h1"),
      summary: section.querySelector(".contest-status__meta"),
      heading: section.querySelector(".jury-code-first h2"),
      source: section.querySelector(".contest-status__sources"),
      status: section.querySelector(".contest-status__progress"),
      cases: section.querySelector(".jury-case-results"),
      times: section.querySelector(".contest-status__run-panels"),
      compile: section.querySelector(".contest-status__compile"),
      compileText: section.querySelector(".contest-status__compile pre"),
      diagnostics: section.querySelector(".contest-status__diagnostics")
    };
    parts.title.textContent = "제출 #" + id;
    var refresh = section.querySelector(".jury-live-results button");
    refresh.textContent = "결과 새로고침";
    var timer = null;
    var shown = null;
    function load() {
      fetch("/participant/submissions/" + encodeURIComponent(id), { credentials: "same-origin", cache: "no-store" })
        .then(function (response) { if (!response.ok) throw new Error(); return response.json(); })
        .then(function (detail) {
          // 내용이 그대로면 다시 그리지 않는다. 열어 둔 입출력이 닫히면 안 된다.
          var next = JSON.stringify(detail);
          if (next !== shown) {
            shown = next;
            renderSubmissionDetail(detail, parts);
          }
          // 채점이 끝나면 더 부르지 않는다. 코드를 고르는 중에 선택이 풀리면 안 된다.
          if (detail.verdict && timer) { clearInterval(timer); timer = null; }
        })
        .catch(function () {
          parts.summary.textContent = "제출을 불러오지 못했습니다. 공개 대회의 최근 제출만 볼 수 있습니다.";
          if (timer) { clearInterval(timer); timer = null; }
        });
    }
    refresh.addEventListener("click", load);
    load();
    timer = setInterval(load, 5000);
  }

  // 운영자 제출 목록과 같은 표기. 실행하지 않은 테스트는 회색 ?로 남는다.
  var CASE_MARKS = { AC: "✓", WA: "w", TLE: "t", RTE: "r", MLE: "m", OLE: "o", NO: "n" };

  function renderCaseBadges(td, row) {
    td.className = "contest-status__cases";
    if (row.verdict === "CE") return;
    var cases = row.cases || [];
    var total = Math.max(typeof row.tests === "number" ? row.tests : 0, cases.length);
    for (var index = 0; index < total; index++) {
      var verdict = cases[index];
      var badge = document.createElement("span");
      badge.className = "contest-status__case contest-status__case--" + (verdict ? verdictLabel(verdict)[1] : "pending");
      badge.textContent = verdict ? CASE_MARKS[verdict] || verdict.charAt(0).toLowerCase() : "?";
      badge.title = (index + 1) + "번 " + (verdict ? verdictLabel(verdict)[0] : "실행 안 함");
      td.appendChild(badge);
    }
  }

  function renderStatusRows(tbody, rows) {
    tbody.innerHTML = "";
    if (!rows.length) {
      tbody.innerHTML = '<tr><td colspan="8" class="contest-status__empty">아직 제출이 없습니다.</td></tr>';
      return;
    }
    rows.forEach(function (row) {
      var tr = document.createElement("tr");
      var verdict = VERDICTS[row.verdict] || (row.verdict ? [row.verdict, "wrong"] : ["채점 중", "pending"]);
      var cells = [
        String(row.id),
        formatSubmissionTime(row.time),
        row.team,
        row.problem,
        row.language,
        verdict[0],
        "",
        typeof row.runtime === "number" && row.verdict ? Math.round(row.runtime * 1000) + " ms" : ""
      ];
      cells.forEach(function (text, index) {
        var td = document.createElement("td");
        if (index === 0) {
          var open = document.createElement("a");
          open.className = "contest-status__open";
          open.href = "/contest/status/" + encodeURIComponent(row.id);
          open.textContent = text;
          td.appendChild(open);
        } else {
          td.textContent = text;
        }
        if (index === 3 && row.problem_name) td.title = row.problem_name;
        if (index === 6) renderCaseBadges(td, row);
        if (index === 5) td.className = "contest-status__verdict contest-status__verdict--" + verdict[1];
        tr.appendChild(td);
      });
      tr.addEventListener("click", function (event) {
        if (!event.target.closest("a")) location.assign(tr.querySelector("a").href);
      });
      tbody.appendChild(tr);
    });
  }

  function buildStatusPage() {
    if (!isStatusPage()) return false;
    var target = pageTarget() || document.querySelector("body > .container, body > .container-fluid");
    if (!target || document.querySelector(".contest-status")) return true;
    target.removeAttribute("data-ajax-refresh-target");
    target.removeAttribute("data-ajax-refresh-after");
    document.body.classList.add("participant-portal");
    var section = document.createElement("section");
    section.className = "contest-status contest-shell";
    var submission = location.pathname.match(/^\/contest\/status\/([0-9]+)$/);
    if (submission) {
      target.innerHTML = "";
      target.appendChild(section);
      buildSubmissionPage(section, submission[1]);
      return true;
    }
    section.innerHTML =
      '<h1 class="contest-page-title">채점 현황</h1>' +
      '<p class="contest-status__note" role="status">불러오는 중…</p>' +
      '<div class="table-responsive"><table class="table table-sm contest-status__table">' +
      "<thead><tr><th>제출 번호</th><th>제출 시각</th><th>참가자</th><th>문제</th><th>언어</th><th>결과</th><th>테스트 결과</th><th>시간</th></tr></thead>" +
      "<tbody></tbody></table></div>";
    target.innerHTML = "";
    target.appendChild(section);
    var note = section.querySelector(".contest-status__note");
    var tbody = section.querySelector("tbody");
    var inFlight = false;
    var rows = [];
    var drawn = null;
    function load() {
      if (inFlight || document.hidden) return;
      inFlight = true;
      fetch("/participant/submissions", { credentials: "same-origin", cache: "no-store" })
        .then(function (response) { if (!response.ok) throw new Error(); return response.json(); })
        .then(function (body) {
          rows = body.submissions || [];
          // 목록이 그대로면 다시 그리지 않는다.
          var next = JSON.stringify(rows);
          if (next !== drawn) {
            drawn = next;
            renderStatusRows(tbody, rows);
          }
          note.textContent = "공개 대회의 모든 제출입니다. 최근 " + (body.submissions || []).length + "개, 몇 초마다 새로 고칩니다.";
        })
        .catch(function () { note.textContent = "채점 현황을 불러오지 못했습니다. 잠시 후 다시 시도하세요."; })
        .finally(function () { inFlight = false; });
    }
    load();
    setInterval(load, 5000);
    return true;
  }

  function buildContestLobby() {
    if (location.pathname !== CONTEST_ROOT && !isClarificationsPage()) return;
    var target = pageTarget();
    if (!target || target.dataset.contestLobby === "true") return;

    target.dataset.contestLobby = "true";
    target.removeAttribute("data-ajax-refresh-target");
    target.removeAttribute("data-ajax-refresh-after");

    var selectedContest = new URLSearchParams(location.search).get("contest");
    if (isClarificationsPage()) {
      buildContestDashboard(target, selectedContest || recalledContest());
      return;
    }
    // 참가할 수 있는 대회가 하나뿐이면 DOMjudge는 대회 전환 링크를 그리지 않는다.
    // 그래도 로비는 만들고, 아래에서 현재 대회 카드를 붙인다.
    var links = contestLinks();
    if (selectedContest) {
      buildContestDashboard(target, selectedContest);
      return;
    }

    if (location.hash === "#clarifications") {
      resolveContestName(function (contest) {
        if (contest) history.replaceState({}, "", contestPath("?contest=") + encodeURIComponent(contest) + "#clarifications");
        buildContestDashboard(target, contest || "");
      });
      return;
    }

    target.innerHTML = "";
    var lobby = document.createElement("main");
    lobby.className = "contest-lobby";
    lobby.innerHTML = '<header class="contest-lobby__header"><p class="contest-lobby__eyebrow">KAUPC 2026</p><h1>대회 응시하기</h1></header><section class="contest-lobby__grid" aria-label="참가 가능한 대회"></section>';
    var grid = lobby.querySelector(".contest-lobby__grid");

    links.forEach(function (link) {
      var card = document.createElement("a");
      card.className = "contest-card";
      card.href = contestUrl(link.href);
      card.dataset.contestName = contestName(link);
      card.innerHTML = '<span class="contest-card__status">참가 가능</span><h2></h2><p>문제 풀기 · 제출하기 · 순위표 보기</p><span class="contest-card__action">대회 입장 <span aria-hidden="true">→</span></span>';
      card.querySelector("h2").textContent = displayContestName(card.dataset.contestName);
      card.addEventListener("click", enterContest);
      grid.appendChild(card);
    });
    resolveContestName(function (currentContest) {
      appendCurrentContestCard(grid, currentContest);
      showContestAvailability();
      if (!grid.children.length) {
        grid.innerHTML = '<p class="contest-lobby__empty">참가할 수 있는 대회가 없습니다. 운영진에게 알려 주세요.</p>';
      }
    });
    target.appendChild(lobby);
  }

  // 상단 바의 홈·문제 목록·순위표·제출 버튼은 대회 탭과 문제 표가 이미 제공한다. 로그아웃과 남은 시간만 남긴다.
  function markParticipantNavigation() {
    if (isContestPath()) document.body.classList.add("participant-nav");
  }

  function removeContestSwitcher() {
    if (!isContestPath()) return;
    var trigger = document.getElementById("navbarDropdownContests");
    if (!trigger) return;
    var navItem = trigger.closest("li");
    if (navItem) navItem.remove();
  }

  function copySampleText(pre, button) {
    var text = pre.textContent;
    var done = function (ok) {
      var original = button.textContent;
      button.textContent = ok ? "복사됨" : "복사 실패";
      window.setTimeout(function () {
        button.textContent = original;
      }, 1500);
    };
    var fallbackCopy = function () {
      var area = document.createElement("textarea");
      area.value = text;
      area.style.position = "fixed";
      area.style.opacity = "0";
      document.body.appendChild(area);
      area.select();
      var ok = false;
      try {
        ok = document.execCommand("copy");
      } catch (e) {
        ok = false;
      }
      area.remove();
      done(ok);
    };
    if (navigator.clipboard && navigator.clipboard.writeText) {
      navigator.clipboard.writeText(text).then(function () {
        done(true);
      }, fallbackCopy);
      return;
    }
    fallbackCopy();
  }

  function addSampleCopyButtons(root) {
    root.querySelectorAll(".sample-pane").forEach(function (pane) {
      var pre = pane.querySelector("pre");
      var label = pane.querySelector(".sample-label");
      if (!pre || !label) return;
      var button = document.createElement("button");
      button.type = "button";
      button.className = "sample-copy";
      button.textContent = "복사";
      button.addEventListener("click", function () {
        copySampleText(pre, button);
      });
      label.after(button);
    });
  }

  function buildStatementChrome(statement, label) {
    statement.classList.add("contest-statement");
    var eyebrow = statement.querySelector(".problem-eyebrow");
    var contest = currentContestFromMenu() || recalledContest();
    if (eyebrow && contest && label) {
      eyebrow.textContent = displayContestName(contest) + " · " + label;
    }
    return statement;
  }

  function buildProblemTable() {
    if (!isStatementPage()) return;
    var list = document.querySelector(".problem-list");
    if (!list || list.dataset.problemTable === "true") return;

    var rows = Array.from(list.children).map(function (column) {
      var card = column.querySelector(".card");
      var label = card.querySelector(".card-title").textContent.trim();
      var name = card.querySelector(".card-subtitle").textContent.trim();
      var limit = card.querySelectorAll(".card-subtitle")[1].textContent.trim();
      var statement = card.querySelector('a[href*="/statement"]');
      var submit = card.querySelector('a[href*="/submit/"]');
      return { label: label, name: name, limit: limit, statement: statement, submit: submit };
    });

    var table = document.createElement("table");
    table.className = "problem-table";
    table.innerHTML = "<thead><tr><th>번호</th><th>문제</th><th>제한</th><th>제출</th></tr></thead><tbody></tbody>";
    var body = table.querySelector("tbody");
    rows.forEach(function (problem) {
      var row = document.createElement("tr");
      row.innerHTML = "<td></td><td><a class=\"problem-app__open\"></a></td><td></td><td></td>";
      row.children[0].textContent = problem.label;
      var title = row.querySelector("a");
      title.textContent = problem.name;
      if (problem.statement) {
        title.href = problem.statement.href;
      } else {
        title.removeAttribute("href");
        title.classList.remove("problem-app__open");
        title.title = "지문이 아직 등록되지 않았습니다.";
      }
      title.dataset.label = problem.label;
      title.dataset.name = problem.name;
      if (problem.submit) title.dataset.submitHref = problem.submit.href;
      row.children[2].textContent = problem.limit;
      if (problem.submit) {
        var submit = document.createElement("a");
        submit.href = problem.submit.href;
        submit.className = "problem-table__submit";
        submit.textContent = "제출";
        row.children[3].appendChild(submit);
      }
      body.appendChild(row);
    });

    var app = document.createElement("div");
    app.className = "problem-app";
    var listView = document.createElement("div");
    listView.className = "problem-app__list";
    listView.appendChild(table);
    var detailView = document.createElement("div");
    detailView.className = "problem-app__detail";
    detailView.hidden = true;
    app.appendChild(listView);
    app.appendChild(detailView);
    list.replaceWith(app);

    var heading = document.querySelector("h1");
    var headingDefault = heading ? heading.textContent : "";
    var listUrl = location.pathname;

    function showList(push) {
      detailView.hidden = true;
      detailView.innerHTML = "";
      listView.hidden = false;
      if (heading) heading.textContent = headingDefault;
      if (push) history.pushState({}, "", listUrl);
    }

    function showDetail(url, submitHref, label, name, push) {
      // 이 헤더가 있으면 Caddy가 지문 주소를 문제 목록으로 돌려보내지 않는다.
      return fetch(url, { credentials: "same-origin", headers: { "X-Kaupc-Fetch": "statement" } })
        .then(function (response) {
          if (!response.ok) throw new Error("statement request failed");
          return response.text();
        })
        .then(function (html) {
          var parsed = new DOMParser().parseFromString(html, "text/html");
          var statement = parsed.querySelector(".problem-statement");
          if (!statement) throw new Error("statement missing");
          // 목록으로 돌아가기와 제출은 위쪽 대회 탭이 맡는다. 지문 위에는 따로 메뉴를 두지 않는다.
          detailView.innerHTML = "";
          var statementView = buildStatementChrome(document.importNode(statement, true), label);
          detailView.appendChild(statementView);
          addSampleCopyButtons(detailView);
          listView.hidden = true;
          detailView.hidden = false;
          if (heading) heading.textContent = label ? label + " · " + name : headingDefault;
          window.scrollTo(0, 0);
          if (push) history.pushState({ problemStatement: url, submitHref: submitHref, label: label, name: name }, "", listUrl + "?statement=" + encodeURIComponent(url.match(/\/problems\/([^/]+)\/statement/) ? url.match(/\/problems\/([^/]+)\/statement/)[1] : ""));
        })
        .catch(function () {
          detailView.innerHTML = '<p class="problem-detail__error">지문을 불러오지 못했습니다. 잠시 후 다시 시도하세요.</p>';
          listView.hidden = true;
          detailView.hidden = false;
        });
    }

    listView.addEventListener("click", function (event) {
      var link = event.target.closest("a.problem-app__open");
      if (!link || event.metaKey || event.ctrlKey || event.shiftKey) return;
      event.preventDefault();
      showDetail(link.href, link.dataset.submitHref, link.dataset.label, link.dataset.name, true);
    });

    window.addEventListener("popstate", function (event) {
      if (!document.body.contains(app)) return;
      if (event.state && event.state.problemStatement) {
        showDetail(event.state.problemStatement, event.state.submitHref, event.state.label, event.state.name, false);
      } else {
        showList(false);
      }
    });

    var statementId = new URLSearchParams(location.search).get("statement");
    if (statementId) {
      var problem = rows.find(function (row) {
        return row.statement && new RegExp("/problems/" + statementId.replace(/[.*+?^${}()|[\]\\]/g, "\\$&") + "/statement$").test(new URL(row.statement.href, location.origin).pathname);
      });
      if (problem) showDetail(problem.statement.href, problem.submit && problem.submit.href, problem.label, problem.name, false);
    }
  }

  function tabsAnchor() {
    var boxed = document.querySelector(".submitform");
    if (boxed) return boxed;
    var heading = document.querySelector("h1");
    if (heading) return heading;
    var container = document.querySelector("body > .container, body > .container-fluid");
    return container ? container.firstElementChild : null;
  }

  function pageTitle() {
    if (location.pathname === contestPath("/problems")) return "문제";
    if (location.pathname === contestPath("/submit")) return "제출";
    if (location.pathname === contestPath("/scoreboard")) return "순위표";
    if (location.pathname.indexOf(contestPath("/submission/")) === 0) return "제출 결과";
    if (isStatusPage()) return "채점 현황";
    return "질의응답";
  }

  function applyPageChrome() {
    if (!isContestPath() || location.pathname === CONTEST_ROOT) return;
    document.body.classList.add("participant-portal");
    var heading = document.querySelector(".submitform h1, h1");
    if (heading) {
      heading.textContent = pageTitle();
      heading.classList.add("contest-page-title");
    }
    document.querySelectorAll(".problem-app, .submitform, .contest-clarifications").forEach(function (element) {
      element.classList.add("contest-shell");
    });
    // 순위표는 DOMjudge가 몇 초마다 [data-ajax-refresh-target]의 내용을 통째로 바꾼다.
    // 그래서 안쪽을 감싸지 않고, 바뀌지 않는 그 틀 자체를 상자로 쓴다.
    if (location.pathname === contestPath("/scoreboard")) {
      var refreshTarget = document.querySelector("[data-ajax-refresh-target]");
      if (refreshTarget) refreshTarget.classList.add("contest-shell", "scoreboard-shell");
    }
  }

  function ensureContestPageTitle() {
    var needsTitle = location.pathname === contestPath("/scoreboard") || location.pathname === contestPath("/submit") ||
      isClarificationsPage() || location.hash === "#clarifications";
    if (!needsTitle) return;
    var existing = document.querySelector(".contest-page-title");
    if (existing && !existing.closest(".contest-shell")) return;
    var shell = document.querySelector(".contest-clarifications, .scoreboard-shell, .submitform");
    if (!shell) return;
    var title = document.createElement("h1");
    title.className = "contest-page-title";
    title.textContent = pageTitle();
    shell.before(title);
  }

  function cleanScoreboard() {
    if (location.pathname !== contestPath("/scoreboard")) return;
    var lastModified = document.querySelector(".lastmod");
    if (lastModified) lastModified.textContent = lastModified.textContent.replace(/using\s+DOMjudge/i, "").trim();
    compactScoreCells(document);
    // DOMjudge는 순위표를 주기적으로 새로 받아 표를 통째로 갈아 끼운다. 바뀔 때마다 다시 줄인다.
    new MutationObserver(function () { compactScoreCells(document); })
      .observe(document.body, { childList: true, subtree: true });
  }

  // BOJ 순위표처럼 칸에는 시도 횟수와 맞힌 시각만 남긴다.
  // 맞힘: 위 "+틀린 횟수"(처음에 맞히면 비움), 아래 맞힌 시각(분). 못 맞힘: "-시도 횟수". 채점 중: "?".
  function compactScoreLabel(className, timeText, triesText) {
    var counts = (triesText || "").match(/(\d+)(?:\s*\+\s*(\d+))?/);
    var tries = counts ? parseInt(counts[1], 10) : 0;
    if (/\bscore_correct\b/.test(className)) {
      return { main: tries > 1 ? "+" + (tries - 1) : "", sub: (timeText || "").trim() };
    }
    if (/\bscore_pending\b/.test(className)) return { main: "?", sub: "" };
    return { main: tries ? "-" + tries : "", sub: "" };
  }

  function compactScoreCells(root) {
    Array.prototype.forEach.call(root.querySelectorAll(".score_cell > a > div"), function (cell) {
      if (cell.dataset.compact === "true") return;
      var tries = cell.querySelector("span");
      var time = Array.prototype.filter.call(cell.childNodes, function (node) { return node.nodeType === 3; })
        .map(function (node) { return node.textContent; }).join("").replace(/ /g, " ");
      var label = compactScoreLabel(cell.className, time, tries ? tries.textContent : "");
      cell.dataset.compact = "true";
      cell.innerHTML = "";
      var main = document.createElement("strong");
      main.className = "score-cell__tries";
      main.textContent = label.main;
      cell.appendChild(main);
      if (label.sub) {
        var sub = document.createElement("span");
        sub.className = "score-cell__time";
        sub.textContent = label.sub;
        cell.appendChild(sub);
      }
    });
  }

  function translateSubmissionDetail() {
    var replacements = {
      "Submission details": "제출 정보",
      "Problem:": "문제",
      "Submitted:": "제출 시각",
      "Language:": "언어",
      "Result:": "결과",
      "Compilation successful with the following output": "컴파일에 성공했습니다.",
      "There were no compiler errors or warnings.": "컴파일 에러나 경고가 없습니다."
    };
    var walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    var nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(function (node) {
      var text = node.nodeValue.trim();
      if (replacements[text]) node.nodeValue = node.nodeValue.replace(text, replacements[text]);
    });
    document.querySelectorAll("h1, h2, h3, h4, h5, h6").forEach(function (heading) {
      if (/^Compilation\s+successful\s+with\s+the\s+following\s+output$/i.test(heading.textContent.trim())) {
        heading.textContent = "컴파일 결과";
      }
    });
  }

  function formatExecutionMetrics(detail) {
    var labels = [
      { key: "시간", pattern: /^(?:Run time|Runtime|실행 시간|시간)\s*:?\s*(.+)$/i },
      { key: "메모리", pattern: /^(?:Memory|Memory usage|메모리(?: 사용량)?)\s*:?\s*(.+)$/i }
    ];
    var values = [];
    detail.querySelectorAll("[data-runtime], [data-memory], td, dd, p, div").forEach(function (element) {
      labels.forEach(function (label) {
        var value = element.dataset[label.key === "시간" ? "runtime" : "memory"] || (element.children.length === 0 && (element.textContent || "").trim().match(label.pattern) || [])[1];
        if (value && !values.some(function (entry) { return entry.key === label.key; })) values.push({ key: label.key, value: value.trim() });
      });
    });
    if (!values.length) return;
    var metrics = document.createElement("dl");
    metrics.className = "submission-metrics";
    values.forEach(function (entry) {
      var term = document.createElement("dt");
      term.textContent = entry.key;
      var definition = document.createElement("dd");
      definition.textContent = entry.value;
      metrics.append(term, definition);
    });
    detail.prepend(metrics);
  }

  function structureSubmissionDetail() {
    if (location.pathname.indexOf(contestPath("/submission/")) !== 0) return;
    var detail = document.querySelector(".col-12 > .container");
    if (!detail || detail.classList.contains("submission-detail")) return;
    detail.classList.add("submission-detail", "contest-shell");
    detail.querySelectorAll(".d-flex.flex-row").forEach(function (row) {
      row.classList.add("submission-detail__facts");
    });
    formatExecutionMetrics(detail);
    attachSubmissionCode(detail, submissionIdFrom(location.pathname));
  }

  // 제출 상세(페이지와 모달)에 제출한 코드를 붙인다.
  // DOMjudge 설정 allow_team_submission_download가 켜져 있어야 내려받을 수 있다.
  var lastSubmissionId = null;

  function submissionIdFrom(href) {
    var match = String(href || "").match(/\/submission\/(\d+)/);
    return match ? match[1] : null;
  }

  function attachSubmissionCode(container, submitId) {
    if (!container || !submitId || container.querySelector(".submission-code")) return;
    var section = document.createElement("section");
    section.className = "submission-code";
    section.innerHTML = '<div class="submission-code__head"><h6>제출한 코드</h6><span class="submission-code__name"></span></div>' +
      '<pre class="submission-code__source">불러오는 중…</pre>';
    container.appendChild(section);
    var pre = section.querySelector("pre");
    var url = contestPath("/submission/" + submitId + "/download");
    fetch(url, { credentials: "same-origin" })
      .then(function (response) {
        if (!response.ok) throw new Error(response.status === 404 ? "disabled" : "failed");
        var type = response.headers.get("Content-Type") || "";
        var disposition = response.headers.get("Content-Disposition") || "";
        var name = (disposition.match(/filename="?([^";]+)"?/) || [])[1] || "";
        if (/zip/i.test(type)) return { zip: true, name: name };
        return response.text().then(function (text) { return { text: text, name: name }; });
      })
      .then(function (result) {
        section.querySelector(".submission-code__name").textContent = result.name;
        if (result.zip) {
          pre.outerHTML = '<p class="submission-code__note">파일이 여러 개인 제출입니다. <a href="' + escHtml(url) + '">내려받아 확인하세요.</a></p>';
          return;
        }
        pre.textContent = result.text.replace(/\n$/, "");
        var button = document.createElement("button");
        button.type = "button";
        button.className = "sample-copy submission-code__copy";
        button.textContent = "복사";
        button.addEventListener("click", function () { copySampleText(pre, button); });
        section.querySelector(".submission-code__head").appendChild(button);
      })
      .catch(function (error) {
        pre.outerHTML = '<p class="submission-code__note">' +
          (error.message === "disabled" ? "코드 보기가 꺼져 있습니다. 운영진에게 문의하세요." : "코드를 불러오지 못했습니다.") + "</p>";
      });
  }

  function watchSubmissionModals() {
    if (!isContestPath()) return;
    // DOMjudge 모달은 누른 링크의 data-ajax-modal-after 함수를 부른다. 제출 화면에는 markSeen이 없어 오류가 나므로 채워 둔다.
    if (typeof window.markSeen !== "function") {
      window.markSeen = function ($elem) {
        if ($elem && $elem.closest) $elem.closest("tr").removeClass("unseen");
      };
    }
    document.addEventListener("click", function (event) {
      var link = event.target.closest && event.target.closest('a[href*="/submission/"]');
      var id = link && submissionIdFrom(link.getAttribute("href"));
      if (id && !/\/download$/.test(link.getAttribute("href"))) lastSubmissionId = id;
    }, true);
    new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeType !== 1 || !node.classList.contains("modal")) return;
          var body = node.querySelector(".modal-body");
          if (!body || !body.querySelector(".probid")) return;
          var download = body.querySelector('a[href*="/download"]');
          var id = (download && submissionIdFrom(download.getAttribute("href"))) || lastSubmissionId;
          attachSubmissionCode(body.querySelector(".container") || body, id);
        });
      });
    }).observe(document.body, { childList: true });
  }

  function injectSubmissionHistory() {
    var form = document.querySelector(".submitform");
    if (!form) return;
    fetch(contestPath(""), { credentials: "same-origin" })
      .then(function (response) {
        return response.ok ? response.text() : "";
      })
      .then(function (html) {
        if (!html) return;
        var parsed = new DOMParser().parseFromString(html, "text/html");
        var heading = Array.from(parsed.querySelectorAll(".teamoverview")).find(function (h) {
          return /^(Submissions|제출 현황)$/.test(h.textContent.trim());
        });
        if (!heading) return;
        var table = heading.nextElementSibling;
        var section = document.createElement("div");
        section.className = "submission-history";
        section.appendChild(document.importNode(heading, true));
        if (table) section.appendChild(document.importNode(table, true));
        form.appendChild(section);
        rewriteParticipantLinks(section);
      })
      .catch(function () {
        /* history is best-effort */
      });
  }

  function injectContestTabs() {
    var onClarifications = (location.pathname === CONTEST_ROOT || isClarificationsPage()) && document.querySelector(".contest-clarifications");
    var onStatus = isStatusPage() && document.querySelector(".contest-status");
    if ((!isContestPage() && !onClarifications) || document.querySelector(".contest-tabs")) return;
    var anchor = onClarifications ? document.querySelector(".contest-clarifications") : onStatus ? onStatus : tabsAnchor();
    if (!anchor) return;
    // 탭은 모든 화면에서 페이지 제목보다 위에 둔다.
    var previous = anchor.previousElementSibling;
    if (previous && previous.classList.contains("contest-page-title")) anchor = previous;
    var tabs = document.createElement("nav");
    tabs.className = "contest-tabs";
    tabs.setAttribute("aria-label", "대회 메뉴");
    tabs.innerHTML = '<a href="/contest/problems">문제 목록</a><a href="/contest/submit">제출</a><a href="/contest/status">채점 현황</a><a href="/contest/scoreboard">순위표</a><a href="/contest/clarifications" class="active">질의응답</a>';
    if (!onClarifications) {
      tabs.querySelector('a[href="/contest/clarifications"]').classList.remove("active");
      tabs.querySelectorAll("a").forEach(function (tab) {
        if (tab.pathname === location.pathname || (onStatus && tab.pathname === "/contest/status")) tab.classList.add("active");
      });
    }
    anchor.before(tabs);
    var qna = tabs.querySelector('a[href="/contest/clarifications"]');
    if (qna) qna.href = clarificationsPath();
  }

  // 참가자가 보는 곳에서는 DOMjudge 대신 KAUPC 2026으로 부른다. 운영자 화면은 그대로 둔다.
  function applyKaupcBrand() {
    if (location.pathname.indexOf("/jury") === 0) return;
    document.title = location.pathname === "/login"
      ? "로그인 - KAUPC 2026"
      : document.title.replace(/DOMjudge/g, "KAUPC 2026");
    var brand = document.querySelector(".navbar-brand");
    if (brand && /DOMjudge/.test(brand.textContent)) brand.textContent = "KAUPC 2026";
  }

  // 공개 대회에는 로그인 화면이 없다. 로그인 화면으로 가는 요청은 nginx가 받아 서버에서 게스트로 로그인시킨다
  // (custom/nginx/domjudge-site.conf). 여기서는 따로 할 일이 없다.

  function redirectAnonymousPublicToLogin() {
    if (location.pathname !== "/public") return;
    if (document.querySelector('a[href="/login"]')) location.replace(CONTEST_ROOT);
  }

  function showContestAvailability() {
    if (!isContestPath()) return;
    var clock = document.getElementById("timeleft");
    var beforeStart = typeof window.starttime === "number" && typeof window.initial === "number" && window.initial < window.starttime;
    var afterEnd = typeof window.endtime === "number" && typeof window.initial === "number" && window.initial >= window.endtime;
    if (afterEnd) {
      document.querySelectorAll('.submitform').forEach(function (form) {
        var notice = document.createElement("section");
        notice.className = "contest-availability contest-shell";
        notice.innerHTML = '<h2>대회가 종료되었습니다</h2><p>제출이 마감되었습니다. 문제와 순위표는 계속 확인할 수 있습니다.</p><a href="/contest/problems">문제 목록으로 돌아가기 →</a>';
        form.replaceWith(notice);
      });
    } else if (!beforeStart && typeof window.endtime === "number" && typeof window.initial === "number" && location.pathname.indexOf(contestPath("/submit")) === 0) {
      setTimeout(function () { location.reload(); }, Math.max(1000, (window.endtime - window.initial) * 1000 + 1000));
    }
    if (clock) {
      function translateClock() {
        var text = clock.textContent;
        var translated = text.replace(/time to start:\s*/i, "시작까지 ").replace(/contest over/i, "대회 종료");
        if (translated !== text) clock.textContent = translated;
      }
      translateClock();
      new MutationObserver(translateClock).observe(clock, { childList: true, characterData: true, subtree: true });
    }
    if (beforeStart) {
      document.querySelectorAll('.contest-tabs a, .navbar a[href]').forEach(function (link) {
        if (/^\/contest\/(submit|submission|scoreboard|clarifications)(\/|$|\?)/.test(link.getAttribute("href") || "")) link.hidden = true;
      });
      document.querySelectorAll(".contest-card").forEach(function (card) {
        if (card.getAttribute("href") !== contestPath("/problems")) return;
        card.querySelector(".contest-card__status").textContent = "시작 전";
        card.querySelector("p").textContent = "대회 시작 후 문제 확인과 제출이 가능합니다.";
      });
    }
    document.querySelectorAll(".alert").forEach(function (alert) {
      var text = alert.textContent.trim();
      if (!/No problem texts available at this point|Contest has not yet started - cannot submit/.test(text)) return;
      document.body.classList.add("participant-portal");
      alert.className = "contest-availability contest-shell";
      alert.replaceChildren();
      var heading = document.createElement("h2");
      heading.textContent = beforeStart ? "아직 대회 시작 전입니다" : "현재 문제를 이용할 수 없습니다";
      var message = document.createElement("p");
      message.textContent = beforeStart ? "대회가 시작되면 문제 확인과 코드 제출이 가능합니다." : "대회 운영 상태를 확인하거나 운영진에게 문의해 주세요.";
      alert.append(heading, message);
      if (beforeStart) {
        var schedule = document.createElement("p");
        schedule.textContent = "시작 시각: " + new Date(window.starttime * 1000).toLocaleString("ko-KR", { timeZone: "Asia/Seoul" }) + " (한국시간)";
        alert.appendChild(schedule);
        var remaining = document.createElement("p");
        alert.appendChild(remaining);
        function updateRemaining() { remaining.textContent = clock ? clock.textContent : "상단의 남은 시간을 확인해 주세요."; }
        updateRemaining();
        if (clock) new MutationObserver(updateRemaining).observe(clock, { childList: true, characterData: true, subtree: true });
        setTimeout(function () { location.reload(); }, Math.max(1000, (window.starttime - window.initial) * 1000 + 1000));
      }
      var back = document.createElement("a");
      back.href = CONTEST_ROOT;
      back.textContent = "대회 선택으로 돌아가기 →";
      alert.appendChild(back);
    });
  }

  function improveJuryWorkspace() {
    if (!/^\/jury(?:\/|$)/.test(location.pathname)) return;
    document.body.classList.add("kaupc-jury");
    var juryBar = document.createElement("nav");
    juryBar.className = "jury-quick-nav";
    juryBar.setAttribute("aria-label", "운영자 바로가기");
    juryBar.innerHTML = '<a href="/jury">운영 홈</a><a href="/jury/submissions">제출 · 채점 현황</a><a href="/jury/scoreboard">운영자 순위표</a>';
    var juryHeading = document.querySelector("h1");
    if (juryHeading) juryHeading.before(juryBar);
    if (/^\/jury\/?$/.test(location.pathname)) {
      var heading = document.querySelector("h1");
      if (!heading) return;
      heading.textContent = "KAUPC 운영 대시보드";
      var logo = document.getElementById("djlogo");
      if (logo) logo.hidden = true;
      var menu = heading.parentElement.querySelector(".row.equal");
      if (menu) {
        var shortcuts = document.createElement("nav");
        shortcuts.className = "jury-shortcuts";
        shortcuts.setAttribute("aria-label", "주요 운영 메뉴");
        var names = ["제출 · 채점 현황", "질의응답", "순위표", "채점 서버", "내부 오류", "대회 일정"];
        var patterns = [/\/submissions$/, /\/clarifications$/, /\/scoreboard$/, /\/judgehosts$/, /\/internal-errors$/, /\/contests$/];
        patterns.forEach(function (pattern, index) {
          var original = Array.from(menu.querySelectorAll("a[href]")).find(function (a) { return pattern.test(a.pathname); });
          if (!original) return;
          var link = document.createElement("a"); link.href = original.href; link.textContent = names[index]; shortcuts.appendChild(link);
        });
        heading.after(shortcuts);
        var details = document.createElement("details");
        details.className = "jury-advanced";
        var summary = document.createElement("summary"); summary.textContent = "전체 관리 메뉴 · 고급 설정";
        menu.before(details); details.append(summary, menu);
      }
    }
    if (location.pathname === "/jury/submissions") {
      document.body.classList.add("jury-submissions-page");
      var title = document.querySelector("h1");
      if (title) { title.textContent = "제출 · 채점 현황"; var note = document.createElement("p"); note.className = "jury-workspace-note"; note.textContent = "제출을 열면 코드와 테스트 결과를 먼저 확인할 수 있습니다. 목록은 기존 자동 갱신을 따릅니다."; title.after(note); }
      var refreshArea = document.querySelector("[data-ajax-refresh-target]");
      if (refreshArea) refreshArea.classList.add("jury-submissions-card");
      function simplifySubmissionColumns() {
        document.querySelectorAll(".submissions-table").forEach(function (table) {
          var heads = Array.from(table.querySelectorAll("thead th"));
          var column = 0;
          heads.forEach(function (head) {
            var index = column;
            column += head.colSpan || 1;
            if (!head.classList.contains("table-button-head-left") && !head.classList.contains("table-button-head-right")) return;
            head.hidden = true;
            table.querySelectorAll("tbody tr").forEach(function (row) { if (!row.querySelector("[colspan]") && row.children[index]) row.children[index].hidden = true; });
          });
        });
      }
      simplifySubmissionColumns();
      if (refreshArea) new MutationObserver(simplifySubmissionColumns).observe(refreshArea, {childList:true,subtree:true});
    }
    if (location.pathname === "/jury/scoreboard") {
      if (new URLSearchParams(location.search).get("resolver") === "1") {
        if (!document.querySelector('script[src*="/js/custom/scoreboard-resolver.js"]')) {
          var resolverScript = document.createElement("script"); resolverScript.src = "/js/custom/scoreboard-resolver.js";
          document.head.appendChild(resolverScript);
        }
      } else {
        var resultLink = document.createElement("a"); resultLink.className = "kr-result-link btn btn-primary";
        resultLink.href = "/jury/scoreboard?resolver=1"; resultLink.textContent = "결과 발표";
        var scoreboardTable = document.querySelector("table.desktop-scoreboard");
        if (scoreboardTable) {
          var actionRow = document.createElement("div"); actionRow.style.margin = "12px 0"; actionRow.appendChild(resultLink); scoreboardTable.parentElement.before(actionRow);
          var scoreboardNavbar = document.querySelector('.navbar.fixed-top');
          if (scoreboardNavbar) {
            var fitScoreboardHeader = function () { document.body.style.paddingTop = Math.ceil(scoreboardNavbar.getBoundingClientRect().height + 12) + 'px'; };
            fitScoreboardHeader();
            if (typeof ResizeObserver !== 'undefined') new ResizeObserver(fitScoreboardHeader).observe(scoreboardNavbar);
          }
        }
      }
    }
    var match = location.pathname.match(/^\/jury\/submissions\/(\d+)$/);
    if (!match) return;
    var sourceLink = document.querySelector('a[href$="/' + match[1] + '/source"]');
    if (!sourceLink) return;
    var panel = document.createElement("section"); panel.className = "jury-code-first";
    var h = document.createElement("h2"); h.textContent = "제출 코드 · #" + match[1];
    var source = document.createElement("div"); source.textContent = "코드를 불러오는 중…";
    var live = document.createElement("section"); live.className = "jury-live-results";
    var status = document.createElement("p");
    var cases = document.createElement("div"); cases.className = "jury-case-results";
    var refresh = document.createElement("button"); refresh.type = "button"; refresh.className = "btn btn-outline-secondary btn-sm"; refresh.textContent = "결과 새로고침";
    live.append(status, cases, refresh); panel.append(h, source, live);
    var anchor = document.querySelector("h1");
    var originalCard = anchor && anchor.closest(".card");
    if (originalCard) {
      originalCard.classList.add("jury-submission-header");
      anchor.textContent = "제출 #" + match[1];
      var oldSummary = originalCard.querySelector(".submission-summary");
      if (oldSummary) {
        oldSummary.querySelectorAll(".badge").forEach(function (badge) { badge.remove(); });
        Array.from(oldSummary.children).forEach(function (span) {
          if (span.querySelector('.fa-user, .fa-code, .fa-stopwatch')) { span.remove(); return; }
          span.querySelectorAll("i").forEach(function (icon) { icon.remove(); });
        });
      }
      var actions = originalCard.querySelector('.card-header > div[style*="float"]');
      if (actions) {
        var tools = document.createElement("details"); tools.className = "jury-submission-tools";
        var toolsTitle = document.createElement("summary"); toolsTitle.textContent = "제출 관리 · 재채점";
        actions.before(tools); tools.append(toolsTitle, actions); actions.style.float = "none";
      }
      originalCard.after(panel);
      var diagnostics = document.createElement("details"); diagnostics.className = "jury-advanced";
      var diagTitle = document.createElement("summary"); diagTitle.textContent = "상세 진단 · 실행 시간 그래프 · 내부 로그";
      var next = panel.nextSibling;
      panel.after(diagnostics); diagnostics.appendChild(diagTitle);
      while (next) {
        var following = next.nextSibling;
        if (next.nodeType !== 1 || next.tagName !== "SCRIPT") diagnostics.appendChild(next);
        next = following;
      }
    } else if (anchor) anchor.after(panel);
    fetch(sourceLink.href, { credentials: "same-origin" }).then(function (r) { if (!r.ok) throw new Error(); return r.text(); }).then(function (html) {
      var doc = new DOMParser().parseFromString(html, "text/html");
      var downloads = Array.from(doc.querySelectorAll('.source-tab a[href*="/source?fetch="]')).filter(function (download, index, links) {
        return links.findIndex(function (candidate) { return candidate.getAttribute("href") === download.getAttribute("href"); }) === index;
      });
      if (!downloads.length) throw new Error();
      source.replaceChildren();
      return Promise.all(downloads.map(function (download, i) {
        var filename = document.createElement("h3");
        var tab = doc.querySelectorAll(".source-tab-nav .nav-link")[i]; filename.textContent = tab ? tab.textContent.trim() : "소스 " + (i + 1);
        var pre = document.createElement("pre"); pre.textContent = "불러오는 중…";
        source.append(filename, pre);
        var url = new URL(download.getAttribute("href"), location.origin);
        if (url.origin !== location.origin) throw new Error();
        return fetch(url.href, {credentials:"same-origin"}).then(function (response) {
          if (!response.ok || /text\/html/i.test(response.headers.get("content-type") || "")) throw new Error();
          return response.text();
        }).then(function (code) { pre.textContent = code || "(빈 소스 파일)"; });
      }));
    }).catch(function () { source.textContent = "코드를 불러오지 못했습니다. 기존 ‘소스 보기’ 링크에서 확인해 주세요."; });
    function renderCases(doc) {
      var badges = Array.from(doc.querySelectorAll(".badge-testcase")).filter(function (badge) { return !badge.closest(".lasttcruns, .jury-code-first"); });
      cases.replaceChildren();
      var done = 0, pending = 0;
      badges.forEach(function (badge, index) {
        var text = badge.textContent.trim();
        if (text !== "?" && text !== "↺") done++; else if (badge.classList.contains("text-bg-primary") || badge.classList.contains("text-bg-info")) pending++;
        var item = document.createElement("span"); item.className = "badge jury-case-badge " + badge.className.replace(/\bbadge-testcase\b/g, "");
        var labels = { "?": "대기", "↺": "채점 중", "✓": "정답", "t": "시간 초과", "w": "오답", "r": "실행 오류", "m": "메모리 초과", "o": "출력 초과" };
        item.textContent = "#" + (index + 1) + " " + (labels[text] || text.toUpperCase());
        item.title = badge.parentElement.title || ""; cases.appendChild(item);
      });
      status.textContent = badges.length ? (pending ? "채점 중 · " : "테스트 결과 · ") + done + "/" + badges.length + " 처리 (나머지는 대기 또는 미실행)" : "채점 대기 중이거나 컴파일 결과를 확인하는 중입니다. 아래 상세 판정을 함께 확인하세요.";
      return pending > 0 || !badges.length;
    }
    var timer, inFlight = false, attempts = 0;
    function update() {
      if (inFlight || document.hidden) return;
      inFlight = true;
      fetch(location.href, { credentials: "same-origin" }).then(function (r) { if (!r.ok) throw new Error(); return r.text(); }).then(function (html) {
        var pending = renderCases(new DOMParser().parseFromString(html, "text/html"));
        if (!pending || ++attempts >= 120) clearInterval(timer);
      }).catch(function () { status.textContent = "결과 갱신에 실패했습니다. 잠시 후 새로고침해 주세요."; }).finally(function () { inFlight = false; });
    }
    refresh.addEventListener("click", update);
    if (renderCases(document)) timer = setInterval(update, 5000);
  }

  document.addEventListener("DOMContentLoaded", function () {
    improveJuryWorkspace();
    if (isContestPath() && typeof window.starttime === "number" && typeof window.initial === "number" && window.initial < window.starttime && /^\/contest\/(submit|submission|scoreboard|clarifications)(\/|$)/.test(location.pathname)) {
      location.replace(contestPath("/problems"));
      return;
    }
    applyKaupcBrand();
    redirectAnonymousPublicToLogin();
    currentContestFromMenu();
    rewriteParticipantLinks();
    if (returnToSelectedContest()) return;
    if (returnToContestAfterSubmit()) return;
    markParticipantNavigation();
    if (!buildStatusPage()) buildContestLobby();
    showContestAvailability();
    removeContestSwitcher();
    buildProblemTable();
    applyPageChrome();
    ensureContestPageTitle();
    injectContestTabs();
    showContestAvailability();
    injectSubmissionHistory();
    addPastedCodeSubmission();
    rememberSubmitReturn();
    cleanScoreboard();
    translateSubmissionDetail();
    structureSubmissionDetail();
    watchSubmissionModals();
    askForNickname();
  });
})();
