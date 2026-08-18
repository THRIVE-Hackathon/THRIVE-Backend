document.getElementById("header-mount").append(
    THRIVE.createHeader({
        title: "프로필 수정",
        onClose: function () { window.location.href = "./profile.html"; },
    })
);

var sheet = document.getElementById("gender-sheet");
var genderValue = document.getElementById("gender-value");
var selected = "여성";

document.getElementById("gender-trigger").addEventListener("click", function () {
    sheet.hidden = false;
});

document.querySelectorAll(".sheet__option").forEach(function (btn) {
    btn.addEventListener("click", function () {
        document.querySelectorAll(".sheet__option").forEach(function (b) {
            b.classList.remove("is-selected");
        });
        btn.classList.add("is-selected");
        selected = btn.dataset.gender;
    });
});

document.getElementById("gender-confirm").addEventListener("click", function () {
    genderValue.textContent = selected;
    sheet.hidden = true;
});

// 바텀시트 바깥(어두운 배경) 클릭하면 닫기
sheet.addEventListener("click", function (e) {
    if (e.target === sheet) sheet.hidden = true;
});

// 나이 입력창: 숫자만 입력받고 "세" 자동으로 붙이기
var ageInput = document.getElementById("age-input");
ageInput.addEventListener("focus", function () {
    ageInput.value = ageInput.value.replace("세", "");
});
ageInput.addEventListener("blur", function () {
    var digits = ageInput.value.replace(/[^0-9]/g, "");
    if (digits) ageInput.value = digits + "세";
});

// 저장 버튼: 토스트 띄우고 5초 뒤 사라짐, 그 후 profile.html로 이동
var saveToast = document.getElementById("save-toast");
var toastTimer = null;

document.getElementById("profile-save").addEventListener("click", function () {
    saveToast.hidden = false;
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function () {
        saveToast.hidden = true;
        window.location.href = "./profile.html";
    }, 5000);
});