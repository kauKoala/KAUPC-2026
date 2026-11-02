/**
 * 운영자 화면에 "문제 만들기"와 "대회 만들기" 입구를 만든다.
 *
 * 문제의 원본은 저장소 파일이다. jury UI로 문제를 만들면 DB에만 남아 커밋되지 않으므로,
 * "문제 만들기"는 저장소 파일을 직접 쓰는 문제 에디터로 연결한다.
 * "대회 만들기"는 DOMjudge 기본 화면으로 보낸다(대회는 contest.yaml 한 장이라 저장소 반영이 쉽다).
 */
(function () {
  "use strict";

  var EDITOR_URL = "/authoring/";
  var CONTEST_ADD_URL = "/jury/contests/add";
  var NAV_ID = "problem-editor-link";
  var CARD_ID = "problem-editor-actions";

  function isJury() {
    return window.location.pathname.indexOf("/jury") === 0;
  }

  function makeLink(href, text, external) {
    var link = document.createElement("a");
    link.href = href;
    link.textContent = text;
    if (external) {
      link.target = "_blank";
      link.rel = "noopener";
    }
    return link;
  }

  /** 상단 메뉴에 에디터 링크 */
  function insertNavLink() {
    if (document.getElementById(NAV_ID)) return;
    var menu = document.querySelector("#menuDefault, .navbar-nav");
    if (!menu) return;

    var item = document.createElement("li");
    item.className = "nav-item";
    item.id = NAV_ID;

    var link = makeLink(EDITOR_URL, "문제 에디터", false);
    link.className = "nav-link";
    link.title = "저장소 파일을 직접 편집한다. 저장한 뒤 반영 버튼을 누르면 채점 시스템에 올라간다.";

    item.appendChild(link);
    menu.appendChild(item);
  }

  /** 운영자 첫 화면 맨 위에 만들기 카드 */
  function insertActionCard() {
    if (window.location.pathname.replace(/\/$/, "") !== "/jury") return;
    if (document.getElementById(CARD_ID)) return;

    var anchor = document.querySelector(".card");
    if (!anchor) return;

    var card = document.createElement("div");
    card.className = "card mb-3";
    card.id = CARD_ID;

    var header = document.createElement("div");
    header.className = "card-header";
    header.textContent = "만들기:";

    var body = document.createElement("div");
    body.className = "card-body";

    var list = document.createElement("ul");
    list.className = "list-unstyled mb-0";

    [
      [EDITOR_URL, "문제 만들기", false, "문제 에디터에서 만든다. 결과물이 저장소 파일로 남는다."],
      [CONTEST_ADD_URL, "대회 만들기", false, "DOMjudge 대회 추가 화면으로 간다."]
    ].forEach(function (entry) {
      var row = document.createElement("li");
      row.className = "mb-1";
      var link = makeLink(entry[0], entry[1], entry[2]);
      link.title = entry[3];
      row.appendChild(link);
      list.appendChild(row);
    });

    body.appendChild(list);
    card.appendChild(header);
    card.appendChild(body);
    anchor.parentNode.insertBefore(card, anchor);
  }

  function run() {
    if (!isJury()) return;
    insertNavLink();
    insertActionCard();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", run);
  } else {
    run();
  }
})();
