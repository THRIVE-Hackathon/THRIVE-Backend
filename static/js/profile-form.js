/* ===== profile-form.js : 프로필 입력(A3) 폼 로직 =====
 *
 * 전제 및 동작 방식은 auth-form.js 와 동일한 "점진적 향상":
 *   - JS 없이도: 브라우저 기본 제출 → 서버 검증으로 최종 판정 (안전망)
 *   - JS 있으면: 즉시 검증 / 실시간 조건 표시 / 제출 버튼 활성화 / UX 개선
 *
 * loginjoin2 디자인 반영:
 *   - 성별(FA302): <select> → 세그먼트 토글(여성 / 남성). 선택값은 hidden input으로 전송.
 *   - 나이(FA303): 자유 숫자 입력.
 *                  ※ 서버(Django)에서도 실제 나이를 저장한다.
 *
 * [메시지 노출 규칙] (auth.css 와 동일)
 *   - 중립(빈 값): .field__msg 비움 → :empty 로 숨김
 *   - 틀림: 빨강(.field__msg--error) / 맞음: 초록(.is-ok)
 *   - 제출 시 미완성 항목이 있으면 하단 .auth-form__error 에 '필수 입력란입니다' 노출
 *
 * 폼 식별:  <form data-auth="profile">
 * 데모 모드: <form ... data-demo="true"> 이면 실제 POST를 막고
 *            data-home 경로(홈)로 이동만 시연. (FA305)
 *            → Django 연동 시 data-demo 속성만 제거하면 그대로 POST되고,
 *              서버가 Profile 생성 후 홈으로 리다이렉트한다.
 *
 * 서버 오류 주입(서버 재렌더 시):
 *   - 필드 오류: <div class="field" data-field="nickname" data-server-error="문구">
 */
(function () {
  "use strict";

  var NS = (window.THRIVE = window.THRIVE || {});

  var NICK_MIN = 2;
  var NICK_MAX = 10;
  var AGE_MIN = 1;
  var AGE_MAX = 120;

  /* ---------- .field 메시지 헬퍼 (auth-form.js 와 동일 구조) ---------- */
  function msgOf(fieldEl) {
    return fieldEl ? fieldEl.querySelector(".field__msg") : null;
  }
  function inputOf(fieldEl) {
    return fieldEl ? fieldEl.querySelector(".field__input") : null;
  }
  function setFieldError(fieldEl, text) {
    if (!fieldEl) return;
    var msg = msgOf(fieldEl);
    fieldEl.classList.add("has-error");
    if (msg) {
      msg.classList.add("field__msg--error");
      msg.classList.remove("is-ok");
      msg.textContent = text || "";
    }
  }
  function setFieldOk(fieldEl, text) {
    if (!fieldEl) return;
    var msg = msgOf(fieldEl);
    fieldEl.classList.remove("has-error");
    if (msg) {
      msg.classList.remove("field__msg--error");
      msg.classList.add("is-ok");
      msg.textContent = text || "";
    }
  }
  // 나이 필드 전용: 메시지만 빨강으로 표시하고 테두리는 건드리지 않음(항상 다른 입력과 동일한 회색 유지)
  function setMsgErrorOnly(fieldEl, text) {
    if (!fieldEl) return;
    var msg = msgOf(fieldEl);
    fieldEl.classList.remove("has-error");
    if (msg) {
      msg.classList.add("field__msg--error");
      msg.classList.remove("is-ok");
      msg.textContent = text || "";
    }
  }
  // 중립 상태: 클래스 제거 + 텍스트 비움 -> :empty 로 숨김
  function clearFieldMsg(fieldEl) {
    if (!fieldEl) return;
    var msg = msgOf(fieldEl);
    fieldEl.classList.remove("has-error");
    if (msg) {
      msg.classList.remove("field__msg--error", "is-ok");
      msg.textContent = "";
    }
  }
  function fieldByName(form, name) {
    return form.querySelector('[data-field="' + name + '"]');
  }

  /* ---------- 서버가 주입한 오류 자동 표시 (auth-form.js 와 동일) ---------- */
  function applyServerErrors(form) {
    var fields = form.querySelectorAll("[data-field]");
    Array.prototype.forEach.call(fields, function (f) {
      var err = f.getAttribute("data-server-error");
      if (err) setFieldError(f, err);
    });
  }

  /* =========================================================
   *  프로필 입력 (A3)
   * ========================================================= */
  function initProfile(form) {
    var nickField = fieldByName(form, "nickname");
    var genderField = fieldByName(form, "gender");
    var ageField = fieldByName(form, "age");

    var nickInput = inputOf(nickField);
    var ageInput = inputOf(ageField);
    var genderBtns = genderField
      ? genderField.querySelectorAll(".segmented__btn")
      : [];
    var genderHidden = genderField
      ? genderField.querySelector("[data-gender-value]")
      : null;

    var submitBtn = form.querySelector('button[type="submit"]');
    var formError = form.querySelector(".auth-form__error");

    function nickLen() {
      return nickInput ? nickInput.value.trim().length : 0;
    }
    // FA301: 2~10자
    function nickOk() {
      var n = nickLen();
      return n >= NICK_MIN && n <= NICK_MAX;
    }
    function genderOk() {
      return !!genderHidden && genderHidden.value !== "";
    }
    function ageVal() {
      return ageInput ? ageInput.value.trim() : "";
    }
    // FA303: 나이(양수, 합리적 범위)
    function ageOk() {
      var v = ageVal();
      if (v === "") return false;
      var n = Number(v);
      return Number.isFinite(n) && n >= AGE_MIN && n <= AGE_MAX;
    }

    function clearFormError() {
      if (!formError) return;
      formError.textContent = "";
      formError.removeAttribute("data-server-error");
    }

    // FA301 닉네임 실시간 (빈 값→숨김 / 2~10자→초록 / 그 외→빨강)
    function refreshNick() {
      if (!nickInput) return;
      var n = nickLen();
      if (n === 0) clearFieldMsg(nickField);
      else if (nickOk()) setFieldOk(nickField, "사용 가능한 닉네임입니다");
      else setFieldError(nickField, "닉네임은 2~10자로 입력해주세요");
    }

    // 나이 실시간
    // 디자인(loginjoin2): 빈 값일 때도 항상 "*필수 입력란입니다." 를 빨강으로 노출한다.
    // 단, 다른 입력과 통일감을 위해 테두리는 항상 회색으로 유지(빨간 테두리 없음).
    function refreshAge() {
      if (!ageInput) return;
      if (ageVal() === "") setMsgErrorOnly(ageField, "*필수 입력란입니다.");
      else if (ageOk()) clearFieldMsg(ageField);
      else setMsgErrorOnly(ageField, "나이를 올바르게 입력해주세요");
    }

    // 성별 선택 반영
    function selectGender(btn) {
      Array.prototype.forEach.call(genderBtns, function (b) {
        var on = b === btn;
        b.classList.toggle("is-active", on);
        b.setAttribute("aria-pressed", on ? "true" : "false");
      });
      if (genderHidden) genderHidden.value = btn.getAttribute("data-value") || "";
      clearFieldMsg(genderField);
    }

    // FA305 예외: 세 조건 충족 시에만 [완료] 활성화
    function refreshSubmit() {
      if (!submitBtn) return;
      submitBtn.disabled = !(nickOk() && genderOk() && ageOk());
    }

    if (nickInput) {
      nickInput.addEventListener("input", function () {
        refreshNick();
        clearFormError();
        refreshSubmit();
      });
    }
    if (ageInput) {
      ageInput.addEventListener("input", function () {
        refreshAge();
        clearFormError();
        refreshSubmit();
      });
    }
    Array.prototype.forEach.call(genderBtns, function (btn) {
      btn.addEventListener("click", function () {
        selectGender(btn);
        clearFormError();
        refreshSubmit();
      });
    });

    // 초기 상태(모두 중립, 버튼 비활성)
    // 나이 필드만 예외: 디자인상 기본값이 빨간 "*필수 입력란입니다." 이므로
    // 서버가 이미 다른 오류를 주입한 경우(data-server-error)가 아니면 초기 표시한다.
    if (ageField && !ageField.hasAttribute("data-server-error")) {
      refreshAge();
    }
    refreshSubmit();

    form.addEventListener("submit", function (e) {
      var ok = true;
      clearFormError();

      if (!nickOk()) {
        setFieldError(nickField, "닉네임은 2~10자로 입력해주세요");
        ok = false;
      }
      if (!genderOk()) {
        setFieldError(genderField, "성별을 선택해주세요");
        ok = false;
      }
      if (!ageOk()) {
        setMsgErrorOnly(ageField, ageVal() === "" ? "*필수 입력란입니다." : "나이를 올바르게 입력해주세요");
        ok = false;
      }

      if (!ok) {
        // 하단 통합 안내(디자인의 "*필수 입력란입니다.")
        if (formError) formError.textContent = "필수 입력란입니다.";
        e.preventDefault();
        return;
      }

      // 데모 모드: 실제 전송을 막고 홈으로 이동만 시연 (FA305)
      if (form.dataset.demo === "true") {
        e.preventDefault();
        var home = form.getAttribute("data-home") || "../../../index.html";
        window.location.href = home;
        return;
      }
      // 그 외: 네이티브 제출 → Django 뷰가 Profile 생성 후 홈으로 리다이렉트
    });
  }

  /* ---------- 초기화 ---------- */
  NS.initProfileForm = function initProfileForm(root) {
    var scope = root || document;
    var forms = scope.querySelectorAll('form[data-auth="profile"]');
    Array.prototype.forEach.call(forms, function (form) {
      applyServerErrors(form);
      initProfile(form);
    });
  };

  if (document.readyState !== "loading") NS.initProfileForm();
  else
    document.addEventListener("DOMContentLoaded", function () {
      NS.initProfileForm();
    });
})();
