/* ===== input-field.js : 공통 입력 필드 컴포넌트 =====
 * 명세서 "입력 필드" 반복 컴포넌트: 라벨 · 오류 메시지 위치 통일용.
 *
 * 사용법:
 *   const email = THRIVE.createInputField({
 *     name: "email", label: "이메일", type: "email",
 *     placeholder: "you@example.com", hint: "로그인에 사용할 이메일"
 *   });
 *   form.append(email);           // email 자체가 DOM 요소
 *   const value = email.getValue();
 *   email.setError("이미 가입된 이메일입니다");  // 오류 표시
 *   email.clearError();                          // 오류 해제(힌트 복원)
 *
 * 옵션:
 *   name, label, type, placeholder, value, hint, required, autocomplete
 */
(function () {
  const NS = (window.THRIVE = window.THRIVE || {});

  NS.createInputField = function createInputField(opts) {
    opts = opts || {};
    const name = opts.name || "";
    const label = opts.label || "";
    const type = opts.type || "text";
    const placeholder = opts.placeholder || "";
    const value = opts.value || "";
    const hint = opts.hint || "";
    const required = !!opts.required;
    const autocomplete = opts.autocomplete;

    const field = document.createElement("div");
    field.className = "field";

    const id =
      "field-" + (name || Math.random().toString(36).slice(2, 8));

    const labelEl = document.createElement("label");
    labelEl.className = "field__label";
    labelEl.htmlFor = id;
    labelEl.textContent = label;

    const input = document.createElement("input");
    input.className = "field__input";
    input.id = id;
    input.name = name;
    input.type = type;
    input.placeholder = placeholder;
    input.value = value;
    if (required) input.required = true;
    if (autocomplete) input.autocomplete = autocomplete;

    const msg = document.createElement("p");
    msg.className = "field__msg";
    msg.textContent = hint; // 평소엔 힌트, 오류 시 오류 문구로 교체

    field.append(labelEl, input, msg);

    /* --- 편의 API를 요소에 붙여 반환 --- */
    field.input = input;
    field.getValue = function () {
      return input.value.trim();
    };
    field.setError = function (text) {
      field.classList.add("has-error");
      msg.classList.add("field__msg--error");
      msg.textContent = text || "";
    };
    field.clearError = function () {
      field.classList.remove("has-error");
      msg.classList.remove("field__msg--error");
      msg.textContent = hint;
    };
    field.focus = function () {
      input.focus();
    };

    return field;
  };
})();
