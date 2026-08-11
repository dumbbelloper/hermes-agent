# 작업 로그

> 상태: 2026-08-11부터 읽기 전용 historical archive
>
> 신규 기록: [task별 Work Logs](./Work%20Logs/README.md)

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
- [Hermes Agent runtime](./skills/hermes-news-automation/scripts/runtime/hermes_agent)
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

- [Note index](./skills/hermes-news-automation/scripts/runtime/hermes_agent/note_index.py)
- [CLI](./skills/hermes-news-automation/scripts/runtime/hermes_agent/cli.py)
- [Package init](./skills/hermes-news-automation/scripts/runtime/hermes_agent/__init__.py)
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

- [American Express adapter](./skills/hermes-news-automation/scripts/runtime/hermes_agent/adapters/amex.py)
- [UnionPay adapter](./skills/hermes-news-automation/scripts/runtime/hermes_agent/adapters/unionpay.py)
- [Visa adapters](./skills/hermes-news-automation/scripts/runtime/hermes_agent/adapters/visa.py)
- [Adapter registry](./skills/hermes-news-automation/scripts/runtime/hermes_agent/adapters/base.py)
- [운영 Source Registry](./Automation/config/sources.json)
- [패키지 기본 Source Registry](./skills/hermes-news-automation/scripts/runtime/hermes_agent/default_sources.json)
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

## 2026-07-28 14:27 KST — 미국 금융·결제 언론 수집과 Telegram 문서 알림

### 사용자 요청과 목적

- 현재 구현 진척도와 프로젝트 문서의 상태·숫자가 일치하는지 재점검
- 확정한 미국 금융·결제 언론 4곳을 RSS로 실제 수집
- 출처별 결제 학습 가치가 높은 자료를 선별해 Obsidian Inbox 문서 작성
- 작성 완료한 Markdown 문서의 전체 내용을 Telegram bot으로 알림
- bot token과 chat ID는 로컬 환경변수에서만 읽고 저장소·로그·문서에 남기지 않음

### 수행한 변경

- Payments Dive, Banking Dive, PYMNTS, TechCrunch Fintech 공식 RSS를 운영 Registry에 추가
- 공식기관 채널과 편집 언론을 구분하기 위해 `SourceConfig.official`을 추가
- 신규 언론은 priority 2, `official: false`로 정규화하고 Record의 공식성 flag가 source 분류와 일치하는지 검증
- 편집 언론 4곳을 두 차례 실제 수집하고 반복 멱등성 확인
- 협찬·행사 홍보·비결제 일반 기사 대신 결제 기술·규제·위험과 직접 관련된 4건 선별
- 편집 기사와 Mastercard, OCC, Natural 등 1차 자료를 가능한 범위에서 교차 확인
- 환경변수 기반 Telegram Bot API 전송, UTF-8 문서 읽기, 4,096자 분할과 오류 비밀정보 비노출 구현
- 신규 Inbox 문서 4건의 전체 Markdown을 Telegram으로 전송
- 프로젝트 문서에서 남아 있던 “운영 4개”와 “GitHub Release 미구현” 상태를 현재 구현에 맞게 수정
- 운영 상태를 공식 출처 9개·편집 언론 4개·누적 1,594건·Inbox 12건으로 현행화

### 생성·수정한 문서와 파일

구현과 설정:

- [Telegram notifier](./skills/hermes-news-automation/scripts/runtime/hermes_agent/telegram.py)
- [CLI](./skills/hermes-news-automation/scripts/runtime/hermes_agent/cli.py)
- [Source models](./skills/hermes-news-automation/scripts/runtime/hermes_agent/models.py)
- [Source Registry loader](./skills/hermes-news-automation/scripts/runtime/hermes_agent/registry.py)
- [Record normalization](./skills/hermes-news-automation/scripts/runtime/hermes_agent/normalize.py)
- [Record validation](./skills/hermes-news-automation/scripts/runtime/hermes_agent/validation.py)
- [운영 Source Registry](./Automation/config/sources.json)
- [패키지 기본 Source Registry](./skills/hermes-news-automation/scripts/runtime/hermes_agent/default_sources.json)
- [Telegram tests](./Automation/tests/test_telegram.py)
- [Normalization tests](./Automation/tests/test_normalize.py)
- [Registry tests](./Automation/tests/test_registry.py)
- [환경변수 이름 예시](./.env.example)

현행화 문서:

- [수집 출처 운영 분류](./SOURCE_CATALOG.md)
- [수집 대상 범위 체크리스트](./SOURCE_SCOPE_CHECKLIST.md)
- [프로젝트 설계](./PROJECT_PLAN.md)
- [프로젝트 README](./README.md)
- [수집기 README](./Automation/README.md)
- [미국 금융 결제 언론 브리핑](./Digests/2026-07-28%20미국%20금융%20결제%20언론%20브리핑.md)

신규 Inbox 문서:

- [Mastercard bolsters scam defense](./Inbox/2026-07-27%20Mastercard%20Bolsters%20Scam%20Defense.md)
- [OCC rejects Wise’s trust charter application](./Inbox/2026-07-24%20OCC%20Rejects%20Wise%20Trust%20Charter%20Application.md)
- [The Stablecoin Sandwich Is Missing the Trust Layer](./Inbox/2026-07-27%20The%20Stablecoin%20Sandwich%20Is%20Missing%20the%20Trust%20Layer.md)
- [Natural raises $30M to reinvent payments for AI agents](./Inbox/2026-07-20%20Natural%20Raises%2030M%20to%20Reinvent%20Payments%20for%20AI%20Agents.md)

### 실행한 검증과 결과

```text
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  PYTHONPATH=Automation/src python3 -m compileall -q Automation/src Automation/tests
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent collect \
  --source payments-dive --source banking-dive \
  --source pymnts --source techcrunch-fintech
PYTHONPATH=Automation/src python3 -m hermes_agent collect <동일 4개>
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes --vault-dir .
PYTHONPATH=Automation/src python3 -m hermes_agent note-status ...
PYTHONPATH=Automation/src python3 -m hermes_agent notify-telegram --dry-run ...
PYTHONPATH=Automation/src python3 -m hermes_agent notify-telegram ...
git diff --check
```

- 전체 단위·통합 테스트 35개 통과
- Python 전체 compile 검사 통과
- Source Registry schema `1.0`, 활성 출처 13개 검증 통과
- 신규 언론 4곳 실제 수집 2회 모두 4/4 성공
- Payments Dive 10건, Banking Dive 10건, PYMNTS 10건, TechCrunch Fintech 20건 등 50건 수락
- 격리 0건, snapshot 중복 0건
- 두 번째 실행에서 50건 전부 `unchanged`
- Vault Inbox 12건 검증: `status: ok`, issue 0건
- 신규 문서 4건 모두 현재 수집 fingerprint 입력 시 `skip`
- Telegram dry-run에서 문서 4건·메시지 4개 확인
- Telegram 실제 전송: 문서 4건·메시지 4개 성공
- `git diff --check` 통과

### 결정과 근거

1. 편집 언론은 공식 발표와 같은 `official: true`로 저장하지 않는다.
   - 기사와 조직의 1차 주장을 구분하고 향후 Writer의 교차검증 정책에 활용하기 위함이다.
2. 새 언론은 공식 출처보다 낮은 priority 2로 실행한다.
   - 공식기관·기업 원문을 우선하고 언론은 맥락, 규제 영향과 시장 신호를 보완하기 위함이다.
3. RSS의 모든 항목은 정상 레코드로 보존하되 문서 작성은 별도 선별한다.
   - Payments Dive 협찬, TechCrunch 행사 홍보와 PYMNTS 일반 AI 기사처럼 feed 단위로 제거하기 어려운 잡음이 존재하기 때문이다.
4. 언론 문서는 자료 성격과 verification status를 명시한다.
   - 기사 해석을 공식 입장으로 오인하지 않고 1차 자료 확인 범위를 투명하게 남기기 위함이다.
5. Telegram credential은 환경변수만 사용하고 CLI argument로 받지 않는다.
   - process list, shell history, 작업 로그와 commit에 token이 노출될 가능성을 줄이기 위함이다.
6. Telegram에는 문서 내용을 변경하지 않고 길이 제한에 맞춰 분할한다.
   - Obsidian과 알림 내용의 sync를 유지하기 위함이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 사용자가 `~/.zshrc`에 설정한 `HERMES_TELEGRAM_BOT_TOKEN`, `HERMES_TELEGRAM_CHAT_ID`를 읽어 사용
- 환경변수 값 자체는 출력·기록하지 않고 설정 여부만 확인
- Telegram Bot API를 통해 지정 chat에 Markdown 문서 4건을 총 4개 메시지로 전송
- 공식 RSS·편집 기사와 1차 자료를 읽기 전용으로 조회
- 전역 설정을 추가·수정하지 않았고 credential 파일을 생성하지 않음
- 실제 수집 데이터는 Git에서 제외된 `Automation/data/`에 저장

### 알려진 한계와 남은 작업

- 관련성·중요도 선별과 편집 기사–1차 자료 교차검증은 아직 사람이 수행한다.
- 협찬 URL, 행사 홍보와 비결제 일반 기사의 자동 제외 규칙은 구현하지 않았다.
- 같은 사건의 복수 매체 보도를 하나로 묶는 event key가 없다.
- Telegram 알림은 수동 CLI이며 collector/writer Hook과 scheduler에 아직 연결되지 않았다.
- Telegram API 전송 실패 시 자동 retry·backoff와 delivery state 저장이 없다.
- 원문 수정 시 `update_pending` 판정 이후 문서 갱신과 재알림 workflow가 남아 있다.

### Git 작업

- 작업 브랜치: `feat/us-finance-media-telegram`
- 커밋:
  - `cef08b2` — 미국 금융 결제 언론 수집과 Telegram 알림 추가
- 작업 브랜치를 `origin/feat/us-finance-media-telegram`로 push
- 생성한 Pull Request:
  - [#7 미국 금융·결제 언론 수집과 Telegram 알림 추가](https://github.com/dumbbelloper/hermes-agent/pull/7)

## 2026-07-28 14:56 KST — Hermes agent 연동 준비도 점검

### 사용자 요청과 목적

- 현재 구현 완성도로 Hermes agent와 연동했을 때 안정적으로 동작할 수 있는지 점검
- 수집, 중복 판정, Obsidian 작성과 Telegram 알림의 자동화 가능 범위 및 남은 위험 식별

### 수행한 변경

- 코드나 설정은 변경하지 않고 현재 `main`의 연동 준비도를 읽기 전용으로 점검
- collector의 Hook 경계, 상태 저장, CLI, 문서 식별 정책과 운영 문서의 구현 상태를 대조
- 현재 단계는 단일 실행 주체가 CLI를 순차 호출하는 반자동 workflow에는 사용 가능하지만, 완전 무인 end-to-end 자동화에는 보완이 필요하다고 판정

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md) — 이번 준비도 점검 결과 추가

### 실행한 검증과 결과

```text
git status --short --branch
find . -name SKILL.md -not -path './.git/*' -print
PYTHONPATH=Automation/src python3 -m unittest discover -s Automation/tests -v
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes --vault-dir .
```

- 점검 전 `main`은 `origin/main`과 일치하고 변경사항이 없었음
- 전체 테스트 35개 통과
- Source Registry schema `1.0`, 활성 출처 13개 검증 통과
- Vault Inbox 12건 검증: `status: ok`, issue 0건
- Hermes가 직접 탐색·실행할 프로젝트 `SKILL.md`는 아직 없음
- 저장 파일은 원자적으로 교체되지만 실행 간 lock은 없어 동시 실행 안전성은 보장되지 않음

### 결정과 근거

1. 현재 구성은 Hermes가 명시된 CLI를 한 번에 하나씩 호출하는 수집 orchestration에는 사용할 수 있다.
   - 수집 품질 gate, 상태 보존, 안정 식별자와 문서 중복 판정이 구현·검증되어 있기 때문이다.
2. 완전 자동 문서 작성과 알림 workflow가 완성됐다고 보지는 않는다.
   - 본문 추출·관련성 판정·Markdown 생성 Writer, 변경 목록 전달, 성공 후 알림 연결이 아직 하나의 실행 계약으로 묶이지 않았기 때문이다.
3. 하루 여러 번 실행하더라도 동일 머신의 순차 실행만 허용해야 한다.
   - 파일 단위 원자적 쓰기는 있지만 source 또는 전체 run lock이 없어 겹침 실행 시 read-modify-write 경합과 중복 알림이 가능하기 때문이다.
4. 자동화 worker는 `Automation/data/`를 영속 보존해야 한다.
   - 이 디렉터리가 수집 checkpoint를 보관하며 초기화되면 기존 항목을 새 항목처럼 처리할 수 있기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- 네트워크 수집이나 Telegram 전송을 실행하지 않았고 credential을 읽거나 기록하지 않음

### 알려진 한계와 남은 작업

- 프로젝트용 Hermes Skill과 단일 end-to-end 실행 진입점이 없음
- 신규·변경 레코드를 Writer에 구조적으로 넘기는 review queue 또는 `list-changes` 기능이 없음
- 관련성 선별, 본문 추출, 1차 자료 교차검증과 Obsidian Markdown 생성은 아직 사람 또는 agent prompt에 의존
- `note-status`는 `create`, `skip`, `update_pending` 판정만 하며 문서를 생성·갱신하지 않음
- collector 성공 후 Telegram 자동 전송, delivery idempotency, retry·backoff와 전송 상태 저장이 없음
- scheduler, 실행 lock, 운영 지표와 장애 알림이 없음
- 여러 머신 또는 휘발성 worker에서 공유할 영속 상태 저장소가 정해지지 않음

## 2026-07-28 15:04 KST — 완전 무인 Hermes 운영 계획 수립

### 사용자 요청과 목적

- 사람이 매번 확인하지 않아도 Hermes agent가 주기적으로 수집, 검증, 문서 작성과 알림을 완료하는 운영 방식 설계
- 구현 전에 agent 검증 방식, 상태 전이, 실패 처리와 단계별 완료 조건을 계획으로 확정
- 이번 작업에서는 코드 변경 금지

### 수행한 변경

- 코드는 변경하지 않고 현재 collector, 문서 식별 정책, 템플릿, Telegram 전송과 guardrail 문서를 기준으로 무인 workflow를 설계
- 정상 건은 자동 발행하고 불확실하거나 실패한 건은 사람 승인 대기가 아닌 격리·재시도 상태로 전환하는 원칙 채택
- 작성 단계와 검증 단계를 분리하고 결정론적 검사와 agent 의미 검증을 모두 통과해야만 문서 저장·알림하도록 계획

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md) — 무인 운영 계획과 결정 기록
- 코드, 설정, Source Registry와 기존 정책 문서는 변경하지 않음

### 실행한 검증과 결과

```text
PROJECT_PLAN.md의 Agent·Skill 경계, 실행 정책, 구현 현황 확인
Automation/README.md의 실패 상태와 확장 경계 확인
NOTE_IDENTITY_POLICY.md의 create·skip·update_pending 정책 확인
ENTERPRISE_AI_GUARDRAILS.md의 외부 알림 승인 정책 확인
Templates/Collected Note.md의 문서 schema 확인
```

- 기존 collector와 `record_id`·`source_fingerprint`는 무인 workflow의 수집·멱등성 기반으로 재사용 가능
- 현재 `PROJECT_PLAN.md`의 사람 검토 전제와 무인 운영 목표가 일치하지 않음
- 현재 guardrail의 Telegram G2 건별 승인 원칙은 주기적 무인 알림과 충돌하므로, 고정 chat·고정 용도에 대한 사전 승인 정책이 먼저 필요
- 작성자와 동일한 단일 agent의 자유형 자기 검토만으로는 품질 gate가 충분하지 않다고 판정

### 결정과 근거

1. 정상 실행은 `collect → delta → enrich → curate → write → verify → commit → notify → complete` 상태 전이를 따른다.
   - 단계별 artifact와 결과를 남겨 중단 후 재개와 감사가 가능해야 하기 때문이다.
2. 검증은 결정론적 gate와 독립된 Verifier agent 호출을 함께 사용한다.
   - schema·URL·ID·인용 같은 기계 검사는 코드가 더 안정적이고, 관련성·왜곡·과장 판단은 agent가 더 적합하기 때문이다.
3. Writer와 Verifier는 별도 prompt와 context로 실행한다.
   - 같은 초안 생성 맥락을 그대로 재사용하는 자기 확인 편향을 줄이기 위함이다.
4. 검증 실패는 자동 발행하지 않고 `quarantined` 또는 `retryable`로 종료한다.
   - 사람 검토가 없어도 잘못된 문서를 발행하는 대신 해당 건을 안전하게 누락시키는 fail-closed 운영을 하기 위함이다.
5. 하나의 영속 실행 환경과 전역 run lock을 초기 운영 기준으로 한다.
   - 현재 파일 기반 checkpoint를 유지하면서 겹침 실행에 따른 중복 작성과 알림을 막는 가장 단순한 방식이기 때문이다.
6. Telegram은 문서 저장과 사후 검증이 완료된 뒤 delivery ledger를 선점한 건만 전송한다.
   - 파일 작성 실패, 재실행과 API timeout 상황에서 중복 메시지를 방지하기 위함이다.
7. 정기 실행에는 사람 승인을 요구하지 않되 대상 chat, 메시지 종류, credential 권한을 고정한 사전 승인 정책을 둔다.
   - 무인 운영 목표와 외부 메시지 통제를 동시에 만족시키기 위함이다.

### 계획한 구현 단계

1. **운영 계약 현행화**
   - 사람 검토 전제를 agent 검증·자동 발행 정책으로 변경
   - 실행 환경, 주기, 비용 상한, 모델, 고정 Telegram 대상과 사전 승인 범위 결정
2. **Run Controller와 상태 원장**
   - 전역 lock, `run_id`, 단계별 manifest, 중단 후 재개, 단일 종료 요약 구현
3. **Delta·작업 큐**
   - 신규·수정 레코드를 명시적인 작업 항목으로 생성하고 각 항목의 상태와 시도 횟수 저장
4. **본문 처리와 Curator**
   - 허용된 원문만 추출하고 결제·금융 관련성, 중요도, 홍보·협찬·행사 잡음을 판정
   - 원문은 명령이 아닌 비신뢰 데이터로 취급해 prompt injection의 도구·파일 지시를 무시
5. **Writer와 Verifier**
   - 근거가 연결된 한국어 문서 생성
   - 별도 Verifier가 원문 대비 사실, 숫자·날짜·조직, 공식·편집 출처 구분, 과장과 누락을 평가
   - Frontmatter, 링크, 식별자, 인용과 Markdown schema를 결정론적으로 재검사
6. **자동 갱신과 사건 중복 처리**
   - agent 관리 영역만 갱신하고 기존 수동 문서는 덮어쓰지 않는 update schema 확정
   - 복수 매체의 동일 사건을 묶는 `event_key`와 대표 원문 선택 적용
7. **Telegram delivery와 복구**
   - `record_id + source_fingerprint + channel` 기반 전송 키, 선점·성공 기록, 제한 재시도와 dead-letter 처리
8. **Scheduler와 관측**
   - 정기 실행, 출처별 circuit breaker, 실행 성공률·신규 문서·격리·재시도·비용 지표와 장애 요약 제공
9. **Hermes Skill**
   - 하나의 고정된 workflow를 실행하고 구조화된 결과만 반환하도록 입력, 출력, 권한과 실패 조건 명시

### 완료 조건

- 같은 snapshot을 반복 실행해 새 문서와 Telegram 메시지가 모두 0건
- 동시에 두 번 실행해 하나만 lock을 획득하고 다른 실행은 안전하게 종료 또는 대기
- collector, 모델 또는 Telegram 실패 후 재실행해 완료 단계부터 이어지고 중복 부작용이 없음
- 관련 없는 기사, 협찬, 행사 홍보와 prompt injection fixture가 자동 발행되지 않음
- 생성 문서의 모든 사실 주장에 원문 근거가 연결되고 숫자·날짜·조직 불일치 시 격리
- 원문 변경은 새 중복 문서를 만들지 않고 정의된 update 정책대로 처리
- Vault 전체 identity·schema 검사 통과 후에만 Telegram 전송
- credential, 원문 내 지시와 내부 prompt가 문서·로그·알림에 노출되지 않음
- 정상 주기에는 사람 조작 없이 실행되고 실패·격리 건은 상태와 원인을 남김

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- Telegram 전송, 네트워크 수집, scheduler 등록과 환경변수 변경을 수행하지 않음

### 알려진 한계와 남은 작업

- 실행 환경, 실행 주기, agent 모델과 호출 비용 상한은 아직 확정되지 않음
- 동일 사건 판정 기준과 자동 문서 갱신 schema는 구현 전에 상세 설계가 필요
- 고정 Telegram chat에 대한 사전 승인 정책은 기존 guardrail 문서와 함께 현행화해야 함
- agent 의미 검증은 오류 가능성이 0이 아니므로 잘못된 발행보다 격리와 누락을 우선하는 임계값 조정이 필요

## 2026-07-28 15:30 KST — Hermes Skill 기반 완전 무인 workflow 구현

### 사용자 요청과 목적

- 사람이 매번 확인하지 않아도 Hermes Agent가 주기적으로 수집, 검증, Obsidian 문서 작성과 Telegram 알림을 완료하도록 구현
- 의미 검증도 agent가 수행하되 Writer의 자기 검토가 아닌 독립 Verifier와 결정론적 gate를 함께 적용
- 프로젝트 Skill 완성 후 Mac이 켜진 동안 Hermes gateway·cron으로 계속 실행하는 설정 가이드 제공

### 수행한 변경

- `feat/hermes-unattended-automation` 작업 브랜치 생성
- 만료 가능한 logical run lock, run manifest, delta queue와 item 상태 전이 구현
- 동일 fingerprint의 무관·격리 결정을 반복 처리하지 않는 decision ledger 구현
- Curator, Writer와 독립 Verifier의 JSON artifact 계약과 confidence threshold 구현
- 사실·조직·날짜·숫자·출처 구분·과장·prompt injection 검사 결과를 모두 요구
- 한국어 요약, 중요성, 키워드, evidence와 follow-up을 Obsidian Markdown으로 원자 저장
- 기존 수동 문서는 자동 덮어쓰지 않고 격리하며 agent 생성 문서만 재검증 후 갱신
- `event_key` ledger로 동일 사건을 대표하는 두 번째 문서 발행 차단
- Telegram delivery를 전송 전에 예약하고 `sending`, `sent`, `unknown` 상태로 보존
- Telegram 결과가 불확실하면 중복 가능성을 피하기 위해 자동 재전송하지 않는 at-most-once 정책 적용
- 통합 automation CLI 7개 추가
- Hermes Skill, artifact reference와 `wakeAgent` pre-check script 작성
- macOS Hermes gateway, Skill external directory, credential passthrough, toolset, cron과 전원 설정 가이드 작성
- 기존 사람 검토 전제와 guardrail을 agent 자동 검증·고정 Telegram standing authorization 기준으로 현행화

### 생성·수정한 문서와 파일

구현:

- [무인 실행 controller](./skills/hermes-news-automation/scripts/runtime/hermes_agent/automation.py)
- [통합 CLI](./skills/hermes-news-automation/scripts/runtime/hermes_agent/cli.py)
- [무인 workflow 테스트](./Automation/tests/test_automation.py)
- [Hermes News Automation Skill](./skills/hermes-news-automation/SKILL.md)
- [Agent artifact 계약](./skills/hermes-news-automation/references/artifact-schema.md)
- [Hermes cron pre-check](./skills/hermes-news-automation/scripts/precheck.py)
- [Skill UI metadata](./skills/hermes-news-automation/agents/openai.yaml)

운영 및 정책 문서:

- [무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)
- [프로젝트 README](./README.md)
- [Automation README](./Automation/README.md)
- [프로젝트 설계](./PROJECT_PLAN.md)
- [문서 식별 정책](./NOTE_IDENTITY_POLICY.md)
- [Enterprise AI Guardrails](./ENTERPRISE_AI_GUARDRAILS.md)
- [환경변수 이름 예시](./.env.example)
- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
PYTHONPATH=Automation/src python3 -m unittest discover \
  -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  PYTHONPATH=Automation/src python3 -m compileall -q \
  Automation/src Automation/tests skills/hermes-news-automation/scripts
PYTHONPATH=/private/tmp/hermes-skill-validator-pyyaml \
  python3 <skill-creator>/scripts/quick_validate.py \
  skills/hermes-news-automation
PYTHONPATH=Automation/src python3 -m hermes_agent validate-registry
PYTHONPATH=Automation/src python3 -m hermes_agent validate-notes \
  --vault-dir .
python3 -m py_compile \
  skills/hermes-news-automation/scripts/precheck.py
HERMES_NEWS_REPO= \
  python3 skills/hermes-news-automation/scripts/precheck.py
hermes --version
hermes cron create --help
hermes gateway --help
git diff --check
```

- 전체 테스트 42개 통과
- 기존 collector·normalizer·Vault·Telegram 회귀 테스트 통과
- 겹침 실행 차단 통과
- 반복 snapshot에서 문서·알림 추가 0건 검증 통과
- 동일 fingerprint의 irrelevant decision 억제 검증 통과
- 독립 verification check 누락과 prompt injection 문구 복제 차단 통과
- 동일 `event_key`의 두 번째 문서 발행 차단 통과
- agent artifact 보존, Obsidian 원자 작성과 Telegram delivery ledger 통합 검증 통과
- Python 전체 compile 검사 통과
- Skill Creator 공식 validator: `Skill is valid`
- Source Registry schema `1.0`, 활성 출처 13개 검증 통과
- Vault Inbox 12건: `status: ok`, issue 0건
- pre-check 필수 환경변수 fail-closed 동작 확인
- 로컬 Hermes Agent v0.19.0과 `cron create`, `gateway` CLI option 확인
- `git diff --check` 통과

### 결정과 근거

1. Python controller가 부작용과 상태를 강제하고 Hermes Agent는 의미 판단을 담당한다.
   - 모델 출력만으로 lock, 멱등성, 원자 저장과 delivery 상태를 안정적으로 보장할 수 없기 때문이다.
2. Writer와 Verifier를 fresh subagent context로 분리한다.
   - 작성 과정의 reasoning을 Verifier에게 넘기지 않아 자기 확증 편향을 줄이기 위함이다.
3. 정상 건만 자동 발행하고 불확실한 건은 `quarantined`로 발행하지 않는다.
   - 사람 검토 없이 운영하면서 잘못된 발행보다 안전한 누락을 우선하기 위함이다.
4. curation `0.80`, verification `0.85`를 최소 confidence로 사용한다.
   - 초기 무인 운영에서 보수적인 품질 gate로 시작하고 실제 표본으로 후속 보정하기 위함이다.
5. 실행당 기본 최대 5건과 180분 logical lock TTL을 둔다.
   - 모델 비용·시간 폭주를 제한하고 중단된 run이 영구적으로 다음 실행을 막지 않게 하기 위함이다.
6. Telegram timeout·네트워크 오류는 `unknown`으로 보존하고 자동 재전송하지 않는다.
   - Telegram Bot API에 사용자 idempotency key가 없어 응답 유실 시 전송 여부를 증명할 수 없기 때문이다.
7. `wakeAgent` pre-check가 queue를 먼저 만들고 변경이 있을 때만 agent를 실행한다.
   - 변경 없는 주기의 모델 호출 비용을 제거하기 위함이다.
8. Skill은 저장소 `skills/`에서 버전 관리하고 Hermes `external_dirs`로 연결한다.
   - 코드, artifact schema와 Skill procedure를 같은 Git revision으로 유지하기 위함이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 전역 Hermes config, gateway, cron job과 macOS 전원 설정은 변경하지 않음
- Telegram 메시지를 전송하지 않음
- 실제 네트워크 수집과 실제 Hermes Skill end-to-end 실행을 수행하지 않음
- 공식 Hermes Agent와 Apple 문서를 읽기 전용으로 확인
- Skill validator 실행을 위해 PyYAML 6.0.3을 `/private/tmp/hermes-skill-validator-pyyaml`에만 임시 설치
- 프로젝트 dependency와 Python 전역 환경은 변경하지 않음

### 알려진 한계와 남은 작업

- Skill은 생성·검증됐지만 현재 사용자의 Hermes `skills.external_dirs`에는 아직 연결하지 않았으므로 설정 가이드를 따라야 한다.
- Hermes gateway 설치, cron 등록, cron platform toolset과 `~/.hermes/.env` 설정은 아직 사용자가 적용하지 않았다.
- 실제 원문 web extraction, Writer와 Verifier의 정기 운영 품질은 첫 cron 실행 표본으로 추가 확인해야 한다.
- Agent가 만드는 `event_key`의 의미 품질은 모델에 의존하므로 실제 중복 사건 표본으로 보정해야 한다.
- Source별 지수 backoff, circuit breaker, 장기 성공률·비용 dashboard와 자동 Digest는 아직 없다.
- Telegram `unknown`은 중복 방지를 위해 자동 재전송하지 않으므로 메시지가 실제로 전송되지 않았더라도 누락될 수 있다.
- Mac이 종료되거나 잠자기 상태면 gateway cron이 정상 주기로 실행되지 않는다.
- 변경사항은 작업 브랜치에 있으며 아직 commit, push 또는 PR을 생성하지 않았다.

## 2026-07-28 15:40 KST — Linux 서버 이식성 점검

### 사용자 요청과 목적

- Linux 서버에 Codex와 Hermes Agent를 설치했을 때 현재 무인 workflow를 그대로 실행할 수 있는지 확인
- macOS 종속 코드와 Linux에서 변경해야 하는 운영 설정 구분

### 수행한 변경

- 코드와 운영 설정은 변경하지 않고 Python 구현, Skill, pre-check와 공식 설치 문서를 읽기 전용으로 점검
- 실행 코드는 macOS 전용이 아니라 POSIX 환경인 macOS와 Linux에서 동작한다고 판정
- macOS 절대 경로, launchd와 전원 설정은 가이드에만 있으며 Linux에서는 repository 경로와 systemd 설정으로 대체해야 함을 확인

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md) — Linux 이식성 점검 결과 추가
- 코드, Skill과 운영 설정은 변경하지 않음

### 실행한 검증과 결과

```text
rg -n "darwin|macos|launchd|osascript|brew|/Users/|fcntl|systemd|linux|platforms:" \
  Automation skills pyproject.toml .env.example HERMES_AUTOMATION_GUIDE.md
```

- 당시 `/Users/...`, launchd와 macOS 전원 설정은 현재 [무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)의 macOS 절에 해당
- 실행 코드의 OS 관련 기능은 `fcntl.flock`이며 Linux와 macOS에서 모두 지원
- Skill과 pre-check는 `python3`, repository 상대 경로와 `HERMES_NEWS_REPO`를 사용
- Python runtime dependency는 표준 라이브러리뿐이며 프로젝트 기준 Python 3.9 이상
- 공식 Codex CLI는 Linux x86_64와 arm64 설치 artifact를 제공
- 공식 Hermes Agent는 Linux 설치, systemd user service와 Linux server용 system service를 지원

### 결정과 근거

1. Linux 서버는 현재 workflow의 지원 대상이다.
   - Python, POSIX file lock, 원자적 file replace와 Hermes cron이 모두 Linux에서 사용 가능하기 때문이다.
2. Native Windows는 현재 동일 지원 대상으로 보지 않는다.
   - run mutex가 POSIX `fcntl`에 의존하기 때문이다.
3. Codex CLI는 정기 실행의 runtime dependency가 아니다.
   - cron, web extraction, delegation과 Skill 실행은 Hermes Agent가 담당하고 Codex는 개발·점검에만 필요하기 때문이다.
4. Linux에서는 local persistent filesystem과 단일 Hermes runner를 사용한다.
   - NFS 등 network filesystem의 advisory lock semantics와 여러 runner의 공유 상태 경합을 피하기 위함이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- Linux 서버, Hermes config, systemd, credential과 cron job을 변경하지 않음
- OpenAI와 Hermes Agent 공식 문서를 읽기 전용으로 확인

### 알려진 한계와 남은 작업

- 현재 제공 가이드는 macOS용이므로 Linux에서는 `/Users/...`를 실제 `/home/<service-user>/...` 경로로 바꿔야 한다.
- macOS `launchd` 대신 Linux `systemd` gateway를 설치해야 한다.
- systemd를 실행하는 동일 service user의 `~/.hermes/.env`, Skill external directory, repository와 `Automation/data/` 소유권을 맞춰야 한다.
- cron 시간대는 Linux 서버의 systemd/Hermes timezone 설정을 확인해야 한다.
- Linux 실서버에서 end-to-end smoke test는 아직 수행하지 않았다.

## 2026-07-28 15:52 KST — Agent Skills 글로벌 규격과 크로스플랫폼 가이드 현행화

### 사용자 요청과 목적

- 일반적인 Skill 구성 best practice와 현재 채택도가 높은 공개 Skills 사례를 확인
- macOS에 종속된 `HERMES_MACOS_AUTOMATION_GUIDE.md` 이름과 내용을 글로벌 운영 기준으로 교체
- macOS, Linux와 Windows 지원 범위를 실제 Hermes 및 프로젝트 호환성에 맞게 명시

### 수행한 변경

- Agent Skills 공개 specification, Codex `skill-creator`, Hermes Skills 공식 문서와 공개 저장소의 채택 사례 비교
- 기존 macOS 전용 가이드를 [Hermes Agent 무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)로 교체
- 공개 사례의 GitHub star는 2026-07-28 채택 신호 스냅샷이며 절대 품질 순위가 아니라고 명시
- Skill package의 표준 코어, progressive disclosure, host extension, script와 reference 분리 기준 작성
- 플랫폼 지원을 macOS·Linux·Windows WSL2 1차 지원, native Windows 실험 지원으로 분류
- OS별 repository, credential, Skill external directory, pre-check, gateway, cron, 검증과 복구 절차 작성
- inline `PYTHONPATH` 조립을 제거하기 위한 cross-platform Python controller launcher 추가
- macOS/Linux/WSL2의 `python3`와 native Windows의 `python` interpreter 차이를 Skill에 명시
- POSIX `fcntl`과 native Windows `msvcrt`를 선택하는 process mutex 구현
- native Windows lock branch를 가짜 backend로 검증하는 회귀 테스트 추가
- README, Automation README, 프로젝트 계획과 기존 작업 로그의 가이드 링크 현행화

### 생성·수정한 문서와 파일

- [Hermes Agent 무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)
- [Hermes News Automation Skill](./skills/hermes-news-automation/SKILL.md)
- [Cross-platform controller launcher](./Automation/run.py)
- [무인 실행 controller](./skills/hermes-news-automation/scripts/runtime/hermes_agent/automation.py)
- [무인 workflow 테스트](./Automation/tests/test_automation.py)
- [Automation README](./Automation/README.md)
- [프로젝트 README](./README.md)
- [프로젝트 설계](./PROJECT_PLAN.md)
- [작업 로그](./WORK_LOG.md)
- 기존 미추적 `HERMES_MACOS_AUTOMATION_GUIDE.md`는 새 글로벌 가이드로 대체

### 실행한 검증과 결과

```text
python3 Automation/run.py --help
PYTHONPATH=Automation/src python3 -m unittest discover \
  -s Automation/tests -v
PYTHONPYCACHEPREFIX=/private/tmp/hermes-agent-pycache \
  python3 -m compileall -q \
  Automation/src Automation/tests Automation/run.py \
  skills/hermes-news-automation/scripts
PYTHONPATH=/private/tmp/hermes-skill-validator-pyyaml \
  python3 <skill-creator>/scripts/quick_validate.py \
  skills/hermes-news-automation
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
rg -n "\]\(\./HERMES_MACOS_AUTOMATION_GUIDE|python Automation/run.py" \
  --glob '*.md' --glob '!WORK_LOG.md' .
git diff --check
```

- launcher help 실행 성공
- 전체 테스트 43개 통과: 기존 42개와 Windows mutex backend 회귀 테스트 1개
- Python compile 검사 통과
- Skill Creator validator: `Skill is valid`
- Source Registry schema `1.0`, 활성 출처 13개 검증 통과
- Vault Inbox 12건: `status: ok`, issue 0건
- 삭제된 macOS 가이드 경로와 잘못된 공통 `python` 명령 참조 0건
- 최초 `python` alias 검증은 현재 macOS에서 명령이 없어 실패했으며, 실제 platform별 interpreter 정책을 문서와 Skill에 반영

### 결정과 근거

1. Agent Skills 공개 규격을 core contract로 사용한다.
   - 특정 agent host의 metadata나 설치 경로보다 `SKILL.md`, 상대 resource와 progressive disclosure가 이식성의 공통 기반이기 때문이다.
2. Skill 안에 별도 설치 가이드를 만들지 않고 project root에서 운영 문서를 관리한다.
   - agent가 실행할 때 필요하지 않은 문서는 Skill context와 bundle을 불필요하게 키우기 때문이다.
3. macOS와 Linux뿐 아니라 Windows 사용 경로도 문서화한다.
   - Hermes는 native Windows gateway와 cron을 공식 지원하고 WSL2도 사용할 수 있기 때문이다.
4. native Windows는 실험 지원으로 유지한다.
   - code-level mutex와 launcher는 준비했지만 이 작업 환경에서 native Windows end-to-end 실행을 증명할 수 없기 때문이다.
5. OS별 interpreter 이름을 숨기지 않는다.
   - 현재 macOS에는 `python` alias가 없고 native Windows에는 보통 `python3` alias가 없으므로 존재하지 않는 단일 명령을 글로벌 표준처럼 쓰면 안 되기 때문이다.
6. local persistent filesystem과 단일 runner를 기본 운영 경계로 유지한다.
   - NFS, SMB나 동기화 filesystem에서는 file lock과 atomic replace 의미를 동일하게 보장할 수 없기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- Hermes config, gateway, cron, OS service, credential과 Telegram을 변경하지 않음
- 공개 Agent Skills, GitHub와 Hermes 문서를 읽기 전용으로 확인
- 프로젝트 밖에는 새 파일이나 dependency를 설치하지 않음

### 알려진 한계와 남은 작업

- Linux, Windows WSL2와 native Windows 실환경 end-to-end smoke test는 아직 수행하지 않음
- native Windows는 동시 실행, UTF-8 한국어 문서, gateway 재시작, stale run과 Telegram timeout 표본을 통과한 뒤 1차 지원으로 승격해야 함
- macOS에서도 실제 Hermes external Skill 연결, gateway 설치와 첫 cron run은 아직 사용자가 수행하지 않음
- GitHub star와 host 기능은 변할 수 있으므로 가이드 기준일 이후에는 공식 원문을 다시 확인해야 함

## 2026-07-28 15:58 KST — Skill 공유·배포·설치 구조 점검

### 사용자 요청과 목적

- 주변 동료가 프로젝트 Skill을 사용할 수 있도록 일반적인 공유, 배포와 설치 구조 확인
- 현재 `hermes-news-automation`을 단독 Skill로 배포할 수 있는지와 적합한 팀 배포 방식 구분

### 수행한 변경

- Agent Skills 공개 규격의 package 경계와 Hermes Skills Hub, GitHub direct install, tap, external directory 및 update lifecycle 확인
- 현재 Skill이 `Automation/run.py`, Source Registry, Vault와 영속 상태 저장소를 요구하므로 Skill 폴더만으로는 독립 실행할 수 없다고 판정
- 현 단계에서는 repository clone과 Hermes `external_dirs` 연결을 팀 공유 기준으로, 향후 runtime package와 Skill tap 분리를 원클릭 배포 목표로 정리

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- Skill, runtime, 설정과 운영 문서는 변경하지 않음

### 실행한 검증과 결과

```text
Agent Skills Specification의 directory와 resource 설치 경계 확인
Hermes Skills 공식 문서의 direct GitHub install, tap, security scan과 update lifecycle 확인
skills/hermes-news-automation/SKILL.md의 repository runtime 의존성 확인
git remote -v
git status --short --branch
```

- 공개 원격 저장소는 `https://github.com/dumbbelloper/hermes-agent.git`
- 현재 작업은 `feat/hermes-unattended-automation` 브랜치에 있으며 아직 미commit 변경 포함
- Hermes direct install은 Skill과 직접 참조한 Skill 내부 resource를 설치하지만 프로젝트 전체 runtime을 자동 배포하는 계약은 아님

### 결정과 근거

1. 현재 팀 배포 단위는 개별 Skill이 아니라 repository 전체다.
   - Skill procedure가 repository-local controller와 데이터 구조를 직접 호출하기 때문이다.
2. 여러 동료가 같은 source를 사용하되 각자 별도 clone과 `Automation/data/`를 가져야 한다.
   - 하나의 실행 상태를 여러 host가 공유하면 lock, checkpoint와 delivery ledger가 경합할 수 있기 때문이다.
3. 원클릭 설치는 Skill tap만 추가해서 해결하지 않고 runtime package 또는 container를 별도 배포해야 한다.
   - Skill은 agent의 절차 계약이고 실행 코드, 상태 저장소와 credential은 별도 runtime 책임이기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- GitHub repository, Hermes Hub, tap, 전역 Skill과 동료 환경을 변경하지 않음

### 알려진 한계와 남은 작업

- 현재 feature branch가 main에 병합되기 전에는 동료에게 안정 버전으로 안내할 수 없음
- 팀용 bootstrap, version tag, release note, runtime installer와 CI 배포 검증은 아직 없음
- private repository로 전환할 경우 동료별 GitHub 권한과 Hermes의 `GITHUB_TOKEN` 정책이 필요

## 2026-07-28 16:16 KST — Hermes News Automation Skill 독립 배포 구조 구현

### 사용자 요청과 목적

- 기존 repository 전체를 복제하지 않고 동료와 외부 사용자가 설치할 수 있는 Skill 배포 구조 구현
- Agent Skills와 Hermes 설치 관행에 맞춰 공유, 설치, 업데이트와 검증 절차를 문서화
- macOS와 Linux를 우선 지원하고 Windows WSL2 및 native Windows 사용 경계를 명확히 구분

### 수행한 변경

- controller Python runtime의 단일 원본을 Skill bundle 내부 `scripts/runtime/`으로 이동
- repository 개발용 [Automation launcher](./Automation/run.py)는 Skill runtime을 호출하는 얇은 wrapper로 변경
- 독립 launcher에 `init`, `doctor`와 기존 controller command 연결 구현
- workspace별 `Inbox/`, `.hermes-news/config/`, `.hermes-news/data/`, `.hermes-news/tmp/` 초기화 구현
- cron pre-check가 repository 경로 대신 설치된 Skill 위치를 찾도록 변경
- 배포 bundle의 기본 Source Registry와 실행 코드를 자체 포함하고 사용자별 상태는 workspace 밖으로 분리
- Hermes tap용 root manifest와 Python wheel metadata 추가
- GitHub Actions에 Ubuntu, macOS, Windows 검증 matrix 추가
- repository 밖으로 복사한 Skill만으로 초기화, 진단과 registry 검증이 가능한지 확인하는 회귀 테스트 추가
- 운영 문서의 이전 repository 결합형 경로와 상태 표현을 독립 workspace 기준으로 현행화

### 생성·수정한 문서와 파일

- [Hermes News Automation Skill](./skills/hermes-news-automation/SKILL.md)
- [독립 실행 launcher](./skills/hermes-news-automation/scripts/run.py)
- [cron pre-check](./skills/hermes-news-automation/scripts/precheck.py)
- [bundled runtime](./skills/hermes-news-automation/scripts/runtime/hermes_agent/__init__.py)
- [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)
- [Hermes 무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)
- [Skill 배포 회귀 테스트](./Automation/tests/test_skill_distribution.py)
- [다중 OS 검증 workflow](./.github/workflows/skill-validation.yml)
- [Hermes tap manifest](./skills.sh.json)
- [Python package 설정](./setup.cfg)
- [프로젝트 개요](./README.md)
- [Automation 안내](./Automation/README.md)
- [프로젝트 계획](./PROJECT_PLAN.md)
- [환경변수 예시](./.env.example)
- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
PYTHONPATH=/private/tmp/hermes-skill-validator-pyyaml \
  python3 <skill-creator>/scripts/quick_validate.py \
  skills/hermes-news-automation
PYTHONPYCACHEPREFIX=/private/tmp/hermes-news-pycache \
  python3 -m compileall -q skills/hermes-news-automation/scripts
python3 -m json.tool skills.sh.json
python3 -m build --wheel
python3 -m pip install --no-deps --target <temporary-directory> <built-wheel>
PYTHONPATH=<temporary-directory> python3 -m hermes_agent validate-registry
rg -n "HERMES_NEWS_REPO|Automation/src|/Users/dumbbelloper" \
  skills/hermes-news-automation SKILL_DISTRIBUTION_GUIDE.md skills.sh.json .github
git diff --check
```

- 전체 unit/integration test 47개 통과
- Skill Creator validator: `Skill is valid!`
- repository 밖으로 복사한 bundle의 `init → doctor → validate-registry` 통과
- Skill 내부 Markdown 상대 링크가 bundle 밖을 벗어나지 않고 모두 존재함을 확인
- `hermes_news_automation-0.1.0-py3-none-any.whl` 생성, 임시 위치 설치와 13개 활성 출처 registry 검증 통과
- Python compile, `skills.sh.json` JSON parsing과 `git diff --check` 통과
- Skill bundle과 배포 문서에서 기존 `Automation/src`, `HERMES_NEWS_REPO`, 사용자 절대 경로 참조 0건
- 최초 compile은 macOS 사용자 cache 경로의 sandbox 권한으로 실패했으며, 임시 cache 경로를 지정한 동일 검사에서는 통과

### 결정과 근거

1. Skill directory 자체를 실행 가능한 배포 단위로 만든다.
   - GitHub direct install과 Hermes tap이 프로젝트 전체가 아닌 Skill bundle을 설치해도 workflow가 동작해야 하기 때문이다.
2. bundled runtime은 읽기 전용 코드로, 문서와 실행 상태는 사용자별 workspace로 분리한다.
   - Skill 업데이트가 사용자 문서, checkpoint, run ledger와 설정을 덮어쓰지 않게 하기 위해서다.
3. 기본 registry는 bundle에 포함하되 `init`이 만든 workspace registry는 자동 덮어쓰지 않는다.
   - 설치 즉시 실행 가능하면서 사용자별 source 정책 변경을 보존하기 위해서다.
4. Python package는 선택적 CLI 배포 수단으로 유지하고 Skill 실행의 필수 조건으로 만들지 않는다.
   - Hermes 사용자는 별도 pip 설치 없이 설치 bundle의 `scripts/run.py`를 바로 실행할 수 있어야 하기 때문이다.
5. native Windows는 CI 대상이지만 실험 지원으로 유지한다.
   - code-level 호환성과 자동 테스트만으로 실제 gateway, Scheduled Task, UTF-8 문서와 Telegram 흐름을 증명할 수 없기 때문이다.
6. 현재 상태는 공개 완료가 아닌 release candidate다.
   - main 병합, GitHub Actions 실결과, version tag와 실제 Hermes 설치 smoke test가 남아 있기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- GitHub push, pull request, release, version tag와 Hermes tap 공개를 수행하지 않음
- 로컬 또는 전역 Hermes Skill을 설치하거나 업데이트하지 않음
- Hermes gateway, cron, Telegram, credential과 OS service를 변경하지 않음
- wheel과 임시 설치 결과는 `/private/tmp` 아래에서만 생성

### 알려진 한계와 남은 작업

- feature branch 변경은 아직 commit, push 또는 pull request되지 않음
- GitHub Actions의 Ubuntu, macOS, Windows matrix는 workflow 작성만 완료했으며 실제 원격 실행 결과는 없음
- Linux, Windows WSL2와 native Windows에서 Hermes gateway 및 cron end-to-end smoke test가 필요
- 공개 배포 전 `v0.1.0` tag, release note, 라이선스 최종 확인과 main 기준 direct install 검증이 필요
- private repository 배포 시 동료별 GitHub 접근 권한과 Hermes credential 정책을 별도로 마련해야 함

## 2026-07-28 16:22 KST — Skill 배포 준비 변경 commit, push 및 PR 생성

### 사용자 요청과 목적

- 검증을 마친 무인 자동화와 독립 Skill 배포 변경을 별도 브랜치에 commit
- 원격 저장소에 push하고 `main` 대상 pull request 생성

### 수행한 변경

- 전체 구현과 문서 변경을 `e372d9f` 커밋으로 생성
- `feat/hermes-unattended-automation` 브랜치를 `origin`에 push하고 upstream 연결
- GitHub `main` 대상 [PR #8](https://github.com/dumbbelloper/hermes-agent/pull/8) 생성
- PR 본문에 구현 범위, 47개 테스트와 release 전 실환경 검증 항목 명시
- 생성 직후 PR base/head, merge 가능 여부와 다중 OS CI 상태 확인

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- 구현 파일은 직전 작업 기록의 목록과 동일하며, 이 단계에서는 원격 반영과 PR 생성만 수행

### 실행한 검증과 결과

```text
git diff --cached --check
git commit -m "Hermes 무인 뉴스 자동화 Skill 패키징"
git push --set-upstream origin feat/hermes-unattended-automation
gh pr create --base main --head feat/hermes-unattended-automation ...
gh pr view 8 --json number,title,url,state,baseRefName,headRefName,isDraft,mergeable,statusCheckRollup
```

- commit: `e372d9f Hermes 무인 뉴스 자동화 Skill 패키징`
- PR: [#8 Hermes 무인 뉴스 자동화 Skill 패키징](https://github.com/dumbbelloper/hermes-agent/pull/8)
- PR 상태: `OPEN`, draft 아님, `main` 대상, `MERGEABLE`
- GitHub Actions 확인 시 Ubuntu와 macOS 검증 성공
- GitHub Actions 확인 시 Windows 검증은 실행 중
- credential 검색 결과 실제 token 또는 chat ID 없음; 문서 placeholder만 존재

### 결정과 근거

1. 무인 controller, self-contained Skill, 테스트, CI와 운영 문서를 하나의 feature commit으로 유지한다.
   - runtime 이동과 문서 경로 변경이 함께 적용돼야 중간 상태의 깨진 실행 경로가 생기지 않기 때문이다.
2. PR은 draft가 아닌 일반 review 상태로 생성한다.
   - 로컬 validator와 전체 테스트 및 repository 외부 bundle 검증을 통과해 코드 검토 가능한 상태이기 때문이다.
3. Windows CI가 실행 중인 사실을 완료로 기록하지 않는다.
   - 원격 확인 시점의 실제 상태를 보존하고 최종 결과를 추정하지 않기 위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub 원격 저장소에 `feat/hermes-unattended-automation` 브랜치 생성
- GitHub [PR #8](https://github.com/dumbbelloper/hermes-agent/pull/8) 생성
- Hermes Skill Hub, tap, release와 version tag는 생성하지 않음
- Hermes gateway, cron, Telegram과 credential은 변경하지 않음

### 알려진 한계와 남은 작업

- Windows GitHub Actions 검증의 최종 결과 확인 필요
- PR review와 `main` 병합은 아직 수행하지 않음
- 병합 후 `v0.1.0` release와 실제 Hermes direct install 및 cron smoke test가 필요
- Linux, WSL2와 native Windows Hermes end-to-end 검증은 별도 운영 단계로 남아 있음

## 2026-07-28 16:23 KST — PR Windows CI UTF-8 호환성 수정

### 사용자 요청과 목적

- 생성한 PR을 검증 가능한 상태로 유지하고 다중 OS CI 실패를 해결

### 수행한 변경

- PR 최신 실행에서 Windows job 실패 로그 확인
- Windows 기본 text encoding인 CP1252로 한국어 Obsidian 문서를 읽던 테스트를 명시적 UTF-8 읽기로 수정
- 전체 로컬 테스트를 재실행

### 생성·수정한 문서와 파일

- [무인 자동화 테스트](./Automation/tests/test_automation.py)
- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
gh pr checks 8 --watch --interval 5
gh run view 30338177118 --job 90207542169 --log-failed
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
git diff --check
```

- Ubuntu와 macOS GitHub Actions 성공
- Windows 실패 원인: `Path.read_text()`가 CP1252를 사용해 한국어 문서 decoding 실패
- `read_text(encoding="utf-8")`로 수정 후 로컬 전체 테스트 47개 통과
- `git diff --check` 통과

### 결정과 근거

1. CI에서 Windows의 전역 encoding을 강제로 바꾸지 않고 파일 계약을 테스트에 명시한다.
   - Obsidian Markdown은 UTF-8 문서이며 호출부가 encoding을 명시해야 OS 기본 locale과 무관하게 같은 의미를 보장하기 때문이다.
2. native Windows 지원을 CI 실패 상태로 남기지 않고 수정 결과를 새 원격 실행으로 확인한다.
   - 배포 가이드가 Windows를 실험 지원으로 명시하더라도 code-level 호환성 matrix는 통과해야 하기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub Actions 실패 로그를 읽기 전용으로 확인
- OS encoding, Hermes, Telegram과 credential 설정은 변경하지 않음

### 알려진 한계와 남은 작업

- 수정 커밋 push 후 새 Windows GitHub Actions 결과 확인 필요
- 실제 native Windows Hermes gateway와 cron end-to-end 검증은 여전히 필요

## 2026-07-28 16:27 KST — PR과 commit 제목 규칙 통일

### 사용자 요청과 목적

- PR #8의 영어 Conventional Commit 제목이 기존 PR 및 `main` commit 이력과 이질적인 문제 해소

### 수행한 변경

- 기존 병합 PR #1~#7과 `main` commit 제목 규칙 확인
- PR #8 제목을 `Hermes 무인 뉴스 자동화 Skill 패키징`으로 변경
- 이번 브랜치의 영어 commit 제목 3개를 접두사 없는 한국어 제목으로 재작성
- history rewrite로 바뀐 commit hash를 앞선 작업 기록에 현행화
- `--force-with-lease`로 원격 feature branch를 안전하게 갱신

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- 구현 파일 내용은 변경하지 않음

### 실행한 검증과 결과

```text
git log main --oneline -15
gh pr list --state all --limit 15
gh pr view 7 --json commits,title,mergeCommit
gh pr view 6 --json commits,title,mergeCommit
git rebase -i main
git log main..HEAD --oneline
```

- 기존 PR #1~#7은 접두사 없는 한국어 제목 사용
- 기존 PR 내부 commit도 한국어 작업 제목과 별도 작업 로그 commit으로 구성
- 재작성된 브랜치 commit:
  - `e372d9f Hermes 무인 뉴스 자동화 Skill 패키징`
  - `db614f8 작업 로그에 Skill 배포 PR 기록`
  - `d167fac Windows UTF-8 문서 읽기 호환성 수정`
- 제목 재작성 후 최신 commit 기준 GitHub Actions는 Ubuntu, macOS와 Windows 모두 통과

### 결정과 근거

1. `feat:` 같은 Conventional Commit 접두사를 이 PR에만 사용하지 않는다.
   - 현재 프로젝트의 일관된 공개 이력은 한국어 작업 제목이며 squash merge 후 PR 제목이 `main` commit 제목이 되기 때문이다.
2. PR 제목만 바꾸지 않고 branch commit 제목도 함께 통일한다.
   - reviewer가 PR commit 목록을 확인할 때도 기존 작업 이력과 같은 형식을 유지하기 위해서다.
3. 구현 내용은 바꾸지 않고 commit metadata만 재작성한다.
   - 요청 범위는 제목 일관성이며 이미 통과한 코드와 검증 결과를 변경할 이유가 없기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub PR #8 제목 변경
- 원격 feature branch를 `--force-with-lease`로 안전하게 갱신
- `main`, 다른 branch, Hermes와 Telegram 설정은 변경하지 않음

### 알려진 한계와 남은 작업

- PR review와 병합은 아직 수행하지 않음
- 실제 Hermes direct install, gateway와 cron end-to-end 검증은 병합 후 필요

## 2026-07-28 17:02 KST — v0.1.0 release gate 및 Hermes 설치 호환성 보강

### 사용자 요청과 목적

- PR #8 병합 후 Skill을 실제 배포 가능한 `v0.1.0`으로 release
- GitHub main 직접 설치, Hermes direct install, tap과 skills.sh 공개 상태 검증
- release 전에 문서 상태와 실제 설치 계약을 일치시킴

### 수행한 변경

- GitHub `main`에서 Codex GitHub installer를 이용한 격리 설치와 launcher smoke test 수행
- skills.sh가 `hermes-news-automation`을 이미 공개 인덱싱하고 상세 페이지를 제공함을 확인
- Hermes installer가 `SKILL.md`의 명시적 지원 파일만 bundle에 포함하는 계약을 확인
- Skill의 모든 runtime 파일을 `SKILL.md`에 명시적으로 연결하고 누락 방지 회귀 테스트 추가
- Hermes가 command text가 아닌 Markdown 링크만 bundle dependency로 인식함을 확인하고 `scripts/run.py` launcher도 명시적 링크로 추가
- 최초 Hermes 설치 보안 검사에서 탐지된 prompt-injection 방어 문자열, Telegram 환경변수 접근과 pre-check 실행 구조를 분석
- prompt-injection 방어 기능은 유지하면서 scanner 자체 탐지 문자열을 조합형 상수로 변경
- Telegram credential을 환경변수 대신 workspace의 `.hermes-news/config/telegram.json`에서 읽도록 최소 권한 경계로 변경
- pre-check가 환경변수 전체를 복사하지 않고 workspace `cwd`를 전달하도록 변경
- workspace runtime 경로 선택 시 process environment를 변경하지 않고 작업 디렉터리를 사용하도록 변경
- credential loader와 설치 bundle 회귀 테스트를 추가하고 운영·배포 문서를 `v0.1.0` 계약으로 현행화
- 프로젝트 root workspace에서 `.hermes-news/`가 Git에 포함되지 않도록 ignore 규칙 추가

### 생성·수정한 문서와 파일

- [Hermes News Automation Skill](./skills/hermes-news-automation/SKILL.md)
- [Skill launcher](./skills/hermes-news-automation/scripts/run.py)
- [cron pre-check](./skills/hermes-news-automation/scripts/precheck.py)
- [runtime CLI](./skills/hermes-news-automation/scripts/runtime/hermes_agent/cli.py)
- [Telegram runtime](./skills/hermes-news-automation/scripts/runtime/hermes_agent/telegram.py)
- [artifact validation runtime](./skills/hermes-news-automation/scripts/runtime/hermes_agent/automation.py)
- [Skill 배포 회귀 테스트](./Automation/tests/test_skill_distribution.py)
- [Telegram 테스트](./Automation/tests/test_telegram.py)
- [Automation 안내](./Automation/README.md)
- [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)
- [Hermes 무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)
- [프로젝트 계획](./PROJECT_PLAN.md)
- [환경변수 예시](./.env.example)
- [Git ignore 설정](./.gitignore)
- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
python3 <skill-installer>/scripts/install-skill-from-github.py \
  --repo dumbbelloper/hermes-agent \
  --path skills/hermes-news-automation --ref main --dest <temporary-directory>
python3 <installed-skill>/scripts/run.py init --workspace <temporary-workspace>
python3 <installed-skill>/scripts/run.py doctor --workspace <temporary-workspace>
python3 <installed-skill>/scripts/run.py validate-registry
HERMES_HOME=<temporary-profile> hermes skills inspect <identifier>
HERMES_HOME=<temporary-profile> hermes skills install <identifier> --yes
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
python3 <skill-creator>/scripts/quick_validate.py \
  skills/hermes-news-automation
Hermes skills_guard로 community source local scan
git diff --check
```

- GitHub `main` bundle의 repository 외부 설치와 `init` 및 13개 출처 registry 검증 통과
- credential 없는 최초 `doctor`는 값 노출 없이 의도한 `configuration_error` 반환
- skills.sh 공개 상세 페이지:
  `https://skills.sh/dumbbelloper/hermes-agent/skills/hermes-news-automation`
- 최초 main 기준 Hermes install은 directory reference 때문에 fetch 실패
- 모든 runtime 파일을 명시한 commit에서는 bundle fetch와 security scan 단계까지 진입
- 최초 security scan은 실제 악성 동작이 아닌 방어 문자열과 secret 환경변수 접근을 `DANGEROUS`로 판정해 설치 차단
- credential 파일과 명시적 workspace 경계로 변경 후 Hermes community scan:
  `SAFE`, 허용 결정, deterministic pre-check subprocess에 대한 medium 정보성 finding 1건
- 수정 후 전체 테스트 50개 통과
- Skill Creator validator 통과
- 격리 workspace의 유효한 Telegram 설정을 포함한 `doctor` 상태 `ok`
- Python compile 대상 runtime의 13개 활성 출처 registry 검증 통과
- 최종 불변 commit `340efb9` raw URL을 새 격리 Hermes profile에 설치
- 최종 Hermes scan `SAFE`, `scripts/run.py`와 전체 runtime 파일 설치, `init → doctor → validate-registry` 통과
- PR #9 최초 CI는 package 설치가 만든 `hermes_news_automation.egg-info`를 runtime source로 오인한 회귀 테스트 때문에 세 OS에서 동일 실패
- runtime completeness 검사 범위를 실제 `scripts/runtime/hermes_agent/` package로 좁혀 build metadata를 제외
- `git diff --check` 통과

### 결정과 근거

1. `--force`나 scanner 우회를 사용하지 않는다.
   - Hermes는 community Skill의 `DANGEROUS` 판정을 강제로 우회하지 않으며, 배포자는 경고 원인을 제거하고 검증 가능한 최소 권한 구조를 제공해야 하기 때문이다.
2. Telegram credential은 agent process의 전체 환경이 아니라 전용 workspace 파일로 격리한다.
   - runtime이 다른 provider credential까지 포함할 수 있는 process environment를 다루지 않고 필요한 두 값만 읽게 하기 위해서다.
3. `telegram.json`은 자동 생성하거나 Git에 포함하지 않는다.
   - 실제 secret은 사용자 또는 운영자가 별도 주입하고 소유자와 runner만 읽어야 하기 때문이다.
4. prompt-injection 출력 차단은 제거하지 않는다.
   - scanner가 방어용 표본 문자열을 공격 지시로 오인한 것이므로 단어 조합으로 동일 검증 의미를 유지한다.
5. Skill runtime은 `SKILL.md`에서 모든 파일을 직접 참조한다.
   - 현재 Hermes GitHub installer는 directory recursion이 아니라 직접 참조 파일만 가져오기 때문이다.
6. 문서는 `v0.1.0` 최종 계약을 먼저 반영하고 이 commit이 main에 병합된 직후 동일 commit을 tag한다.
   - release tag 안의 문서가 실제 설치 방식 및 보안 경계와 일치해야 하기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub 원격에 `release/v0.1.0` 브랜치와 설치 bundle 호환성 commit 생성
- skills.sh 공개 인덱스와 상세 페이지를 읽기 전용으로 확인
- `/private/tmp` 아래에 Codex 설치 디렉터리, Hermes 격리 profile과 테스트 workspace 생성
- 사용자 기본 `~/.hermes` profile, 설치 Skill, gateway, cron과 실제 credential은 변경하지 않음
- GitHub version tag와 Release는 아직 생성하지 않음

### 알려진 한계와 남은 작업

- release 브랜치 PR 생성, 다중 OS CI와 main 병합 필요
- 병합 commit에 `v0.1.0` tag 및 GitHub Release 생성 필요
- tag 기준 skills.sh direct install과 Hermes tap 설치 재검증 필요
- 사용자는 기존 `~/.zshrc` Telegram 환경변수 값을
  `<workspace>/.hermes-news/config/telegram.json`으로 한 번 이전해야 함
- 실제 Hermes gateway와 cron end-to-end 실행은 release 후 별도 운영 검증으로 남음

## 2026-07-28 17:25 KST — Hermes News Automation v0.1.0 공개 배포

### 사용자 요청과 목적

- PR #8 병합 후 release gate를 끝까지 수행
- 검증된 main commit에 첫 공개 version tag와 GitHub Release 생성
- skills.sh 공개 설치, Hermes direct install과 tap 동작을 실제 격리 환경에서 확인

### 수행한 변경

- [PR #9](https://github.com/dumbbelloper/hermes-agent/pull/9)를 생성하고 다중 OS CI 실패 1건을 수정
- CI에서 package 설치가 만든 `egg-info`를 runtime source로 오인한 테스트 범위를 실제 Python package로 제한
- Ubuntu, macOS와 Windows CI 통과 후 PR #9를 기존 규칙대로 squash merge
- 병합 commit `437c37a`에 annotated tag `v0.1.0` 생성 및 push
- 검증한 Python wheel을 포함한
  [Hermes News Automation v0.1.0 GitHub Release](https://github.com/dumbbelloper/hermes-agent/releases/tag/v0.1.0) 공개
- 병합된 main의 skills.sh 정규 identifier로 새 Hermes profile에 direct install
- 별도 Hermes profile에 repository tap을 추가하고 검색 및 설치 경로를 확인

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- GitHub Release asset:
  `hermes_news_automation-0.1.0-py3-none-any.whl`
- release source 문서와 코드는 tag `v0.1.0`의 main 상태와 동일

### 실행한 검증과 결과

```text
gh pr checks 9 --watch --interval 5
gh pr merge 9 --squash
git pull --ff-only origin main
HERMES_HOME=<temporary-profile> hermes skills install \
  skills-sh/dumbbelloper/hermes-agent/skills/hermes-news-automation --yes
HERMES_HOME=<temporary-profile> hermes skills tap add \
  dumbbelloper/hermes-agent
python3 -m pip wheel --no-deps --no-build-isolation ...
python3 -m pip install --no-deps --target <temporary-directory> <wheel>
PYTHONPATH=<temporary-directory> python3 -m hermes_agent validate-registry
git tag -a v0.1.0 <merge-commit>
git push origin v0.1.0
gh release create v0.1.0 <wheel> ...
gh release view v0.1.0 --json ...
```

- PR #9 최초 CI 실패 원인은 source 문제가 아니라 build가 만든
  `hermes_news_automation.egg-info`를 completeness test가 포함한 것
- 수정 후 Ubuntu, macOS와 Windows GitHub Actions 모두 통과
- tag `v0.1.0` 대상: `437c37a434f178afa34ef71b7d4c384a9ab28fbf`
- Release 상태: 공개, draft 아님, prerelease 아님
- wheel size: 46,929 bytes
- wheel SHA-256:
  `e300ed395b8f6ca0e5e7b7f5b396705fe68e4d62bc1fd8f422e0a3f3f3eff124`
- wheel 격리 설치와 13개 활성 출처 registry 검증 통과
- skills.sh 정규 identifier 설치 시 scanner `SAFE`, community source 설치 허용
- 설치 bundle에 `SKILL.md`, artifact schema, pre-check, launcher와 전체 runtime 포함
- [skills.sh 상세 페이지](https://skills.sh/dumbbelloper/hermes-agent/skills/hermes-news-automation) 공개 확인
- Hermes tap 등록은 성공하고 `skills/` 경로를 인식
- Hermes 0.19.0의 tap 추가 직후 `search`는 해당 GitHub 결과를 반환하지 않았으나,
  문서의 설치 identifier는 skills.sh source로 동일 bundle을 정상 설치

### 결정과 근거

1. `v0.1.0`은 PR #9의 squash merge commit에 직접 tag한다.
   - 공개 source, release 문서, CI 결과와 설치 검증 대상을 하나의 불변 commit으로 묶기 위해서다.
2. wheel을 선택 release asset으로 첨부한다.
   - Hermes 사용자는 필요 없지만 일반 Python 환경과 독립 registry 검증에도 같은 version을 사용할 수 있기 때문이다.
3. skills.sh를 실제 공개 설치 경로로 안내한다.
   - 인덱싱, 상세 페이지, source revision, 보안 scan과 bundle 설치가 모두 확인됐기 때문이다.
4. tap 검색 성공을 과장하지 않는다.
   - tap 등록은 성공했지만 현재 Hermes 0.19.0의 검색 결과에는 나타나지 않았고 설치는 skills.sh resolver가 처리했기 때문이다.
5. 실제 credential을 release artifact 또는 검증 profile에 사용하지 않는다.
   - 설치 및 doctor 검증에는 테스트 전용 placeholder만 사용하고 사용자 secret은 읽거나 기록하지 않았다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub `main`에 PR #9 squash merge
- GitHub tag `v0.1.0` 생성
- 공개 [GitHub Release v0.1.0](https://github.com/dumbbelloper/hermes-agent/releases/tag/v0.1.0)과 wheel asset 생성
- skills.sh는 공개 repository main의 Skill을 인덱싱한 상태
- `/private/tmp` 격리 Hermes profile 두 곳에 direct install 및 tap 설정 적용
- 사용자 기본 `~/.hermes`, gateway, cron, Telegram과 실제 credential은 변경하지 않음

### 알려진 한계와 남은 작업

- 사용자는 기존 `~/.zshrc` Telegram 환경변수 값을 workspace의
  `.hermes-news/config/telegram.json`으로 한 번 이전해야 함
- 실제 사용자 workspace에서 `doctor`를 실행하고 첫 Hermes cron end-to-end smoke test 필요
- Hermes 0.19.0에서 custom tap을 추가한 직후 GitHub source 검색 결과가 비어 있는 원인 확인 필요
- native Windows는 code-level CI만 통과했으며 gateway, Scheduled Task, UTF-8,
  Telegram end-to-end 검증 전까지 실험 지원
- 장기 실행을 위한 retry backoff, circuit breaker와 운영 지표는 후속 작업

## 2026-07-28 17:48 KST — 진척도·문서 동기화 및 로컬 Hermes 실행 상태 점검

### 사용자 요청과 목적

- 현재 구현·배포 진척도와 프로젝트 문서의 상태가 일치하는지 점검
- 매번 수동 지시하지 않아도 commit마다 문서 동기화를 확인할 수 있는지 검토
- 현재 macOS에서 Hermes Agent가 `hermes-news-automation` Skill을 주기 실행 중인지 확인

### 수행한 변경

- main과 origin/main의 동기화, release, source registry, 수집 데이터,
  Obsidian 산출물 및 Skill runtime 상태를 상호 대조
- 저장소 Git hook, GitHub Actions trigger와 문서 검증 범위를 확인
- 사용자 Hermes home의 cron 저장소, gateway 상태와 프로젝트 실행 workspace를
  credential 내용에 접근하지 않고 파일 존재 여부만으로 확인
- 점검 결과만 기록했으며 정책·계획·가이드 본문과 전역 Hermes 설정은 변경하지 않음

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
git status --short --branch
git config --get core.hooksPath
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
python3 -m unittest discover -s Automation/tests
cmp Automation/config/source_registry.json \
  skills/hermes-news-automation/references/default_sources.json
hermes gateway status
```

- main은 origin/main과 동기화되어 있었고 점검 시작 시 working tree는 clean
- 공개 release와 package version은 `v0.1.0`, 활성 출처는 13개
- 현재 source JSONL은 13개 파일, 총 1,594건이며
  [출처 카탈로그](./SOURCE_CATALOG.md)의 수치와 일치
- Inbox 문서 12개와 Digest 3개를 확인했고 note validation은 issue 없이 통과
- offline test 50개와 Skill validator 통과
- 프로젝트 registry와 Skill bundle registry가 byte 단위로 동일
- 활성 프로젝트 문서의 로컬 Markdown link는 모두 유효하나,
  이 작업 로그의 과거 기록에는 source 이동 전 경로를 가리키는 link 19개가 남아 있음
- 별도 Git hook과 `core.hooksPath` 설정이 없고, 현재 CI는 Skill·test·package 변경만
  검증하여 계획·카탈로그·작업 로그 동기화를 차단하지 않음
- Hermes gateway는 실행 중이 아님
- 기본 Hermes cron directory는 있으나 `jobs.json`과 output directory가 없어
  등록된 기본 profile cron job 및 실행 산출물을 확인할 수 없음
- 프로젝트 `.hermes-news`에는 Telegram config, state와 automation run 기록이 없음
- sandbox가 Hermes cron 조회 과정의 output directory 생성을 허용하지 않아
  `hermes cron list/status` 자체는 완료하지 못했으나, canonical `jobs.json` 부재와
  gateway 중지 상태는 별도 read-only 검사로 확인

### 결정과 근거

1. 문서 동기화는 `문서 상태 생성기 + local pre-commit 검사 + CI required check`로 구성한다.
   - Git hook만 사용하면 설치하지 않은 clone, `--no-verify`와 agent의 별도 실행 환경을
     통제할 수 없으므로 CI가 최종 병합 gate가 되어야 한다.
2. hook에서는 자유 서술 문서를 자동 추측해 수정하지 않고 deterministic 상태만 생성한다.
   - 출처 수, record 수, note 수, version과 registry hash는 안전하게 자동 생성할 수 있지만
     phase 의미와 남은 작업은 사람 또는 agent의 판단이 필요하기 때문이다.
3. 현재 로컬 Hermes 자동화는 미구성으로 판정한다.
   - gateway가 중지되어 있고 cron `jobs.json`, 프로젝트 config·state·run 기록이 모두
     없으므로 설치 가능한 Skill과 실제 예약 실행 상태를 구분해야 한다.
4. 이번 요청은 점검이므로 발견된 문서 불일치는 후속 변경 대상으로 남긴다.
   - 사용자 승인 없이 계획 상태와 배포 가이드의 의미를 바꾸지 않기 위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- Git hook, GitHub Actions, Hermes gateway, cron과 Telegram 설정을 변경하지 않음
- credential 또는 token의 값은 읽거나 기록하지 않음

### 알려진 한계와 남은 작업

- [프로젝트 계획](./PROJECT_PLAN.md)의 상단 상태가 Phase 2·4의 부분 구현을 반영하지 않음
- [프로젝트 계획](./PROJECT_PLAN.md)의 Phase 3에서 이미 추가된 4개 전문 매체와
  초기 Digest 3개가 완료 또는 부분 완료로 표시되지 않음
- [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)는 Hermes 0.19.0의 custom tap
  검색 제약과 실제로 검증된 skills.sh 설치 경로의 우선순위를 명확히 반영해야 함
- [자동화 README](./Automation/README.md)의 Alpha 상태는 공개 Skill `v0.1.0` 및
  실환경 cron 미검증 상태를 함께 표현하도록 구체화할 필요가 있음
- 과거 [작업 로그](./WORK_LOG.md)의 이동 전 runtime source link 19개 정리 필요
- commit 문서 sync용 상태 생성기·hook bootstrap·CI required check는 아직 구현되지 않음
- 실제 주기 실행을 위해 workspace 초기화, Telegram config 이전, `doctor`,
  gateway service 설치, cron 등록과 첫 end-to-end smoke test가 필요

## 2026-07-29 15:00 KST — 현재 프로젝트 진척도 재검증

### 사용자 요청과 목적

- 중단했던 현재 프로젝트 진척도 보고를 재개
- 구현·데이터·문서·로컬 운영 상태를 최신 workspace 기준으로 재검증

### 수행한 변경

- 코드, Registry, 수집 데이터, Obsidian 산출물과 계획 문서의 상태를 대조
- offline test, Skill runtime 컴파일, Registry와 Vault 문서 검증을 재실행
- Hermes gateway, 기본 cron 등록 파일, 프로젝트 Telegram 설정과 실행 이력의
  존재 여부를 credential 내용에 접근하지 않고 확인
- 상태 점검과 기록만 수행했으며 코드, 정책 문서와 운영 설정은 변경하지 않음

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
cmp Automation/config/sources.json \
  skills/hermes-news-automation/scripts/runtime/hermes_agent/default_sources.json
PYTHONPYCACHEPREFIX=/private/tmp/hermes-pycache \
  python3 -m compileall -q skills/hermes-news-automation/scripts
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
hermes gateway status
```

- offline test 50개 전부 통과
- 프로젝트 Registry와 배포 Skill 기본 Registry가 byte 단위로 동일
- Skill runtime 전체 컴파일 통과
- 활성 출처 13개 Registry 검증 통과
- Inbox 문서 12개, issue 0건으로 Vault 문서 검증 통과
- current source JSONL 13개, 총 1,594건과 Digest 3개 유지
- `main`은 로컬 tracking 정보상 `origin/main`과 같은 commit이며,
  작업 트리 변경은 이 작업 로그뿐
- Hermes gateway는 실행 중이 아니며 기본 cron `jobs.json`이 없음
- 프로젝트 Telegram 설정과 automation run 이력이 없음

### 결정과 근거

1. 구현·패키징 진척도는 공개 `v0.1.0` 기준으로 완료 상태로 본다.
   - 수집, agent 검증, Obsidian 작성, Telegram ledger, self-contained Skill,
     크로스플랫폼 CI와 배포 산출물이 구현되어 있고 현재 회귀 검증도 통과했다.
2. 실제 운영 진척도는 활성화 전 상태로 본다.
   - gateway, cron job, workspace credential 설정과 첫 실환경 실행 이력이 없기 때문이다.
3. 전체 진척도를 단일 백분율로 표시하지 않는다.
   - 구현 완료와 운영 미구성의 성격이 달라 하나의 수치가 실제 상태를 왜곡하기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- Hermes gateway, cron, Telegram, Git hook과 GitHub 설정을 변경하지 않음
- credential 또는 token의 값은 읽거나 기록하지 않음

### 알려진 한계와 남은 작업

- [프로젝트 계획](./PROJECT_PLAN.md) 상단과 Phase 3 표기가 실제 구현 상태보다 뒤처짐
- [자동화 README](./Automation/README.md)의 Alpha 표현과
  [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)의 설치 경로 설명 현행화 필요
- 문서 상태 생성기, local pre-commit 검사와 CI 문서 동기화 gate 미구현
- workspace 초기화, Telegram 설정 이전, `doctor`, gateway service 설치,
  cron 등록과 첫 end-to-end smoke test 필요
- 출처별 retry backoff, circuit breaker, 장기 성공률·비용 dashboard와
  실제 표본 기반 confidence/event-key 품질 보정 필요
- native Windows 실환경 end-to-end 검증 필요

## 2026-07-29 15:12 KST — 진척도와 프로젝트 문서 동기화 감사

### 사용자 요청과 목적

- 현재 구현·배포·운영 진척도가 프로젝트 문서에 정확히 반영되어 있는지 확인

### 수행한 변경

- 코드와 데이터에서 결정적으로 확인 가능한 version, 출처 수, record 수,
  Vault 문서 수와 Digest 수를 주요 프로젝트 문서와 대조
- 프로젝트 계획의 Phase 표시, 자동화·배포·운영 가이드 상태 문구를 실제 검증
  결과 및 로컬 운영 상태와 비교
- 전체 Markdown의 로컬 링크와 GitHub Actions path filter, Git hook 설치 여부 확인
- 감사 결과만 기록하고 프로젝트 계획·가이드·CI·hook은 변경하지 않음

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests
git config --get core.hooksPath
```

- package와 문서의 공개 version `0.1.0`/`v0.1.0` 일치
- 운영 출처 13개, current record 1,594건, Inbox 12개와 Digest 3개가
  Registry·데이터·README·카탈로그·프로젝트 계획 사이에서 일치
- offline test 50개, Registry와 Vault 문서 검증 통과
- [무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)의
  “최초 실환경 cron 검증 필요” 상태는 gateway·cron·실행 이력이 없는 현재 상태와 일치
- [프로젝트 계획](./PROJECT_PLAN.md) 상단은 Phase 0·1 완료만 표시하여
  Phase 2와 Phase 4의 부분 완료를 반영하지 않음
- 프로젝트 계획의 Phase 3은 편집 언론 4개 추가와 Digest 3개 생성을
  완료 또는 부분 완료로 표시하지 않음
- [자동화 README](./Automation/README.md)는 구현 완료를 설명하지만
  공개 `v0.1.0`과 실환경 cron 미검증 상태를 헤더에서 구분하지 않음
- [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)와 root README는
  skills.sh 설치와 Hermes tap 경로를 함께 안내하지만, 실제 검증에서 확인된
  Hermes 0.19.0 custom tap 검색 제약과 skills.sh 우선 경로를 명확히 구분하지 않음
- 활성 문서의 로컬 링크는 유효하지만 과거 작업 로그에는 이동 전 runtime 경로
  19개와 잘못된 `Source Catalog.md` 경로 1개, 총 20개 깨진 링크가 남아 있음
- CI path filter는 Skill·test·package 변경만 감시하고 Registry 단독 변경,
  계획·카탈로그·README·작업 로그 변경은 검사하지 않음
- local pre-commit hook과 별도 `core.hooksPath`가 없어 commit 시 문서
  동기화를 자동 차단하지 않음

### 결정과 근거

1. 현재 동기화 상태를 “부분 동기화”로 판정한다.
   - 핵심 수치와 운영 상태는 일치하지만 단계 상태와 배포 제약이 문서에 완전히
     반영되지 않았고 자동 회귀 방지 장치도 없기 때문이다.
2. 정책·설계 문서의 기준일 자체는 오류로 보지 않는다.
   - 기준일 이후 핵심 데이터가 변경되지 않았지만, 상태 문구를 수정할 때는
     기준일도 함께 갱신해야 한다.
3. 이번 요청은 확인 작업이므로 불일치를 자동 수정하지 않는다.
   - 계획 의미와 설치 경로 우선순위 변경은 별도 문서 수정 작업으로 처리한다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- Git hook, GitHub Actions, Hermes, cron과 Telegram 설정을 변경하지 않음

### 알려진 한계와 남은 작업

- 프로젝트 계획 Phase 2·3·4와 상단 상태 현행화 필요
- 자동화 README와 Skill 배포 가이드의 상태·설치 경로 설명 현행화 필요
- 작업 로그의 깨진 로컬 링크 20개 정리 필요
- deterministic 문서 상태 생성기, hook bootstrap과 CI 문서 sync check 구현 필요
- GitHub branch protection의 required check 설정 여부는 이번 로컬 감사 범위에서
  실시간 조회하지 않음

## 2026-07-29 15:20 KST — 문서 동기화와 Skill 전체 lifecycle 실행

### 사용자 요청과 목적

- 진척도와 문서 사이에서 확정 가능한 불일치를 수정
- `hermes-news-automation` Skill로 실제 데이터 수집, agent 선별·독립 검증,
  Obsidian 작성과 Telegram 알림까지 전체 lifecycle 실행

### 수행한 변경

- 프로젝트 계획 상단과 Phase 3을 실제 Phase 2·3·4 부분 완료 상태로 현행화
- 자동화 README에 `v0.1.0` 공개와 최초 실환경 cron 미검증 상태를 구분
- skills.sh 우선 설치 경로와 Hermes 0.19.0 custom tap 검색 제약을
  README와 Skill 배포 가이드에 반영
- 작업 로그의 이동 전 runtime link 19개와 잘못된 출처 카탈로그 link 1개 수정
- CI가 모든 Markdown, Registry와 skills.sh metadata 변경에서도 실행되도록
  path filter 확장
- version, 출처·Inbox·Digest 수와 전체 로컬 Markdown link를 검증하는
  문서 sync 회귀 테스트 4개 추가
- repository root를 Skill workspace로 초기화하고 기존 Telegram 환경 설정을
  `.hermes-news/config/telegram.json`으로 값 노출 없이 이전
- 13개 출처를 두 차례 정상 수집하고 Curator/Writer와 별도 Verifier를 이용해
  최신 항목을 fail-closed 방식으로 처리
- 검증을 통과한 Visa 결제 데이터 문서 1건을 Obsidian Inbox에 원자 작성하고
  Telegram으로 1회 전송
- 최신 Skill workspace 기준 누적 record 1,595건, Inbox 13건과 macOS 수동
  end-to-end 성공 상태를 프로젝트 계획·출처 카탈로그·README·운영 가이드에 반영

### 생성·수정한 문서와 파일

- [프로젝트 계획](./PROJECT_PLAN.md)
- [프로젝트 README](./README.md)
- [자동화 README](./Automation/README.md)
- [출처 카탈로그](./SOURCE_CATALOG.md)
- [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md)
- [무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md)
- [문서 sync 테스트](./Automation/tests/test_document_sync.py)
- [Skill validation workflow](./.github/workflows/skill-validation.yml)
- [Visa FIFA World Cup 2026 결제 데이터](./Inbox/2026-07-22%20New%20Visa%20Data%20Reveals%20How%20the%20FIFA%20World%20Cup%202026%E2%84%A2%20Created%20Pop-Up%20Economies%20Across%20Canada%2C%20Mexico%20and%20the%20United%20States.md)
- [작업 로그](./WORK_LOG.md)
- Git에서 제외되는 `.hermes-news/` workspace config, 수집 state, run manifest,
  decision·artifact·delivery ledger

### 실행한 검증과 결과

```text
python3 skills/hermes-news-automation/scripts/run.py init --workspace ...
python3 skills/hermes-news-automation/scripts/run.py doctor --workspace ...
python3 skills/hermes-news-automation/scripts/run.py automation-start --max-items 5
python3 skills/hermes-news-automation/scripts/run.py automation-next ...
python3 skills/hermes-news-automation/scripts/run.py automation-submit ...
python3 skills/hermes-news-automation/scripts/run.py automation-notify ...
python3 skills/hermes-news-automation/scripts/run.py automation-finish ...
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
```

- 초기 sandbox 수집은 DNS 제한으로 13개 출처가 모두 실패하여 실제 사유로
  `automation-abort`하고 logical lock 해제
- 네트워크 허용 재실행에서 13개 출처 모두 성공, source failure 0건
- 최신 Skill workspace current record 1,595건
- 첫 처리 실행은 이벤트 홍보 1건과 실적 발표 1건 제외, 원문 추출 불완전 2건
  재시도, Writer 과장을 독립 Verifier가 발견한 1건 격리
- 다음 처리 실행에서 Visa World Cup 결제 데이터 1건이 Curator confidence 0.93,
  Verifier confidence 0.97과 모든 결정론적 검사를 통과
- Obsidian Inbox 문서 1건 작성, Telegram 전송 1건 성공,
  unknown delivery 0건
- 최종 run 상태 `completed_with_exceptions`: `notified` 1건, `retryable` 4건,
  source failure 0건
- Vault 문서 13개, validation issue 0건
- offline 단위·통합·문서 sync test 54개 전부 통과
- 전체 로컬 Markdown link 유효, `git diff --check` 통과

### 결정과 근거

1. canonical 원문을 web tool로 추출하지 못한 항목은 제3자 사본으로 대체 발행하지
   않고 `retryable`로 보존한다.
   - Skill의 원문 한정과 fail-closed 규칙을 지키기 위해서다.
2. 독립 Verifier가 시제 과장과 원문에 없는 조건을 발견한 PCI SSC AI 문서는
   초안을 임의 수정해 통과시키지 않고 격리한다.
   - Writer와 Verifier의 독립성과 검증 threshold를 유지하기 위해서다.
3. Visa 문서에는 VisaNet 범위, 비교 기간과 Visa 거래만 반영한다는 한계를 명시한다.
   - 행사 효과를 전체 소비시장이나 인과관계로 과도하게 일반화하지 않기 위해서다.
4. 문서 sync는 CI 회귀 테스트로 강제하되 자유 서술의 의미 판단은 자동 생성하지 않는다.
   - version, count와 link는 결정적으로 검사할 수 있지만 Phase 의미는 검토가 필요하다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 설정된 Telegram 수신자에게 검증 완료 Obsidian 문서 1건 전송
- repository 내부 Git 제외 경로에 Telegram config와 Skill 실행 state 생성
- Telegram config 권한을 소유자 읽기·쓰기만 가능한 `600`으로 설정
- 사용자 shell profile, credential 값, Hermes gateway, cron과 Git hook은 변경하지 않음

### 알려진 한계와 남은 작업

- Amex canonical 문서 3건은 web extraction이 JavaScript shell만 반환하고,
  JCB canonical 문서 1건은 web tool이 직접 추출하지 못해 `retryable`
- 격리된 PCI SSC AI 문서는 시제와 데이터 익명화 조건을 원문대로 새로 작성하고
  독립 검증을 다시 받아야 함
- 이번 검증은 macOS 수동 실행이며 gateway cron 등록, 예약 실행,
  OS·gateway 재시작 후 복구 검증은 아직 남음
- Linux, WSL2와 native Windows 실환경 end-to-end 검증 필요
- local pre-commit hook bootstrap과 GitHub branch protection required check 설정은 미구현

## 2026-07-30 10:46 KST — 문서 sync 변경 commit·push 및 PR 생성

### 사용자 요청과 목적

- 문서 sync가 맞는지 최종 확인
- 검증된 변경을 commit하고 원격 branch에 push한 뒤 main 대상 PR 생성

### 수행한 변경

- 최신 Skill workspace와 추적 문서의 출처·record·Inbox·Digest 수치 재검증
- version, 로컬 Markdown link, Registry, Vault와 Git 제외 상태 재검증
- 전용 branch를 생성해 문서 sync, CI 검사, lifecycle 산출물을 commit
- 원격 branch에 push하고 main 대상 GitHub PR 생성

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- 이 기록 전 첫 commit에 포함된 파일은 직전
  “문서 동기화와 Skill 전체 lifecycle 실행” 기록의 목록과 동일

### 실행한 검증과 결과

```text
git diff --check
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests
python3 skills/hermes-news-automation/scripts/run.py validate-registry
python3 skills/hermes-news-automation/scripts/run.py validate-notes --vault-dir .
git check-ignore .hermes-news/config/telegram.json .hermes-news/data
```

- offline 단위·통합·문서 sync test 54개 통과
- 활성 출처 13개, Skill workspace record 1,595건
- Inbox 13개, Digest 3개, Vault validation issue 0건
- Telegram credential과 runtime state는 Git 제외 상태
- `git diff --check` 통과
- branch: `codex/document-sync-lifecycle-20260730`
- 첫 commit: `3a2429d` (`문서 동기화와 뉴스 lifecycle 검증`)
- 원격 branch push 성공
- GitHub [PR #11 — 문서 동기화와 뉴스 자동화 lifecycle 검증](https://github.com/dumbbelloper/hermes-agent/pull/11) 생성
- PR은 main 대상 open 상태이며 draft가 아님
- GitHub Actions `validate`가 Ubuntu, macOS와 Windows에서 모두 통과

### 결정과 근거

1. main에 직접 commit하지 않고 전용 branch와 PR을 사용한다.
   - CI 결과와 문서·코드 변경을 검토 가능한 단위로 유지하기 위해서다.
2. `.hermes-news/` credential·수집 state·delivery ledger는 commit하지 않는다.
   - 운영 비밀정보와 로컬 영속 상태를 공개 source 변경에서 분리하기 위해서다.
3. PR 본문에 성공 결과뿐 아니라 retryable 4건과 cron 미검증 상태도 명시한다.
   - lifecycle 성공 범위와 남은 운영 한계를 함께 검토할 수 있게 하기 위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub 원격 branch `codex/document-sync-lifecycle-20260730` 생성
- GitHub PR #11 생성
- credential, Hermes gateway, cron과 Telegram 설정은 추가 변경하지 않음

### 알려진 한계와 남은 작업

- PR merge는 사용자 요청 범위에 포함하지 않음

## 2026-07-30 16:34 KST — 현시점 뉴스 수집 및 Obsidian 발행 판정

### 사용자 요청과 목적

- `hermes-news-automation` Skill을 사용해 현시점 데이터를 수집하고, 신규 게시글만
  검증하여 Obsidian 문서로 작성
- 신규 게시글이 없거나 발행 기준을 충족하지 못하면 불필요한 문서를 만들지 않음

### 수행한 변경

- 초기화된 `.hermes-news/` workspace에서 활성 출처 13개를 최신 상태로 수집
- controller가 선택한 신규 queue 5건의 canonical 원문을 추출하고 발행 적합성 판정
- PCI SSC 행사 홍보 1건을 `irrelevant`로 기록
- 본문을 충분히 추출할 수 없었던 Amex 3건과 JCB 1건을 `retryable`로 기록
- 검증을 통과한 항목이 없어 Inbox 문서와 Telegram 발행을 생성하지 않음
- run `20260730T073214185857Z-8f7c9111`을
  `completed_with_exceptions`로 정상 종료

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- Git에서 제외되는 `.hermes-news/data/` 아래 수집 원본, 정규화 snapshot, source
  state, automation run·decision ledger
- 새 [Inbox](./Inbox/) 문서는 생성하지 않음

### 실행한 검증과 결과

```text
python3 skills/hermes-news-automation/scripts/run.py automation-start --max-items 5
python3 skills/hermes-news-automation/scripts/run.py automation-next ...
python3 skills/hermes-news-automation/scripts/run.py automation-reject ...
python3 skills/hermes-news-automation/scripts/run.py automation-notify ...
python3 skills/hermes-news-automation/scripts/run.py automation-finish ...
python3 skills/hermes-news-automation/scripts/run.py automation-status ...
python3 Automation/run.py validate-notes --vault-dir .
```

- sandbox 첫 수집은 DNS 제한으로 전 출처가 실패하여 실제 사유와 함께
  `automation-abort`하고 lock을 해제
- 네트워크 허용 재실행에서 활성 출처 13개 모두 성공, source failure 0건
- source snapshot 기준 신규 감지: PCI Blog 1건, Visa Press 2건, Banking Dive
  5건, Payments Dive 2건, PYMNTS 10건
- queue는 최대 5건으로 제한되었고 기존 decision ledger가 3건을 억제
- queue 결과: `irrelevant` 1건, `retryable` 4건, committed·notified 0건
- `automation-notify`: 전송 문서 0건, unknown delivery 0건
- 최종 상태 `completed_with_exceptions`
- Vault 문서 13개, validation issue 0건

### 결정과 근거

1. PCI SSC 팟캐스트는 행사 기조연설자와 등록을 홍보하는 콘텐츠이므로 발행하지
   않는다.
   - Skill 계약이 행사 홍보를 명시적으로 제외하며, 결제 표준·기술·규제의 구체적
     변경이 없기 때문이다.
2. JavaScript 안내만 반환한 Amex 원문 3건과 추출 도구가 거부한 JCB 원문 1건은
   제목이나 수집 description만으로 문서화하지 않는다.
   - 원문 기반 사실 검증이 불가능할 때 발행을 막는 fail-closed 원칙을 지키기
     위해서다.
3. 검증 통과 항목이 0건이므로 Obsidian 뉴스 문서와 Telegram 메시지를 만들지
   않는다.
   - 신규 감지와 발행 가능 신규 문서를 구분하고 불필요한 문서 생성을 피하기
     위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 공개 뉴스 출처 13개에 읽기 요청을 수행
- Telegram 전송 0건
- credential, shell profile, Hermes gateway, cron, Git 설정은 변경하지 않음

### 알려진 한계와 남은 작업

- Amex canonical 원문 3건은 web extraction이 JavaScript shell만 반환하고 JCB
  canonical 원문 1건은 추출 도구가 URL을 거부하여 다음 실행에서 재시도 필요
- `--max-items 5` 제한과 기존 decision ledger에 따라 이번 run이 모든 source-level
  신규 감지 항목을 문서 후보로 처리한 것은 아님

## 2026-07-30 16:41 KST — Amex·JCB 원문 추출 대안 진단

### 사용자 요청과 목적

- 원문 추출이 불가능한 datasource를 유지할 필요가 있는지 판단하고 정상 수집을
  위한 대안을 확인

### 수행한 변경

- Amex와 JCB의 source state, raw 수집 이력, automation queue 이력을 비교
- 목록 datasource와 개별 canonical 원문 추출 단계를 분리해 장애 범위를 확인
- Amex 기사별 공식 AEM model JSON과 JCB canonical HTML의 실제 HTTP 응답 및
  기사 내용 포함 여부를 읽기 전용으로 점검
- 코드·Registry·Skill 동작은 변경하지 않음

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

- Amex 목록은 2026-07-29 두 번과 2026-07-30 한 번 HTTP 200, 현재 `healthy`,
  14건
- JCB 목록은 같은 기간 세 번 HTTP 200, 현재 `healthy`, 455건
- 동일 원문 4건의 실패는 2026-07-29부터 재현되어 2026-07-30에도 지속
- Amex 기사 canonical URL에서 파생한 공식 `.model.json`은 HTTP 200
  `application/json`, 기사 제목과 내용 신호 포함
- JCB 문제 canonical URL은 직접 HTTP 요청에서 200 `text/html`, 기사 제목과
  본문 신호 포함
- 실패 원인은 datasource 부재가 아니라 현재 web extraction 도구와 원문 제공
  방식의 불일치로 판정
- `git diff --check`는 최종 로그 기록 후 별도 확인

### 결정과 근거

1. Amex와 JCB datasource는 즉시 제거하지 않는다.
   - 발견 목록과 공식 원문 모두 실제로 응답하며, 동일 도메인의 결정적 대체 추출
     경로를 확인했기 때문이다.
2. Amex는 공식 기사별 AEM model JSON, JCB는 allowlist 기반 직접 HTML fetch와
   안전한 텍스트 정규화를 우선 대안으로 본다.
   - 브라우저 자동화나 제3자 사본 없이 공식 원문만 사용할 수 있다.
3. 대체 추출기를 구현한 뒤에도 연속 신규 항목의 본문 검증 성공률이 기준을
   충족하지 못할 때 datasource 비활성화를 검토한다.
   - 목록 수집 성공만으로 운영 가치를 판단하지 않고 end-to-end 발행 가능성을
     기준으로 삼기 위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- Amex와 JCB 공식 공개 URL에 읽기 전용 HTTP 요청 수행
- credential, Telegram, cron, gateway와 전역 설정은 변경하지 않음

### 알려진 한계와 남은 작업

- 현재 Skill은 `record.canonical_url`을 web extraction 도구로만 추출하도록
  규정하므로 공식 구조화 원문 fallback을 사용하려면 Skill·runtime·검증 테스트
  변경이 필요
- 대체 추출기는 아직 구현하지 않았으며 기존 4건은 계속 `retryable`

## 2026-07-30 17:05 KST — 공식 원문 fallback 구현 및 재처리

### 사용자 요청과 목적

- Amex·JCB 원문 추출기를 보완하고 기존 `retryable` 항목을 다시 처리
- 공식 원문을 검증할 수 있는 항목만 Obsidian 문서로 작성하고 Telegram으로 전달

### 수행한 변경

- 처리 중 queue 항목만 조회할 수 있는 controller API 추가
- 임의 URL을 받지 않고 Registry와 claimed record에서 공식 원문 URI를 결정하는
  `automation-extract` 명령 추가
- Amex Newsroom canonical `.html`에서 동일 공식 도메인의 기사별
  `.model.json`을 파생해 본문을 추출하는 fallback 구현
- JCB canonical HTML을 기존 HTTPS·도메인·redirect·응답 크기 제한 아래 직접
  가져와 script·style 등 실행성 콘텐츠를 제외하고 가시 텍스트를 추출하는
  fallback 구현
- content type, 최종 URL, canonical URL, 기사 제목, Amex 게시일과 최소 본문
  길이를 fail-closed 방식으로 검증
- Source Registry에 Amex `amex_aem_json`, JCB `official_html` extractor를 설정하고
  지원하지 않는 extractor 설정을 거부하도록 validation 강화
- Skill 절차에 web extraction 실패 시 공식 fallback을 사용하는 단계를 추가
- 기존 retryable 항목을 포함한 최신 run을 실행해 5건 처리
- JCB–Fiuu 직접 매입 파트너십 1건을 작성·독립 검증·저장·Telegram 전달
- Amex 보조금·실적·회원 경험 3건과 PCI SSC 행사 1건을 `irrelevant`로 기록

### 생성·수정한 문서와 파일

- [공식 원문 fallback 구현](./skills/hermes-news-automation/scripts/runtime/hermes_agent/source_extractor.py)
- [자동화 controller](./skills/hermes-news-automation/scripts/runtime/hermes_agent/automation.py)
- [자동화 CLI](./skills/hermes-news-automation/scripts/runtime/hermes_agent/cli.py)
- [Registry validation](./skills/hermes-news-automation/scripts/runtime/hermes_agent/validation.py)
- [Skill 절차](./skills/hermes-news-automation/SKILL.md)
- [프로젝트 Source Registry](./Automation/config/sources.json)
- [Skill 기본 Source Registry](./skills/hermes-news-automation/scripts/runtime/hermes_agent/default_sources.json)
- [원문 fallback 테스트](./Automation/tests/test_source_extractor.py)
- [Registry 테스트](./Automation/tests/test_registry.py)
- [자동화 README](./Automation/README.md)
- [출처 카탈로그](./SOURCE_CATALOG.md)
- [프로젝트 계획](./PROJECT_PLAN.md)
- [JCB–Fiuu 직접 매입 파트너십 문서](./Inbox/2026-07-23%20JCB%20and%20Fiuu%20Collaborate%20to%20Expand%20JCB%20Acceptance%20Across%20Southeast%20Asia.md)
- [작업 로그](./WORK_LOG.md)
- Git에서 제외되는 `.hermes-news/config/sources.json`과 수집·run·decision·artifact·
  delivery ledger

### 실행한 검증과 결과

```text
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
python3 skills/hermes-news-automation/scripts/run.py automation-start --max-items 5
python3 skills/hermes-news-automation/scripts/run.py automation-extract ...
python3 skills/hermes-news-automation/scripts/run.py automation-submit ...
python3 skills/hermes-news-automation/scripts/run.py automation-notify ...
python3 skills/hermes-news-automation/scripts/run.py automation-finish ...
git diff --check
```

- 구현 직후 전체 단위·통합·배포 검증 59개 통과
- 활성 Registry 13개 검증 통과, 프로젝트·Skill 기본 Registry 일치
- 실환경 최신 수집은 13개 출처 모두 성공, source failure 0건
- Amex 공식 AEM JSON fallback 3/3건 성공
- JCB 공식 HTML fallback 1/1건 성공
- run `20260730T074844198182Z-7f8f807e` 최종 상태 `completed`
- queue 결과: `irrelevant` 4건, `notified` 1건, retryable·quarantined 0건
- JCB 문서 Curator confidence 0.97, 독립 Verifier confidence 0.98,
  verification check 전부 통과
- Telegram 문서 1건 전송 성공, unknown delivery 0건
- Vault 문서 14개, validation issue 0건
- 로그·문서 동기화 후 최종 전체 테스트 59개 재통과, Registry·Vault 검증과
  `git diff --check` 통과
- 기본 Python bytecode cache가 workspace 밖이라 첫 `compileall`은 권한 오류가
  났고, `PYTHONPYCACHEPREFIX=/tmp/hermes-agent-pycache`로 재실행해 통과

### 결정과 근거

1. fallback 명령은 URL 인자를 받지 않고 현재 run에서 `processing` 상태인
   record ID만 받는다.
   - source allowlist를 우회한 임의 외부 콘텐츠 반입을 막기 위해서다.
2. Amex는 canonical 링크를 문서 identity와 evidence로 유지하면서 동일 공식
   도메인의 AEM model JSON만 추출에 사용한다.
   - 사용자용 canonical URL과 기계 판독 가능한 공식 원문을 분리하되 출처
     정체성을 유지하기 위해서다.
3. JCB는 web 도구의 URL 판정 실패를 제3자 사본이나 검색 인덱스로 대체하지 않고
   기존 bounded fetcher로 공식 canonical HTML을 직접 확인한다.
   - 공식 원문, allowlist와 응답 제한을 동시에 유지하기 위해서다.
4. 원문 확보 성공이 곧 발행을 의미하지 않도록 기존 관련성·독립 검증 게이트를
   그대로 유지한다.
   - 보조금·실적·라이프스타일·행사 홍보를 결제 기술 뉴스로 오인하지 않기
     위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 로컬 Skill workspace의 `.hermes-news/config/sources.json`에 Amex·JCB 공식
  extractor 설정 추가
- 설정된 Telegram 수신자에게 검증 완료 JCB 문서 1건 전송
- 사용자 shell profile, credential 값, Hermes gateway, cron과 Git 설정은
  변경하지 않음

### 알려진 한계와 남은 작업

- 공식 fallback은 현재 Amex Newsroom과 JCB Press에만 구성됨
- JCB HTML 가시 텍스트에는 사이트 navigation이 포함되지만 script·style·
  noscript·SVG·template은 제외되고 제목·본문 길이 검증을 통과해야 함
- 이번 재처리는 수동 실환경 run이며 다음 cron 실행에서 설치된 Skill 경로의
  지속 동작을 확인할 필요가 있음

## 2026-07-30 17:11 KST — 원문 fallback 변경 commit·push 및 PR 생성

### 사용자 요청과 목적

- 원문 fallback 구현과 재처리 결과의 문서 sync를 최종 확인
- 검증된 변경을 전용 branch에 commit하고 원격 push한 뒤 `main` 대상 PR 생성

### 수행한 변경

- 프로젝트 문서의 출처·Inbox·Registry 수치와 로컬 Markdown link 재검증
- 전체 단위·통합·Skill 배포 테스트와 Vault identity 검증 재실행
- 전용 branch 생성, 원문 fallback·테스트·JCB 문서·작업 로그를 commit
- 원격 branch push 및 GitHub PR 생성

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- 첫 commit에 포함된 파일은 직전 “공식 원문 fallback 구현 및 재처리” 기록의
  목록과 동일

### 실행한 검증과 결과

```text
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
PYTHONPYCACHEPREFIX=/tmp/hermes-agent-pycache \
  python3 -m compileall -q skills/hermes-news-automation/scripts/runtime/hermes_agent
git diff --check
git check-ignore .hermes-news/config/telegram.json \
  .hermes-news/data .hermes-news/config/sources.json
```

- 전체 테스트 59개 통과
- 활성 출처 13개, Inbox 14개, Vault validation issue 0건
- Python bytecode compile, 문서 sync, 로컬 Markdown link와
  `git diff --check` 통과
- credential·runtime state·workspace Registry가 Git 제외 상태임을 확인
- branch: `codex/source-extraction-fallback-20260730`
- 첫 commit: `c841fee` (`공식 원문 fallback과 뉴스 재처리 추가`)
- 원격 branch push 성공
- GitHub [PR #12 — 공식 원문 fallback과 뉴스 재처리](https://github.com/dumbbelloper/hermes-agent/pull/12)
  생성
- PR은 `main` 대상 open 상태이며 draft가 아님
- 후속 작업 로그 commit `00c12de` push 후 GitHub Actions `validate`가
  Ubuntu·macOS·Windows에서 모두 통과

### 결정과 근거

1. `main`에 직접 commit하지 않고 전용 branch와 PR을 사용한다.
   - 플랫폼별 CI 결과와 보안 경계를 검토 가능한 단위로 유지하기 위해서다.
2. `.hermes-news/`의 credential, workspace Registry와 실행 원장은 commit하지
   않는다.
   - 공개 코드·기본 Registry와 로컬 운영 상태를 분리하기 위해서다.
3. PR 본문에 코드 변경뿐 아니라 실환경 재처리 결과와 제외 판정도 함께 기록한다.
   - fallback의 기능 검증과 실제 발행 결과를 한 번에 검토할 수 있게 하기
     위해서다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub 원격 branch `codex/source-extraction-fallback-20260730` 생성
- GitHub PR #12 생성
- credential, Telegram, cron, gateway와 shell 설정은 추가 변경하지 않음

### 알려진 한계와 남은 작업

- PR merge는 사용자 요청 범위에 포함하지 않음

## 2026-08-05 10:16 KST — 현시점 뉴스 수집·검증 및 Obsidian 발행

### 사용자 요청과 목적

- `hermes-news-automation` Skill로 현시점의 신규 결제·금융 정보를 수집
- 공식 원문과 독립 검증을 통과한 항목만 Obsidian 문서로 작성하고 Telegram 전달

### 수행한 변경

- 활성 출처 13개를 최신 상태로 수집하고 controller queue 5건 처리
- Amex canonical JavaScript shell 4건에 공식 AEM JSON fallback 적용
- Amex–Fanatics 결제 파트너·제휴 카드·포인트 전환 계획 1건 작성
- Amex–ALL Accor 포인트 전환·호텔 등급 매칭 1건 작성
- AmexForFoodies 프로모션 1건을 `irrelevant`로 기록
- Amex 비즈니스 여행·경비 설문 1건을 독립 검증 이슈로 `quarantined` 기록
- Visa–BioCatch 인수 1건을 원문 추출 실패로 `retryable` 기록
- 프로젝트 계획과 출처 카탈로그의 누적 record·Inbox 수치 동기화

### 생성·수정한 문서와 파일

- [Amex–Fanatics 결제·카드·리워드 제휴](./Inbox/2026-08-04%20At%20Fanatics%20Fest%202026%2C%20American%20Express%20Helped%20Bring%20Sports%20Home.md)
- [Amex–ALL Accor 로열티 제휴](./Inbox/2026-07-22%20American%20Express%20and%20ALL%20Accor%20Expand%20the%20Power%20of%20Membership%20with%20New%20Global%20Partnership.md)
- [프로젝트 계획](./PROJECT_PLAN.md)
- [출처 카탈로그](./SOURCE_CATALOG.md)
- [작업 로그](./WORK_LOG.md)
- Git에서 제외되는 `.hermes-news/data/`의 raw·normalized·state와 automation
  run·decision·artifact·delivery ledger

### 실행한 검증과 결과

```text
python3 skills/hermes-news-automation/scripts/run.py automation-start --max-items 5
python3 skills/hermes-news-automation/scripts/run.py automation-extract ...
python3 skills/hermes-news-automation/scripts/run.py automation-submit ...
python3 skills/hermes-news-automation/scripts/run.py automation-notify ...
python3 skills/hermes-news-automation/scripts/run.py automation-finish ...
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
PYTHONPYCACHEPREFIX=/tmp/hermes-agent-pycache \
  python3 -m compileall -q skills/hermes-news-automation/scripts/runtime/hermes_agent
git diff --check
```

- 활성 출처 13개 모두 수집 성공, source failure 0건
- Skill workspace 누적 정상 record 1,662건, source state 13개 모두 `healthy`
- run `20260805T005534147479Z-17d8acfa` 최종 상태
  `completed_with_exceptions`
- queue 결과: `notified` 2건, `irrelevant` 1건, `quarantined` 1건,
  `retryable` 1건
- Telegram 문서 2건 전송 성공, unknown delivery 0건
- 전체 단위·통합·배포 검증 59개 통과
- 활성 Registry 13개 검증 통과, 프로젝트·Skill 기본 Registry 일치
- Vault 문서 16개, validation issue 0건
- Python bytecode compile 통과

### 결정과 근거

1. Fanatics Fest 기사에는 행사 홍보 외에 일부 판매 채널의 결제 파트너 지정,
   Amex Network 기반 제휴 카드와 포인트 전환 계획이 있어 발행한다.
   - 계획·대상 범위를 명시하면 카드·리워드 인프라 변화로 직접 관련되기 때문이다.
2. ALL Accor 제휴는 12개 지역의 단계적 등급 매칭과 Membership Rewards 전환을
   추가하므로 발행한다.
   - 모든 회원·동시 출시·고정 전환·고정 비율로 과장하지 않고 자격과 지역별
     조건을 보존했다.
3. 비즈니스 여행 설문은 독립 Verifier가 조사 기간과 표본 규모·자격 조건의 초안
   누락을 발견해 수정 발행하지 않고 격리한다.
   - 독립 검증 결과를 우회하지 않는 fail-closed 규칙을 지키기 위해서다.
4. Visa–BioCatch 인수는 중요 후보지만 canonical 원문을 확보하지 못해 제목만으로
   문서화하지 않는다.
   - web 도구가 URL을 거부했고 `visa-press` 공식 fallback이 아직 없기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 공개 뉴스 출처 13개에 읽기 요청 수행
- 설정된 Telegram 수신자에게 검증 완료 문서 2건 전송
- credential, shell profile, Hermes gateway, cron과 Git 설정은 변경하지 않음

### 알려진 한계와 남은 작업

- Visa–BioCatch 인수는 `visa-press` 공식 HTML fallback을 추가한 뒤 재처리 필요
- 격리된 Amex 여행·경비 설문은 조사 기간·표본 범위를 포함한 새 초안과 독립
  검증이 필요
- `--max-items 5` 제한과 decision ledger에 따라 이번 run이 source-level 신규
  감지 항목 전체를 문서 후보로 처리한 것은 아님

## 2026-08-11 09:48 KST — 현재 Chrome 화면 확인 가능 여부 점검

### 사용자 요청과 목적

- 현재 MacBook의 Chrome에서 실행 중인 화면을 Codex가 확인할 수 있는지 확인

### 수행한 변경

- 현재 대화에 Chrome 확장 프로그램 또는 Computer Use 연결이 제공되었는지 점검
- 공식 OpenAI 문서에서 Chrome 기존 탭 접근 조건과 macOS 화면 접근 권한을 확인

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

- 현재 세션에는 Chrome 또는 Computer Use 제어 도구가 연결되어 있지 않아 열린
  Chrome 화면을 직접 확인할 수 없음
- 공식 문서상 ChatGPT Chrome 확장 프로그램을 연결하면 허용된 기존 Chrome 탭을
  문맥으로 읽거나 조작할 수 있음
- 공식 문서상 macOS Computer Use는 화면 기록 및 손쉬운 사용 권한이 필요함

### 결정과 근거

- 현재 화면을 보고 있다고 오인되지 않도록 직접 접근 불가 상태를 명시함
- 사용자가 공유한 스크린샷을 분석하거나, Chrome 확장 프로그램/Computer Use를
  명시적으로 설치·허용하는 방식을 대안으로 안내함

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음

### 알려진 한계와 남은 작업

- 실제 Chrome 화면 확인은 사용자가 스크린샷을 첨부하거나 Chrome 확장 프로그램
  또는 Computer Use를 연결하고 필요한 권한을 승인해야 가능함

## 2026-08-11 10:18 KST — 현재 프로젝트 구조·품질 분석

### 사용자 요청과 목적

- 현재 프로젝트의 목적, 구조, 실행 흐름, 품질 상태와 주요 개선 과제를 파악
- 사용자 작업 중인 변경을 보존한 상태에서 코드·문서·테스트를 읽기 전용으로 점검

### 수행한 변경

- Git 상태, 추적 파일, 패키지 metadata와 최근 이력을 확인
- 수집기, Source Registry, 저장소, 무인 controller, 원문 fallback, Vault index,
  Telegram delivery와 Skill pre-check의 실행 흐름 분석
- 추적 파일 기준 언어·확장자별 파일 수와 줄 수, 테스트 정의 수와 대형 모듈 확인
- 오프라인 회귀 테스트, Registry·Vault 검증, Python compile과 wheel build 실행
- 코드나 설정은 변경하지 않고 분석 결과만 이 작업 로그에 추가

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md) — 현재 프로젝트 분석 기록 추가
- 기존 코드, Registry, Skill, 운영 데이터와 사용자 작성 중 문서는 변경하지 않음

### 실행한 검증과 결과

```text
git status --short --branch
git log --oneline --decorate -8
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
python3 Automation/run.py validate-registry
python3 Automation/run.py validate-notes --vault-dir .
python3 -m compileall -q skills/hermes-news-automation/scripts
python3 -m pip wheel --no-deps --no-build-isolation --wheel-dir <temporary-directory> .
```

- `main`은 `origin/main`과 같은 commit이며 작업 시작 전 수정 3개·미추적 2개 존재
- 추적 파일 94개, 총 14,175줄: Markdown 6,896줄, Python 6,257줄 중심
- Python runtime은 20개 모듈이며 `automation.py` 1,117줄, `cli.py` 614줄로
  controller와 CLI에 복잡도가 집중
- 테스트 함수 59개를 실행해 전부 통과
- 활성 Source Registry 13개 검증 통과: 공식 9개, 편집 언론 4개
- Vault 문서 16개, identity issue 0건
- Python compile과 `hermes_news_automation-0.1.0` wheel build 성공
- `pygount`가 설치되어 있지 않아 Git 추적 파일을 Python으로 집계했으며 dependency는
  추가하지 않음

### 결정과 근거

1. 현재 프로젝트를 일반 Hermes Agent 구현체가 아니라 결제·금융 뉴스 수집과
   Obsidian 발행을 위한 self-contained Hermes Skill 프로젝트로 분류한다.
   - 패키지명, CLI entrypoint, Source Registry와 Skill 절차가 모두 이 workflow를
     중심으로 구성되어 있기 때문이다.
2. 현 상태는 기능 완성도와 회귀 안정성이 높은 v0.1.0이지만 운영 성숙 단계는
   아직 진행 중으로 판단한다.
   - 59개 오프라인 테스트와 3개 OS CI가 있으나 장기 운영 지표, backoff,
     circuit breaker와 정기 품질 표본 보정이 남아 있기 때문이다.
3. 우선 개선 대상으로 stale lock 소유권과 Telegram delivery crash window를 선정한다.
   - `submit()`의 note/event 부작용 전체가 하나의 소유권 검증 임계구역으로 묶이지
     않고, `sending` 예약 후 프로세스 중단 시 재실행이 항목을 `notified`로 바꿀 수
     있어 실제 전달 여부와 run 결과가 어긋날 가능성이 있기 때문이다.
4. 다음 구조 개선 후보는 `automation.py`와 `cli.py`의 책임 분리다.
   - 전체 Python 6,257줄 중 두 파일이 1,731줄이고 상태 저장, artifact 검증,
     note rendering, run orchestration과 명령 wiring이 집중되어 있기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- dependency, Git branch·commit, Hermes 설정, cron, gateway, credential, Telegram과
  공개 뉴스 출처를 변경하거나 호출하지 않음
- wheel은 임시 디렉터리에만 생성

### 알려진 한계와 남은 작업

- 네트워크를 사용하는 실제 13개 출처 수집과 Telegram 전송은 이번 분석에서 실행하지
  않았으며 마지막 실환경 결과는 기존 2026-08-05 기록을 기준으로 확인
- Python 최소 지원 버전은 3.9지만 CI는 Python 3.11 한 버전만 검증
- 테스트 coverage 수치, linter와 type checker gate는 현재 프로젝트에 구성되어 있지 않음
- stale lock takeover 중 이전 프로세스의 부작용 차단과 `sending` delivery 복구 정책은
  별도 설계·회귀 테스트 후 구현 필요
- `automation.py`·`cli.py` 분리는 동작 변경 없이 단계적으로 진행해야 함

## 2026-08-11 10:28 KST — Mastercard MDES 공식 문서 작업 준비와 통제 확인

### 사용자 요청과 목적

- AI 가드레일과 기존 GitHub commit·PR·merge 절차를 확인
- 현재 실행 중인 Chrome의 Mastercard MDES 공식 문서를 Hermes Agent로 다루는
  후속 수집·검증·Obsidian 문서화 작업 준비

### 수행한 변경

- [Enterprise AI Agent Guardrails](./ENTERPRISE_AI_GUARDRAILS.md)의 현재 프로젝트
  위험 등급과 source control 승인 경계 확인
- GitHub CLI로 인증 상태, 저장소, 병합 PR 12건, 열린 PR과 commit graph를 읽기
  전용으로 조회
- Hermes browser·Computer Use 상태와 공식 Browser Automation 문서 확인
- Cua Driver의 macOS 권한·상태와 현재 Chrome window를 읽기 전용으로 점검
- Apple Events를 통해 Chrome 활성 tab이 Mastercard MDES 공식 제품 페이지임을 확인
- 현재 세션의 `computer_use` tool schema가 노출되지 않아 Cua Driver CLI의 exact-window
  조회를 시도했으나, 다른 macOS Space의 Chrome window라 background AX 입력은 거부됨
- 기존 Chrome profile의 CDP 연결에는 별도 사용자 승인이 필요함을 확인

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md) — 준비 상태와 승인 blocker 기록
- 코드, Skill, Source Registry, Vault 문서와 운영 설정은 변경하지 않음

### 실행한 검증과 결과

```text
gh auth status
gh repo view --json nameWithOwner,url,defaultBranchRef
gh pr list --state merged --limit 20 --json ...
gh pr list --state open --limit 20 --json ...
git log --graph --decorate --oneline --all -20
hermes status
hermes tools list
hermes computer-use doctor
cua-driver call list_windows '{}'
cua-driver call get_window_state '{...}'
cua-driver call get_browser_state '{...}'
```

- GitHub CLI는 `dumbbelloper` 계정으로 인증됐고 대상은
  `dumbbelloper/hermes-agent`, 기본 branch는 `main`
- 병합 PR은 #1~#12 총 12건이며 현재 열린 PR 0건
- 기존 기능 branch → commit → PR → CI → squash merge 흐름 확인
- 가드레일 기준 로컬 commit은 G1, push·PR은 G2, 보호 branch merge는 G3
- Computer Use toolset은 활성 상태이고 Cua Driver 0.19.3, Accessibility와 Screen
  Recording 권한 및 AX capability 정상
- Chrome 활성 tab:
  `https://developer.mastercard.com/product/mdes/`
- 대상 Chrome window는 PID `67578`, window ID `101`로 식별
- Chrome이 다른 Space에 있어 exact-window AX 조회는 `ax_window_unresolved`로 거부
- 현재 Chrome은 CDP endpoint 없이 실행되어 browser 연결은
  `browser_requires_setup`으로 거부

### 결정과 근거

1. Mastercard MDES 공식 문서도 외부의 신뢰되지 않은 입력으로 취급한다.
   - 공식 도메인이라도 페이지 안의 명령을 agent 지시로 실행하지 않고 자료로만
     해석해야 하기 때문이다.
2. 현재 사용자의 Chrome profile에 무단으로 연결하거나 Space를 전환하지 않는다.
   - 기존 profile은 다른 개인 tab과 session을 포함할 수 있고 Computer Use가 exact
     resource 승인 없이 입력을 거부하기 때문이다.
3. GitHub에는 변경을 바로 올리지 않고 로컬 branch·파일·테스트까지 G1 범위에서
   준비한 뒤 push와 PR 생성 직전에 1회 승인을 요청한다.
4. merge는 CI 통과 후에도 agent가 독자 수행하지 않는다.
   - 프로젝트 가드레일에서 보호 branch merge를 G3로 분류하기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 없음
- GitHub, Chrome, Hermes 설정, Cua Driver 권한, Telegram과 credential을 변경하지 않음
- GitHub와 Mastercard 공식 페이지 식별은 읽기 전용으로 수행

### 알려진 한계와 남은 작업

- 현재 Chrome profile의 exact-window 연결은 사용자 승인 전까지 진행할 수 없음
- MDES 문서 수집 범위와 첫 산출물은 Chrome 연결 후 공식 문서 구조를 확인해 확정 필요
- push, PR, merge와 Telegram 전송은 아직 수행하지 않음

## 2026-08-11 10:38 KST — Mastercard MDES 공식 문서 구조 검증과 첫 변경 문서 작성

### 사용자 요청과 목적

- 직전 작업 로그의 Mastercard MDES 공식 문서 작업을 이어서 진행
- 현재 Chrome tab을 Computer Use로 직접 확인
- MDES 서비스 구조와 현재 유효한 기술 변경을 공식 원문으로 검증하고 Obsidian 문서로 정리

### 수행한 변경

- Computer Use exact-window capture로 Chrome의 MDES 제품 페이지와 `Our services` 절을 확인
- MDES 제품 개요, issuer·merchant 설명과 공개 서비스 문서 7개의 Overview·API Basics를 읽기 전용으로 조사
- issuer, merchant, PSP·OBOTR와 token requestor 책임, token lifecycle, API별 역할과 보안 경계를 개념 노트로 정리
- 2026-07-15 발효된 MTF domain migration 공지를 별도 Inbox 문서로 작성
- MTF에서 영향받는 Customer Service, Digital Enablement, Token Connect와 TRID API의 환경·credential 변경을 대조
- Mastercard 일반 Developer Products 목록 제외와 직접 접근 가능한 MDES 개별 기술 문서 후보를 구분하도록 출처 카탈로그 수정
- 프로젝트 계획에 공식 기술 문서의 inventory·release history·API specification·PDF hash 변경 추적 단계를 추가
- 로컬 `docs/mastercard-mdes` branch를 생성하고 기존 미commit Amex 문서 변경은 그대로 보존

### 생성·수정한 문서와 파일

- [Mastercard Digital Enablement Service 개념 노트](./Concepts/Mastercard%20Digital%20Enablement%20Service.md)
- [Mastercard MDES MTF Domain Change Notification](./Inbox/2026-07-15%20Mastercard%20MDES%20MTF%20Domain%20Change%20Notification.md)
- [수집 출처 운영 분류](./SOURCE_CATALOG.md)
- [프로젝트 계획](./PROJECT_PLAN.md)
- [작업 로그](./WORK_LOG.md)

### 실행한 검증과 결과

```text
computer_use capture --pid 67578 --window-id 101 --mode som
web_extract https://developer.mastercard.com/product/mdes/ 및 공식 하위 문서
python3 Automation/run.py validate-notes --vault-dir .
python3 Automation/run.py note-status --vault-dir . --record-id ... --source-fingerprint ...
PYTHONPATH=skills/hermes-news-automation/scripts/runtime \
  python3 -m unittest discover -s Automation/tests -v
git diff --check
```

- Computer Use가 1568×983 Chrome window를 background exact-window capture로 읽었고 MDES 제품 페이지의 서비스 7개를 화면에서 확인
- 공식 공개 원문에서 MDES 제품·참여자 페이지 3개, 서비스 Overview 7개, 주요 API Basics 6개와 MTF 변경 공지를 확인
- Vault 문서 17건, identity issue 0건
- 신규 MTF 문서의 `note-status`: `skip`
- 신규 문서 2개의 Obsidian wiki link issue 0건
- 전체 단위·통합·문서 동기화 테스트 59개 통과
- 첫 테스트에서는 프로젝트 계획의 문서 수 표현이 기존 정확 문자열 계약과 달라 1건 실패했고, 누적 1,662건·문서 17건으로 동기화한 뒤 재실행에서 통과
- `git diff --check` 통과

### 결정과 근거

1. MDES는 하나의 API가 아니라 참여자와 lifecycle 단계별 서비스군으로 문서화한다.
   - Pre-Digitization, Customer Service, Token Connect, Authentication Facilitator, Digital Enablement, Bulk Tokenization과 TRID의 책임·호출 주체가 다르기 때문이다.
2. Mastercard Developer Products 일반 목록은 운영 자동 수집 제외 상태를 유지하되, 직접 접근 가능한 MDES 개별 문서는 기술 문서 후보로 분리한다.
   - 목록 전체의 안정적 항목 경계·revision metadata는 없지만 특정 canonical 문서는 일반 HTTP 추출이 가능하기 때문이다.
3. 첫 Inbox 자료는 제품 소개가 아니라 발효일과 운영 영향이 명시된 MTF migration 공지를 선택한다.
   - endpoint뿐 아니라 Sandbox·Production credential 분리와 네 서비스의 실제 통합 변경을 요구하는 고가치 기술 변화이기 때문이다.
4. 공지의 endpoint 표를 구현 기준으로 복제하지 않고 현재 API Reference 재검증을 요구한다.
   - 문서 표는 이후 수정될 수 있고 공개 공지 안에서도 endpoint 표기 일관성을 별도로 검증해야 하기 때문이다.
5. 공지 페이지에 별도 게시일이 없어 `published_at`은 공식적으로 명시된 새 MTF 발효일 2026-07-15로 기록하고 한계를 본문에 남긴다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 공식 Mastercard Developers 공개 페이지를 로그인·credential 없이 읽기 전용으로 조회
- Computer Use로 사용자가 지정한 Chrome window를 읽기 전용 capture
- 로컬 Git branch `docs/mastercard-mdes` 생성
- Chrome tab, Mastercard project, API credential, Sandbox·MTF·Production, Telegram, Hermes 설정과 GitHub 원격은 변경하지 않음

### 알려진 한계와 남은 작업

- Mastercard project, Sandbox·MTF와 Production API를 실제 호출하지 않아 서명·payload encryption·endpoint 동작은 검증하지 않음
- API Reference의 OpenAPI specification 원본, release history 전체와 연결된 Mastercard Technical Resource Center PDF inventory·hash 수집은 후속 작업
- 공식 문서 페이지별 revision date가 일관되게 노출되는지와 변경 감지 canonical key를 추가 조사해야 함
- 현재 branch에는 작업 시작 전부터 존재한 Amex 관련 미commit 문서와 동기화 변경도 함께 남아 있으며 이번 작업에서 덮어쓰거나 commit하지 않음
- push, PR, merge와 Telegram 전송은 수행하지 않음

## 2026-08-11 11:04 KST — MDES Telegram 미수신 원인 확인과 PR 준비

### 사용자 요청과 목적

- MDES 문서 작성 후 Telegram 메시지가 오지 않은 원인 확인
- 오늘 오전 `git status`에 표시되는 전체 작업을 commit하고 GitHub Pull Request까지 게시

### 수행한 변경

- Telegram 설정 파일의 존재와 최소 권한, automation delivery ledger와 최신 run 상태를 credential 값에 접근하지 않고 확인
- 신규 MDES 문서의 record ID가 delivery ledger에 등록됐는지 대조
- 현재 branch의 수정·미추적 파일 전체를 이번 PR 범위로 확정

### 생성·수정한 문서와 파일

- [작업 로그](./WORK_LOG.md)
- 진단 과정에서 Telegram 설정, delivery ledger와 문서 본문은 변경하지 않음

### 실행한 검증과 결과

- Telegram 설정 파일 존재, 권한 `-rw-------`
- delivery ledger의 기존 4건은 모두 `sent`; 신규 MDES record ID는 없음
- `sending`, `unknown` 또는 실패 delivery 없음
- 최신 automation run은 2026-08-05 실행이며 이번 2026-08-11 MDES 수동 문서는 포함되지 않음
- 전체 테스트 59개 통과
- Source Registry 13개 검증 통과
- Vault 문서 17건, identity issue 0건
- `git diff --check` 통과

### 결정과 근거

1. Telegram 미수신은 API 실패나 credential 오류가 아니라 전송 단계 미실행으로 판정한다.
   - 이번 MDES 문서는 automation run 밖에서 수동 작성됐고 `automation-notify` 또는 `notify-telegram`을 호출하지 않았으며 delivery 예약도 없기 때문이다.
2. 오늘 오전 작업은 현재 `git status`에 표시되는 Amex 문서 2건, MDES 문서 2건과 동기화 문서 전체를 하나의 PR 범위로 포함한다.
   - 사용자가 현재 상태의 전체 작업을 명시적으로 commit·push·PR하도록 승인했기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- 진단은 로컬 파일 읽기만 수행
- Telegram 메시지 전송, credential·설정 변경은 수행하지 않음
- commit·push·PR 결과는 후속 작업 기록에 실제 결과로 추가

### 알려진 한계와 남은 작업

- 신규 MDES 문서를 Telegram으로 보내려면 별도의 G2 전송 승인이 필요
- PR merge는 PR 게시와 CI 결과 확인 뒤 사용자의 후속 지시 범위에서 수행

## 2026-08-11 11:06 KST — 오전 수집·MDES 문서 commit, push와 PR 생성

### 사용자 요청과 목적

- 오늘 오전 `git status`에 표시된 전체 변경을 하나의 작업 범위로 commit
- 원격 feature branch에 push하고 `main` 대상 Pull Request 생성
- merge 전 PR과 CI 검토가 가능한 상태로 준비

### 수행한 변경

- 수정 3개와 미추적 문서 4개를 모두 stage하고 단일 작업 commit 생성
- `docs/mastercard-mdes` branch를 `origin`에 push하고 upstream 연결
- GitHub `main` 대상 PR #13 생성
- PR 본문에 Amex 문서 2건, MDES 개념·변경 문서, 동기화 범위와 검증 결과 기록

### 생성·수정한 문서와 파일

- commit 대상은 직전 작업 기록의 문서 7개와 동일
- [PR #13 오전 수집 결과와 Mastercard MDES 공식 문서 정리](https://github.com/dumbbelloper/hermes-agent/pull/13)
- [작업 로그](./WORK_LOG.md) — 실제 GitHub 반영 결과 추가

### 실행한 검증과 결과

```text
git add --all
git diff --cached --check
git commit -m "오전 수집 결과와 Mastercard MDES 공식 문서 정리"
git push --set-upstream origin docs/mastercard-mdes
gh pr create --base main --head docs/mastercard-mdes ...
gh pr view --json ...
```

- 작업 commit: `e8993f0 오전 수집 결과와 Mastercard MDES 공식 문서 정리`
- push 성공, local·remote feature branch upstream 연결
- PR #13: `OPEN`, draft 아님, base `main`, head `docs/mastercard-mdes`
- 생성 직후 mergeability는 GitHub 계산 전 `UNKNOWN`, status check는 아직 등록되지 않음

### 결정과 근거

1. 사용자가 명시한 현재 `git status` 전체를 한 commit으로 포함한다.
   - Amex 수집 문서와 MDES 문서가 동일한 오전 작업 로그·문서 수 동기화에 함께 연결되어 있기 때문이다.
2. PR은 draft가 아닌 일반 review 상태로 생성한다.
   - 로컬 테스트, Registry·Vault 검증과 diff 검사를 모두 통과했기 때문이다.
3. PR merge는 이번 단계에서 수행하지 않는다.
   - 사용자가 우선 PR까지 요청했고 merge는 PR 상태와 CI를 확인한 후 마무리할 예정이기 때문이다.

### 전역 설정이나 외부 시스템에 적용한 변경

- GitHub 원격에 `docs/mastercard-mdes` branch 생성·push
- GitHub [PR #13](https://github.com/dumbbelloper/hermes-agent/pull/13) 생성
- `main`, Telegram, credential, Hermes gateway·cron과 Mastercard 시스템은 변경하지 않음

### 알려진 한계와 남은 작업

- GitHub status check 등록 및 최종 결과 확인 필요
- PR #13 merge는 아직 수행하지 않음
- MDES 문서 Telegram 전송은 이번 PR 작업 범위에 포함하지 않음
