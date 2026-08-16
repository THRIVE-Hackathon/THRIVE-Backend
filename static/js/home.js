/* ===== home.js : 회복 루틴(plan) 구동 스크립트 =====
 *
 * 대상: plan.html 의 #recovery-list
 *   · 카운터 항목 → 백엔드 훅(.recovery-btn / .recovery-count)
 *   · 토글 항목   → 프론트 체크박스 디자인(.routine-check__input)
 * 저장: 변경분을 localStorage 에 큐로 쌓았다가 /recovery/{tripId}/items/sync/ 로 배치 전송
 *       (오프라인이면 큐에 보관 → 온라인 복귀/주기 타이머에 자동 재전송)
 *
 * ※ 이 파일은 tripId 를 DOM(data-trip-id)에서 읽으므로 Django 템플릿 태그가 필요 없음
 *   → 정적 파일로 그대로 동작. #recovery-list 가 없는 페이지에선 즉시 return(무해).
 *
 * [기존 데모 home.js 대체 안내]
 *   과거 home.js(폼 .routine / data-count-input / /home/routine/... )는 이 파일로 대체됨.
 *   base.html 은 home.js 를 전역 로드하지 않으며, plan.html 의 {% block scripts %} 에서만 로드함.
 */
(function () {
  const container = document.getElementById("recovery-list");
  if (!container) return; // plan 이외 화면에서는 아무것도 하지 않음

  const tripId = container.dataset.tripId;
  const storageKey = `thrive_pending_recovery_${tripId}`;

  function getCsrfToken() {
    const m = document.cookie.match(/csrftoken=([^;]+)/);
    return m ? m[1] : "";
  }
  function loadPending() {
    try { return JSON.parse(localStorage.getItem(storageKey)) || {}; }
    catch (e) { return {}; }
  }
  function savePending(p) {
    localStorage.setItem(storageKey, JSON.stringify(p));
  }

  // 서버 응답을 화면에 반영 (카운트/토글 상태/현재 점수)
  function applyResponse(data) {
    Object.entries(data.items || {}).forEach(([itemId, info]) => {
      const item = container.querySelector(`[data-item-id="${itemId}"]`);
      if (!item) return;
      if (item.dataset.mode === "counter") {
        const c = item.querySelector(".recovery-count");
        if (c) c.textContent = info.count;
      } else {
        const cb = item.querySelector(".routine-check__input");
        if (cb) cb.checked = info.status === "completed";
      }
    });
    if (typeof data.current_score !== "undefined" && data.current_score !== null) {
      const el = document.querySelector("[data-current-score]");
      if (el) el.textContent = data.current_score;
    }
  }

  function flushPending() {
    const pending = loadPending();
    if (!Object.values(pending).some((v) => v !== 0)) return;
    fetch(`/recovery/${tripId}/items/sync/`, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-CSRFToken": getCsrfToken() },
      body: JSON.stringify({ deltas: pending }),
    })
      .then((res) => { if (!res.ok) throw new Error("sync failed"); return res.json(); })
      .then((data) => { savePending({}); applyResponse(data); })
      .catch(() => {}); // 실패 시 큐 유지 → 다음 기회에 재전송
  }

  function queue(itemId, delta) {
    const pending = loadPending();
    pending[itemId] = (pending[itemId] || 0) + delta;
    savePending(pending);
    if (navigator.onLine) flushPending();
  }

  // --- 카운터(백엔드 훅): +/- 버튼 ---
  container.querySelectorAll(".recovery-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest("[data-item-id]");
      const countEl = item.querySelector(".recovery-count");
      const cur = parseInt(countEl.textContent, 10) || 0;
      const delta = btn.dataset.action === "increment" ? 1 : -1;
      const next = Math.max(0, cur + delta);
      if (next === cur) return;            // 0에서 감소는 무시(서버도 0 미만 불가)
      countEl.textContent = next;          // 낙관적 업데이트
      queue(item.dataset.itemId, delta);
    });
  });

  // --- 토글(프론트 체크박스 디자인): change ---
  container.querySelectorAll(".routine-check__input").forEach((cb) => {
    cb.addEventListener("change", () => {
      const item = cb.closest("[data-item-id]");
      queue(item.dataset.itemId, cb.checked ? 1 : -1);
    });
  });

  window.addEventListener("online", flushPending);
  setInterval(flushPending, 15000);
  flushPending(); // 진입 시 밀린 큐 정리
})();