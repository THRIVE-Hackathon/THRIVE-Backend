/* ===== tab-bar.js : 하단 탭바 컴포넌트 =====
 * [아이콘 방식 변경] 인라인 <svg> 대신 icons.css 의 svg-icon(mask) 클래스를 사용.
 *   · 기록 → svg-icon--record   · 메인(홈) → svg-icon--home   · 설정 → svg-icon--account
 *   크기/색상은 icons.css 의 `.app-tabbar__icon.svg-icon` 규칙 + 상위 .is-active 색상 규칙이 담당.
 *
 * 사용법:
 *   const tabbar = THRIVE.createTabBar({ active: "home" });
 *   appEl.append(tabbar);
 *
 * 옵션:
 *   active     {"record"|"home"|"mypage"}  현재 활성 탭 (기본 "home")
 *   onNavigate {function(key, href)}       이동 가로채기(옵션, SPA/데모용)
 */
(function () {
  const NS = (window.THRIVE = window.THRIVE || {});

  /* 서버에서 hrefs를 넘기지 않았을 때의 폴백
     (권장: 템플릿에서 {% url %} 로 직접 주입 -> 이 값은 사용되지 않음)
     현재는 정적 HTML 데모 단계라 상대경로로 채워 화면 이동이 가능하게 함. */
  const DEFAULT_HREFS = {
  record: "/src/pages/record/record.html",
  home: "/index.html",
  mypage: "/src/pages/mypage/profile.html",
};

  const TABS = [
    { key: "record", label: "기록", href: DEFAULT_HREFS.record, iconClass: "svg-icon--record" },
    { key: "home", label: "메인", href: DEFAULT_HREFS.home, iconClass: "svg-icon--home" },
    { key: "mypage", label: "설정", href: DEFAULT_HREFS.mypage, iconClass: "svg-icon--account" },
  ];

  NS.createTabBar = function createTabBar(opts) {
    opts = opts || {};
    const active = opts.active || "home";
    const onNavigate = opts.onNavigate;

    const nav = document.createElement("nav");
    nav.className = "app-tabbar";
    nav.setAttribute("aria-label", "메인 내비게이션");

    TABS.forEach(function (tab) {
      const item = document.createElement("a");
      item.className = "app-tabbar__item";
      item.href = tab.href;
      item.dataset.key = tab.key;

      if (tab.key === active) {
        item.classList.add("is-active");
        item.setAttribute("aria-current", "page");
      }

      item.innerHTML =
        '<span class="app-tabbar__icon svg-icon ' + tab.iconClass + '" aria-hidden="true"></span>' +
        '<span class="app-tabbar__label">' + tab.label + "</span>";

      item.addEventListener("click", function (e) {
        if (typeof onNavigate === "function") {
          e.preventDefault();
          onNavigate(tab.key, tab.href);
        }
      });

      nav.appendChild(item);
    });

    return nav;
  };
})();