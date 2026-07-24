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
