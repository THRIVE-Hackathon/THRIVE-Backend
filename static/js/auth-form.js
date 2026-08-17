/* ===== auth-form.js : 로그인 · 회원가입 폼 로직 =====
 *
 * 전제: 백엔드(Django)가 HTML을 서버 렌더링하고, 폼 POST를 직접 처리
 * 따라서 이 스크립트는 점진적 향상으로 동작
 *   - JS 없이도: 브라우저 기본 제출 → 서버 검증으로 최종 판정 (안전망)
 *   - JS 있으면: 즉시 형식 검사 / 실시간 조건 표시 / 제출 버튼 활성화 / UX 개선
 *
 * [메시지 노출 규칙]
 *   - 입력 전(중립): 메시지 비움("") → auth.css 의 :empty 규칙으로 렌더링 안 됨
 *   - 틀림: 빨강(.field__msg--error)
 *   - 맞음: 초록(.is-ok)
 *
 * 폼 식별:  <form data-auth="login">  ,  <form data-auth="signup">
 * 데모 모드: <form ... data-demo="true"> 이면 실제 POST를 막고 검증만 확인.
 *            → Django 연동 시 data-demo 속성만 제거하면 그대로 POST
 *
 * 서버 오류 주입(서버 재렌더 시):
 *   - 필드 오류:  <div class="field" data-field="email" data-server-error="문구">
 *   - 폼 오류  :  <p class="auth-form__error" data-server-error="문구">
 */
(function () {
  "use strict";

  var NS = (window.THRIVE = window.THRIVE || {});

  var EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  var PW_MIN = 8;

  /* ---------- .field 메시지 헬퍼 (common.css 구조와 동일) ----------
   * 세 가지 상태만 사용:
   *   setFieldError(빨강) / setFieldOk(초록) / clearFieldMsg(비움->숨김)
   */
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
  // 중립 상태: 클래스 제거 + 텍스트 비움 -> :empty 로 숨겨짐
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

  /* ---------- 서버가 주입한 오류 자동 표시 ---------- */
  function applyServerErrors(form) {
    var fields = form.querySelectorAll("[data-field]");
    Array.prototype.forEach.call(fields, function (f) {
      var err = f.getAttribute("data-server-error");
      if (err) setFieldError(f, err);
    });
    var formErr = form.querySelector(".auth-form__error");
    if (formErr) {
      var e = formErr.getAttribute("data-server-error");
      if (e) formErr.textContent = e;
    }
  }

  /* ---------- 데모 안내(서버 미연동 시) ---------- */
  function demoNotice(form, text) {
    var el = form.querySelector(".auth-form__demo");
    if (!el) {
      el = document.createElement("p");
      el.className = "auth-form__demo text-caption";
      form.appendChild(el);
    }
    el.textContent = text;
  }

  /* ---------- 이메일 필드 실시간 갱신(로그인 · 회원가입 공용) ----------
   *   빈 값       -> 숨김
   *   올바른 형식 -> 초록(맞음)
   *   타이핑 중 형식오류 -> 숨김, 빨강은 blur / submit 에서 표시.
   */
  function refreshEmail(emailField, emailInput) {
    var v = emailInput ? emailInput.value.trim() : "";
    if (!v) clearFieldMsg(emailField);
    else if (EMAIL_RE.test(v)) setFieldOk(emailField, "올바른 이메일 형식입니다");
    else clearFieldMsg(emailField);
  }

  /* =========================================================
   *  로그인 (A1)
   * ========================================================= */
  function initLogin(form) {
    var emailField = fieldByName(form, "email");
    var pwField = fieldByName(form, "password");
    var emailInput = inputOf(emailField);
    var pwInput = inputOf(pwField);
    var formError = form.querySelector(".auth-form__error");

    // 통합 오류 문구(FA103 예외 + 클라이언트 형식/필수 검증 공통).
    // 디자인: 필드마다 따로 표시하지 않고 비밀번호 필드 아래 한 줄로만 노출.
    var COMBINED_ERROR_TEXT = "이메일과 비밀번호를 다시 확인해주세요.";

    function showCombinedError() {
      if (formError) formError.textContent = COMBINED_ERROR_TEXT;
    }
    function clearCombinedError() {
      if (!formError) return;
      formError.textContent = "";
      formError.removeAttribute("data-server-error");
    }
    // 필드 아래 텍스트는 남기지 않고 테두리만 빨강으로 표시(경고 문구는 통합 안내가 담당)
    function markFieldError(fieldEl) {
      if (fieldEl) fieldEl.classList.add("has-error");
    }
    function clearFieldErrorClass(fieldEl) {
      if (fieldEl) fieldEl.classList.remove("has-error");
    }

    // FA101 이메일 형식: 로그인 화면은 "올바른 이메일입니다" 같은 실시간 확인(초록) 표시를 하지 않는다.
    // 입력 중엔 항상 중립(메시지 숨김·테두리 기본)이고, 오류는 통합 안내(비밀번호 아래)에서만 다룬다.
    if (emailInput) {
      emailInput.addEventListener("input", function () {
        clearFieldMsg(emailField);
        clearFieldErrorClass(emailField);
        clearCombinedError();
      });
      emailInput.addEventListener("blur", function () {
        var v = emailInput.value.trim();
        if (v && !EMAIL_RE.test(v)) {
          markFieldError(emailField);
        }
      });
    }
    if (pwInput) {
      pwInput.addEventListener("input", function () {
        clearFieldErrorClass(pwField);
        clearCombinedError();
      });
    }

    form.addEventListener("submit", function (e) {
      var ok = true;
      clearCombinedError();

      var emailVal = emailInput ? emailInput.value.trim() : "";
      var emailValid = EMAIL_RE.test(emailVal);
      var pwValid = !!(pwInput && pwInput.value);

      if (!emailValid) {
        markFieldError(emailField);
        ok = false;
      } else {
        clearFieldErrorClass(emailField);
      }
      if (!pwValid) {
        markFieldError(pwField);
        ok = false;
      } else {
        clearFieldErrorClass(pwField);
      }

      if (!ok) {
        showCombinedError();
        e.preventDefault();
        return;
      }
      // 데모 모드면 실제 전송 차단(서버 연동 전 미리보기용)
      if (form.dataset.demo === "true") {
        e.preventDefault();
        demoNotice(
          form,
          "검증 통과(데모). 서버 연동 시 data-demo 제거하면 이 폼이 그대로 POST됩니다."
        );
      }
      // 그 외: 네이티브 제출 → Django 뷰가 인증/세션 처리 (FA103)
    });
  }

  /* =========================================================
   *  회원가입 (A2)
   * ========================================================= */
  function initSignup(form) {
    var emailField = fieldByName(form, "email");
    var pwField = fieldByName(form, "password");
    var pw2Field = fieldByName(form, "password-confirm");
    var emailInput = inputOf(emailField);
    var pwInput = inputOf(pwField);
    var pw2Input = inputOf(pw2Field);
    var agree = form.querySelector('input[name="agree_privacy"], input[name="terms_agreed"]');
    var submitBtn = form.querySelector('button[type="submit"]');
    var pwHint = form.querySelector("[data-pw-hint]"); // = pwField 의 .field__msg

    function emailOk() {
      return !!emailInput && EMAIL_RE.test(emailInput.value.trim());
    }
    function pwLenOk() {
      return !!pwInput && pwInput.value.length >= PW_MIN;
    }
    function pwMatch() {
      return !!pwInput && !!pw2Input && pwInput.value === pw2Input.value;
    }
    function agreed() {
      return !!agree && agree.checked;
    }

    // FA203 비밀번호 실시간 조건 표시 (빈 값→숨김 / 8자↑→초록 / 미만→빨강)
    function refreshPwHint() {
      if (!pwHint || !pwInput) return;
      if (!pwInput.value) {
        pwHint.textContent = "";
        pwHint.classList.remove("field__msg--error", "is-ok");
        pwField.classList.remove("has-error");
      } else if (pwLenOk()) {
        pwHint.textContent = "사용 가능한 비밀번호입니다.";
        pwHint.classList.remove("field__msg--error");
        pwHint.classList.add("is-ok");
        pwField.classList.remove("has-error");
      } else {
        pwHint.textContent =
          "8자 이상 입력해주세요. (현재 " + pwInput.value.length + "자)";
        pwHint.classList.add("field__msg--error");
        pwHint.classList.remove("is-ok");
        pwField.classList.add("has-error");
      }
    }

    // FA204 비밀번호 확인 (빈 값→숨김 / 일치→초록 / 불일치→빨강)
    function refreshMatch() {
      if (!pw2Input) return;
      if (!pw2Input.value) {
        clearFieldMsg(pw2Field);
      } else if (pwMatch()) {
        setFieldOk(pw2Field, "비밀번호가 일치합니다");
      } else {
        setFieldError(pw2Field, "비밀번호가 일치하지 않습니다");
      }
    }

    // FA206 조건 충족 시에만 [가입 완료] 활성화
    function refreshSubmit() {
      if (!submitBtn) return;
      submitBtn.disabled = !(emailOk() && pwLenOk() && pwMatch() && agreed());
    }

    if (emailInput) {
      emailInput.addEventListener("input", function () {
        refreshEmail(emailField, emailInput);
        refreshSubmit();
      });
      emailInput.addEventListener("blur", function () {
        var v = emailInput.value.trim();
        if (v && !emailOk()) setFieldError(emailField, "이메일 형식이 올바르지 않습니다");
        refreshSubmit();
      });
    }
    if (pwInput) {
      pwInput.addEventListener("input", function () {
        refreshPwHint();
        refreshMatch();
        refreshSubmit();
      });
    }
    if (pw2Input) {
      pw2Input.addEventListener("input", function () {
        refreshMatch();
        refreshSubmit();
      });
    }
    if (agree) agree.addEventListener("change", refreshSubmit);

    // 초기 상태 반영(모두 중립 → 메시지 숨김)
    refreshPwHint();
    refreshSubmit();

    form.addEventListener("submit", function (e) {
      var ok = true;
      if (!emailOk()) {
        setFieldError(emailField, "이메일 형식이 올바르지 않습니다");
        ok = false;
      }
      if (!pwLenOk()) {
        setFieldError(pwField, "비밀번호는 8자 이상이어야 합니다");
        ok = false;
      }
      if (!pwMatch()) {
        setFieldError(pw2Field, "비밀번호가 일치하지 않습니다");
        ok = false;
      }
      if (!agreed()) ok = false; // 버튼 비활성이라 도달 드묾

      if (!ok) {
        e.preventDefault();
        return;
      }
      if (form.dataset.demo === "true") {
        e.preventDefault();
        // 데모: data-next(예: profile.html)가 있으면 A3로 이동만 시연.
        // (서버 연동 시엔 data-demo 제거 → 서버가 A3로 리다이렉트)
        var next = form.getAttribute("data-next");
        if (next) {
          window.location.href = next;
          return;
        }
        demoNotice(
          form,
          "검증 통과(데모). 서버 연동 시 data-demo 제거하면 이 폼이 그대로 POST됩니다."
        );
      }
      // 그 외: 네이티브 제출 → Django 뷰가 중복 확인/해싱/생성 후 A3로 리다이렉트
    });
  }

  /* ---------- 초기화 ---------- */
  NS.initAuthForm = function initAuthForm(root) {
    var scope = root || document;
    var forms = scope.querySelectorAll("form[data-auth]");
    Array.prototype.forEach.call(forms, function (form) {
      applyServerErrors(form);
      var kind = form.getAttribute("data-auth");
      if (kind === "login") initLogin(form);
      else if (kind === "signup") initSignup(form);
    });
  };

  if (document.readyState !== "loading") NS.initAuthForm();
  else
    document.addEventListener("DOMContentLoaded", function () {
      NS.initAuthForm();
    });
})();
