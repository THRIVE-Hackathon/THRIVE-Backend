/* ===== recovery-report.js : 회복 리포트 화면 로직 =====
 *
 * 점진적 향상:
 *   · JS 없이도: 설문 radio 선택 후 '확인'(form 속성으로 연결) 제출 → 서버 저장 → 홈
 *     그리고 점수 추이 SVG 는 HTML 에 박아둔 폴백 좌표로 그대로 노출된다.
 *   · JS 있으면: 데모 모드에서 실제 POST 없이 홈 이동만 시연하고,
 *     화면의 예측/직후/최종 점수(data-*-score)를 읽어 SVG 를 다시 그린다.
 *
 * 점수 추이 그래프(FS701) — 백엔드 데이터에 따라 움직인다:
 *   서버는 아래 span 에 숫자만 주입하면 된다(SVG 좌표를 직접 계산할 필요 없음).
 *     <span data-predicted-score>…</span>  (예측)
 *     <span data-immediate-score>…</span>  (직후)
 *     <span data-final-score>…</span>       (최종)
 *   로드 시 이 값들을 읽어:
 *     · x : 아래 3열 범례 중심과 일치(1/6·1/2·5/6 → viewBox 320 기준 53.33/160/266.67)
 *     · y : 세 점수의 실제 범위에 맞춰 자동 스케일(항상 기울기가 보이도록 여백 padding)
 *   범위를 서버가 고정하고 싶으면 <svg ... data-min="60" data-max="100"> 를 준다.
 */
(function () {
  "use strict";

  /* =========================================================
   *  1) 설문 폼 제출 (데모: 홈 이동만 시연)
   * ========================================================= */
  var form = document.getElementById("survey-form");
  if (form) {
    form.addEventListener("submit", function (e) {
      var isDemo = form.getAttribute("data-demo") === "true";
      if (!isDemo) return; // 연동 모드: 기본 제출
      e.preventDefault();
      var home = form.getAttribute("data-home") || "../../../index.html";
      window.location.href = home;
    });
  }

  /* =========================================================
   *  2) 점수 추이 그래프 — 데이터 구동 렌더
   * ========================================================= */

  // SVG 좌표계 상수 (recovery-report.html 의 viewBox·범례 정렬과 일치시킬 것)
  var VIEW_W = 320;
  var X = [
    VIEW_W * (1 / 6), // 예측  ≈ 53.33
    VIEW_W * (1 / 2), // 직후  = 160
    VIEW_W * (5 / 6), // 최종  ≈ 266.67
  ];
  var Y_TOP = 20; // 점수 높을수록 위(작은 y)
  var Y_BOTTOM = 80; // 점수 낮을수록 아래(큰 y)

  function round2(n) {
    return Math.round(n * 100) / 100;
  }

  function numFrom(selector, fallback) {
    var el = document.querySelector(selector);
    if (!el) return fallback;
    var v = parseFloat(String(el.textContent).replace(/[^0-9.\-]/g, ""));
    return isNaN(v) ? fallback : v;
  }

  // 세 점수의 실제 범위에 맞춰 [lo, hi] 산정(여백 40%). 모두 같으면 ±5 로 벌린다.
  function autoRange(scores) {
    var lo = Math.min.apply(null, scores);
    var hi = Math.max.apply(null, scores);
    if (hi === lo) return { min: lo - 5, max: hi + 5 };
    var pad = (hi - lo) * 0.4;
    return { min: lo - pad, max: hi + pad };
  }

  function redrawTrend(opts) {
    var svg = document.querySelector(".trend-chart");
    if (!svg) return;
    opts = opts || {};

    // 점수: 인자 우선 → 없으면 화면(span)에서 읽기
    var scores = [
      typeof opts.predicted === "number"
        ? opts.predicted
        : numFrom("[data-predicted-score]", 0),
      typeof opts.immediate === "number"
        ? opts.immediate
        : numFrom("[data-immediate-score]", 0),
      typeof opts.final === "number"
        ? opts.final
        : numFrom("[data-final-score]", 0),
    ];

    // 범위: 인자 → svg data-min/max → 자동
    var dMin = parseFloat(svg.getAttribute("data-min"));
    var dMax = parseFloat(svg.getAttribute("data-max"));
    var range;
    if (typeof opts.min === "number" && typeof opts.max === "number") {
      range = { min: opts.min, max: opts.max };
    } else if (!isNaN(dMin) && !isNaN(dMax) && dMax > dMin) {
      range = { min: dMin, max: dMax };
    } else {
      range = autoRange(scores);
    }

    function y(score) {
      var t = (score - range.min) / (range.max - range.min);
      t = Math.max(0, Math.min(1, t));
      return round2(Y_BOTTOM - t * (Y_BOTTOM - Y_TOP));
    }

    var ys = scores.map(y);

    // 폴리라인
    var poly = svg.querySelector("polyline");
    if (poly) {
      poly.setAttribute(
        "points",
        X.map(function (x, i) {
          return round2(x) + "," + ys[i];
        }).join(" ")
      );
    }

    // 원(예측·직후) — 문서 순서상 첫 두 개의 circle
    var circles = svg.querySelectorAll("circle");
    if (circles[0]) {
      circles[0].setAttribute("cx", round2(X[0]));
      circles[0].setAttribute("cy", ys[0]);
    }
    if (circles[1]) {
      circles[1].setAttribute("cx", round2(X[1]));
      circles[1].setAttribute("cy", ys[1]);
    }

    // 별(최종) — 바깥 <g> 위치만 옮긴다(안쪽 path 가 별을 g 원점에 정렬)
    var star = svg.querySelector("g");
    if (star) {
      star.setAttribute(
        "transform",
        "translate(" + round2(X[2]) + "," + ys[2] + ")"
      );
    }

    // 접근성 라벨 갱신
    svg.setAttribute(
      "aria-label",
      "점수 추이: 예측 " +
        scores[0] +
        "점, 직후 " +
        scores[1] +
        "점, 최종 " +
        scores[2] +
        "점"
    );
  }

  // 외부에서도 호출 가능하도록 노출(수동 갱신·테스트용)
  window.THRIVE = window.THRIVE || {};
  window.THRIVE.redrawTrend = redrawTrend;

  // 로드 시 화면 값 기준으로 1회 자동 렌더 → 백엔드가 숫자만 바꿔도 그래프가 따라 움직임
  if (document.readyState !== "loading") redrawTrend();
  else document.addEventListener("DOMContentLoaded", function () {
    redrawTrend();
  });
})();