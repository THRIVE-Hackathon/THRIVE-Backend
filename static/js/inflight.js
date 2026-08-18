/* ===== inflight.js : 비행 중 할 일 리스트 구동 스크립트 =====
 *
 * home.js(회복 루틴용)와 동일한 패턴이지만 대상/엔드포인트가 다르므로
 * home.js를 직접 수정하지 않고 별도 파일로 분리했다.
 *
 * 대상: inflight.html 의 #inflight-list
 *   · 카운터 항목 → .inflight-btn / .inflight-count
 *   · 토글 항목   → .routine-check__input (home.js와 동일 디자인 재사용)
 * 저장: 변경분을 localStorage 에 큐로 쌓았다가 /recovery/{tripId}/checks/sync/ 로 배치 전송
 *       (오프라인이면 큐에 보관 → 온라인 복귀/주기 타이머에 자동 재전송)
 *
 * ※ #inflight-list 가 없는 페이지에선 즉시 return(무해).
 */
(function () {
  const container = document.getElementById("inflight-list");
  if (!container) return; // 비행 중 화면 이외에서는 아무것도 하지 않음

  const tripId = container.dataset.tripId;
  const storageKey = `thrive_pending_inflight_${tripId}`;

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

  // 서버 응답을 화면에 반영 (카운트/토글 상태)
  function applyResponse(data) {
    Object.entries(data.counts || {}).forEach(([checkType, count]) => {
      const item = container.querySelector(`[data-item-id="${checkType}"]`);
      if (!item) return;
      if (item.dataset.mode === "counter") {
        const c = item.querySelector(".inflight-count");
        if (c) c.textContent = count;
      } else {
        const cb = item.querySelector(".routine-check__input");
        if (cb) cb.checked = count > 0;
      }
    });
  }

  function flushPending() {
    const pending = loadPending();
    if (!Object.values(pending).some((v) => v !== 0)) return;
    fetch(`/recovery/${tripId}/checks/sync/`, {
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

  // --- 카운터: +/- 버튼 ---
  container.querySelectorAll(".inflight-btn").forEach((btn) => {
    btn.addEventListener("click", () => {
      const item = btn.closest("[data-item-id]");
      const countEl = item.querySelector(".inflight-count");
      const cur = parseInt(countEl.textContent, 10) || 0;
      const delta = btn.dataset.action === "increment" ? 1 : -1;
      const next = Math.max(0, cur + delta);
      if (next === cur) return;            // 0에서 감소는 무시
      countEl.textContent = next;          // 낙관적 업데이트
      queue(item.dataset.itemId, delta);
    });
  });

  // --- 토글: change ---
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
