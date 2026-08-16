/* ===== header.js : 상단 헤더 컴포넌트 =====
 * 가운데 제목 + 우측 닫기(X). 좌측 뒤로가기는 옵션.
 * 좌/우 슬롯 폭이 같아 제목은 항상 화면 정중앙 정렬.
 *
 * [아이콘 방식 변경] 인라인 <svg> 대신 icons.css 의 svg-icon(mask) 클래스를 사용.
 *   · 뒤로가기 → svg-icon--left (IconLeft.svg)
 *   · 닫기(X)  → svg-icon--close (IconClose.svg)
 *   크기/색상은 icons.css 의 `.app-header__btn .svg-icon` 규칙이 담당.
 *
 * 사용법:
 *   const header = THRIVE.createHeader({
 *     title: "비행 여정 등록",
 *     onClose: function () { history.back(); }
 *   });
 *   appEl.prepend(header);
 *
 *   // 뒤로가기 + 제목
 *   THRIVE.createHeader({ title: "레이오버 가이드", onBack: () => history.back() });
 *
 * 옵션:
 *   title    {string}           가운데 제목
 *   onBack   {function()}       주면 좌측에 뒤로가기(←) 표시
 *   onClose  {function()}       주면 우측에 닫기(X) 표시
 *   bordered {boolean}          하단 구분선 표시 (기본 false)
 *
 * 반환된 요소에 .setTitle(text) 헬퍼가 붙어 있음.
 */
(function () {
  const NS = (window.THRIVE = window.THRIVE || {});

  NS.createHeader = function createHeader(opts) {
    opts = opts || {};
    const title = opts.title || "";
    const onBack = opts.onBack;
    const onClose = opts.onClose;
    const bordered = !!opts.bordered;

    const header = document.createElement("header");
    header.className = "app-header" + (bordered ? " app-header--bordered" : "");

    // 좌: 뒤로가기 (옵션)
    if (typeof onBack === "function") {
      const back = document.createElement("button");
      back.type = "button";
      back.className = "app-header__btn app-header__btn--back";
      back.setAttribute("aria-label", "뒤로가기");
      back.innerHTML = iconLeft();
      back.addEventListener("click", onBack);
      header.appendChild(back);
    }

    // 가운데: 제목
    const titleEl = document.createElement("h1");
    titleEl.className = "app-header__title";
    titleEl.textContent = title;
    header.appendChild(titleEl);

    // 우: 닫기 (옵션)
    if (typeof onClose === "function") {
      const close = document.createElement("button");
      close.type = "button";
      close.className = "app-header__btn app-header__btn--close";
      close.setAttribute("aria-label", "닫기");
      close.innerHTML = iconClose();
      close.addEventListener("click", onClose);
      header.appendChild(close);
    }

    header.setTitle = function (text) {
      titleEl.textContent = text || "";
    };

    return header;
  };

  /* --- 아이콘 (static/icons/*.svg 를 mask 로 불러옴, icons.css 필요) --- */
  function iconLeft() {
    return '<span class="svg-icon svg-icon--left" aria-hidden="true"></span>';
  }
  function iconClose() {
    return '<span class="svg-icon svg-icon--close" aria-hidden="true"></span>';
  }
})();