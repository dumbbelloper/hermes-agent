# Hermes Agent 최소 수집기

> 기준일: 2026-07-29
> 상태: v0.1.0 공개 — 수집·agent 검증·Obsidian 작성·Telegram workflow 구현, 최초 실환경 cron 검증 필요
> 라이선스: [Apache License 2.0](../LICENSE)

Hermes Agent의 실행 가능한 수집·문서화 기반이다. 공식 공개 출처와 선별 편집 언론에서 제목, 원문 URL, 게시일과 설명을 가져와 공통 레코드로 정규화한다. 무인 controller는 신규·변경 queue, logical lock, agent artifact 검증, Obsidian 원자 저장과 Telegram delivery ledger를 관리한다. Python runtime의 단일 원본은 배포 가능한 [Hermes News Automation Skill](../skills/hermes-news-automation/SKILL.md)의 `scripts/runtime/`에 있으며, `Automation/run.py`는 repository 개발용 launcher다.

## 현재 지원 출처

| Source ID    | 조직                             | 채널            | 방식         |
| ------------ | ------------------------------ | ------------- | ---------- |
| `visa-press` | Visa                           | Press release | 공식 목록 HTML |
| `visa-developer-release-notes` | Visa | Developer release notes | 공식 정적 HTML |
| `visa-acceptance-devices-ios-releases` | Visa | iOS SDK releases | 공식 Atom |
| `amex-newsroom` | American Express | Newsroom | 공식 AEM JSON |
| `unionpay-company-news` | UnionPay International | Company News | 공식 JSON |
| `unionpay-market-news` | UnionPay International | Market News | 공식 JSON |
| `jcb-press`  | JCB                            | Press release | 공식 JSON    |
| `emvco-news` | EMVCo                          | News          | 공식 RSS     |
| `pci-blog`   | PCI Security Standards Council | Blog          | 공식 RSS     |
| `payments-dive` | Payments Dive | Payments News | 편집 RSS |
| `banking-dive` | Banking Dive | Banking News | 편집 RSS |
| `pymnts` | PYMNTS | Payments News | 편집 RSS |
| `techcrunch-fintech` | TechCrunch | Fintech News | 편집 RSS |

출처의 URI, 허용 도메인과 품질 기준은 [config/sources.json](./config/sources.json)에서 관리한다. 배포 패키지에는 같은 내용의 기본 Registry가 포함되며 테스트에서 두 파일의 일치 여부를 검사한다. 별도 Registry는 전역 `--config` 옵션으로 지정할 수 있다.

현재 Registry에 포함할 출처의 판정 기준과 제외 근거는 [SOURCE_CATALOG.md](../SOURCE_CATALOG.md)에서 관리한다. WAF 우회, 브라우저 자동화 또는 검색 인덱스 폴백이 필요한 출처는 운영 Registry에 넣지 않는다.

## 설계 원칙

- 등록된 HTTPS 출처와 명시된 도메인만 허용하고 공식 채널과 편집 언론을 구분한다.
- source별 파싱과 공통 정규화·검증·저장을 분리한다.
- canonical URL과 source ID로 안정적인 레코드 ID를 만든다.
- 원본 응답과 SHA-256을 남겨 결과를 재현할 수 있게 한다.
- 빈 응답, 전량 격리 또는 과도한 격리 발생 시 마지막 정상 상태를 덮어쓰지 않는다.
- 목록에서 일시적으로 사라진 레코드는 자동 삭제하지 않는다.
- 외부 dependency 없이 Python 표준 라이브러리만 사용한다.

## 실행

저장소 루트에서 Python 3.9 이상으로 실행한다.

```bash
python3 Automation/run.py validate-registry
```

전체 활성 출처 수집:

```bash
python3 Automation/run.py collect
```

특정 출처만 수집:

```bash
python3 Automation/run.py collect \
  --source emvco-news \
  --source pci-blog
```

상태 확인:

```bash
python3 Automation/run.py show-state \
  --source emvco-news
```

Vault 문서 식별 필드와 중복 검사:

```bash
python3 Automation/run.py validate-notes \
  --vault-dir .
```

Writer가 특정 레코드를 처리해야 하는지 확인:

```bash
python3 Automation/run.py note-status \
  --vault-dir . \
  --record-id <record-id> \
  --source-fingerprint <source-fingerprint>
```

결과는 `create`, `skip`, `update_pending` 중 하나다. 같은 `record_id`가 여러 문서에 있거나 ID가 `source_id`·`canonical_url`과 일치하지 않으면 자동 처리를 중단한다. 상세 정책은 [NOTE_IDENTITY_POLICY.md](../NOTE_IDENTITY_POLICY.md)를 따른다.

작성 완료한 Markdown 문서의 전체 내용을 Telegram으로 전송:

```bash
python3 Automation/run.py notify-telegram \
  --file "Inbox/example.md"
```

Telegram credential은 `.hermes-news/config/telegram.json`의 `bot_token`,
`chat_id`에서 읽으며 CLI 인자나 출력으로 노출하지 않는다. 이 파일은 Git 추적에서
제외하고 소유자만 읽도록 설정한다. 메시지가 Telegram의 4,096자 제한을 넘으면 원문
문자를 보존해 여러 메시지로 분할한다. 실제 전송 전에는 `--dry-run`으로 파일별
메시지 수를 확인할 수 있다.

기본 데이터 위치는 `Automation/data/`이며 Git 추적에서 제외된다. 다른 위치를 사용하려면 `collect`와 `show-state`에 `--data-dir`을 지정한다.

## 무인 workflow

Hermes Skill이 사용하는 상태 전이는 다음과 같다.

```text
collect → pending → processing
                   ├─ irrelevant
                   ├─ quarantined
                   ├─ retryable
                   └─ committed → notified
```

Run 시작:

```bash
python3 Automation/run.py automation-start \
  --vault-dir . \
  --data-dir Automation/data \
  --max-items 5
```

반환된 `run_id`로 다음 항목을 claim한다.

```bash
python3 Automation/run.py automation-next \
  --vault-dir . --data-dir Automation/data --run-id <run-id>
```

관련 없거나 검증할 수 없는 항목은 발행하지 않고 상태를 기록한다.

```bash
python3 Automation/run.py automation-reject \
  --vault-dir . --data-dir Automation/data --run-id <run-id> \
  --record-id <record-id> \
  --disposition irrelevant \
  --reason "결제·금융 산업과 직접 관련되지 않은 자료다."
```

canonical URL의 web extraction이 JavaScript shell 또는 도구 오류로 실패하면
Registry에 공식 fallback이 설정된 처리 중 항목만 controller로 추출할 수 있다.

```bash
python3 Automation/run.py automation-extract \
  --vault-dir . --data-dir Automation/data --run-id <run-id> \
  --record-id <record-id>
```

현재 Amex Newsroom은 동일 공식 도메인의 기사별 AEM model JSON, JCB Press는
allowlist 기반 canonical HTML fetch를 사용한다. 임의 URL은 입력받지 않으며 HTTPS,
도메인, redirect, 응답 크기, content type, canonical URL과 기사 제목 일치를
검증한다. 반환 텍스트는 계속 신뢰하지 않는 외부 입력으로 취급한다.

Curator, Writer와 독립 Verifier 결과를 JSON artifact로 제출한다.

```bash
python3 Automation/run.py automation-submit \
  --vault-dir . --data-dir Automation/data --run-id <run-id> \
  --record-id <record-id> \
  --input Automation/tmp/<artifact>.json
```

Artifact는 관련성 confidence `0.80` 이상, 검증 confidence `0.85` 이상, 모든 verification check 통과, 한국어 요약, 원문 evidence와 identity 일치를 만족해야 한다. 상세 계약은 [artifact schema](../skills/hermes-news-automation/references/artifact-schema.md)에서 관리한다.

문서 검증 후 Telegram 전송과 run 종료:

```bash
python3 Automation/run.py automation-notify \
  --vault-dir . --data-dir Automation/data --run-id <run-id>

python3 Automation/run.py automation-finish \
  --vault-dir . --data-dir Automation/data --run-id <run-id>
```

진단과 비정상 run 종료:

```bash
python3 Automation/run.py automation-status \
  --vault-dir . --data-dir Automation/data --run-id <run-id>

python3 Automation/run.py automation-abort \
  --vault-dir . --data-dir Automation/data --run-id <run-id> \
  --reason "실행을 계속할 수 없는 원인"
```

전체 실행에는 만료 가능한 logical lock이 적용된다. 동일 fingerprint의 `irrelevant`·`quarantined` 결정은 다시 queue에 넣지 않는다. Telegram은 전송 전에 delivery key를 예약해 `sending`, `sent`, `unknown` 상태를 보존하며 불확실한 전송을 자동 반복하지 않는다.

macOS, Linux와 Windows의 Hermes gateway, Skill 연결, token 절약 pre-check와 cron 설정은 [Hermes Agent 무인 자동화 가이드](../HERMES_AUTOMATION_GUIDE.md)를 따른다.

### 자율 운영 switch와 quota gate

`Automation/autonomy.py`는 live OpenAI Codex rate-limit window, 30일 standing authorization switch와 clean `main` coordinator를 확인한 뒤에만 기존 news pre-check를 실행한다. 기본값은 primary window 80% 사용 시 새 agent 작업을 시작하지 않는 fail-closed 정책이며, 허용된 cycle도 최대 1개 item만 처리하고 다음 3시간 cycle에서 quota를 다시 확인한다.

```bash
python3 Automation/autonomy.py status
python3 Automation/autonomy.py on
python3 Automation/autonomy.py off
```

`on`은 switch를 먼저 fail-closed로 끄고 gateway 시작과 고정 cron job resume가 모두 성공한 경우에만 30일 승인 기간을 갱신한다. `off`는 switch를 먼저 끈 뒤 cron job을 pause하며 gateway 자체는 다른 서비스가 사용할 수 있도록 유지한다. controller는 자신이 들어 있는 exact repository path 밖의 control 요청을 거부한다. 작업 로그 파일명은 다음 명령으로 충돌 없이 생성한다.

cron wrapper는 [hermes-news-autonomy-wrapper.py](hermes-news-autonomy-wrapper.py)를 `~/.hermes/scripts/hermes-news-autonomy.py`에 mode `0700`으로 설치한다. Hermes scheduler는 pre-run script를 script directory에서 실행하므로 `~/.hermes/scripts/hermes-news-autonomy.workspace`에 repository 절대 경로를 mode `0600`으로 기록한다. `HERMES_NEWS_WORKSPACE`가 명시되면 환경변수가 이 파일보다 우선한다. repository fetch URL과 push URL은 모두 allowlist를 통과해야 한다.

```bash
python3 Automation/autonomy.py task-log \
  --task-id <run-or-task-id> \
  --slug <short-name>
```

병렬 task는 각자 `automation/*` branch와 Git worktree를 사용하고 [Work Logs](../Work%20Logs/README.md)에 독립 로그 파일을 생성한다. 자동화가 허용하는 외부 변경은 해당 branch push, PR 생성·수정과 고정 Telegram recipient 알림까지이며 merge는 수행하지 않는다.

## 데이터 구조

```text
Automation/data/
├── raw/<source-id>/
│   ├── <run-id>.<json|xml|html|bin>
│   └── <run-id>.meta.json
├── normalized/
│   ├── current/<source-id>.jsonl
│   └── snapshots/<source-id>/<run-id>.jsonl
├── quarantine/<source-id>/<run-id>.jsonl
├── state/<source-id>.json
└── automation/
    ├── active-run.json
    ├── decisions.json
    ├── deliveries.json
    ├── events.json
    └── runs/<run-id>/
        ├── manifest.json
        ├── queue.json
        └── artifacts/<record-id>.json
```

정규화 레코드의 핵심 필드는 다음과 같다.

- `id`, `schema_version`
- `source_id`, `organization`, `channel`
- `title`, `url`, `canonical_url`
- `published_at`, `discovered_at`
- `language`, `official`, `discovery_method`
- 선택 필드: `category`, `description`, `external_id`, `metadata`

`current`는 지금까지 확인한 레코드의 누적 정상 상태다. `snapshots`는 실행 시점에 출처가 반환한 목록이며, `raw`는 파싱 전 원본이다.

## 품질 게이트와 장애 처리

다음 조건에서는 해당 실행을 실패로 기록하고 기존 `current`를 보존한다.

- HTTP 접근 차단, 일시 오류, timeout 또는 허용되지 않은 redirect
- 최초 URI와 redirect 목적지의 HTTPS·도메인 allowlist 위반
- 응답 크기 제한 초과
- 파서가 인식할 수 없는 응답 구조
- 후보 0건
- 모든 후보의 정규화·검증 실패
- Source Registry에 지정한 최대 격리 비율 초과

상태는 `healthy`, `degraded`, `unhealthy`로 기록한다. 연속 실패 3회부터 `unhealthy`가 된다. Source report의 `retryable` 분류와 item의 `retryable` 상태는 다음 cron 실행에서 재평가한다. 출처별 지수 backoff와 circuit breaker는 아직 구현하지 않았다.

## 테스트

테스트는 네트워크 없이 fixture만 사용한다.

```bash
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover \
  -s Automation/tests \
  -v
```

현재 테스트 범위:

- American Express AEM JSON, UnionPay JSON, JCB JSON, RSS·Atom, Visa Press·Release Notes HTML 파싱
- 날짜와 URL 정규화
- 공식 도메인 검증
- 안정적인 ID와 멱등성
- 신규·수정·동일 레코드 판정
- 수집 실패와 빈 snapshot 발생 시 이전 상태 보존
- Source Registry 타입과 source 선택 검증
- 네트워크 요청 전 최초 URI·redirect 목적지 차단
- Vault 필수 identity field, 안정 ID와 canonical URL 일치 검증
- 중복 `record_id` 탐지와 `create`·`skip`·`update_pending` 판정
- 공식·편집 출처 분류와 Telegram 원문 보존 분할·전송 오류 처리
- logical run lock과 겹침 실행 차단
- 반복 snapshot의 문서·알림 멱등성
- agent artifact threshold, 독립 verification check와 prompt injection 복제 차단
- Obsidian 원자 저장, 결정 ledger와 Telegram delivery ledger

## 확장 경계

새 출처 유형은 `adapters`에 `parse(source, response)` 계약을 구현하고 adapter registry에 등록한다. 수집 전후 이벤트는 `Hook` 계약으로 분리해 두었으며, 향후 관측, 알림, skill 또는 agent orchestration을 연결할 수 있다.

다음 단계 후보는 다음과 같다.

1. EMVCo 규격과 PCI SSC 문서함의 항목 단위 변경 감지
2. Mastercard 등 직접 접근이 제한된 출처의 공식 RSS·API 재확인
3. 출처별 본문 추출 품질 향상과 근거 보존
4. 실제 자료 표본을 이용한 `event_key` 생성 품질과 대표 자료 선택 보정
5. 출처별 retry backoff, circuit breaker와 운영 지표
6. 자동 일간·주간 Digest
7. API와 frontend app
8. 검토 완료 데이터를 이용한 newsletter

frontend와 newsletter는 이 수집 데이터의 소비자다. 수집·정규화 계층은 특정 UI나 발행 채널에 종속되지 않도록 유지한다.

## 현재 한계

- 공식 출처 9개와 편집 언론 4개를 운영 코드로 승격했다.
- 출처별 전체 목록을 수집하며 `freshness_days` 기반 증분 요청은 아직 적용하지 않는다.
- 본문 추출, 관련성 분류와 의미 검증은 Python 코드가 아니라 Hermes Skill과 agent toolset에 의존한다.
- 같은 `event_key`의 두 번째 문서는 발행하지 않지만 event key 자체는 agent 판단이므로 실제 표본을 이용한 품질 보정이 필요하다.
- Telegram Bot API는 idempotency key를 지원하지 않으므로 timeout 시 delivery를 `unknown`으로 고정하고 자동 재전송하지 않는다.
- source별 지수 backoff, circuit breaker와 자동 Digest는 아직 없다.
- 기여 가이드, 행동 강령과 보안 제보 정책은 아직 없다.
