# Hermes Agent 최소 수집기

> 기준일: 2026-07-24
> 상태: Alpha — 공식 출처 메타데이터 수집과 보존 계층 구현
> 라이선스: [Apache License 2.0](../LICENSE)

Hermes Agent의 첫 번째 실행 가능한 수집기다. 공식 공개 출처에서 제목, 원문 URL, 게시일과 설명을 가져와 공통 레코드로 정규화한다. 현재 단계에서는 원문 본문 복제, LLM 요약, Obsidian 문서 생성, 뉴스레터 발행을 수행하지 않는다.

## 현재 지원 출처

| Source ID | 조직 | 채널 | 방식 |
| --- | --- | --- | --- |
| `visa-press` | Visa | Press release | 공식 목록 HTML |
| `jcb-press` | JCB | Press release | 공식 JSON |
| `emvco-news` | EMVCo | News | 공식 RSS |
| `pci-blog` | PCI Security Standards Council | Blog | 공식 RSS |

출처의 URI, 허용 도메인과 품질 기준은 [config/sources.json](./config/sources.json)에서 관리한다. 배포 패키지에는 같은 내용의 기본 Registry가 포함되며 테스트에서 두 파일의 일치 여부를 검사한다. 별도 Registry는 전역 `--config` 옵션으로 지정할 수 있다.

## 설계 원칙

- 공식 HTTPS 출처와 명시된 도메인만 허용한다.
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

- JCB JSON, RSS, Atom, Visa HTML 파싱
- 날짜와 URL 정규화
- 공식 도메인 검증
- 안정적인 ID와 멱등성
- 신규·수정·동일 레코드 판정
- 수집 실패와 빈 snapshot 발생 시 이전 상태 보존
- Source Registry 타입과 source 선택 검증
- 네트워크 요청 전 최초 URI·redirect 목적지 차단

## 확장 경계

새 출처 유형은 `adapters`에 `parse(source, response)` 계약을 구현하고 adapter registry에 등록한다. 수집 전후 이벤트는 `Hook` 계약으로 분리해 두었으며, 향후 관측, 알림, skill 또는 agent orchestration을 연결할 수 있다.

다음 단계 후보는 다음과 같다.

1. GitHub Release와 YouTube용 공식 API·feed adapter
2. Mastercard 등 직접 접근이 제한된 출처의 통제된 fallback
3. 원문 본문 추출과 근거 보존
4. 관련성·중요도 평가와 사람 검토 큐
5. Obsidian 문서 초안 생성
6. scheduler, retry, 알림과 운영 지표
7. API와 frontend app
8. 검토 완료 데이터를 이용한 newsletter

frontend와 newsletter는 이 수집 데이터의 소비자다. 수집·정규화 계층은 특정 UI나 발행 채널에 종속되지 않도록 유지한다.

## 현재 한계

- 네 개 출처만 운영 코드로 승격했다.
- 출처별 전체 목록을 수집하며 `freshness_days` 기반 증분 요청은 아직 적용하지 않는다.
- 본문 추출, 의미 기반 중복, 관련성 분류와 요약은 포함하지 않는다.
- Hook 실패 격리, scheduler, 재시도와 알림은 포함하지 않는다.
- 기여 가이드, 행동 강령과 보안 제보 정책은 아직 없다.
