// 提前应用主题，避免深色模式启动时闪白；存储不可用时仍能正常使用。
(function () {
  var theme = "system";
  try { theme = localStorage.getItem("dualmind-theme") || "system"; } catch (_) {}
  var dark = theme === "dark" || (theme === "system" && matchMedia("(prefers-color-scheme: dark)").matches);
  document.documentElement.dataset.theme = dark ? "dark" : "light";
})();
