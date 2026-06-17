document.addEventListener("DOMContentLoaded", function () {
  const toggleBtn = document.getElementById("menu-toggle");
  const wrapper = document.getElementById("wrapper");

  if (toggleBtn && wrapper) {
    toggleBtn.addEventListener("click", function (e) {
      e.preventDefault();
      wrapper.classList.toggle("toggled");
    });
  }
});
