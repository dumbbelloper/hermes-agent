# Hermes Agent 프로젝트 설계

> 기준일: 2026-07-29
>
> 상태: Phase 0·1 완료 · Phase 2·3·4 부분 완료 · self-contained Hermes Skill v0.1.0 공개 배포 · 최초 실환경 cron 검증 필요

## 1. 목표

바쁜 일상에서도 글로벌 결제 네트워크 생태계의 중요한 변화를 놓치지 않도록 다음 과정을 반복 가능하게 만든다.

1. 공식 채널과 신뢰할 수 있는 뉴스에서 신규 자료를 수집한다.
2. 중복과 저가치 자료를 제거하고 중요도를 판정한다.
3. 원문의 의미를 보존한 한국어 요약과 학습 키워드를 작성한다.
4. Obsidian에서 검색하고 연결하기 쉬운 Markdown 문서로 저장한다.
5. 주기적으로 무인 실행하고 실패와 격리 원인을 감사 가능한 상태로 남긴다.

## 2. 추적 범위

전체 추적 후보와 초기 수집 범위의 선정 상태는 [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)에서 관리한다.
실제 운영·후보·제외 출처와 판정 근거는 [SOURCE_CATALOG.md](./SOURCE_CATALOG.md)에서 관리한다.

### 우선 추적 대상

- Visa
- Mastercard
- American Express
- UnionPay
- JCB

### 출처 우선순위

1. 공식 개발자 문서, 제품 문서, 표준 및 규격
2. 공식 뉴스룸, 보도자료, 기업 블로그
3. 공식 GitHub 저장소와 릴리스
4. 공식 YouTube 채널
5. 규제기관, 표준화 기구, 거래소 등 1차 출처
6. 신뢰할 수 있는 전문 매체와 일반 뉴스

공식 자료를 우선하며 뉴스는 공식 발표의 맥락, 시장 반응, 경쟁 구도를 보완하는 용도로 사용한다.

## 3. 수집 전략

출처마다 가장 안정적인 공개 인터페이스를 선택한다.

| 출처 유형 | 1차 수집 방식 | 대체 방식 | 수집할 정보 |
| --- | --- | --- | --- |
| 공식 사이트·블로그 | RSS/Atom 또는 sitemap | 목록 페이지 변경 감지 | 제목, URL, 게시일, 본문, 작성 주체 |
| 뉴스룸·보도자료 | RSS 또는 목록 페이지 | 검색 API/검색 엔진 | 제목, URL, 게시일, 본문 |
| GitHub | GitHub API의 release/event 조회 | Atom feed | 저장소, 버전, 변경 내역, 게시일 |
| YouTube | 채널 RSS | YouTube Data API | 영상 제목, URL, 게시일, 설명, 자막 유무 |
| 뉴스 | 허가된 RSS/API | 검색 결과의 원문 링크 | 매체, 제목, URL, 게시일, 본문 |

### 수집 원칙

- robots.txt, 서비스 약관, API 사용 제한과 콘텐츠 저작권을 준수한다.
- 원문 전체를 Vault에 복제하지 않고 링크, 메타데이터, 자체 요약 중심으로 저장한다.
- URL 정규화와 원문 고유 ID로 같은 자료의 중복 저장을 막는다.
- 게시 시각과 최초 발견 시각을 별도로 기록한다.
- 동적 페이지나 수집 실패는 즉시 브라우저 자동화로 우회하지 않고 실패 큐에 남긴다.
- 로그와 체크포인트를 남겨 중단 이후에도 마지막 성공 지점부터 재개한다.

## 4. 처리 파이프라인

```text
Source Registry
    → Fetch
    → Normalize
    → Deduplicate
    → Durable Delta Queue
    → Curator Agent
    → Writer Agent
    → Independent Verifier Agent
    → Deterministic Validate
    → Atomic Write
    → Telegram Delivery Ledger
```

### 단계별 책임

1. **Source Registry**
   - 추적할 조직, 채널, URL, 수집 방식, 실행 주기, 언어를 관리한다.
2. **Fetch**
   - 마지막 실행 이후 새로 발행된 항목의 메타데이터와 접근 가능한 원문을 가져온다.
3. **Normalize**
   - 날짜, 조직명, URL, 콘텐츠 유형을 공통 스키마로 변환한다.
4. **Deduplicate**
   - canonical URL, 외부 ID, 제목 유사도, 본문 해시로 중복을 판정한다.
5. **Relevance Filter**
   - 결제 기술, 네트워크 정책, 제품, 보안, 표준, 규제, 파트너십 등 관심 범위와의 관련성을 평가한다.
6. **Enrich & Summarize**
   - 핵심 내용, 의미, 기술 학습 키워드를 원문 근거 안에서 작성한다.
7. **Validate**
   - 제목과 원문 링크 존재 여부, 날짜 형식, 요약의 근거성, 중복 여부를 검사한다.
8. **Write Markdown**
   - 정해진 템플릿으로 원자적 문서를 생성한다.
9. **Delivery**
   - 검증된 문서만 Telegram에 전송하고 delivery 상태를 기록한다.

## 5. 문서 규격 초안

### 파일과 제목

- 문서의 H1 제목은 원문의 제목을 그대로 사용한다.
- 파일명에는 운영체제에서 사용할 수 없는 문자를 치환한다.
- 같은 제목이 존재하면 게시일 또는 짧은 콘텐츠 ID를 파일명에 추가한다.
- 원문 제목을 번역하지 않는다. 필요한 경우 본문 요약에서 한국어로 뜻을 설명한다.

### Frontmatter

```yaml
---
source: "Visa"
source_type: "official-blog"
original_url: "https://example.com/original"
published_at: "2026-07-24"
collected_at: "2026-07-24T09:00:00+09:00"
language: "en"
topics:
  - tokenization
  - digital-identity
importance: "high"
status: "reviewed"
---
```

필수 필드는 `source`, `source_type`, `original_url`, `published_at`, `collected_at`이다. `importance`와 `status`는 자동화 초기에는 검토 가능한 값으로 유지한다.

### 본문 템플릿

```markdown
# 원문 제목 그대로

## 원문

- [원문 보기](https://example.com/original)
- 발행: YYYY-MM-DD
- 출처: Organization / Channel

## 요약

원문에서 확인되는 핵심 내용을 한국어로 간결하게 정리한다.

## 왜 중요한가

결제 생태계, 경쟁 구도, 운영 또는 제품 관점의 의미를 정리한다.

## 기술 학습 키워드

- [[Tokenization]] — 이 자료에서 알아야 할 이유
- [[Passkey]] — 이 자료에서 알아야 할 이유

## 확인할 점

- 추가 검증이나 후속 추적이 필요한 내용
```

원문에 기술 학습 요소가 없다면 `기술 학습 키워드` 절은 생략할 수 있다. 추론이나 해석은 원문에 나온 사실과 구분해 표현한다.

## 6. 제안 폴더 구조

```text
.
├── README.md
├── PROJECT_PLAN.md
├── Inbox/
│   └── 수집 직후 검토 전 문서
├── Sources/
│   └── 조직 및 채널별 출처 설명
├── Notes/
│   ├── Visa/
│   ├── Mastercard/
│   ├── American Express/
│   ├── UnionPay/
│   ├── JCB/
│   └── Industry/
├── Digests/
│   └── 일간·주간 요약
├── Concepts/
│   └── 기술 및 산업 개념 노트
├── Templates/
│   └── 문서 템플릿
└── Automation/
    └── 설정, 상태, 로그 및 실행 코드
```

초기에는 폴더를 모두 만들지 않는다. 실제 수집 샘플로 문서 흐름을 검증한 뒤 필요한 폴더만 생성한다.

## 7. Agent와 Skill 경계

Agent와 skill의 권한, 승인, 운영 환경 및 감사 기준은 [ENTERPRISE_AI_GUARDRAILS.md](./ENTERPRISE_AI_GUARDRAILS.md)를 따른다.

### 적용 Agent

- **Collector**: Python pipeline이 allowlist, 품질 gate, checkpoint와 delta queue를 관리한다.
- **Curator Agent**: fresh subagent context에서 관련성, 중요도와 `event_key`를 판단한다.
- **Writer Agent**: 원문 근거 안에서 한국어 요약, 의미와 학습 키워드를 구조화한다.
- **Verifier Agent**: Writer와 분리된 fresh context에서 모든 사실, 숫자, 날짜, 조직과 과장을 대조한다.

### 적용 Skill

- [Hermes News Automation](./skills/hermes-news-automation/SKILL.md)
  - durable run 생성과 queue 처리
  - 허용된 원문 추출
  - Curator·Writer·Verifier 분리
  - 결정론적 artifact 검사와 Obsidian 원자 저장
  - Telegram delivery와 run 종료

Agent는 의미 판단을 담당하고 Python controller는 상태 전이, 임계값, 파일·알림 부작용과 멱등성을 강제한다.

## 8. 실행 및 검토 정책

- 기본 실행 주기: Hermes cron에서 3시간마다, 사용자 설정으로 조정
- 수집 범위: 마지막 성공 시각 이후 발행 또는 수정된 항목
- 자동 저장 위치: 검증을 통과한 문서는 `Inbox/`
- 정상 문서 승인: Curator·독립 Verifier·결정론적 gate 모두 통과 시 자동
- 중요 항목: 일간 Digest에 포함
- 실패 항목: `irrelevant`, `quarantined`, `retryable`, `notify_unknown`과 원인을 기록
- 동일 원문 업데이트: agent 생성 문서만 재검증 후 갱신하고 수동 문서는 격리
- 불확실한 항목: 사람 승인을 기다리지 않고 fail-closed로 발행하지 않음

정상 경로는 사람 개입 없이 완료한다. Agent나 검증기가 확신하지 못하는 항목은 자동 발행하지 않는 방식으로 정확성을 우선한다.

## 9. 단계별 구현 계획

### 구현 현황 — 2026-07-28

- [x] Phase 0 공식 출처 조사와 수집 품질 검증
- [x] versioned Source Registry와 공식 도메인 allowlist
- [x] Visa HTML, JCB JSON, EMVCo RSS, PCI SSC RSS adapter
- [x] 공통 스키마, URL·날짜 정규화와 레코드 검증
- [x] 원본·snapshot·누적 정상 상태·격리·source health 저장
- [x] 빈 snapshot과 수집 실패 시 마지막 정상 상태 보존
- [x] CLI와 네트워크 없는 fixture 회귀 테스트
- [x] 공식 9개·편집 언론 4개, 추가 구현 후보와 수집 제외 출처 분류
- [x] 수집 `record_id`를 이용한 Vault 문서 인덱스와 중복 작성 방지 판정
- [x] logical run lock, durable manifest와 delta queue
- [x] Curator·Writer·독립 Verifier artifact 계약과 결정론적 gate
- [x] Obsidian Inbox 원자 작성과 agent 문서 자동 갱신
- [x] Telegram delivery ledger와 불확실 전송 중복 방지
- [x] Hermes Skill과 token 절약 `wakeAgent` pre-check
- [x] repository 밖에서 실행 가능한 self-contained Skill runtime
- [x] GitHub direct install·Hermes tap 배포 구조와 격리 설치 smoke test
- [x] macOS·Linux·Windows Skill CI matrix
- [x] 선별 GitHub Release Atom 수집
- [x] workspace credential 파일 기반 Telegram 문서 알림
- [x] Hermes gateway·cron 운영 가이드
- [ ] 출처별 retry backoff, circuit breaker와 장기 운영 지표

구현 세부 사항과 실행법은 [Automation/README.md](./Automation/README.md)에서 관리한다.

### Phase 0 — 설계 검증

- [x] 추적 대상별 공식 채널 목록 작성
- [x] 출처의 RSS, sitemap, API 제공 여부 확인
- [x] 590건 메타데이터와 136건 원문 추출 표본 검증
- [x] 관련성 보존 기준과 자동 제외 원칙 확정
- [x] 접근 차단·브라우저 의존 출처를 운영 범위에서 제외

### Phase 1 — 최소 수집기

- [x] 운영 Source Registry 정의
- [x] RSS/Atom, 공식 JSON과 정적 HTML 수집 구현
- [x] 상태 저장, URL 정규화, 중복 제거 구현
- [x] 선별한 GitHub Release Atom 수집 구현
- [x] 원문 링크 중심의 Inbox 문서 생성 자동화

### Phase 2 — 요약 및 품질 관리

- [x] Hermes web extraction과 한국어 요약 workflow
- [x] 기술 키워드 추출 및 Concepts 링크 생성
- [x] identity schema와 링크 자동 검증
- [x] 수동 문서 격리와 agent 문서 자동 갱신 구분
- [ ] 실제 정기 실행 표본을 이용한 confidence threshold 보정
- [x] 같은 `event_key`의 두 번째 문서 발행 차단
- [ ] 실제 표본을 이용한 event key 생성·대표 자료 선택 품질 보정

### Phase 3 — 채널 확장

- [x] 공개 JSON·정적 HTML 기반 비-RSS 공식 사이트 지원
- [ ] YouTube 채널 지원
- [x] 금융·결제 전문 뉴스 출처 4개 추가
- [ ] 규제기관 출처 추가
- [x] 초기 수집 결과 Digest 3개 생성
- [ ] 일간·주간 Digest 자동 생성

### Phase 4 — 운영 자동화

- [x] Hermes Skill 기반 cron 실행 설계와 크로스플랫폼 설정 가이드
- [x] Skill 내부 runtime 단일 원본과 workspace `init`·`doctor`
- [x] GitHub direct install·tap·skills.sh 배포 metadata
- [x] logical lock, stale run 회수와 item retry 상태
- [x] 신규 항목 수, item 결과와 delivery 상태 원장
- [ ] 출처별 backoff·circuit breaker
- [ ] 장기 성공률·비용 dashboard와 정기 품질 샘플링

## 10. 결정 현황

| 항목 | 상태 | 결정 또는 남은 선택 |
| --- | --- | --- |
| 구현 언어와 런타임 | 결정 | Python 3.9 이상, runtime dependency 없음 |
| 현재 실행 환경 | 결정 | macOS·Linux·Windows WSL2를 1차 지원하고 native Windows는 실험 지원. 설치 workspace의 `.hermes-news/data/`에 local 영속 상태 저장 |
| Skill 배포 | 결정 | `skills/hermes-news-automation/` self-contained bundle, GitHub direct install과 Hermes tap. 세부 기준은 [Skill 배포 가이드](./SKILL_DISTRIBUTION_GUIDE.md) |
| 운영 출처 | 결정 | 직접 접근 가능한 공식 출처 9개와 편집 언론 4개, 세부 기준은 [SOURCE_CATALOG.md](./SOURCE_CATALOG.md) |
| 차단 출처 처리 | 결정 | WAF 우회, 검색 인덱스와 브라우저 자동화 폴백 없이 제외 |
| 문서 식별과 중복 방지 | 결정 | `record_id`, `source_fingerprint`와 실행 시 Vault index 사용. 세부 기준은 [NOTE_IDENTITY_POLICY.md](./NOTE_IDENTITY_POLICY.md) |
| 문서 승인 | 결정 | Curator confidence 0.80, 독립 Verifier 0.85와 결정론적 gate 통과 시 자동 발행 |
| LLM 정책 | 부분 결정 | Hermes cron의 Writer·Verifier 분리, 모델·provider와 비용 상한은 사용자 환경에서 설정 |
| 중요도·실행 상한 | 결정 | importance 3단계, 기본 실행당 최대 5건 |
| 원문 수정·삭제 | 부분 결정 | agent 문서는 재검증 후 갱신, 수동 문서는 격리. 원문 삭제 정책은 후속 |
| 운영 자동화 환경 | 결정 | laptop은 로그인·전원·네트워크 유지, Linux server는 systemd, Windows는 WSL2 우선. 세부 기준은 [무인 자동화 가이드](./HERMES_AUTOMATION_GUIDE.md) |

## 11. 현재 문서 작성 작업

운영 출처 13개의 최신 자료 중 결제 기술·표준·보안 변화와 직접 관련된 항목을 소량 선별해 `Inbox/` 초안을 작성한다. 2026-07-30 Skill workspace의 누적 1,595건에서 14건을 문서화했다.

- [x] 안정적인 신규 항목 탐지와 원문 제목·링크 보존 검증
- [x] agent artifact의 한국어 요약·중요성·근거 필수화
- [x] 기술 키워드와 Concepts 링크 형식 자동 생성
- [x] 실행당 기본 상한 5건과 중요도 3단계 확정
- [ ] 같은 사건의 조직 간 발표를 연결하는 방식 검증

향후 실제 cron 실행 표본으로 confidence threshold, 격리율과 사건 grouping 품질을 보정한다.
