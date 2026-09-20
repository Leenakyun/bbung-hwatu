# 자동 테스트

프로젝트 기준 디렉터리:

    backend/

실행:

    python3 run_tests.py

현재 포함된 테스트:

- tests/test_engine_simulation.py
  - 초보 AI 20게임
  - 중수 AI 20게임
  - 각 게임 20라운드
  - 라운드 승자 -> 다음 라운드 선 승계 검사
  - 최종 게임 종료까지 진행 검사

- tests/test_api_game_flow.py
  - Flask API 실제 요청 흐름
  - BEGINNER / INTERMEDIATE 각각 테스트
  - POST /api/games
  - GET /api/games/<id>
  - POST /draw
  - POST /discard
  - POST /continue
  - POST /bbung/pass
  - POST /next-round
  - /continue 응답의 players 등 전체 게임 스키마 검사

새 기능 수정 후 권장 순서:

1. python3 run_tests.py
2. 자동 테스트 PASS 확인
3. 브라우저 수동 UX 확인
