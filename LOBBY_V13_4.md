# Lobby v13.4

- 로그인 성공 후 `authView.hidden = true`가 `.auth-view { display:grid }`에 덮이던 문제 수정.
- 전역 `[hidden] { display:none !important; }` 규칙 추가.
- 로그인/로비/게임 화면은 한 번에 하나만 표시.
