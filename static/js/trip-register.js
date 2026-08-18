// 헤더: X 버튼 클릭 시 커스텀 확인 모달 열기
    document.getElementById("header-mount").append(
      THRIVE.createHeader({
        title: "비행 여정 등록",
        onClose: function () {
          document.getElementById("close-confirm-modal").hidden = false;
        },
      })
    );
    document.getElementById("close-cancel").addEventListener("click", function () {
      document.getElementById("close-confirm-modal").hidden = true;
    });
    document.getElementById("close-confirm").addEventListener("click", function () {
      window.location.href = "./record.html";
    });

    // STEP 이동
    document.querySelectorAll("[data-next]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var next = btn.dataset.next;
        document.querySelectorAll(".trip-step").forEach(function (s) { s.hidden = true; });
        document.querySelector('.trip-step[data-step="' + next + '"]').hidden = false;
      });
    });
    document.querySelectorAll("[data-prev]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        var prev = btn.dataset.prev;
        document.querySelectorAll(".trip-step").forEach(function (s) { s.hidden = true; });
        document.querySelector('.trip-step[data-step="' + prev + '"]').hidden = false;
      });
    });

    // 경유 여부: '있음' 선택 시에만 대기 시간 노출
    // (선택 스타일은 .survey-option :checked CSS 가 담당 → JS 로 스타일 조작 안 함)
    document.querySelectorAll('input[name="via"]').forEach(function (input) {
      input.addEventListener('change', function () {
        document.getElementById('wait-time-field').style.display =
          input.value === 'yes' ? 'flex' : 'none';
      });
    });
    // 장거리 비행 여부 / 평소 컨디션은 라디오 :checked CSS 로만 처리(별도 JS 불필요)

    // 확인 버튼 → 다음 화면 이동
    document.getElementById("trip-confirm").addEventListener("click", function () {
      window.location.href = "./expected-score.html";
    });

    // 출발 공항 선택 바텀시트
    var airportSheet = document.getElementById("airport-sheet");
    var departureValue = document.getElementById("departure-value");
    var selectedAirport = "";

    document.getElementById("departure-trigger").addEventListener("click", function () {
      airportSheet.hidden = false;
    });
    document.querySelectorAll("#airport-list .airport-list__item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll("#airport-list .airport-list__item").forEach(function (b) {
          b.classList.remove("is-selected");
        });
        btn.classList.add("is-selected");
        selectedAirport = btn.dataset.airport;
      });
    });
    document.getElementById("airport-confirm").addEventListener("click", function () {
      if (selectedAirport) {
        departureValue.textContent = selectedAirport;
        departureValue.style.color = "var(--color-text)";
        departureValue.style.fontWeight = "600";
      }
      airportSheet.hidden = true;
      checkStep1();
    });
    airportSheet.addEventListener("click", function (e) {
      if (e.target === airportSheet) airportSheet.hidden = true;
    });

    // 출발일 선택 바텀시트
    var dateSheet = document.getElementById("date-sheet");
    var dateValueEl = document.getElementById("depart-date-value");

    document.getElementById("depart-date-trigger").addEventListener("click", function () {
      dateSheet.hidden = false;
    });
    document.getElementById("date-confirm").addEventListener("click", function () {
      var y = document.getElementById("date-year").value;
      var m = document.getElementById("date-month").value;
      var d = document.getElementById("date-day").value;
      if (y && m && d) {
        dateValueEl.textContent = y + "년 " + m + "월 " + d + "일";
      }
      dateSheet.hidden = true;
    });
    dateSheet.addEventListener("click", function (e) {
      if (e.target === dateSheet) dateSheet.hidden = true;
    });

    // STEP 1 유효성 검사: 공항 선택돼야 다음 버튼 활성화
    var step1NextBtn = document.getElementById('step1-next');
    function checkStep1() {
      step1NextBtn.disabled = !selectedAirport;
    }
    checkStep1();

    // 도착지 선택 바텀시트
    var arrivalSheet = document.getElementById("arrival-sheet");
    var arrivalValue = document.getElementById("arrival-value");
    var arrivalError = document.getElementById("arrival-error");
    var selectedArrival = "";

    document.getElementById("arrival-trigger").addEventListener("click", function () {
      arrivalSheet.hidden = false;
    });
    document.querySelectorAll("#arrival-list .airport-list__item").forEach(function (btn) {
      btn.addEventListener("click", function () {
        document.querySelectorAll("#arrival-list .airport-list__item").forEach(function (b) {
          b.classList.remove("is-selected");
        });
        btn.classList.add("is-selected");
        selectedArrival = btn.dataset.airport;
      });
    });
    document.getElementById("arrival-confirm").addEventListener("click", function () {
      if (selectedArrival) {
        arrivalValue.textContent = selectedArrival;
        arrivalValue.style.color = "var(--color-text)";
        arrivalValue.style.fontWeight = "600";
        arrivalError.style.display = "none";
      }
      arrivalSheet.hidden = true;
    });
    arrivalSheet.addEventListener("click", function (e) {
      if (e.target === arrivalSheet) arrivalSheet.hidden = true;
    });

    // 도착일 선택 바텀시트
    var arriveDateSheet = document.getElementById("arrive-date-sheet");
    var arriveDateValueEl = document.getElementById("arrive-date-value");

    document.getElementById("arrive-date-trigger").addEventListener("click", function () {
      arriveDateSheet.hidden = false;
    });
    document.getElementById("arrive-date-confirm").addEventListener("click", function () {
      var y2 = document.getElementById("arrive-date-year").value;
      var m2 = document.getElementById("arrive-date-month").value;
      var d2 = document.getElementById("arrive-date-day").value;
      if (y2 && m2 && d2) {
        arriveDateValueEl.textContent = y2 + "년 " + m2 + "월 " + d2 + "일";
      }
      arriveDateSheet.hidden = true;
    });
    arriveDateSheet.addEventListener("click", function (e) {
      if (e.target === arriveDateSheet) arriveDateSheet.hidden = true;
    });

    // 도착 시각 선택 바텀시트
    var arriveTimeSheet = document.getElementById("arrive-time-sheet");
    var arriveTimeValueEl = document.getElementById("arrive-time-value");

    document.getElementById("arrive-time-trigger").addEventListener("click", function () {
      arriveTimeSheet.hidden = false;
    });
    document.getElementById("arrive-time-confirm").addEventListener("click", function () {
      var h = document.getElementById("arrive-time-hour").value;
      var min = document.getElementById("arrive-time-minute").value;
      if (h && min) {
        arriveTimeValueEl.textContent = h.padStart(2, "0") + ":" + min.padStart(2, "0");
      }
      arriveTimeSheet.hidden = true;
    });
    arriveTimeSheet.addEventListener("click", function (e) {
      if (e.target === arriveTimeSheet) arriveTimeSheet.hidden = true;
    });

    // 여행 기간 선택 바텀시트
    var tripLengthSheet = document.getElementById("trip-length-sheet");
    var tripLengthValueEl = document.getElementById("trip-length-value");

    document.getElementById("trip-length-trigger").addEventListener("click", function () {
      tripLengthSheet.hidden = false;
    });
    document.getElementById("trip-length-confirm").addEventListener("click", function () {
      var days = document.getElementById("trip-length-days").value;
      if (days) {
        tripLengthValueEl.textContent = days + "일";
      }
      tripLengthSheet.hidden = true;
    });
    tripLengthSheet.addEventListener("click", function (e) {
      if (e.target === tripLengthSheet) tripLengthSheet.hidden = true;
    });

    // 마지막 비행 일자 선택 바텀시트
    var lastFlightSheet = document.getElementById("last-flight-sheet");
    var lastFlightValueEl = document.getElementById("last-flight-value");

    document.getElementById("last-flight-trigger").addEventListener("click", function () {
      lastFlightSheet.hidden = false;
    });
    document.getElementById("last-flight-confirm").addEventListener("click", function () {
      var y3 = document.getElementById("last-flight-year").value;
      var m3 = document.getElementById("last-flight-month").value;
      var d3 = document.getElementById("last-flight-day").value;
      if (y3 && m3 && d3) {
        lastFlightValueEl.textContent = y3 + "년 " + m3 + "월 " + d3 + "일";
      }
      lastFlightSheet.hidden = true;
    });
    lastFlightSheet.addEventListener("click", function (e) {
      if (e.target === lastFlightSheet) lastFlightSheet.hidden = true;
    });

    // 총 비행 시간 선택 바텀시트
    var totalFlightTimeSheet = document.getElementById("total-flight-time-sheet");
    var totalFlightTimeValueEl = document.getElementById("total-flight-time-value");

    document.getElementById("total-flight-time-trigger").addEventListener("click", function () {
      totalFlightTimeSheet.hidden = false;
    });
    document.getElementById("total-flight-time-confirm").addEventListener("click", function () {
      var th = document.getElementById("total-flight-hour").value;
      var tm = document.getElementById("total-flight-minute").value;
      if (th && tm) {
        totalFlightTimeValueEl.textContent = th + "시간 " + tm + "분";
      }
      totalFlightTimeSheet.hidden = true;
    });
    totalFlightTimeSheet.addEventListener("click", function (e) {
      if (e.target === totalFlightTimeSheet) totalFlightTimeSheet.hidden = true;
    });
    // 출발 시각 / 대기 시간 바텀시트
    (function () {
      var departTimeSheet = document.getElementById("depart-time-sheet");
      var departTimeValueEl = document.getElementById("depart-time-value");
      var departTimeTrigger = document.getElementById("depart-time-trigger");

      if (departTimeTrigger) {
        departTimeTrigger.addEventListener("click", function () {
          departTimeSheet.hidden = false;
        });
      }
      document.getElementById("depart-time-confirm").addEventListener("click", function () {
        var dh = document.getElementById("depart-time-hour").value;
        var dm = document.getElementById("depart-time-minute").value;
        if (dh && dm) {
          departTimeValueEl.textContent = dh.padStart(2, "0") + ":" + dm.padStart(2, "0");
        }
        departTimeSheet.hidden = true;
      });
      departTimeSheet.addEventListener("click", function (e) {
        if (e.target === departTimeSheet) departTimeSheet.hidden = true;
      });

      var waitTimeSheet = document.getElementById("wait-time-sheet");
      var waitTimeValueEl = document.getElementById("wait-time-value");
      var waitTimeField = document.getElementById("wait-time-field");

      if (waitTimeField) {
        waitTimeField.addEventListener("click", function () {
          waitTimeSheet.hidden = false;
        });
      }
      document.getElementById("wait-time-confirm").addEventListener("click", function () {
        var wh = document.getElementById("wait-time-hour").value;
        var wm = document.getElementById("wait-time-minute").value;
        if (wh && wm) {
          waitTimeValueEl.textContent = wh + "시간 " + wm + "분";
        }
        waitTimeSheet.hidden = true;
      });
      waitTimeSheet.addEventListener("click", function (e) {
        if (e.target === waitTimeSheet) waitTimeSheet.hidden = true;
      });
    })();