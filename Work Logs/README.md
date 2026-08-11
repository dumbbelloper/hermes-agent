# 작업 로그 인덱스

> 기준일: 2026-08-11
>
> 상태: 병렬 작업용 운영 규칙

이 폴더는 Hermes Agent와 병렬 worker가 수행한 작업을 task 단위의 독립 Markdown 파일로 보관한다. 루트의 [WORK_LOG.md](../WORK_LOG.md)는 2026-08-11 이전 기록을 보존하는 archive이며 새 작업을 append하지 않는다.

## 경로 규칙

```text
Work Logs/YYYY/MM/YYYY-MM-DDTHHMMSS.ffffffZ-<task-id>-<slug>.md
```

- timestamp는 UTC이며 microsecond까지 기록한다.
- `task-id`는 cron run ID, kanban task ID, session ID 또는 동등한 고유 ID를 사용한다.
- 동일 task를 후속 commit에서 갱신할 때는 같은 파일을 수정한다.
- 서로 다른 task와 worker는 같은 파일을 수정하지 않는다.
- log index나 월별 집계 파일을 매 작업마다 수정하지 않는다. 필요하면 별도 집계 task가 생성한다.

## 필수 내용

- 작업 일시
- task/run ID와 실행 주체
- 사용자 요청과 목적
- 수행한 변경
- 생성·수정한 문서와 파일
- 실행한 검증과 결과
- 내린 결정과 근거
- 전역 설정이나 외부 시스템에 적용한 변경
- 알려진 한계와 남은 작업

비밀정보, credential, token과 개인정보는 기록하지 않는다. 완료되지 않은 작업은 완료로 표시하지 않고 상태와 blocker를 기록한다.
