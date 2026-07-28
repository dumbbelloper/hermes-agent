# 작업 로그

Hermes Agent 프로젝트에서 수행한 작업과 검증 결과를 시간순으로 기록한다.

## 2026-07-24 — 프로젝트 초기 설계와 Enterprise AI Guardrails

### 요청과 목적

- 글로벌 결제 생태계의 변화를 수집하고 Obsidian 문서로 정리하는 프로젝트 설명 작성
- 수집 대상, 수집 방법, 문서 형식, agent·skill 확장 방향 설계
- 전체 추적 범위와 초기 범위를 체크리스트로 관리
- GitHub 저장소 관리를 위한 제외 규칙 설정
- AI agent가 회사와 팀 업무에 접근할 때 필요한 조직 수준의 guardrail 설계
- 모든 Git push가 사람의 승인을 거치도록 Codex 전역 설정 적용

### 완료한 작업

- [x] 프로젝트 소개 작성
- [x] 수집·선별·요약·Obsidian 저장 파이프라인 설계
- [x] 전체 추적 범위와 초기 수집 범위 분리
- [x] GitHub용 `.gitignore` 작성
- [x] GitHub 원격 `main` push 상태 확인
- [x] Enterprise AI Agent Guardrails 작성
- [x] Codex 전역 sandbox와 승인 기본값 설정
- [x] Git 실행의 전역 승인 규칙 작성 및 정책 엔진 테스트
- [x] 향후 작업 로그 작성을 프로젝트 지속 지침에 반영

### 주요 문서

- [README.md](./README.md)
- [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)
- [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)
- [AGENTS.md](./AGENTS.md)
- [.gitignore](./.gitignore)

### Enterprise Guardrails 설계 내용

다음 범위를 개인 CLI 설정이 아닌 조직 수준의 통제로 정리했다.

- G0~G4 위험 등급과 승인 정책
- Source control과 협업
- CI/CD, release와 production 배포
- Infrastructure as Code와 cloud
- Kubernetes와 runtime
- Database와 데이터
- Identity, secret과 보안 정책
- 고객 및 외부 커뮤니케이션
- 결제, 재무와 상거래
- 보안 운영과 사고 대응
- 역할 분리, 감사, 복구, break-glass
- Codex command rule의 역할과 우회 가능성

통제 설계는 NIST AI RMF, NIST SP 800-53, OWASP Agentic AI, GitHub, HashiCorp, Kubernetes, OPA, AWS IAM, SLSA, npm, PCI SSC 공식 자료를 기준으로 작성했다.

### Codex 전역 설정 변경

사용자 전역 설정 파일:

```text
/Users/dumbbelloper/.codex/config.toml
```

적용한 기본값:

```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"
approvals_reviewer = "user"

[sandbox_workspace_write]
network_access = false
```

기존 설정 백업:

```text
/Users/dumbbelloper/.codex/config.toml.backup-20260724
```

전역 Git 규칙:

```text
/Users/dumbbelloper/.codex/rules/production-guardrails.rules
```

정책은 sandbox 경계를 넘어야 하는 모든 Git 실행을 `prompt`로 처리한다. 단순한 `["git", "push"]` 규칙보다 넓게 설정해 다음 형태를 포함한다.

- `git push` 뒤의 모든 option, remote, refspec
- `--force-with-lease`, `--force`, `--mirror`
- remote branch와 tag 삭제
- `git -C <path> push`
- `git -c <config> push`
- Git alias
- `/usr/bin/git`
- `/opt/homebrew/bin/git`

### 검증 결과

Codex `execpolicy`로 다음 명령이 모두 `prompt`로 판정되는 것을 확인했다.

```text
git push --force-with-lease origin main
git -C /tmp/example push origin main
/usr/bin/git push --mirror
/opt/homebrew/bin/git push origin main
```

비Git 명령인 `gh pr view 1`은 해당 규칙과 일치하지 않았다. 새 전역 설정을 적용한 상태에서 Codex CLI가 정상적으로 시작되고 규칙 파일을 읽는 것도 확인했다.

GitHub 상태 확인 당시 로컬 `main`과 원격 `origin/main`은 동일한 커밋 `e5934d2`를 가리켰다.

### 주요 결정

1. Agent의 로컬 prompt는 최종 보안 경계가 아니다.
2. Production 안전은 GitHub ruleset, deployment approval, IAM, RBAC, database 권한 등 대상 시스템에서 강제해야 한다.
3. 모든 Git 실행을 규칙 대상으로 삼아 subcommand 앞에 global option이 오는 형태와 Git alias를 포함한다.
4. Project 내부 작업은 자동화하되 network와 workspace 외부 접근은 기본 승인 대상으로 둔다.
5. G4 작업은 agent에게 실행 credential을 제공하지 않는 것을 기본값으로 한다.

### 알려진 한계

- Codex command prefix 규칙은 별도 프로그램이나 script가 내부에서 Git을 실행하는 모든 간접 경로를 완전히 증명하지 못한다.
- 다른 AI 제품, 수동 terminal, CI runner, 유출된 credential에는 Codex 전역 규칙이 적용되지 않는다.
- `danger-full-access`, 무제한 network, 별도 binary 복사본은 로컬 규칙의 보호를 약화할 수 있다.
- 따라서 GitHub branch protection, required review와 production credential 분리가 추가로 필요하다.
- 전역 설정 변경은 새 Codex 세션에서 가장 확실하게 반영된다.

### 다음 작업

- [ ] GitHub `main` branch ruleset 설정
- [ ] GitHub Actions와 production environment 사용 시 required reviewer 설정
- [ ] 조직과 업무에 맞는 G2·G3·G4 승인자 매트릭스 확정
- [ ] 실제 사용하는 cloud, Kubernetes, database, package registry별 강제 정책 작성
- [ ] Source Registry의 실제 공식 URI 조사

### Git 작업

작업 브랜치:

```text
docs/enterprise-ai-guardrails
```

파일별 한글 커밋:

- `76d622c` — 프로젝트 작업 기록 지침 추가 (`AGENTS.md`)
- `285ffb0` — 엔터프라이즈 AI 가드레일 문서 추가 (`ENTERPRISE_AI_GUARDRAILS.md`)
- `9c8d934` — 프로젝트 설계에 가드레일 기준 연결 (`PROJECT_PLAN.md`)
- `9d44f11` — 프로젝트 주요 문서 링크 추가 (`README.md`)
- `ae405bf` — 초기 작업 내역과 검증 결과 기록 (`WORK_LOG.md`)
- `f70158d` — 가드레일 문서 서식 정리 (`ENTERPRISE_AI_GUARDRAILS.md`)

각 커밋은 하나의 파일만 변경하도록 분리했다. `WORK_LOG.md` 역시 별도 커밋으로 관리한다.

생성한 Pull Request:

- [#1 엔터프라이즈 AI 에이전트 가드레일 문서화](https://github.com/dumbbelloper/hermes-agent/pull/1)

작업 브랜치를 `origin/docs/enterprise-ai-guardrails`로 push했고, GitHub CLI 재인증 후 PR을 생성했다.

## 2026-07-24 — 공식 데이터 수집 체계 검증과 결과 문서화

### 요청과 목적

- Obsidian 문서를 자동 생성하기 전에 공식 데이터 수집 품질을 우선 검증
- 글로벌 결제 네트워크와 표준 기관의 실제 수집 경로, 메타데이터, 원문 추출, 관련성, 중복 및 장애 대응 평가
- 반복 실험에서 확인한 성공, 실패와 운영 결정을 사용자가 직접 검토할 수 있는 문서로 작성

### 완료한 작업

- [x] 초기 Source Registry 18개 출처 설계 및 URI·상태 검사
- [x] Visa, Mastercard, American Express, UnionPay, JCB 공식 뉴스 수집 경로 검증
- [x] EMVCo와 PCI SSC 뉴스·기술 문서 채널 검증
- [x] Visa, Mastercard, American Express 기술 채널 변경 감지 검증
- [x] 정규화 레코드 590건의 필수 메타데이터 검사
- [x] 교차 출처 원문 9건과 JCB 시간축 원문 127건 추출 검사
- [x] URL 정규화, 중복 제거, 증분 실행과 수정 감지 검사
- [x] 접근 차단, 일시 오류, 원문 삭제, 파싱 실패와 복구 정책 검사
- [x] 2019~2021년 미사용 시간축 데이터 76건으로 관련성 보존 성능 독립 검증
- [x] 검증 결과와 구현 권장안을 Obsidian 문서로 작성

### 생성·수정한 문서

- [DATA_COLLECTION_VALIDATION_REPORT.md](./DATA_COLLECTION_VALIDATION_REPORT.md) 추가
- [README.md](./README.md)에 검증 보고서 링크 추가
- [WORK_LOG.md](./WORK_LOG.md)에 본 작업 기록 추가

### 주요 검증 결과

| 항목 | 결과 |
| --- | ---: |
| 등록 출처 | 18개 |
| 활성·검증 출처 | 15개 |
| 글로벌 네트워크 뉴스 | 5/5개 조직 |
| EMVCo·PCI SSC 뉴스·문서 | 4/4개 |
| 정규화 목록 데이터 | 590건 |
| 원문 추출 | 136/136건 |
| 기술 출처 변경 감지 | 6/6개 |
| 독립 관련성 검증 | 76건 |
| 최소 관련성 정밀도 | 94.7% |
| 최소 관련성 재현율 | 96.4% |

중복, 동일 입력 재실행, 한 항목 수정, 잘못된 날짜와 도메인, 본문 중복, HTTP 403·429·5xx·404, DNS·timeout, 파싱 실패와 복구 시나리오도 검사했다. 모든 장애 시나리오에서 이전 정상 데이터를 보존하도록 결정했다.

### 주요 결정과 근거

1. `collect`와 `review`는 모두 보존하고 고신뢰 항목만 자동 제외한다.
   - 시간축 독립 검증에서 관련 데이터 보존은 90% 기준을 통과했지만, 세 등급 정확도와 검토 큐 비율은 운영 자동화 기준에 미달했다.
2. 규칙 기반 `collect/review` 자동 우선순위 개선은 중단한다.
   - 보정셋 점수는 높일 수 있었으나 미사용 연도에서 일반화되지 않았다.
3. Mastercard 뉴스는 직접 어댑터가 아니라 통제된 공식 검색 인덱스 폴백으로 격리한다.
   - 일반 HTTP와 헤드리스 브라우저 모두 Akamai에 차단됐고 공격적인 우회를 시도하지 않았다.
4. American Express 뉴스는 홈페이지 카드가 아니라 17개 공식 AEM 카테고리 모델을 사용한다.
5. 출처 실패나 빈 응답이 발생해도 마지막 정상 상태를 덮어쓰지 않는다.
6. 기술 문서, 뉴스, GitHub와 YouTube는 신호와 구조가 다르므로 별도 어댑터와 품질 기준을 사용한다.

### 전역 설정과 외부 시스템 변경

- 없음
- 모든 수집 실험은 공식 공개 원문을 읽기 전용으로 조회했다.
- Git push, PR 생성, 배포 또는 외부 시스템 쓰기는 수행하지 않았다.

### 알려진 한계와 남은 작업

- Mastercard 뉴스룸 직접 자동 수집은 Akamai 차단 때문에 해결되지 않았다.
- `collect/review` 우선순위는 본문 기반 의미 모델과 별도 정답셋 검증 전까지 자동화하지 않는다.
- UnionPay의 현재 공개 개발자 포털 URI는 확인되지 않았다.
- JCB의 별도 공개 개발자 문서 허브는 확인되지 않았다.
- Apple Pay, Samsung Pay, HCE, Ethereum, Solana, 스테이블코인과 국내 카드사는 이번 초기 품질 게이트에 포함하지 않았다.
- 이번 실험 코드는 `/private/tmp`에서 실행했으므로 재현 가능한 프로젝트 코드로 승격하는 작업이 필요하다.

### Git 작업

- 작업 브랜치: `docs/data-collection-validation`
- 파일별 한글 커밋:
  - `8461407` — 데이터 수집 검증 보고서 추가 (`DATA_COLLECTION_VALIDATION_REPORT.md`)
  - `ff25a42` — README에 데이터 수집 검증 보고서 연결 (`README.md`)
  - `9f75f8d` — 데이터 수집 검증 작업 기록 추가 (`WORK_LOG.md`)
  - `0c9e0ed` — 데이터 수집 검증 보고서 서식 보정 (`DATA_COLLECTION_VALIDATION_REPORT.md`)
- 작업 브랜치를 `origin/docs/data-collection-validation`로 push했다.
- 생성한 Pull Request:
  - [#2 공식 데이터 수집 검증 결과 문서화](https://github.com/dumbbelloper/hermes-agent/pull/2)

## 2026-07-24 — 최소 공식 데이터 수집기 구현

### 요청과 목적

- 검증용 실험을 재현 가능한 프로젝트 코드로 승격
- 향후 agent, skill, hook, frontend와 newsletter로 확장할 수 있는 데이터 기반 마련
- Obsidian 문서 생성보다 공식 데이터의 수집·정규화·보존 품질을 우선 확보

### 완료한 작업

- [x] Python 3.9 이상에서 실행되는 표준 라이브러리 기반 패키지 구성
- [x] versioned Source Registry와 엄격한 설정 타입 검증 구현
- [x] Visa 공식 보도자료 HTML adapter 구현
- [x] JCB 공식 보도자료 JSON adapter 구현
- [x] EMVCo와 PCI SSC RSS·Atom adapter 구현
- [x] 공식 도메인 allowlist, URL·날짜·HTML 텍스트 정규화 구현
- [x] 안정적인 레코드 ID, 중복 및 수정 판정 구현
- [x] 원본 응답, SHA-256, snapshot, 누적 정상 상태와 격리 저장 구현
- [x] 빈 snapshot과 장애 발생 시 이전 정상 상태 보존 구현
- [x] source health와 연속 실패 상태 구현
- [x] 향후 skill·알림·관측 연동을 위한 Hook 이벤트 경계 구현
- [x] CLI와 오프라인 fixture 회귀 테스트 구현
- [x] 실제 공식 출처 반복 dry-run과 멱등성 검증
- [x] Apache License 2.0 공식 전문과 package metadata 적용
- [x] wheel에 라이선스와 기본 Source Registry를 포함하는 배포 구조 구현
- [x] 저장소 밖의 가상환경에서 wheel 설치 후 CLI 실행 검증
- [x] 최초 URI와 redirect 목적지의 HTTPS·도메인 사전 차단 구현

### 생성·수정한 파일

- [LICENSE](./LICENSE)
- [pyproject.toml](./pyproject.toml)
- [Automation/README.md](./Automation/README.md)
- [Automation/config/sources.json](./Automation/config/sources.json)
- [Automation/src/hermes_agent](./Automation/src/hermes_agent)
- [Automation/tests](./Automation/tests)
- [README.md](./README.md)
- [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- [.gitignore](./.gitignore)

### 검증 결과

오프라인 fixture 기반 단위·통합 테스트 21개와 전체 Python compile 검사를 통과했다. Source Registry에는 활성 공식 출처 4개가 등록되어 있다.

2026-07-24 실제 공식 출처 dry-run 결과:

| 출처 | 후보 | 수락 | 격리 | 3차 동일 실행 |
| --- | ---: | ---: | ---: | ---: |
| EMVCo News | 2 | 2 | 0 | 2 unchanged |
| JCB Press | 454 | 454 | 0 | 454 unchanged |
| PCI SSC Blog | 50 | 50 | 0 | 50 unchanged |
| Visa Press | 95 | 95 | 0 | 95 unchanged |
| 합계 | 601 | 601 | 0 | 601 unchanged |

첫 실행에서 JCB의 비정형 날짜 `FEB, 05,2024` 한 건을 발견해 격리했다. 날짜 정규화 규칙과 회귀 테스트를 추가한 후 454건 전부를 수락했다. HTML 설명의 markup과 구두점 공백도 정리했으며, 같은 코드로 세 번째 실행했을 때 601건이 모두 `unchanged`로 판정됐다.

검증 명령:

```text
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPATH=Automation/src python3 -m compileall -q Automation/src Automation/tests
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent collect --data-dir <임시 디렉터리>
git diff --check
```

별도의 깨끗한 Python 3.9 가상환경에서 `hermes_agent-0.1.0-py3-none-any.whl`을 생성했다. wheel에 공식 `LICENSE`와 기본 Source Registry가 포함된 것을 확인하고, 저장소 밖에서 설치한 `hermes-collector validate-registry`가 4개 출처를 정상적으로 읽는 것도 검증했다.

보안 재검토에서 redirect 이후에만 도메인을 확인하던 사각지대를 발견했다. 최초 URI와 redirect 목적지를 실제 요청 전에 HTTPS·allowlist로 검사하도록 변경하고, 허용되지 않은 최초 URI·redirect와 허용된 subdomain redirect 테스트를 추가했다. 강화 후 실제 공식 출처 4곳을 다시 수집해 601건 모두 `unchanged`, 격리 0건임을 확인했다.

### 주요 결정과 근거

1. runtime dependency를 추가하지 않고 표준 라이브러리로 최소 수집기를 시작했다.
   - 설치·공급망 부담을 줄이고 adapter 계약과 데이터 품질을 먼저 검증하기 위함이다.
2. 원본, 실행 snapshot과 누적 정상 상태를 분리했다.
   - 출처 변경을 재현하고 일시 누락이나 장애로 기존 데이터를 잃지 않기 위함이다.
3. 빈 응답과 과도한 격리는 성공으로 간주하지 않는다.
   - 파서 파손을 정상적인 신규 0건으로 오판하는 것을 막기 위함이다.
4. UI, 요약과 newsletter를 수집 계층에서 분리했다.
   - 향후 여러 소비자가 같은 검증 데이터를 사용할 수 있게 하기 위함이다.
5. 공개 라이선스는 Apache License 2.0으로 확정했다.
   - 사용자의 명시적 결정에 따라 Apache 공식 라이선스 전문을 루트 `LICENSE`에 추가하고 패키지 메타데이터에 반영했다.

### 전역 설정과 외부 시스템 변경

- 없음
- 공식 공개 URI 4곳을 읽기 전용으로 조회했다.
- 실제 수집 결과는 `/private/tmp` 아래에 저장했으며 저장소에는 포함하지 않았다.
- 외부 package index에서는 임시 가상환경에 빌드 도구만 내려받았고 프로젝트 package를 게시하지 않았다.
- package 게시나 배포는 수행하지 않았다.

### Git 작업

- 작업 브랜치: `feat/minimum-collector`
- 한글 로컬 커밋:
  - `af29f4a` — 최소 공식 데이터 수집기 구현
  - `4137e20` — 수집 실행 데이터 Git 추적 제외
  - `09e5591` — 최소 수집기 실행과 확장 구조 문서화
  - `f2e3da1` — README에 라이선스와 최소 수집기 연결
  - `d26c0dd` — 프로젝트 계획에 최소 수집기 현황 반영
- `WORK_LOG.md`는 본 기록을 별도 커밋으로 관리한다.
- 작업 브랜치를 `origin/feat/minimum-collector`로 push했다.
- 생성한 Pull Request:
  - [#3 최소 공식 데이터 수집기 구현](https://github.com/dumbbelloper/hermes-agent/pull/3)

### 알려진 한계와 남은 작업

- GitHub Release, YouTube, Mastercard fallback과 국내 카드사 adapter는 아직 구현하지 않았다.
- 현재는 목록 메타데이터만 수집하며 원문 본문, 관련성, 요약과 Obsidian 문서는 생성하지 않는다.
- freshness 기반 요청, scheduler, retry, 알림과 운영 지표는 아직 구현하지 않았다.
- Hook 구현체의 실패 격리 정책은 후속 설계가 필요하다.
- `CONTRIBUTING.md`, 행동 강령, 보안 정책과 CI는 아직 없다.

## 2026-07-28 — 구현 진행상황과 문서 동기화 점검

### 요청과 목적

- 현재 저장소의 구현·Git·GitHub 상태를 기준으로 프로젝트 문서의 진행상황 표시가 맞는지 점검
- 완료·미완료 범위, 과거 검증 결과와 현재 운영 코드의 차이를 구분
- 문서 갱신이 필요한 항목과 우선순위를 후속 작업자가 확인할 수 있게 기록

### 수행한 점검

- 로컬 브랜치, 작업 트리, 원격 추적 브랜치와 `main` 대비 커밋 상태 확인
- GitHub Pull Request 1~3의 현재 병합 상태와 status check 유무를 읽기 전용으로 확인
- `README.md`, 프로젝트 계획, 범위 체크리스트, 수집 검증 보고서, 가드레일, 자동화 문서와 작업 로그 상호 대조
- Source Registry, adapter, pipeline, 보존 상태, CLI와 테스트 구현을 문서의 완료 주장과 대조
- 내부 Markdown 링크가 가리키는 프로젝트 파일과 디렉터리의 존재 여부 확인

### 확인한 현재 상태

- 최소 수집기 PR [#3](https://github.com/dumbbelloper/hermes-agent/pull/3)은 2026-07-24에 병합됐다. PR 1~3은 모두 병합 상태다.
- 로컬은 여전히 `feat/minimum-collector` 브랜치이며 로컬 `origin/main`은 PR #3 병합 전 상태다. 작업 브랜치와 그 원격 추적 브랜치는 같은 커밋이고 작업 트리는 이번 기록 전까지 깨끗했다.
- 운영 코드의 활성 Source Registry는 Visa, JCB, EMVCo, PCI SSC 네 출처다.
- 현재 구현은 목록 메타데이터 수집·정규화·보존까지이며 원문 본문 수집, 관련성 분류, 요약, Obsidian Inbox 작성, GitHub Release·YouTube adapter, scheduler·retry·알림은 없다.

### 문서 동기화 점검 결과

1. **높음 — 범위 조사 체크리스트가 검증 보고서와 불일치**
   - [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)의 `초기 범위 조사 현황`은 “실제 작업 완료 상태”라고 정의하지만 공통 조사 항목과 대상 7개가 모두 미완료다.
   - 반면 [DATA_COLLECTION_VALIDATION_REPORT.md](./DATA_COLLECTION_VALIDATION_REPORT.md)와 이 작업 로그는 18개 출처 등록, 15개 활성 검증과 대상별 URI·수집 방식 조사를 완료했다고 기록한다.
   - 조사 완료, 부분 완료, 구현 완료를 분리해 체크리스트를 갱신해야 한다.
2. **중간 — 프로젝트 계획의 사전 결정·단계 상태가 일부 과거 상태**
   - [PROJECT_PLAN.md](./PROJECT_PLAN.md)의 `구현 전에 결정할 사항`에 구현 언어와 런타임이 미결정으로 남아 있지만 Python 3.9 이상으로 이미 결정·구현됐다.
   - Phase 1 정의에는 GitHub Release와 Inbox 문서 생성까지 포함되지만 현재 “최소 수집기”는 그보다 작은 Alpha 범위다. 구현 현황 체크박스는 정확하므로 Phase 상태를 `부분 완료`로 명시하는 편이 명확하다.
3. **중간 — 가드레일의 현재 기능 설명이 구현보다 앞섬**
   - [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)는 현재 기능을 “공개 자료 수집과 Obsidian 문서 작성”으로 표현한다.
   - 실제 코드는 Obsidian 문서를 작성하지 않으므로 “현재 구현”과 “향후 허용할 기능”을 구분해야 한다.
4. **중간 — GitHub와 로컬 진행상황 표시가 최신이 아님**
   - 작업 로그는 PR 생성까지만 기록하고 현재 병합 상태를 별도로 요약하지 않았다.
   - 로컬 `main`과 `origin/main` 참조도 PR #3 병합 커밋을 반영하지 않아, 로컬 Git 상태만 보면 구현이 아직 `main`에 들어가지 않은 것처럼 보인다.
5. **낮음 — README의 현재형 설명이 Alpha 범위와 혼동될 수 있음**
   - [README.md](./README.md)는 수집 자료를 요약·키워드와 함께 문서화한다고 현재형으로 설명하지만 실제 자동화는 아직 메타데이터 수집까지만 지원한다.
   - 프로젝트 목표와 현재 구현 상태를 짧게 분리하면 [Automation/README.md](./Automation/README.md)와 더 잘 맞는다.
6. **낮음 — 검증 보고서의 역사적 상태가 현재 상태처럼 보일 수 있음**
   - 검증 보고서의 `수집기 구현 전` 상태는 2026-07-24 당시에는 정확하지만 현재 문서 체계에서는 역사적 스냅샷임을 더 명확히 표시할 필요가 있다.

### 생성·수정한 문서와 파일

- [WORK_LOG.md](./WORK_LOG.md)에 이번 점검 기록 추가
- 진단 요청 범위를 유지하기 위해 다른 문서와 구현 코드는 수정하지 않음

### 실행한 검증과 결과

```text
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  PYTHONPATH=Automation/src python3 -m compileall -q Automation/src Automation/tests
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
git diff --check
```

- 단위·통합 테스트 21개 통과
- Python 전체 compile 검사 통과
- Registry schema `1.0`, 활성 출처 4개 검증 통과
- `git diff --check` 통과
- 기본 compile 실행은 sandbox 밖의 사용자 cache 경로에 쓰려다 권한 오류가 발생했다. bytecode cache를 `/private/tmp`로 지정한 동일 검사에서는 통과했다.

### 결정과 근거

1. 과거 실험의 18개 Source Registry와 현재 운영 코드의 4개 Registry는 서로 다른 단계의 결과이므로 숫자 자체를 오류로 판정하지 않았다.
2. 기준일이 명시된 과거 보고서는 보존하고, 현재 상태 문서에서 후속 구현으로 연결하는 방식이 이력 추적에 적합하다고 판단했다.
3. 사용자의 요청은 점검이므로 동기화 수정은 수행하지 않고 불일치와 우선순위만 기록했다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- GitHub PR 상태를 읽기 전용으로 조회했으며 Git fetch, push, PR 수정, 배포는 수행하지 않았다.

### 알려진 한계와 남은 작업

- 2026-07-28 현재 공식 출처 4곳의 실시간 수집은 다시 실행하지 않았다. 이번 결과는 코드, 오프라인 회귀 테스트와 기존 검증 기록의 동기화 점검이다.
- 로컬 원격 참조를 갱신하지 않았으므로 실제 GitHub `main`의 병합 커밋은 GitHub 조회 결과로 확인했다.
- 위 여섯 문서 불일치는 아직 수정되지 않았으며, 우선 범위 체크리스트와 프로젝트 계획부터 갱신해야 한다.

## 2026-07-28 — 문서 현행화, 운영 출처 확정과 초기 수집 문서 작성

### 요청과 목적

- 최소 수집기 진척도에 맞춰 프로젝트 문서를 최신 상태로 현행화
- Akamai, Cloudflare 등 WAF 차단이나 브라우저 의존으로 수집이 어려운 사이트를 우회하지 않고 제외
- 운영 수집 대상, 추가 구현 후보와 수집 불가·제외 출처의 사유를 명시적으로 분류
- 수집 대상이 확정되면 실제 수집을 시작하고 Obsidian에서 검토할 초기 문서 작성

### 수행한 변경

- 프로젝트 목표와 현재 자동화 범위를 분리하고 2026-07-28 구현 상태를 문서에 반영
- Phase 0 완료, Phase 1 부분 완료와 결정·미결정 항목을 프로젝트 계획에 표시
- 초기 조사 체크리스트의 실제 완료 상태를 검증 보고서와 일치시킴
- 과거 18개 실험 Registry와 현재 4개 운영 Registry를 구분
- 운영·후보·제외 판정 기준과 출처별 근거를 별도 출처 문서로 확정
- 가드레일의 현재 기능 설명을 메타데이터 수집과 사람 검토 기반 문서 작성으로 수정
- 확정된 공식 출처 4곳을 두 번 실제 수집해 결과와 멱등성 확인
- 최신 수집 자료 중 기술·표준·보안 가치가 높은 자료를 출처별 1건씩 선별
- Inbox 초안 4건, Concepts 노트 4건, 초기 Digest 1건과 수집 문서 템플릿 작성

### 운영 출처 판정

현재 고정 운영 출처:

| Source ID | 조직·채널 | 방식 |
| --- | --- | --- |
| `visa-press` | Visa Press Releases | 정적 HTML |
| `jcb-press` | JCB Press | 공식 JSON |
| `emvco-news` | EMVCo News | 공식 RSS |
| `pci-blog` | PCI SSC Blog | 공식 RSS |

추가 구현 후보는 UnionPay Media Center, Visa Developer Release Notes, American Express Newsroom AEM model, EMVCo Specifications, PCI SSC Document Library와 allowlist 기반 GitHub Release로 분리했다.

운영 제외:

- Mastercard 뉴스룸: 일반 HTTP 수집에서 Akamai `Access Denied` 403
- Mastercard Developer Products와 American Express Developer Documentation: 본문 항목이 없는 JavaScript 셸
- UnionPay·JCB의 확인되지 않은 별도 개발자 문서 URI
- 저신호 JCB YouTube와 결제 네트워크 GitHub 조직 전체
- 검색 인덱스 또는 브라우저 자동화 기반 폴백

이번 재검증에서 Cloudflare 차단 출처는 별도로 확인되지 않았지만 동일한 제외 원칙을 문서화했다.

### 실제 수집 결과

2026-07-28 첫 실행:

| 출처 | 후보 | 수락 | 격리 | 신규 |
| --- | ---: | ---: | ---: | ---: |
| EMVCo News | 2 | 2 | 0 | 2 |
| JCB Press | 454 | 454 | 0 | 454 |
| PCI SSC Blog | 50 | 50 | 0 | 50 |
| Visa Press | 95 | 95 | 0 | 95 |
| 합계 | 601 | 601 | 0 | 601 |

즉시 반복 실행에서 601건 모두 `unchanged`, 신규·수정·격리 0건이었다. 수집 원본과 상태는 Git에서 제외된 `Automation/data/`에 저장했다.

### 생성·수정한 문서와 파일

현행화:

- [README.md](./README.md)
- [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)
- [DATA_COLLECTION_VALIDATION_REPORT.md](./DATA_COLLECTION_VALIDATION_REPORT.md)
- [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)
- [Automation/README.md](./Automation/README.md)

출처와 템플릿:

- [SOURCE_CATALOG.md](./SOURCE_CATALOG.md)
- [Templates/Collected Note.md](./Templates/Collected%20Note.md)

초기 수집 문서:

- [Visa Stablecoin Platform](./Inbox/2026-07-16%20Visa%20Introduces%20Platform%20for%20Stablecoin%20Minting%20Movement%20and%20Management.md)
- [JCB·Circle Stablecoin MOU](./Inbox/2026-07-14%20JCB%20Signs%20MOU%20with%20Circle%20to%20Explore%20Stablecoin%20Collaboration.md)
- [EMVCo Digital Payment Credential](./Inbox/2026-06-23%20EMVCo%20Requests%20Feedback%20on%20Verifiable%20Digital%20Credentials.md)
- [PCI DSS와 NIST CSF mapping](./Inbox/2026-07-23%20Mapping%20PCI%20DSS%204.0.1%20to%20NIST%20CSF%202.0.md)
- [2026-07-28 초기 수집 브리핑](./Digests/2026-07-28%20초기%20수집%20브리핑.md)

개념 노트:

- [Stablecoin](./Concepts/Stablecoin.md)
- [Digital Payment Credential](./Concepts/Digital%20Payment%20Credential.md)
- [PCI DSS](./Concepts/PCI%20DSS.md)
- [NIST Cybersecurity Framework](./Concepts/NIST%20Cybersecurity%20Framework.md)

### 실행한 검증과 결과

```text
PYTHONPATH=Automation/src python3 -m hermes_agent collect --data-dir Automation/data
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  PYTHONPATH=Automation/src python3 -m compileall -q Automation/src Automation/tests
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
git diff --check
```

- 실제 수집 2회 모두 출처 4/4 성공
- 첫 실행 601건 수락, 격리 0건
- 두 번째 실행 601건 모두 변경 없음
- 오프라인 단위·통합 테스트 21개 통과
- Python 전체 compile 검사 통과
- Registry schema `1.0`, 활성 출처 4개 검증 통과
- `git diff --check` 통과
- 초기 문서의 Obsidian wiki link가 모두 실제 Inbox·Concepts 문서로 연결됨

### 결정과 근거

1. 운영 범위는 조직 대표성을 맞추기보다 안정적으로 직접 수집 가능한 공식 출처를 우선해 4개로 고정했다.
2. Mastercard를 억지로 포함하기 위해 검색 인덱스나 브라우저 폴백을 유지하지 않는다.
3. 일반 HTTP 200만으로 운영 출처에 추가하지 않고 항목 단위 parser, fixture와 반복 수집 검증을 승격 조건으로 삼는다.
4. 601건을 한꺼번에 문서화하지 않고 출처별 고가치 항목 1건으로 문서 흐름과 품질을 먼저 검증한다.
5. 발표 사실과 해석을 구분하고 beta, MOU·PoC, draft처럼 성숙도를 문서에 명시한다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 전역 설정 변경 없음
- 공식 공개 사이트를 읽기 전용으로 조회
- 공식 출처에 대한 로그인, credential 사용, WAF 우회, 외부 시스템 쓰기와 배포는 수행하지 않음
- GitHub에는 아래 작업 브랜치 push와 Pull Request 생성만 수행
- 로컬 `Automation/data/`에 수집 원본·정규화 결과·상태 파일 생성. 해당 경로는 Git 추적에서 제외됨

### Git 작업

- 작업 브랜치: `docs/source-catalog-and-initial-notes`
- 커밋:
  - `c294b56` — 수집 출처 확정과 초기 문서 작성
- 작업 브랜치를 `origin/docs/source-catalog-and-initial-notes`로 push
- 생성한 Pull Request:
  - [#4 수집 출처 확정과 초기 Obsidian 문서 작성](https://github.com/dumbbelloper/hermes-agent/pull/4)

### 알려진 한계와 남은 작업

- Inbox 문서 작성은 아직 자동화되지 않아 이번 4건은 실제 수집 결과와 공식 원문을 사람이 검토하는 방식으로 작성했다.
- 전체 601건 중 4건만 선별했다. 중요도 기준과 일간 문서 상한은 이 초안을 검토한 뒤 확정해야 한다.
- 추가 구현 후보는 Source Registry에 포함하지 않았으며 adapter와 회귀 테스트 전에는 수집하지 않는다.
- 공식 사이트 구조와 접근 정책은 변경될 수 있으므로 출처 판정 기준일을 유지하고 변경 시 재검증해야 한다.
- scheduler, retry, 알림, 원문 본문 추출과 Inbox 자동 생성은 아직 구현되지 않았다.

## 2026-07-28 — Vault 문서 식별과 중복 작성 방지 구현

### 요청과 목적

- 하루에 여러 번 Collector·Writer Skill 또는 Hermes Agent가 실행돼도 같은 수집 자료의 문서를 중복 생성하지 않게 함
- 사람이 작성한 기존 문서와 Hermes가 작성할 문서를 식별하고 원문 메타데이터 변경을 구분
- 기존 Inbox 문서에 실제 수집 레코드의 안정 ID를 연결
- 별도 작업 브랜치에서 검증, commit, push와 Pull Request 생성

### 수행한 변경

- `source_id`와 `canonical_url`의 SHA-256인 기존 `Record.id`를 문서의 `record_id`로 승격
- `discovered_at`을 제외한 정규화 레코드 hash를 `source_fingerprint`로 기록
- `Inbox/`와 `Notes/` Frontmatter를 실행 시 scan하는 `VaultNoteIndex` 구현
- 동일 자료의 상태를 `create`, `skip`, `update_pending`으로 판정하는 API 구현
- 필수 identity field, SHA-256 형식, canonical URL, 파생 ID와 중복 ID 검증 구현
- `validate-notes`와 `note-status` CLI 추가
- 기존 Inbox 4건에 실제 `record_id`, `source_fingerprint`, `canonical_url`과 작성 주체·검사 시각 추가
- 수집 문서 템플릿과 프로젝트·자동화 문서에 identity field와 실행법 반영
- 문서 식별, 멱등성, 충돌과 향후 migration 기준을 별도 정책으로 작성

### 생성·수정한 문서와 파일

구현과 테스트:

- [Automation/src/hermes_agent/note_index.py](./Automation/src/hermes_agent/note_index.py)
- [Automation/src/hermes_agent/cli.py](./Automation/src/hermes_agent/cli.py)
- [Automation/src/hermes_agent/__init__.py](./Automation/src/hermes_agent/__init__.py)
- [Automation/tests/test_note_index.py](./Automation/tests/test_note_index.py)

정책과 사용법:

- [NOTE_IDENTITY_POLICY.md](./NOTE_IDENTITY_POLICY.md)
- [Templates/Collected Note.md](./Templates/Collected%20Note.md)
- [Automation/README.md](./Automation/README.md)
- [PROJECT_PLAN.md](./PROJECT_PLAN.md)
- [README.md](./README.md)

기존 문서 backfill:

- [Visa Stablecoin Platform](./Inbox/2026-07-16%20Visa%20Introduces%20Platform%20for%20Stablecoin%20Minting%20Movement%20and%20Management.md)
- [JCB·Circle Stablecoin MOU](./Inbox/2026-07-14%20JCB%20Signs%20MOU%20with%20Circle%20to%20Explore%20Stablecoin%20Collaboration.md)
- [EMVCo Digital Payment Credential](./Inbox/2026-06-23%20EMVCo%20Requests%20Feedback%20on%20Verifiable%20Digital%20Credentials.md)
- [PCI DSS와 NIST CSF mapping](./Inbox/2026-07-23%20Mapping%20PCI%20DSS%204.0.1%20to%20NIST%20CSF%202.0.md)

### 실행한 검증과 결과

```text
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  PYTHONPATH=Automation/src python3 -m compileall -q Automation/src Automation/tests
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes --vault-dir .
PYTHONPATH=Automation/src python3 -m hermes_agent note-status ...
git diff --check
```

- 전체 단위·통합 테스트 26개 통과
- Python 전체 compile 검사 통과
- Source Registry 4개 검증 통과
- Vault Inbox 4건 검증: `status: ok`, issue 0건
- 현재 fingerprint 입력: `skip`
- 같은 ID와 변경된 fingerprint 입력: `update_pending`
- 새로운 ID 입력: `create`
- 중복 ID, 파생 ID 불일치, 필수 field 누락과 비정규 URL 회귀 테스트 통과
- Markdown 상대 링크와 Obsidian wiki link 검증 통과
- fail-closed 직접 API 검사를 추가한 첫 실행에서 invalid Vault의 신규 ID가 `create`로 먼저 반환되는 테스트 실패를 발견했다. validation issue를 신규 판정보다 먼저 거부하도록 순서를 수정한 후 전체 26개 테스트가 통과했다.

### 결정과 근거

1. 영구 note index 파일 대신 실행 시 Vault를 scan한다.
   - 여러 PC·branch·Obsidian 변경 이후 stale cache가 기준 데이터가 되는 것을 피하기 위함이다.
2. `record_id`와 `source_fingerprint`의 역할을 분리한다.
   - 같은 자료의 정체성과 같은 자료 내부의 변경을 독립적으로 판정하기 위함이다.
3. 같은 ID의 원문 변경은 자동 덮어쓰기 대신 `update_pending`으로 보낸다.
   - 사람이 작성한 요약과 해석을 보존하기 위함이다.
4. 서로 다른 공식 출처의 같은 사건은 다른 `record_id`로 유지한다.
   - 출처별 주장과 원문을 보존하고 사건 단위 통합은 별도 event key로 처리하기 위함이다.
5. 기존 Inbox 4건은 `created_by: manual`로 기록했다.
   - 실제 작성 주체를 보존하고 향후 Hermes 생성 문서와 구분하기 위함이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 전역 설정 변경 없음
- 본 구현과 검증은 로컬 파일과 기존 수집 데이터만 사용
- 외부 공식 사이트 조회, credential 사용과 배포는 수행하지 않음
- GitHub에는 아래 작업 브랜치 push와 Pull Request 생성만 수행

### Git 작업

- 작업 브랜치: `feat/note-idempotency`
- 커밋:
  - `ef083d2` — Vault 문서 중복 방지 기반 구현
- 작업 브랜치를 `origin/feat/note-idempotency`로 push
- 생성한 Pull Request:
  - [#5 Vault 문서 식별과 중복 작성 방지 구현](https://github.com/dumbbelloper/hermes-agent/pull/5)

### 알려진 한계와 남은 작업

- 현재 기능은 Writer의 판정까지만 제공하며 `create` 문서 생성이나 `update_pending` Frontmatter 갱신은 아직 수행하지 않는다.
- 자동·수동 본문을 안전하게 부분 갱신하려면 managed block 경계를 추가로 설계해야 한다.
- Source ID 변경 또는 공식 URL 이전으로 `record_id`가 바뀌는 경우 alias migration 기능이 필요하다.
- 같은 사건의 여러 공식 발표를 묶는 event key와 의미 기반 중복 판정은 별도 작업이다.

## 2026-07-28 — 현시점 수집 대상 상태 점검

### 요청과 목적

- 현재 Source Registry의 운영 수집 대상 확인
- 운영 4개 출처의 실제 접근·파싱·수락 상태와 최신 게시일 재검증
- 추가 구현 후보와 주요 제외 출처의 일반 HTTP 접근 상태가 기존 분류와 일치하는지 확인

### 수행한 점검과 결과

운영 출처를 임시 데이터 경로에서 실제 수집했다.

| Source ID | 결과 | 수락 | 격리 | 최신 게시일 |
| --- | --- | ---: | ---: | --- |
| `visa-press` | 성공 | 95 | 0 | 2026-07-22 |
| `jcb-press` | 성공 | 454 | 0 | 2026-07-14 |
| `emvco-news` | 성공 | 2 | 0 | 2026-07-15 |
| `pci-blog` | 성공 | 50 | 0 | 2026-07-27 |
| 합계 | 4/4 성공 | 601 | 0 |  |

후보 출처:

- UnionPay Media Center: HTTP 200, 정적 HTML
- Visa Developer Release Notes: HTTP 200, 정적 HTML
- American Express Newsroom: HTTP 200이나 4,253 byte의 불완전한 홈페이지 응답
- EMVCo Specifications: HTTP 200, 검색 페이지로 redirect
- PCI SSC Document Library: HTTP 200

제외 출처:

- Mastercard Press Releases: Akamai `Access Denied` HTTP 403 유지
- Mastercard Developer Products: HTTP 200이나 1,629 byte JavaScript 셸
- American Express Developer Documentation: HTTP 200이나 1,864 byte JavaScript 셸

### 생성·수정한 문서와 파일

- [WORK_LOG.md](./WORK_LOG.md)에 점검 결과 추가
- Source Registry, 출처 분류와 구현 코드는 변경하지 않음
- 실제 수집 결과는 `/private/tmp/hermes-target-check.HHtbr1`에 저장

### 실행한 검증

```text
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent collect --data-dir <임시 경로>
curl -L -sS --max-time 25 <후보·제외 공식 URI>
```

- Registry schema `1.0`, 활성 출처 4개 확인
- 운영 출처 4/4 수집 성공
- 후보·제외 출처 HTTP 상태와 응답 크기 확인

### 결정과 근거

1. 현재 고정 운영 범위는 Visa Press, JCB Press, EMVCo News와 PCI SSC Blog 4개를 유지한다.
2. 후보 출처는 HTTP 200만으로 승격하지 않는다.
   - 항목 parser, fixture, 품질 게이트와 반복 수집 멱등성 검증이 아직 없기 때문이다.
3. Mastercard 뉴스룸은 Akamai 403이 유지되므로 제외 상태를 유지한다.
4. JavaScript 셸만 반환하는 개발자 포털은 브라우저 자동화 없이 제외 상태를 유지한다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 전역 설정과 외부 시스템 변경 없음
- 공식 공개 URI를 읽기 전용으로 조회
- 로그인, credential, WAF 우회, push와 배포는 수행하지 않음

### 알려진 한계와 남은 작업

- 이번 실제 수집은 임시 새 상태에서 한 번 수행했으며 반복 실행 멱등성은 기존 검증 결과를 따른다.
- HTTP 200은 항목 단위 수집 가능성을 보장하지 않으므로 후보 승격에는 adapter 구현이 필요하다.
- 출처의 접근 정책과 구조는 이후 변경될 수 있어 운영 실행에서 계속 health를 확인해야 한다.

## 2026-07-28 12:30 KST — RSS·API 우선 운영 출처 확장과 신규 문서 작성

### 사용자 요청과 목적

- 기존 조사 대상 중 RSS·Atom 또는 공식 API·JSON을 제공하는 곳을 최우선으로 운영 수집에 포함
- feed/API가 없더라도 일반 HTTP에서 쉽게 파싱 가능한 정적 사이트까지 포함
- 조건을 만족하는 출처를 실제 수집하고, 고가치 신규 자료를 Obsidian 문서로 작성
- WAF 차단, JavaScript 렌더링 의존, 필수 게시일 부재 또는 장기 정체 출처는 명확한 근거로 제외·보류

### 수행한 변경

- 운영 Source Registry를 4개에서 9개로 확장
- American Express Newsroom의 공개 AEM model JSON adapter 구현
- UnionPay Media Center가 사용하는 Company News·Market News JSON adapter 구현
- Visa Developer Release Notes의 월별 정적 HTML adapter 구현
- Visa Acceptance Devices iOS SDK의 공식 GitHub Release Atom feed 등록
- American Express AEM 중복 목록 제거, `/content/amex` 내부 경로의 공개 URL 변환 구현
- Visa 월 단위 Release Notes에 `date_precision: month`를 기록하고 의미 query로 월별 안정 ID 분리
- adapter별 네트워크 없는 fixture와 회귀 테스트 추가
- 운영·후보·제외 출처 분류, 범위 체크리스트, 프로젝트 계획과 실행 문서 현행화
- 신규 채널의 기술 신호가 높은 4건을 원문까지 검증해 Inbox 문서로 작성
- 확장 결과와 문서 링크를 Digest로 작성

### 생성·수정한 문서와 파일

구현과 설정:

- [American Express adapter](./Automation/src/hermes_agent/adapters/amex.py)
- [UnionPay adapter](./Automation/src/hermes_agent/adapters/unionpay.py)
- [Visa adapters](./Automation/src/hermes_agent/adapters/visa.py)
- [Adapter registry](./Automation/src/hermes_agent/adapters/base.py)
- [운영 Source Registry](./Automation/config/sources.json)
- [패키지 기본 Source Registry](./Automation/src/hermes_agent/default_sources.json)
- [Adapter tests](./Automation/tests/test_adapters.py)
- [Registry tests](./Automation/tests/test_registry.py)
- [American Express fixture](./Automation/tests/fixtures/amex.json)
- [UnionPay fixture](./Automation/tests/fixtures/unionpay.json)
- [Visa Release Notes fixture](./Automation/tests/fixtures/visa_release_notes.html)

현행화 문서:

- [수집 출처 운영 분류](./SOURCE_CATALOG.md)
- [수집 대상 범위 체크리스트](./SOURCE_SCOPE_CHECKLIST.md)
- [프로젝트 설계](./PROJECT_PLAN.md)
- [프로젝트 README](./README.md)
- [수집기 README](./Automation/README.md)
- [수집 출처 확장 브리핑](./Digests/2026-07-28%20수집%20출처%20확장%20브리핑.md)

신규 Inbox 문서:

- [Visa Intelligent Commerce Agent APIs](./Inbox/2026-04-01%20Visa%20Intelligent%20Commerce%20Agent%20APIs.md)
- [Visa Acceptance Devices iOS SDK 3.7.0](./Inbox/2026-05-29%20Visa%20Acceptance%20Devices%20iOS%20SDK%203.7.0.md)
- [Amex Mid-Sized Businesses Prioritize AI Expense Management](./Inbox/2026-06-03%20Amex%20Mid-Sized%20Businesses%20Prioritize%20AI%20Expense%20Management.md)
- [OpenWay Adds Full UnionPay Product Support to Way4](./Inbox/2026-03-10%20OpenWay%20Adds%20Full%20UnionPay%20Product%20Support%20to%20Way4.md)

### 실행한 검증과 결과

```text
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  PYTHONPATH=Automation/src python3 -m compileall -q Automation/src Automation/tests
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent collect
PYTHONPATH=Automation/src python3 -m hermes_agent collect
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes --vault-dir .
PYTHONPATH=Automation/src python3 -m hermes_agent note-status ...
git diff --check
```

- 전체 단위·통합 테스트 29개 통과
- Python 전체 compile 검사 통과
- Source Registry schema `1.0`, 활성 출처 9개 검증 통과
- 실제 수집 2회 모두 9/9 성공
- 누적 정상 레코드 1,544건, 격리 0건, snapshot 중복 0건
- 두 번째 실행에서 1,544건 전부 `unchanged`
- Vault Inbox 8건 검증: `status: ok`, issue 0건
- 신규 문서 4건 모두 현재 수집 fingerprint 입력 시 `skip`
- `git diff --check` 통과

### 결정과 근거

1. 공식 RSS·Atom과 공개 JSON을 정적 HTML보다 우선한다.
   - 항목 경계와 필수 메타데이터가 명확하고 브라우저 렌더링 없이 반복 재현할 수 있기 때문이다.
2. American Express는 불완전한 HTML 홈페이지 대신 홈페이지가 직접 사용하는 AEM model JSON을 운영 원본으로 사용한다.
   - 인증·우회 없이 기사 URL, 최초 게시일과 카테고리를 구조화해 제공하기 때문이다.
3. UnionPay는 Media Center 내부 공개 JSON 중 Company News와 Market News만 운영한다.
   - 두 채널은 2026년까지 갱신되고 1차 기업·시장 발표를 제공한다. Media Reports는 외부 기사 재게시 성격과 정체, Statements는 2017년 이후 정체로 제외했다.
4. Visa Developer Use Cases는 정적 파싱이 가능해도 게시일이 없어 보류한다.
   - 발견일을 게시일처럼 저장하면 과거 자료가 신규 자료로 오인되고 문서 identity의 의미가 훼손되기 때문이다.
5. Visa GitHub는 조직 전체가 아니라 최근 release가 실제 존재하는 Acceptance Devices iOS SDK만 allowlist에 넣는다.
   - 조사한 나머지 저장소는 release feed가 비어 있거나 2022년 이후 정체됐다.
6. 누적 1,544건을 모두 문서로 만들지 않고 신규 채널별 고가치 기술 자료 4건을 우선 작성한다.
   - 과거 전체 자료 복제보다 현재 학습 가치와 사람 검토 가능성을 우선하고, 나머지 정상 레코드는 향후 관련성·중요도 큐의 입력으로 보존한다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 전역 설정 변경 없음
- credential, token, 로그인, WAF 우회와 브라우저 자동화 사용 없음
- 공식 공개 HTTPS 출처를 읽기 전용으로 조회
- 수집 원본과 정규화 결과는 Git에서 제외된 로컬 `Automation/data/`에 저장
- 작업 브랜치를 GitHub 원격 저장소에 push하고 Pull Request를 생성
- 배포와 전역 설정 변경은 수행하지 않음

### Git 작업

- 작업 브랜치: `feat/expand-collectable-sources`
- 커밋:
  - `c1a181c` — RSS API 우선 수집 출처 확장 및 문서 작성
- 작업 브랜치를 `origin/feat/expand-collectable-sources`로 push
- 생성한 Pull Request:
  - [#6 RSS·API 우선 수집 출처 확장 및 신규 문서 작성](https://github.com/dumbbelloper/hermes-agent/pull/6)

### 알려진 한계와 남은 작업

- 원문 본문 추출, 관련성·중요도 판정과 Inbox 작성은 아직 완전 자동화되지 않았다.
- American Express 현재 homepage model은 최근·추천 목록 14건이며 과거 전체 카테고리 archive를 운영 Registry에서 수집하지 않는다.
- UnionPay JSON은 전체 역사 목록을 반환하므로 향후 freshness 기반 증분 요청 또는 처리 최적화가 필요하다.
- Visa Release Notes는 월 단위 날짜만 제공하므로 실제 일자를 추정하지 않고 `published_at_precision: month`를 유지한다.
- EMVCo Specifications와 PCI SSC Document Library는 접근 가능하지만 항목별 버전·수정일 parser와 파일 hash 검증이 남아 있다.
- scheduler, retry, 알림과 문서 writer orchestration은 후속 작업이다.
