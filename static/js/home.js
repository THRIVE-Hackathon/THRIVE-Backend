/* ===== home.js : 홈(비행 후) 화면 로직 =====
 *
 * 설계 원칙 — auth-form.js / profile-form.js 와 동일한 "점진적 향상":
 *   · JS 없이도: 체크리스트는 순수 <form> 이라 통째 제출 → 서버가 저장/재렌더 (안전망)
 *   · JS 있으면: 카운터 ± / 체크 토글을 즉시 반영하고, 연동 시 변경분만 자동저장
 *
 * 데모 모드( <form data-demo="true"> ):
 *   · 실제 네트워크 요청 없이 화면만 동작. 백엔드 연동 시 data-demo 속성만 제거하면
 *     각 변경이 data-save-url 로 개별 POST 된다.
 */
(function () {
  "use strict";

  var form = document.querySelector(".routine");
  if (!form) return;

  var isDemo = form.getAttribute("data-demo") === "true";
  var saveUrl = form.getAttribute("data-save-url") || "";
  var csrfEl = form.querySelector("[data-csrf]");
  var csrfToken = csrfEl ? csrfEl.value : "";

  /* ---------- 공통: 서버 저장 (연동 모드에서만) ---------- */
  function persist(name, value, rollback) {
    if (isDemo || !saveUrl) return; // 데모: UI만
    var body = new URLSearchParams();
    body.set("name", name);
    body.set("value", value);
    fetch(saveUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/x-www-form-urlencoded",
        "X-CSRFToken": csrfToken,
      },
      body: body.toString(),
      credentials: "same-origin",
    })
      .then(function (res) {
        if (!res.ok) throw new Error("save failed: " + res.status);
      })
      .catch(function () {
        // 저장 실패 → 화면 되돌리기 (사용자에게 거짓 상태를 남기지 않음)
        if (typeof rollback === "function") rollback();
      });
  }

  /* ---------- 체크형 항목: 변경 시 저장 ---------- */
  var checks = form.querySelectorAll(".routine-check__input");
  Array.prototype.forEach.call(checks, function (input) {
    input.addEventListener("change", function () {
      persist(input.name, input.checked ? "1" : "0", function () {
        input.checked = !input.checked; // 롤백
      });
    });
  });

  /* ---------- 카운터형 항목: ± 버튼 ---------- */
  var counters = form.querySelectorAll("[data-counter]");
  Array.prototype.forEach.call(counters, function (counter) {
    var name = counter.getAttribute("data-name") || "";
    var min = parseInt(counter.getAttribute("data-min"), 10);
    var max = parseInt(counter.getAttribute("data-max"), 10);
    if (isNaN(min)) min = 0;
    if (isNaN(max)) max = Infinity;

    var numEl = counter.querySelector("[data-count]");
    var input = counter.querySelector("[data-count-input]");
    var minusBtn = counter.querySelector('[data-step="-1"]');
    var plusBtn = counter.querySelector('[data-step="1"]');

    function current() {
      var v = parseInt(numEl.textContent, 10);
      return isNaN(v) ? min : v;
    }

    function render(v) {
      numEl.textContent = String(v);
      if (input) input.value = String(v);
      if (minusBtn) minusBtn.disabled = v <= min;
      if (plusBtn) plusBtn.disabled = v >= max;
    }

    function step(delta) {
      var before = current();
      var next = Math.max(min, Math.min(max, before + delta));
      if (next === before) return;
      render(next);
      persist(name, String(next), function () {
        render(before); // 롤백
      });
    }

    if (minusBtn)
      minusBtn.addEventListener("click", function () {
        step(-1);
      });
    if (plusBtn)
      plusBtn.addEventListener("click", function () {
        step(1);
      });

    render(current()); // 초기 버튼 disabled 상태 반영
  });

  /* ---------- 캘린더 내보내기 (.ics 생성 · FS506/FS206) ----------
   * 연동 모드: data-ics-url(서버 엔드포인트) 로 이동 → 서버가 text/calendar 다운로드.
   * 데모 모드: 화면의 루틴 항목을 읽어 클라이언트에서 .ics 를 즉석 생성·다운로드.
   *            (연동 시 이 블록을 지우지 않아도, data-demo 만 제거하면 서버 URL 로 감)
   * 실패 시: 안내 후 재시도할 수 있게 기본 동작을 막지 않고 콘솔에 남긴다(예외 처리).
   */
  var exportBtn = document.querySelector("[data-export]");
  if (exportBtn) {
    exportBtn.addEventListener("click", function (e) {
      var icsUrl = exportBtn.getAttribute("data-ics-url") || "";

      // 연동 모드: 서버가 .ics 를 생성/다운로드하도록 위임
      if (!isDemo) {
        if (icsUrl) {
          e.preventDefault();
          window.location.href = icsUrl; // 서버가 Content-Disposition 으로 다운로드
        }
        return; // icsUrl 없으면 href 기본 동작(템플릿에서 지정)에 맡김
      }

      // 데모 모드: 클라이언트에서 .ics 생성
      e.preventDefault();
      try {
        var ics = buildRecoveryIcs();
        var filename =
          exportBtn.getAttribute("data-ics-filename") || "recovery.ics";
        downloadIcs(ics, filename);
      } catch (err) {
        // FS206 예외처리: "캘린더 다운로드 실패 안내 후 재시도" — 데모에선 안내만.
        window.alert(
          "캘린더 내보내기에 실패했어요. 잠시 후 다시 시도해 주세요."
        );
        // console 에 원인을 남겨 재시도/디버깅에 활용
        if (window.console) console.error("ICS export failed:", err);
      }
    });
  }

  /* ---- .ics 본문 생성: 화면의 회복 루틴 항목 → VEVENT 목록 ---- */
  function buildRecoveryIcs() {
    var calTitle =
      (exportBtn && exportBtn.getAttribute("data-ics-title")) ||
      "회복 가이드";
    var labels = form.querySelectorAll(".routine-item__label");

    var lines = [];
    lines.push("BEGIN:VCALENDAR");
    lines.push("VERSION:2.0");
    lines.push("PRODID:-//THRIVE//Recovery Guide//KO");
    lines.push("CALSCALE:GREGORIAN");
    lines.push("METHOD:PUBLISH");
    lines.push("X-WR-CALNAME:" + escapeText(calTitle));

    var stamp = toIcsUtc(new Date());
    // 항목별 data-ics-start 가 없으면 "다음 정각"부터 1시간 간격으로 자동 배치
    var autoStart = nextTopOfHour(new Date());

    Array.prototype.forEach.call(labels, function (labelEl, i) {
      var item = labelEl.closest(".routine-item") || labelEl.parentNode;
      var summary = (labelEl.textContent || "").trim();
      if (!summary) return;

      // 시작 시각: 항목의 data-ics-start(로컬시각) 우선, 없으면 자동 배치
      var startAttr = item.getAttribute
        ? item.getAttribute("data-ics-start")
        : null;
      var start = startAttr ? new Date(startAttr) : addHours(autoStart, i);
      if (isNaN(start.getTime())) start = addHours(autoStart, i);

      // 길이(분): data-ics-duration, 기본 30분
      var durAttr =
        (item.getAttribute && item.getAttribute("data-ics-duration")) || "";
      var durMin = parseInt(durAttr, 10);
      if (isNaN(durMin) || durMin <= 0) durMin = 30;
      var end = new Date(start.getTime() + durMin * 60000);

      lines.push("BEGIN:VEVENT");
      lines.push("UID:" + uid(i));
      lines.push("DTSTAMP:" + stamp);
      // 로컬 floating time 으로 기록(사용자 캘린더에서 표시 시각 유지)
      lines.push("DTSTART:" + toIcsLocal(start));
      lines.push("DTEND:" + toIcsLocal(end));
      lines.push("SUMMARY:" + escapeText(summary));
      lines.push(
        "DESCRIPTION:" +
          escapeText("THRIVE 회복 가이드로 생성된 일정입니다.")
      );
      lines.push("END:VEVENT");
    });

    lines.push("END:VCALENDAR");
    return foldLines(lines).join("\r\n");
  }

  /* ---- .ics 다운로드 트리거 ---- */
  function downloadIcs(text, filename) {
    var blob = new Blob([text], { type: "text/calendar;charset=utf-8" });
    var url = URL.createObjectURL(blob);
    var a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    // 메모리 회수(즉시 revoke 하면 일부 브라우저에서 취소되므로 약간 지연)
    setTimeout(function () {
      URL.revokeObjectURL(url);
    }, 1000);
  }

  /* ---- 날짜/문자 헬퍼 (RFC5545) ---- */
  function pad2(n) {
    return (n < 10 ? "0" : "") + n;
  }
  function toIcsLocal(d) {
    // floating local time: YYYYMMDDTHHMMSS (TZID/Z 없음)
    return (
      d.getFullYear() +
      pad2(d.getMonth() + 1) +
      pad2(d.getDate()) +
      "T" +
      pad2(d.getHours()) +
      pad2(d.getMinutes()) +
      pad2(d.getSeconds())
    );
  }
  function toIcsUtc(d) {
    // DTSTAMP 는 UTC 로: YYYYMMDDTHHMMSSZ
    return (
      d.getUTCFullYear() +
      pad2(d.getUTCMonth() + 1) +
      pad2(d.getUTCDate()) +
      "T" +
      pad2(d.getUTCHours()) +
      pad2(d.getUTCMinutes()) +
      pad2(d.getUTCSeconds()) +
      "Z"
    );
  }
  function nextTopOfHour(d) {
    var t = new Date(d.getTime());
    t.setMinutes(0, 0, 0);
    t.setHours(t.getHours() + 1);
    return t;
  }
  function addHours(d, h) {
    return new Date(d.getTime() + h * 3600000);
  }
  function uid(i) {
    return (
      "thrive-" +
      Date.now() +
      "-" +
      i +
      "-" +
      Math.random().toString(36).slice(2, 8) +
      "@thrive.local"
    );
  }
  function escapeText(s) {
    // RFC5545: \\ , ; , , , 개행 이스케이프
    return String(s)
      .replace(/\\/g, "\\\\")
      .replace(/;/g, "\\;")
      .replace(/,/g, "\\,")
      .replace(/\r?\n/g, "\\n");
  }
  function foldLines(lines) {
    // 75 octet 초과 라인은 접는다(CRLF + 공백). 한글은 멀티바이트라 바이트 기준으로 처리.
    var out = [];
    lines.forEach(function (line) {
      var bytes = unescape(encodeURIComponent(line)); // UTF-8 바이트열
      if (bytes.length <= 75) {
        out.push(line);
        return;
      }
      // 바이트 경계를 지키며 접기
      var chunk = "";
      var count = 0;
      var first = true;
      for (var i = 0; i < line.length; i++) {
        var ch = line[i];
        var chBytes = unescape(encodeURIComponent(ch)).length;
        if (count + chBytes > (first ? 75 : 74)) {
          out.push(first ? chunk : " " + chunk);
          first = false;
          chunk = "";
          count = 0;
        }
        chunk += ch;
        count += chBytes;
      }
      if (chunk) out.push(first ? chunk : " " + chunk);
    });
    return out;
  }
})();