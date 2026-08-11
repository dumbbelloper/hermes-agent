# Project Instructions

## 작업 완료 기록

모든 작업을 완료하기 전에 Obsidian에서 확인할 수 있도록 task별 독립 작업 로그를 생성한다. 루트 `WORK_LOG.md`는 과거 기록 archive이며 새 작업을 append하지 않는다.

작업 로그 경로는 다음 형식을 사용한다.

```text
Work Logs/YYYY/MM/YYYY-MM-DDTHHMMSS.ffffffZ-<task-id>-<slug>.md
```

- timestamp는 UTC microsecond까지 포함한다.
- task ID는 cron run ID, kanban task ID, session ID 또는 동등한 고유값을 사용한다.
- 같은 task의 후속 commit은 같은 로그 파일을 갱신할 수 있지만 서로 다른 task와 worker는 같은 파일을 수정하지 않는다.
- 병렬 작업은 독립 Git worktree와 branch에서 수행하고 root checkout을 공유 작업공간으로 수정하지 않는다.
- 공용 index나 월별 집계 파일을 매 task마다 수정하지 않는다. 집계가 필요하면 별도 task로 생성한다.

각 기록에는 다음 내용을 포함한다.

- 작업 일시
- 사용자 요청과 목적
- 수행한 변경
- 생성·수정한 문서와 파일
- 실행한 검증과 결과
- 내린 결정과 근거
- 전역 설정이나 외부 시스템에 적용한 변경
- 알려진 한계와 남은 작업

비밀정보, credential, token, 개인정보는 작업 로그에 기록하지 않는다. 작업이 완료되지 않았으면 완료로 표시하지 않고 현재 상태와 blocker를 기록한다.

## 문서 작성

- 프로젝트 문서는 기본적으로 한국어로 작성한다.
- 실제 파일은 Obsidian에서 탐색할 수 있도록 Markdown 링크로 연결한다.
- 정책과 설계 문서는 기준일과 상태를 명시한다.
- 조사 결과에는 가능한 한 공식 원문 링크를 남긴다.

## 자율 작업의 제한된 standing authorization

`.hermes-news/config/autonomy.json`의 switch가 켜져 있고 승인 기간이 만료되지 않은 unattended job에는 다음 G2 작업이 사전 승인되어 있다.

- repository `dumbbelloper/hermes-agent`의 `automation/*` branch push
- 해당 branch의 Pull Request 생성과 수정
- 기존 프로젝트 Telegram credential이 지정한 고정 recipient에 완성 문서와 task log 전송

다음 작업은 사전 승인 범위가 아니며 자동화에서 수행하지 않는다.

- `main` 직접 push 또는 Pull Request merge
- release, deploy, force push, branch·tag 삭제
- branch protection, credential, recipient, 자동화 정책이나 승인 범위 변경

자율 작업은 root checkout을 clean `main` coordinator로 유지하고 task별 독립 worktree·branch에서 수행한다. quota, switch, 승인 기간, repository identity, clean state, test, diff 또는 task log 검증이 실패하면 외부 변경 없이 중단한다.
clean `main` coordinator는 새 run 직전에 origin 전체 ref를 fetch하고 `git merge --ff-only origin/main`으로만 갱신할 수 있다. fetch URL과 push URL이 모두 allowlist에 있어야 하며, divergence, local commit 또는 merge 필요 상태에서는 중단한다.
