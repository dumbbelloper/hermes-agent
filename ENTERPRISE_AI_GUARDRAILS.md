# Enterprise AI Agent Guardrails

> 상태: Draft
>
> 기준일: 2026-07-28
>
> 적용 대상: Codex를 포함해 코드, 인프라, 데이터, 업무 시스템을 조작할 수 있는 모든 AI agent

## 1. 목적

AI agent가 회사와 팀의 실제 업무를 지원할 때 생산성을 확보하면서도 다음 위험을 통제한다.

- 승인되지 않은 코드 변경과 배포
- 운영 인프라와 데이터의 손상
- 고객, 결제, 재무 및 법적 영향
- 자격증명과 개인정보 유출
- 공급망 침해
- 잘못된 외부 커뮤니케이션
- 감사 불가능한 자동 실행
- 프롬프트 인젝션과 도구 오용

이 문서는 특정 AI 제품의 로컬 권한 설정만을 다루지 않는다. 조직 정책, 사람의 책임, ID와 권한, 개발 절차, CI/CD, 대상 시스템의 강제 통제, 감사 및 사고 대응을 함께 다룬다.

## 2. 기본 원칙

### 2.1 Agent를 신뢰 경계로 사용하지 않는다

Agent의 프롬프트, 로컬 설정, 명령 규칙은 우발적 실행을 줄이는 1차 안전장치다. 최종 강제력은 GitHub, CI/CD, 클라우드 IAM, Kubernetes RBAC, 데이터베이스 권한처럼 대상 시스템이 가져야 한다.

### 2.2 최소 기능, 최소 권한, 최소 자율성

- 필요한 tool과 connector만 제공한다.
- 읽기와 쓰기 권한을 분리한다.
- 개발, 검증, 운영 identity를 분리한다.
- 작업 단위의 단기 자격증명을 사용한다.
- 고영향 행위는 agent가 최종 결정하지 못하게 한다.

### 2.3 제안과 실행을 분리한다

Agent는 변경안, diff, plan, 영향 분석과 rollback 절차를 만들 수 있다. 공유 환경이나 production에 반영하는 결정은 별도의 승인 단계에서 수행한다.

### 2.4 동일 주체의 자기 승인을 금지한다

변경을 생성한 agent 또는 그 agent를 실행한 사용자가 고위험 변경의 유일한 승인자가 되어서는 안 된다. 위험도가 높을수록 독립된 사람 또는 담당 팀의 승인이 필요하다.

### 2.5 실패 시 닫힌 상태를 유지한다

정책 엔진, 승인 시스템, identity 확인, 로깅 또는 대상 식별에 실패하면 실행하지 않는다. 승인 시스템 장애를 자동 승인으로 처리하지 않는다.

### 2.6 대상과 영향 범위를 명시한다

승인은 단순히 명령 문자열을 허용하는 행위가 아니다. 최소한 다음 정보에 대한 승인이어야 한다.

- 실행할 action과 전체 인자
- 대상 조직, 계정, 저장소, 환경, cluster, namespace, database
- 변경 내용과 예상 영향
- 고객 및 데이터 영향
- 복구 또는 rollback 방법
- 변경 요청·티켓·PR 식별자
- 실행 identity와 승인자
- 승인 유효기간

## 3. 위험 등급

| 등급 | 의미 | 기본 처리 |
| --- | --- | --- |
| G0 | 읽기 전용이며 비민감 정보만 사용 | 자동 허용, 기본 로그 |
| G1 | 로컬·격리 환경의 가역적 변경 | 자동 허용, 변경 기록 |
| G2 | 팀 공유 자원 또는 외부 시스템의 가역적 변경 | 실행 직전 사용자 승인 |
| G3 | Production, 고객, 보안, 재무에 영향을 주는 변경 | 독립 승인 + 대상 시스템 gate |
| G4 | 비가역적·대량·규제 대상·권한 경계 변경 | 기본 거부, 예외 시 2인 승인과 break-glass |

### G0 — 읽기 및 분석

예시:

- 공개 문서 검색
- `git status`, `git diff`, 로그 조회
- 읽기 전용 API 호출
- 민감정보가 제거된 모니터링 조회
- 정적 분석과 테스트 결과 해석

### G1 — 로컬 또는 격리된 변경

예시:

- workspace 내부 파일 수정
- 로컬 테스트 실행
- 임시 branch 생성
- 격리된 개발 환경의 fixture 생성
- 배포되지 않는 문서 초안 작성

조건:

- production credential이 없어야 한다.
- 외부 사용자나 공유 시스템에 영향을 주지 않아야 한다.
- 변경을 diff 또는 version control로 복구할 수 있어야 한다.

### G2 — 공유 자원의 가역적 변경

예시:

- `git push`
- Pull Request 생성·수정
- 이슈 생성·상태 변경
- 내부 문서 수정
- 비운영 환경 배포
- 패키지 prerelease 게시
- 팀 채널 메시지 전송

요구사항:

- 실행 직전 사람에게 묻는다.
- 실제 대상과 diff를 보여준다.
- 승인 범위를 해당 action 1회로 제한한다.
- 실행 결과와 actor를 기록한다.

#### 제한된 무인 자동화의 standing authorization

반복형 G2 작업은 사람이 사전에 범위와 종료 조건을 명시한 standing authorization을 부여한 경우에만 실행 직전 승인을 생략할 수 있다. 다음 조건을 모두 만족해야 한다.

- 대상 repository, 고정 recipient, 허용 action과 branch prefix를 명시한다.
- `git push`와 PR 생성·수정까지만 허용하며 보호 branch merge, release, deploy와 credential 변경을 포함하지 않는다.
- 로컬 on/off switch와 최대 30일의 승인 만료 시각을 함께 적용한다.
- quota, identity, clean worktree, diff, test 또는 logging 검증 실패 시 닫힌 상태로 중단한다.
- task별 독립 worktree·branch·감사 로그를 사용하고 shared append log를 수정하지 않는다.
- 실행 결과를 PR과 고정 알림 채널에 남기며 승인자는 언제든 switch를 끌 수 있다.
- 30일마다 사람이 대상, 권한, 사용량과 실패 이력을 재검토하고 `on`으로 승인 기간을 갱신한다.

현재 이 프로젝트의 standing authorization은 `dumbbelloper/hermes-agent` 저장소의 `automation/*` branch push, PR 생성·수정, 그리고 기존 프로젝트 Telegram credential이 지정한 고정 recipient 알림으로 제한한다. 자동 merge는 허용하지 않는다.

### G3 — Production 또는 고객 영향

예시:

- 보호 branch merge
- production 배포와 rollback
- Terraform/OpenTofu apply
- Kubernetes production 변경
- 운영 데이터 migration
- 고객 계정 상태 변경
- feature flag의 전체 사용자 활성화
- 권한, 방화벽, 인증 정책 변경
- 정식 package·release 게시
- 대외 공지, 고객 안내, 법적 답변 전송

요구사항:

- 변경 생성자와 다른 승인자가 검토한다.
- PR, change ticket 또는 deployment request와 연결한다.
- 대상 시스템에서 approval gate를 강제한다.
- 테스트, 정책 검사, 보안 검사를 통과한다.
- rollback 또는 roll-forward 절차를 검증한다.
- 승인 후 변경된 artifact는 재승인을 받는다.

### G4 — 비가역적 또는 중대한 행위

예시:

- production database, bucket, cluster 또는 계정 삭제
- 대량 고객 데이터 변경·삭제·반출
- `git push --force` 또는 보호 tag 삭제
- 감사 로그, backup, 보안 경보 삭제
- IAM 관리자 권한 부여
- root credential 사용
- 암호화 key 삭제 또는 rotation 확정
- 실제 자금 이체, 환불, 정산, 가격·수수료 변경
- 보안 통제 비활성화
- 공개 저장소 전환 또는 기밀 repository 공개
- 개인정보·결제정보를 외부 AI나 connector로 전송

기본 정책:

- Agent에게 실행 기능 또는 credential을 제공하지 않는다.
- 필요한 경우 별도의 break-glass 절차를 사용한다.
- 2인 승인, 강한 인증, 제한 시간, 사유, 녹화·감사 로그를 요구한다.
- 실행 후 즉시 검증하고 사후 검토를 수행한다.

## 4. 인간 의사결정이 필요한 작업

### 4.1 Source control과 협업

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| status, diff, log, blame | G0 | 허용 |
| 로컬 branch와 commit | G1 | 허용하되 기록 |
| 모든 `git push` | G2 | 실행 직전 승인 또는 위 조건을 만족하는 제한된 standing authorization |
| PR 생성·수정·닫기 | G2 | 승인 또는 위 조건을 만족하는 제한된 standing authorization |
| 보호 branch merge | G3 | 독립 reviewer와 GitHub ruleset |
| force push, tag 삭제 | G4 | 기본 거부 |
| repository 삭제·이전·공개 전환 | G4 | 기본 거부 |
| branch protection·ruleset 변경 | G4 | 보안/관리자 승인 |

필수 시스템 통제:

- 기본 branch 직접 push 금지
- Pull Request 필수
- CODEOWNERS 또는 지정 팀 승인
- 마지막 변경자가 아닌 사람의 승인
- 새로운 commit이 추가되면 기존 승인 무효화
- required status checks
- force push와 branch 삭제 금지
- 관리자 우회 최소화 및 감사

### 4.2 CI/CD, release와 배포

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| build, lint, test, scan | G0~G1 | 허용 |
| 배포 plan과 manifest diff | G0~G1 | 허용 |
| 개발 환경 배포 | G1~G2 | 환경에 따라 승인 |
| staging 배포 | G2 | 승인 또는 정책 기반 자동화 |
| production 배포 | G3 | 독립 승인과 protected environment |
| rollback | G3 | 사고 지휘 체계에 따른 승인 |
| release 또는 package 게시 | G3 | 승인된 CI에서만 실행 |
| artifact, release, image 삭제 | G4 | 기본 거부 |

필수 시스템 통제:

- build artifact와 배포 artifact의 동일성 보장
- 승인 이후 artifact 변경 금지
- production environment required reviewer
- 배포 시작자의 자기 승인 금지
- environment별 credential 분리
- OIDC 기반 단기 credential
- third-party action을 검증된 commit SHA로 고정
- CI workflow 최소 권한
- provenance, signature, SBOM 보존
- canary, blue-green 또는 단계적 rollout
- 자동 health check와 중단 조건

### 4.3 Infrastructure as Code와 cloud

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| validate, fmt, plan | G0~G1 | 허용 |
| 개발 계정 apply | G2 | 승인 |
| production apply | G3 | 저장된 plan 독립 승인 |
| destroy, state 조작 | G4 | 기본 거부 |
| IAM·network·KMS 변경 | G3~G4 | 보안 담당 승인 |
| cloud account·project 삭제 | G4 | break-glass |

필수 시스템 통제:

- 개발과 production cloud account 분리
- production write credential을 개발자 workstation과 agent에 상시 저장하지 않음
- CI service identity별 최소 권한
- plan과 apply를 분리하고 동일 plan만 적용
- policy-as-code 검사
- 비용, 보안, 데이터 residency 정책 검사
- production 권한은 JIT·time-bound 방식으로 활성화
- destructive change와 replacement를 별도 표시

### 4.4 Kubernetes와 runtime

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| get, describe, logs | G0~G2 | 데이터 민감도에 따라 허용 |
| diff, dry-run | G1 | 허용 |
| dev namespace apply | G2 | 승인 |
| production apply·patch·scale | G3 | 배포 pipeline에서 승인 |
| delete·drain·cordon·rollback | G3~G4 | 운영 담당 승인 |
| cluster-admin, CRD, admission 변경 | G4 | 기본 거부 |

필수 시스템 통제:

- namespace 단위 최소 RBAC
- Agent에 `cluster-admin` 부여 금지
- production context를 로컬 기본 context로 사용하지 않음
- admission policy로 image registry, privilege, resource limit 강제
- GitOps를 통한 desired state 변경
- break-glass role 별도 관리

### 4.5 Database와 데이터

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| 비민감 read-only query | G0~G1 | 제한된 계정으로 허용 |
| 운영 데이터 조회 | G2 | 목적·범위에 따라 승인과 마스킹 |
| INSERT·UPDATE·DELETE | G3 | 검토된 job 또는 migration |
| schema migration | G3 | plan, backup, rollback 검토 |
| DROP·TRUNCATE·대량 수정 | G4 | 기본 거부 |
| export·copy·외부 전송 | G4 | 개인정보·보안 승인 |
| backup 삭제 또는 retention 변경 | G4 | 기본 거부 |

필수 시스템 통제:

- Agent 전용 read-only database identity
- production write query의 직접 실행 금지
- query row·runtime·cost 제한
- 개인정보 및 결제정보 masking
- 데이터 분류와 residency 검사
- migration pipeline과 사전 backup
- 감사 가능한 query log
- 복구 테스트

### 4.6 Identity, secret과 보안 정책

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| 권한·정책 조회 | G0~G2 | 민감도에 따라 허용 |
| credential 생성·rotation | G3 | 보안 담당 승인 |
| role·policy·group 변경 | G3~G4 | 독립 승인 |
| 관리자·owner 권한 부여 | G4 | 기본 거부 |
| secret 출력·복사·외부 전달 | G4 | 금지 |
| MFA, audit, security control 비활성화 | G4 | 금지 또는 break-glass |

필수 시스템 통제:

- 사용자와 agent identity 분리
- 공유 계정 금지
- SSO, MFA, device posture
- 장기 token 대신 OIDC·federation·short-lived credential
- secret은 agent prompt와 로그에 노출하지 않음
- JIT privileged access
- 정기 access review와 자동 만료
- break-glass 계정의 별도 보관과 사용 알림

### 4.7 고객, 외부 커뮤니케이션과 업무 시스템

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| 초안 작성과 내부 요약 | G0~G1 | 허용 |
| 내부 티켓·문서 수정 | G2 | 승인 |
| 이메일·메신저·SNS 전송 | G2~G3 | 수신자와 본문 확인 후 승인 |
| 고객 계정·권리·상태 변경 | G3 | 담당자 승인 |
| 법무·규제기관·언론 응답 | G4 | 지정 책임자만 수행 |
| 대량 고객 알림 | G4 | 캠페인 승인과 샘플 검증 |

Agent가 작성한 내용은 사실 확인, 기밀정보 검사, 수신자 확인을 거친다. 외부 콘텐츠는 prompt injection 가능성이 있는 신뢰되지 않은 입력으로 취급한다.

#### 제한된 정기 알림의 사전 승인

개인 또는 내부 고정 수신자에게 공개 자료를 요약해 보내는 저영향 정기 알림은 다음 조건을 모두 만족하면 건별 승인 대신 문서화된 standing authorization을 사용할 수 있다. 위험 등급은 G2로 유지한다.

- recipient와 channel이 설정 시점에 고정되고 agent가 변경할 수 없음
- 공개 원문과 자체 요약만 포함하며 개인정보·고객정보·credential이 없음
- 독립된 의미 검증과 결정론적 기밀정보 검사를 모두 통과
- 전송별 idempotency key, 상태, 시각과 결과를 감사 원장에 기록
- 불확실한 전송을 자동 반복하지 않음
- 실행당 문서 수, 주기, 비용과 메시지 길이에 상한 적용
- scheduler pause, credential revoke와 job 제거로 즉시 중단 가능
- 목적, 수신자 또는 콘텐츠 등급이 바뀌면 standing authorization을 무효화하고 다시 승인

이 예외는 고객 안내, 대외 공지, SNS 게시, 법무·규제 대응이나 대량 메시지에는 적용하지 않는다.

### 4.8 결제, 재무와 상거래

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| 거래·정산 보고서 조회 | G1~G2 | 권한과 masking 적용 |
| 환불·취소·credit 지급 | G3~G4 | 금액별 승인 |
| 송금·지급·정산 실행 | G4 | Agent 직접 실행 금지 |
| 가격·수수료·한도 변경 | G4 | 사업·재무·리스크 승인 |
| merchant 또는 고객 지급정보 변경 | G4 | 강한 본인확인과 이중 승인 |
| 결제 key·인증서 변경 | G4 | 보안 절차와 이중 통제 |

결제정보를 다루는 경우 PCI DSS 적용 범위, 데이터 최소화, 환경 분리, 개인별 책임 추적, 변경 통제와 audit log 요구사항을 함께 검토한다.

### 4.9 보안 운영과 사고 대응

| 작업 | 등급 | 기본 정책 |
| --- | --- | --- |
| alert 조회와 증거 수집 | G0~G2 | 허용하되 chain of custody 유지 |
| 티켓 생성과 분류 | G2 | 승인 또는 제한 자동화 |
| 계정 잠금·host 격리 | G3 | incident role 승인 |
| 방화벽 차단·key 폐기 | G3~G4 | 사고 지휘 체계 승인 |
| alert 억제·로그 삭제 | G4 | 기본 거부 |
| 침해 사실 외부 통지 | G4 | 법무·보안 책임자 승인 |

Agent는 사고 대응을 제안할 수 있지만, 증거를 변형하거나 조사 범위를 임의로 확대해서는 안 된다.

## 5. 계층형 통제 구조

```text
조직 정책과 책임
    ↓
Agent·Tool 허용 범위
    ↓
Identity와 단기 Credential
    ↓
CI/CD 및 Policy-as-Code
    ↓
대상 시스템의 강제 Gate
    ↓
감사·탐지·복구
```

### Layer 1 — 조직 정책

- 허용된 AI 제품, 모델, connector, 데이터 등급 정의
- 업무별 risk owner 지정
- 금지 작업과 승인 작업 정의
- 법무, 개인정보, 보안, 규제 요구사항 연결
- 예외와 break-glass 절차 정의

### Layer 2 — Agent 구성

- 업무별 agent와 tool 분리
- tool allowlist
- side-effect가 없는 read tool과 write tool 분리
- 신뢰되지 않은 입력과 system instruction 분리
- 외부 문서의 명령을 실행 지시로 취급하지 않음
- multi-agent 간 권한 상속 제한
- 최대 실행 시간, action 수, 비용, 데이터 양 제한

### Layer 3 — Identity와 접근

- Agent마다 식별 가능한 service identity 사용
- 사용자를 대신하는 경우 사용자 identity와 authorization context 유지
- scope가 좁은 단기 credential 사용
- production 권한 상시 부여 금지
- 네트워크 egress allowlist
- workspace, account, environment별 격리

### Layer 4 — 변경 관리와 CI/CD

- 모든 변경을 ticket, PR, plan과 연결
- deterministic test와 policy check
- 생성자와 승인자 분리
- 승인된 artifact만 배포
- 승인 이후 변경 시 재승인
- 공급망 provenance와 signature 검증

### Layer 5 — 대상 시스템 강제

- GitHub ruleset과 protected branch
- deployment environment reviewer
- cloud IAM, SCP, permissions boundary
- Kubernetes RBAC와 admission policy
- database read-only role와 query 제한
- SaaS connector의 OAuth 최소 scope
- 결제·재무 시스템의 maker-checker 통제

### Layer 6 — 관측과 감사

- 사용자, agent, 모델, tool, action, target, 결과 기록
- 승인자, 승인 시각, 승인 근거 기록
- 민감정보는 로그에서 masking
- 감사 로그를 agent가 수정·삭제할 수 없게 분리
- 고위험 action과 반복 실패에 실시간 alert
- 정기적인 권한·정책·예외 검토

### Layer 7 — 복구와 사고 대응

- kill switch와 credential revoke
- 작업 중단과 queue 격리
- rollback과 restore runbook
- backup 복구 테스트
- agent action trace 보존
- 사고 후 policy와 테스트 보완

## 6. 승인 설계

### 6.1 좋은 승인 요청

승인 화면에는 다음을 함께 제공한다.

```text
요청자: user@example.com via codex-agent-prod
작업: Production deployment
대상: payments-api / ap-northeast-2 / production
변경: image v1.8.2 → v1.8.3
근거: PR #1842, CHG-2026-0712
검증: tests passed, policy passed, vulnerabilities 0 critical
영향: 약 20% traffic부터 canary
복구: v1.8.2로 자동 rollback
승인 만료: 15분
```

### 6.2 나쁜 승인 요청

- “명령 실행을 허용할까요?”
- 전체 명령이나 대상이 보이지 않는 승인
- 세션 전체 또는 영구 승인을 기본 선택
- 서로 다른 여러 작업을 한 번에 승인
- 변경 후에도 계속 유효한 승인
- 승인자가 변경 생성자와 동일한 고위험 작업

### 6.3 승인 정책

- G2: 요청자 본인의 1회 승인 가능
- G3: 담당자 또는 독립 reviewer 승인
- G4: 2인 승인 또는 지정된 break-glass 역할
- 승인은 action, target, artifact digest에 결합
- 변경되면 승인을 무효화
- 시간 제한과 횟수 제한 적용
- 일괄 승인은 동일한 위험과 동일한 대상일 때만 허용

## 7. Codex와 coding agent 적용

### 7.1 설정 계층

조직에서는 다음 순서로 통제한다.

1. 관리자 강제 정책 또는 managed configuration
2. 사용자 전역 config와 rules
3. 신뢰된 프로젝트의 `.codex/config.toml`과 rules
4. 세션별 `/permissions`
5. 일회성 승인

사용자나 프로젝트가 조직의 제한을 완화할 수 없게 관리자 정책을 가장 높은 강제 계층에 둔다.

### 7.2 기본 권장값

```toml
sandbox_mode = "workspace-write"
approval_policy = "on-request"
approvals_reviewer = "user"

[sandbox_workspace_write]
network_access = false
```

- 일상적인 로컬 편집과 테스트는 허용한다.
- workspace 밖 접근과 네트워크는 승인 경계로 둔다.
- `danger-full-access`와 `approval_policy = "never"` 조합은 회사 기본값으로 사용하지 않는다.
- unattended automation은 별도의 제한된 identity와 환경에서 실행한다.

### 7.3 Command rule의 역할

명령 규칙은 다음 용도로 사용한다.

- `prompt`: 외부 영향이 있는 명령을 실행 직전에 확인
- `forbidden`: 조직에서 금지한 명령을 차단
- `allow`: 좁고 검증된 반복 명령만 예외 허용

규칙은 실행 파일과 인자 prefix를 검사한다. 다음 우회 가능성을 고려해야 한다.

- global option이 subcommand 앞에 오는 형태
- Git alias와 shell alias
- 절대 경로로 실행한 binary
- shell wrapper와 복합 명령
- script, Python, Node.js 등이 내부에서 실행한 subprocess
- MCP, connector, SDK 또는 직접 API 호출
- 다른 binary 이름이나 복사본
- full-access 또는 network-enabled 환경

따라서 `git push` prompt 규칙은 유용하지만 GitHub의 branch protection을 대체하지 않는다. 누락 허용치가 0에 가까운 경우 agent에게 production credential 자체를 제공하지 않고 원격 시스템에서 승인 절차를 강제한다.

## 8. 역할과 책임

| 역할 | 책임 |
| --- | --- |
| Business/System Owner | 허용 업무와 risk tolerance 승인 |
| Engineering Owner | 기술 통제와 변경 절차 책임 |
| Security | threat model, 권한, logging, incident control 검토 |
| Privacy/Legal/Compliance | 데이터, 규제, 계약 및 외부 사용 검토 |
| Platform/DevOps | CI/CD, identity, environment gate 구현 |
| Agent Owner | prompt, tool, model, evaluation, 운영 지표 관리 |
| Independent Approver | G3·G4 변경 검토 |
| Internal Audit | 통제 설계와 실행 증거 검증 |

한 사람이 Agent Owner, 고위험 변경 생성자, 유일한 승인자, audit log 관리자를 동시에 맡지 않도록 한다.

## 9. 운영 필수 산출물

- AI agent inventory
- owner와 업무 목적
- 연결된 tool, connector, MCP 목록
- 접근 가능한 데이터 등급
- service identity와 권한 목록
- 위험 등급과 허용 action
- 승인 매트릭스
- evaluation과 red-team 결과
- 변경 이력과 배포 기록
- audit log와 보존 기간
- incident·rollback·decommission runbook
- exception register

## 10. 검증 방법

### 도입 전

- [ ] 정상 업무 시나리오 평가
- [ ] 잘못된 대상과 모호한 요청 테스트
- [ ] direct·indirect prompt injection 테스트
- [ ] tool 결과 위조와 악성 문서 테스트
- [ ] 권한 상승과 credential 탐색 테스트
- [ ] destructive action 우회 테스트
- [ ] alias, wrapper, absolute path, subprocess 테스트
- [ ] 대량·반복 action과 비용 폭주 테스트
- [ ] 승인 변경 후 재사용 테스트
- [ ] network egress와 데이터 유출 테스트
- [ ] kill switch와 rollback 테스트

### 운영 중

- [ ] 고위험 action 수와 승인 거절률 관측
- [ ] 승인 없는 실행 탐지
- [ ] 사용하지 않는 tool과 권한 제거
- [ ] model·prompt·tool 변경 시 재평가
- [ ] connector scope 정기 검토
- [ ] 장기 credential 탐지
- [ ] audit log 누락과 변조 탐지
- [ ] 정책 예외 만료 확인
- [ ] 실제 incident와 near-miss 반영

## 11. 단계별 도입

### Stage 1 — Inventory와 Read-only

- Agent와 연결 시스템 목록화
- production credential 제거
- read-only identity 제공
- logging과 데이터 분류 적용

### Stage 2 — Controlled Write

- G2 작업부터 1회 승인으로 허용
- command·tool 규칙과 대상 allowlist 적용
- PR과 ticket 연결
- 정책 테스트 자동화

### Stage 3 — Gated Production

- G3 작업을 CI/CD와 protected environment로만 수행
- 독립 승인, OIDC, JIT 권한 적용
- artifact provenance와 rollback 검증

### Stage 4 — Continuous Assurance

- red-team과 adversarial evaluation
- anomaly detection
- 권한과 예외 자동 만료
- 통제 효과 측정과 정기 감사

G4 작업은 maturity와 무관하게 기본적으로 agent 직접 실행 대상에서 제외한다.

## 12. 현재 프로젝트에 적용할 초기 기준

Hermes Agent의 현재 자동화 기능은 공개 자료 수집, agent 관련성·근거 검증, Obsidian 문서 생성과 고정 Telegram chat 알림이다. 정상 경로는 사람의 건별 승인 없이 실행하지만 의미 검증과 결정론적 gate 중 하나라도 실패하면 발행하지 않는다. 다음 기준을 적용한다.

- 공개 웹 자료 읽기: G0
- Vault 내부 신규 문서 작성: G1
- 기존 사람이 작성한 문서 덮어쓰기·이동: G2
- Git commit: G1
- 모든 Git push: G2
- GitHub PR·issue 생성과 수정: G2
- 고정 개인 Telegram chat의 검증된 공개 자료 알림: G2 standing authorization
- 외부 사이트 로그인, 댓글, 이메일과 그 밖의 메시지 전송: G2~G3 건별 승인
- API key, cookie, 유료 API 사용: G2 이상
- 개인정보·결제정보 수집: 기본 제외
- source 전체 복제 또는 저작물 재배포: 기본 제외
- Telegram 외 자동 게시, production 배포, 결제 실행: 현재 scope 밖

## 13. 공식 참고자료

- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
- [NIST AI RMF Core](https://airc.nist.gov/airmf-resources/airmf/5-sec-core/)
- [NIST SP 800-53 Rev. 5](https://csrc.nist.gov/pubs/sp/800/53/r5/upd1/final)
- [OWASP LLM06: Excessive Agency](https://genai.owasp.org/llmrisk/llm062025-excessive-agency/)
- [OWASP Agentic AI Threats and Mitigations](https://genai.owasp.org/resource/agentic-ai-threats-and-mitigations/)
- [Codex sandboxing and approvals](https://learn.chatgpt.com/docs/agent-approvals-security)
- [Codex rules](https://learn.chatgpt.com/docs/agent-configuration/rules)
- [GitHub repository rulesets](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets)
- [GitHub ruleset rules](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/available-rules-for-rulesets)
- [GitHub deployments and environments](https://docs.github.com/en/actions/reference/workflows-and-actions/deployments-and-environments)
- [GitHub Actions secure use](https://docs.github.com/en/actions/reference/security/secure-use)
- [GitHub Actions OpenID Connect](https://docs.github.com/en/actions/concepts/security/openid-connect)
- [Terraform automation](https://developer.hashicorp.com/terraform/tutorials/automation/automate-terraform)
- [Kubernetes RBAC good practices](https://kubernetes.io/docs/concepts/security/rbac-good-practices/)
- [Open Policy Agent in CI/CD](https://www.openpolicyagent.org/docs/cicd)
- [SLSA security levels](https://slsa.dev/spec/v1.0/levels)
- [AWS IAM security best practices](https://docs.aws.amazon.com/IAM/latest/UserGuide/best-practices.html)
- [npm trusted publishing](https://docs.npmjs.com/trusted-publishers/)
- [PCI SSC Document Library](https://www.pcisecuritystandards.org/document_library/)
- [PCI SSC glossary: Change Control and Least Privileges](https://www.pcisecuritystandards.org/glossary/)
