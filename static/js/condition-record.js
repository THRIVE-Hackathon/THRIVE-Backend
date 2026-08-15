/* ===== condition-record.js : 오늘 컨디션 기록 폼 로직 =====
 *
 * 점진적 향상:
 *   · JS 없이도: radio 선택 후 제출 → 서버 저장 → 홈 리다이렉트
 *   · JS 있으면: 데모 모드에서 실제 POST 없이 홈 이동만 시연
 *
 * 데모 모드( <form data-demo="true" data-home="../../../index.html"> ):
 *   제출을 가로채 data-home 경로로 이동. 연동 시 data-demo 만 제거하면 그대로 POST.
 */
(function () {
  "use strict";

  var form = document.querySelector(".condition-form");
  if (!form) return;

  form.addEventListener("submit", function (e) {
    var isDemo = form.getAttribute("data-demo") === "true";
    if (!isDemo) return; // 연동 모드: 브라우저 기본 제출

    e.preventDefault();
    var home = form.getAttribute("data-home") || "../../../index.html";
    window.location.href = home;
  });
})();