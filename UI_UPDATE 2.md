# 뻥 화투 UI v2

## 변경 내용
- 프론트 전체 리디자인: 로그인/AI/온라인 로비 + 실제 게임 테이블 화면 분리
- 제공받은 화투패 48장 실제 카드 이미지 연결
- 로비/게임 배경 이미지 적용
- 칩 이미지 장식 적용
- 뽑기/버리기/뻥/바가지/폭탄/승리 효과음 연결
- 로비/게임 BGM 2곡을 MP3 128kbps로 압축하여 포함
- 모바일/태블릿 반응형 레이아웃 추가
- 기존 Flask API/SSE/게임 엔진 구조는 유지

## 서버에서 이미지가 제공되는 방식
현재 별도 이미지 서버가 필요하지 않습니다.
`frontend/assets/` 안의 파일을 GitHub에 올리고 Railway가 재배포되면 Flask가 `/assets/...` 경로로 직접 제공합니다.

예시:
- 저장 파일: `frontend/assets/cards/1_1.png`
- 공개 주소: `https://<railway-domain>/assets/cards/1_1.png`

## GitHub 업데이트
현재 GitHub 저장소의 실제 프로젝트 폴더가 `bbung-hwatu/` 한 단계 안쪽에 있으므로, 그 폴더 안의 `frontend/`와 `backend/`를 이번 버전으로 교체합니다.

특히 새로 추가되는 폴더:
- `frontend/assets/cards/`
- `frontend/assets/bg/`
- `frontend/assets/ui/chips/`
- `frontend/assets/sfx/`
- `frontend/assets/bgm/`

GitHub에 반영되면 연결된 Railway 서비스가 자동 재배포됩니다.

## Railway
기존 설정 유지:
- Root Directory: `/bbung-hwatu`
- Start Command: `gunicorn --chdir backend --bind 0.0.0.0:$PORT --workers 1 --threads 100 --timeout 0 app:app`
- Healthcheck: `/api/health`
- Volume mount: `/data`
