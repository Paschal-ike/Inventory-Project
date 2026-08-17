document.addEventListener("click", function (event) {
  const btn = event.target.closest(".toggle-password-btn");
  if (!btn) return;
  const input = document.getElementById(btn.dataset.togglePassword);
  const icon = btn.querySelector("i");
  if (!input || !icon) return;
  const showing = input.type === "text";
  input.type = showing ? "password" : "text";
  icon.classList.toggle("bi-eye", showing);
  icon.classList.toggle("bi-eye-slash", !showing);
});
