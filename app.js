const form = document.getElementById("analyze-form");
const statusEl = document.getElementById("status");
const analyzeBtn = document.getElementById("analyze-btn");

if (form && statusEl && analyzeBtn) {
  form.addEventListener("submit", () => {
    analyzeBtn.disabled = true;
    statusEl.textContent = "Обробка...";
  });
}

const tabButtons = document.querySelectorAll(".tab-btn");
const tabContents = document.querySelectorAll(".tab-content");

tabButtons.forEach((btn) => {
  btn.addEventListener("click", () => {
    tabButtons.forEach((b) => b.classList.remove("active"));
    tabContents.forEach((c) => c.classList.remove("active"));

    btn.classList.add("active");
    const target = document.getElementById(btn.dataset.target);
    if (target) {
      target.classList.add("active");
    }
  });
});
