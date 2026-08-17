/* ===== calendar-export.js : 회복 가이드 → .ics 캘린더 파일 내보내기 =====
 *
 * "회복 가이드 캘린더로 내보내기" 링크를 훅으로 사용.
 * .js-ics-export 클래스가 붙은 요소를 클릭하면, 그 요소의 data-ics-* 속성값을
 * 읽어 .ics(iCalendar) 파일을 만들고 즉시 다운로드한다. 서버 요청 없이
 * 브라우저에서 바로 파일을 생성하는 클라이언트 전용 기능이라 별도 스크립트로 분리했다.
 *
 * 사용법 (마크업 예시):
 *   <a class="... js-ics-export"
 *      href="#"
 *      data-ics-title="THRIVE 회복 가이드"
 *      data-ics-start="2026-10-12T06:30:00+09:00"
 *      data-ics-end="2026-10-15T06:30:00+09:00"
 *      data-ics-description="피부 보습하기, 물 마시기 등을 확인하세요."
 *      data-ics-location="MXP 말펜사공항">회복 가이드 캘린더로 내보내기</a>
 *
 * data-ics-title / start / end 는 필수. description / location 은 선택.
 * start·end 는 ISO 8601 문자열(타임존 포함 권장).
 *
 * [Django] 각 data-ics-* 값은 서버에서 계산한 실제 여정/회복 일정 문자열로 주입.
 * ※ .js-ics-export 요소가 없는 페이지에선 아무 동작도 하지 않음(무해).
 */
(function () {
  const exportLinks = document.querySelectorAll(".js-ics-export");
  if (!exportLinks.length) return;

  function pad(n) {
    return String(n).padStart(2, "0");
  }

  // Date → UTC 기준 ICS DATETIME 문자열 (YYYYMMDDTHHMMSSZ)
  function toICSDate(date) {
    return (
      date.getUTCFullYear() +
      pad(date.getUTCMonth() + 1) +
      pad(date.getUTCDate()) +
      "T" +
      pad(date.getUTCHours()) +
      pad(date.getUTCMinutes()) +
      pad(date.getUTCSeconds()) +
      "Z"
    );
  }

  // ICS 텍스트 필드 이스케이프 (역슬래시/세미콜론/콤마/개행)
  function escapeText(str) {
    return String(str)
      .replace(/\\/g, "\\\\")
      .replace(/;/g, "\\;")
      .replace(/,/g, "\\,")
      .replace(/\r?\n/g, "\\n");
  }

  function buildICS({ title, start, end, description, location }) {
    const uid = `thrive-${Date.now()}-${Math.random().toString(36).slice(2, 8)}@thrive.app`;
    const lines = [
      "BEGIN:VCALENDAR",
      "VERSION:2.0",
      "PRODID:-//THRIVE//Recovery Guide//KO",
      "CALSCALE:GREGORIAN",
      "METHOD:PUBLISH",
      "BEGIN:VEVENT",
      `UID:${uid}`,
      `DTSTAMP:${toICSDate(new Date())}`,
      `DTSTART:${toICSDate(start)}`,
      `DTEND:${toICSDate(end)}`,
      `SUMMARY:${escapeText(title)}`,
    ];
    if (description) lines.push(`DESCRIPTION:${escapeText(description)}`);
    if (location) lines.push(`LOCATION:${escapeText(location)}`);
    // 시작 30분 전 알림(캘린더 앱이 지원하는 경우)
    lines.push(
      "BEGIN:VALARM",
      "TRIGGER:-PT30M",
      "ACTION:DISPLAY",
      `DESCRIPTION:${escapeText(title)}`,
      "END:VALARM"
    );
    lines.push("END:VEVENT", "END:VCALENDAR");
    return lines.join("\r\n");
  }

  function downloadFile(filename, content) {
    const blob = new Blob([content], { type: "text/calendar;charset=utf-8" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    setTimeout(() => URL.revokeObjectURL(url), 1000);
  }

  exportLinks.forEach((el) => {
    el.addEventListener("click", (e) => {
      e.preventDefault();
      const { icsTitle, icsStart, icsEnd, icsDescription, icsLocation } = el.dataset;
      if (!icsTitle || !icsStart || !icsEnd) return; // 필수값 없으면 조용히 무시

      const start = new Date(icsStart);
      const end = new Date(icsEnd);
      if (isNaN(start.getTime()) || isNaN(end.getTime())) return;

      const ics = buildICS({
        title: icsTitle,
        start,
        end,
        description: icsDescription,
        location: icsLocation,
      });
      downloadFile("thrive-recovery-guide.ics", ics);
    });
  });
})();
