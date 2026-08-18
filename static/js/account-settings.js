document.getElementById("header-mount").append(
    THRIVE.createHeader({
        title: "계정 설정",
        onClose: function () { window.location.href = "./profile.html"; },
    })
);
document.getElementById("withdraw-link").addEventListener("click", function (e) {
    e.preventDefault();
    document.getElementById("withdraw-modal").hidden = false;
});
document.getElementById("withdraw-cancel").addEventListener("click", function () {
    document.getElementById("withdraw-modal").hidden = true;
});