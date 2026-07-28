# Hermes Agent 최소 수집기

> 기준일: 2026-07-28
> 상태: Alpha — 공식·편집 출처 메타데이터 수집과 Telegram 알림 구현
> 라이선스: [Apache License 2.0](../LICENSE)

Hermes Agent의 첫 번째 실행 가능한 수집기다. 공식 공개 출처와 선별 편집 언론에서 제목, 원문 URL, 게시일과 설명을 가져와 공통 레코드로 정규화한다. 현재 단계에서는 원문 본문 복제, LLM 요약, Obsidian 문서 자동 생성과 뉴스레터 발행을 수행하지 않는다.

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
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
```

전체 활성 출처 수집:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent collect
```

특정 출처만 수집:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent collect \
  --source emvco-news \
  --source pci-blog
```

상태 확인:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent show-state \
  --source emvco-news
```

Vault 문서 식별 필드와 중복 검사:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes \
  --vault-dir .
```

Writer가 특정 레코드를 처리해야 하는지 확인:

```bash
PYTHONPATH=Automation/src python3 -m hermes_agent note-status \
  --vault-dir . \
  --record-id <record-id> \
  --source-fingerprint <source-fingerprint>
```

결과는 `create`, `skip`, `update_pending` 중 하나다. 같은 `record_id`가 여러 문서에 있거나 ID가 `source_id`·`canonical_url`과 일치하지 않으면 자동 처리를 중단한다. 상세 정책은 [NOTE_IDENTITY_POLICY.md](../NOTE_IDENTITY_POLICY.md)를 따른다.

작성 완료한 Markdown 문서의 전체 내용을 Telegram으로 전송:

```bash
export HERMES_TELEGRAM_BOT_TOKEN="<bot-token>"
export HERMES_TELEGRAM_CHAT_ID="<chat-id>"

PYTHONPATH=Automation/src python3 -m hermes_agent notify-telegram \
  --file "Inbox/example.md"
```

credential은 CLI 인자로 받지 않고 환경변수만 사용한다. 메시지가 Telegram의 4,096자 제한을 넘으면 원문 문자를 보존해 여러 메시지로 분할한다. 실제 전송 전에는 `--dry-run`으로 파일별 메시지 수를 확인할 수 있다. 변수 이름만 담은 예시는 [`.env.example`](../.env.example)에 있으며 실제 값은 commit하지 않는다.

기본 데이터 위치는 `Automation/data/`이며 Git 추적에서 제외된다. 다른 위치를 사용하려면 `collect`와 `show-state`에 `--data-dir`을 지정한다.

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
└── state/<source-id>.json
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

상태는 `healthy`, `degraded`, `unhealthy`로 기록한다. 연속 실패 3회부터 `unhealthy`가 된다. 재시도 실행기와 알림 정책은 아직 구현하지 않았다.

## 테스트

테스트는 네트워크 없이 fixture만 사용한다.

```bash
PYTHONPATH=Automation/src python3 -m unittest discover \
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

## 확장 경계

새 출처 유형은 `adapters`에 `parse(source, response)` 계약을 구현하고 adapter registry에 등록한다. 수집 전후 이벤트는 `Hook` 계약으로 분리해 두었으며, 향후 관측, 알림, skill 또는 agent orchestration을 연결할 수 있다.

다음 단계 후보는 다음과 같다.

1. EMVCo 규격과 PCI SSC 문서함의 항목 단위 변경 감지
2. Mastercard 등 직접 접근이 제한된 출처의 공식 RSS·API 재확인
3. 원문 본문 추출과 근거 보존
4. 관련성·중요도 평가와 사람 검토 큐
5. Obsidian 문서 초안 생성
6. scheduler, retry와 운영 지표
7. API와 frontend app
8. 검토 완료 데이터를 이용한 newsletter

frontend와 newsletter는 이 수집 데이터의 소비자다. 수집·정규화 계층은 특정 UI나 발행 채널에 종속되지 않도록 유지한다.

## 현재 한계

- 공식 출처 9개와 편집 언론 4개를 운영 코드로 승격했다.
- 출처별 전체 목록을 수집하며 `freshness_days` 기반 증분 요청은 아직 적용하지 않는다.
- 본문 추출, 의미 기반 중복, 관련성 분류와 요약은 포함하지 않는다.
- Telegram 문서 전송은 수동 CLI이며 Hook 연동, scheduler와 재시도는 포함하지 않는다.
- 기여 가이드, 행동 강령과 보안 제보 정책은 아직 없다.
