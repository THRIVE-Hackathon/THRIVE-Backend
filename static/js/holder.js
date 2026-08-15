/* ===== holder.js : 선택 트리거(홀더) 컴포넌트 =====
 * 상태:
 *   기본(빈 값)  : gray-100 테두리 + gray-400 플레이스홀더
 *   채움(선택됨) : violet-200 테두리 + gray-900 텍스트  (setValue 호출 시 자동 전환)
 *
 * 사용법:
 *   const dest = THRIVE.createHolder({
 *     placeholder: "도착지",
 *     onClick: function () { openAirportPicker(dest); }
 *   });
 *   form.append(dest);
 *
 *   dest.setValue("ICN 인천국제공항");  // 채움 상태로 전환
 *   dest.clear();                       // 기본(빈) 상태로 복귀
 *   const v = dest.getValue();          // "" 또는 선택값
 *
 * 옵션:
 *   placeholder {string}       빈 상태 안내 문구
 *   value       {string}       초기 선택값(있으면 채움 상태로 시작)
 *   name        {string}       숨은 input name (폼 전송용, 옵션)
 *   onClick     {function()}   탭 시 실행(선택 화면 열기 등)
 *   disabled    {boolean}
 */
(function () {
  const NS = (window.THRIVE = window.THRIVE || {});

  NS.createHolder = function createHolder(opts) {
    opts = opts || {};
    const placeholder = opts.placeholder || "선택";
    const name = opts.name || "";
    const onClick = opts.onClick;

    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "holder";
    if (opts.disabled) btn.disabled = true;

    const textEl = document.createElement("span");
    textEl.className = "holder__text";

    // 폼 전송이 필요하면 숨은 input 동기화
    let hidden = null;
    if (name) {
      hidden = document.createElement("input");
      hidden.type = "hidden";
      hidden.name = name;
    }

    btn.innerHTML = ""; // reset
    btn.appendChild(textEl);
    btn.insertAdjacentHTML("beforeend", chevron());
    if (hidden) btn.appendChild(hidden);

    let value = "";

    function render() {
      const filled = value !== "";
      textEl.textContent = filled ? value : placeholder;
      btn.classList.toggle("is-filled", filled);
      if (hidden) hidden.value = value;
      btn.setAttribute(
        "aria-label",
        (opts.label || placeholder) + (filled ? ": " + value : ", 선택 안 됨")
      );
    }

    /* --- API --- */
    btn.setValue = function (v) {
      value = (v == null ? "" : String(v)).trim();
      render();
    };
    btn.getValue = function () {
      return value;
    };
    btn.clear = function () {
      value = "";
      render();
    };

    if (typeof onClick === "function") {
      btn.addEventListener("click", function () {
        if (!btn.disabled) onClick(btn);
      });
    }

    btn.setValue(opts.value || "");
    return btn;
  };

  /* 오른쪽 chevron (회색). 채움/기본 공통 */
  function chevron() {
    return (
      '<svg class="holder__chevron" viewBox="0 0 24 24" fill="none" aria-hidden="true">' +
      '<polyline points="6 9 12 15 18 9" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>' +
      "</svg>"
    );
  }
})();