# Contributing

Thanks for helping make DualMind useful and easy to understand.

1. Open an issue describing the user problem before proposing a large change.
2. Fork the repository, create a branch, and follow the setup in the README.
3. Keep the existing Codex CLI + Gemini integration working. Prefer the standard library and small functions over new frameworks.
4. Run `python -B -m unittest test_dualmind test_dualmind_web -v` and `node --check frontend/app.js`.
5. For UI changes, verify light/dark themes, narrow windows, 1920×1080, and short windows. Use `python test_dualmind_web.py --serve --root <temporary-folder>` for an isolated mock UI. The fixture writes its port to `browser-test.json`; open the bare localhost URL. Never commit that runtime file.
6. Describe the behavior change, test results and limitations in your pull request. Screenshots must use mock or intentionally public content.

Tests must mock model calls. Do not call live models in CI or commit keys, session files, local histories or credential caches. Do not enable automatic retries, paid fallbacks or unbounded conversations without an explicit design discussion.

The frontend currently uses Chinese labels. English and Spanish documentation are maintained alongside it; interface translation contributions are welcome.
