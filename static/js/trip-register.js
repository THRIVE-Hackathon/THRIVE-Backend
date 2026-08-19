/*
 * trip-register.js  (백엔드 static/js/ 에 배치)
 * create_step1.html / create_step2.html 공용.
 *
 * 역할: THRIVE 디자인의 바텀시트/라디오 UI에서 고른 값을
 *       숨겨진 실제 Django 폼 컨트롤(name 기준)에 주입한다.
 *       한 파일이 두 페이지를 모두 담당하므로 요소 존재 여부를 항상 확인한다.
 */
(function () {
  "use strict";

  var pad = function (v) { return String(v).padStart(2, "0"); };
  var byName = function (name) { return document.querySelector('[name="' + name + '"]'); };

  /* ── 공통: 시트 열기/닫기 ─────────────────────────────── */
  document.querySelectorAll("[data-sheet]").forEach(function (trigger) {
    trigger.addEventListener("click", function () {
      var sheet = document.getElementById(trigger.getAttribute("data-sheet"));
      if (sheet) sheet.hidden = false;
    });
  });
  document.querySelectorAll(".sheet-overlay").forEach(function (overlay) {
    overlay.addEventListener("click", function (e) {
      if (e.target === overlay) overlay.hidden = true;
    });
  });
  var closeSheet = function (el) {
    var overlay = el.closest(".sheet-overlay");
    if (overlay) overlay.hidden = true;
  };

  /* ── 공통: 리스트형 시트(공항/여행기간) 항목 선택 ──────── */
  document.querySelectorAll(".airport-list").forEach(function (list) {
    list.querySelectorAll(".airport-list__item").forEach(function (item) {
      item.addEventListener("click", function () {
        list.querySelectorAll(".airport-list__item").forEach(function (b) {
          b.classList.remove("is-selected");
        });
        item.classList.add("is-selected");
      });
    });
  });

  /* 트리거 라벨을 '선택됨' 스타일로 갱신 */
  function setTriggerLabel(id, text) {
    var el = document.getElementById(id);
    if (!el) return;
    el.textContent = text;
    el.style.color = "var(--color-text)";
    el.style.fontWeight = "600";
  }

  /* 리스트형 확정: 숨은 <select>(name)에 값 주입 + 라벨 갱신 */
  function confirmListSheet(targetName, labelId) {
    var list = document.querySelector('.airport-list[data-target="' + targetName + '"]');
    if (!list) return;
    var chosen = list.querySelector(".airport-list__item.is-selected");
    if (!chosen) { closeSheet(list); return; }
    var select = byName(targetName);
    if (select) select.value = chosen.getAttribute("data-value");
    setTriggerLabel(labelId, chosen.textContent.trim());
    closeSheet(list);
    refreshGates();
  }

  /* ── 날짜/시각 조합 상태 (step2) ───────────────────────── */
  var dt = {
    depart: { date: null, time: null },
    arrive: { date: null, time: null }
  };
  var FIELD_OF = { depart: "departure_at", arrive: "arrival_at" };

  function recomposeDateTime(prefix) {
    var s = dt[prefix];
    var hidden = byName(FIELD_OF[prefix]);
    if (hidden && s.date && s.time) {
      hidden.value = s.date.y + "-" + pad(s.date.m) + "-" + pad(s.date.d)
                   + "T" + pad(s.time.h) + ":" + pad(s.time.min);
    }
    refreshGates();
  }

  /* ── 확정(입력) 버튼 라우팅 ────────────────────────────── */
  document.querySelectorAll("[data-confirm]").forEach(function (btn) {
    btn.addEventListener("click", function () {
      var kind = btn.getAttribute("data-confirm");

      if (kind === "origin")        return confirmListSheet("origin_airport", "origin-value");
      if (kind === "destination")   return confirmListSheet("destination_airport", "destination-value");
      if (kind === "trip-length")   return confirmListSheet("trip_duration_days", "trip-length-value");

      if (kind === "wait") {
        var wh = parseInt(document.getElementById("wait-hour").value, 10) || 0;
        var wm = parseInt(document.getElementById("wait-minute").value, 10) || 0;
        var hidden = byName("max_layover_minutes");
        if (hidden) hidden.value = wh * 60 + wm;
        setTriggerLabel("wait-time-value", wh + "시간 " + pad(wm) + "분");
        return closeSheet(btn);
      }

      if (kind === "depart-date" || kind === "arrive-date") {
        var p = kind === "depart-date" ? "depart" : "arrive";
        var pre = p === "depart" ? "dd" : "ad";
        var y = document.getElementById(pre + "-year").value;
        var m = document.getElementById(pre + "-month").value;
        var d = document.getElementById(pre + "-day").value;
        if (y && m && d) {
          dt[p].date = { y: y, m: m, d: d };
          setTriggerLabel(p + "-date-value", y + "년 " + m + "월 " + d + "일");
          recomposeDateTime(p);
        }
        return closeSheet(btn);
      }

      if (kind === "depart-time" || kind === "arrive-time") {
        var pp = kind === "depart-time" ? "depart" : "arrive";
        var prefix2 = pp === "depart" ? "dt" : "at";
        var h = document.getElementById(prefix2 + "-hour").value;
        var min = document.getElementById(prefix2 + "-min").value;
        if (h !== "" && min !== "") {
          dt[pp].time = { h: h, min: min };
          setTriggerLabel(pp + "-time-value", pad(h) + ":" + pad(min));
          recomposeDateTime(pp);
        }
        return closeSheet(btn);
      }
    });
  });

  /* ── 경유 여부: 'none' 외 선택 시에만 대기 시간 노출 ──── */
  var waitRow = document.getElementById("wait-time-trigger");
  function syncWaitVisibility() {
    var checked = document.querySelector('input[name="layover_count"]:checked');
    if (!waitRow) return;
    var show = checked && checked.value !== "none";
    waitRow.hidden = !show;
    if (!show) {
      var hidden = byName("max_layover_minutes");
      if (hidden) hidden.value = "";
      setTriggerLabel("wait-time-value", "Select...");
    }
  }
  document.querySelectorAll('input[name="layover_count"]').forEach(function (r) {
    r.addEventListener("change", syncWaitVisibility);
  });

  /* ── 닫기 확인 모달 ────────────────────────────────────── */
  var closeTrigger = document.getElementById("close-trigger");
  var closeModal = document.getElementById("close-confirm-modal");
  var closeCancel = document.getElementById("close-cancel");
  if (closeTrigger && closeModal) {
    closeTrigger.addEventListener("click", function () { closeModal.hidden = false; });
  }
  if (closeCancel && closeModal) {
    closeCancel.addEventListener("click", function () { closeModal.hidden = true; });
  }

  /* ── 다음/확인 버튼 활성화 게이트 ──────────────────────── */
  function refreshGates() {
    var step1Next = document.getElementById("step1-next");
    if (step1Next) {
      var o = byName("origin_airport"), d = byName("destination_airport");
      step1Next.disabled = !(o && o.value && d && d.value);
    }
    var step2Next = document.getElementById("step2-next");
    if (step2Next) {
      var dep = byName("departure_at"), arr = byName("arrival_at"), dur = byName("trip_duration_days");
      step2Next.disabled = !(dep && dep.value && arr && arr.value && dur && dur.value);
    }
  }

  /* ── 새로고침/검증 오류 후 재진입: 숨은 값 → 라벨 복원 ── */
  function hydrate() {
    // 공항
    [["origin_airport", "origin-value"], ["destination_airport", "destination-value"]].forEach(function (pair) {
      var sel = byName(pair[0]);
      if (sel && sel.value) {
        var opt = sel.options[sel.selectedIndex];
        if (opt) setTriggerLabel(pair[1], opt.text.trim());
      }
    });
    // 여행 기간
    var dur = byName("trip_duration_days");
    if (dur && dur.value) {
      var o = dur.options[dur.selectedIndex];
      if (o) setTriggerLabel("trip-length-value", o.text.trim());
    }
    // 대기 시간
    var wait = byName("max_layover_minutes");
    if (wait && wait.value) {
      var total = parseInt(wait.value, 10) || 0;
      setTriggerLabel("wait-time-value", Math.floor(total / 60) + "시간 " + pad(total % 60) + "분");
    }
    // 출발/도착 일시
    [["depart", "departure_at"], ["arrive", "arrival_at"]].forEach(function (pair) {
      var hidden = byName(pair[1]);
      if (hidden && hidden.value) {
        var mt = /^(\d{4})-(\d{2})-(\d{2})T(\d{2}):(\d{2})/.exec(hidden.value);
        if (mt) {
          dt[pair[0]].date = { y: mt[1], m: mt[2], d: mt[3] };
          dt[pair[0]].time = { h: mt[4], min: mt[5] };
          setTriggerLabel(pair[0] + "-date-value", mt[1] + "년 " + mt[2] + "월 " + mt[3] + "일");
          setTriggerLabel(pair[0] + "-time-value", mt[4] + ":" + mt[5]);
        }
      }
    });
    syncWaitVisibility();
    refreshGates();
  }

  hydrate();
})();
