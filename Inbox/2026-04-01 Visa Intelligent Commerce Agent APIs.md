---
note_schema_version: "1.0"
record_id: "5b8c36bb23126f45342d45a5c12527791609e419c33f5a1e7710a0ad7b19331d"
source_fingerprint: "caf260a3b989fd5db87c68a14f52c1a0a8650e89f776755affe8ec471d09327c"
source: "Visa"
source_id: "visa-developer-release-notes"
source_type: "official-developer-release-notes"
canonical_url: "https://developer.visa.com/site/release_notes?month=2026-04"
original_url: "https://developer.visa.com/site/release_notes"
published_at: "2026-04-01"
published_at_precision: "month"
collected_at: "2026-07-28T12:23:19+09:00"
first_collected_at: "2026-07-28T12:23:19+09:00"
last_checked_at: "2026-07-28T12:23:19+09:00"
language: "en"
discovery_method: "official-static-html"
verification_status: "official-page-verified"
created_by: "manual"
generator: "manual-review"
generator_version: "1.0"
topics:
  - agentic-commerce
  - payment-credentials
  - consent
  - spending-controls
importance: "high"
status: "draft"
---

# Visa Intelligent Commerce Agent APIs

## 원문

- [Visa Developer 2026년 4월 Release Notes](https://developer.visa.com/site/release_notes)
- 발행: 2026-04 (원문이 일 단위 날짜를 제공하지 않아 수집 레코드는 2026-04-01로 정규화)
- 출처: Visa / Developer Release Notes
- 수집·검증: Visa의 공식 정적 HTML 릴리스 노트에서 월별 항목을 수집하고 원문 확인

## 요약

Visa는 2026년 4월 개발자 릴리스 노트에 Visa Intelligent Commerce Agent API를 추가했다. 주요 흐름은 소비자 카드 등록, 구매 지시 생성·수정·취소, 구매 시작과 결제 credential 조회, 주문·배송·결제 이벤트 통지다.

카드 등록 시 소비자의 등록 허가를 `assuranceData`로 기록하고, 개인화 신호 조회에 동의했다면 `consentData`에 남긴다. 구매 지시는 디지털 카드 사용 승인뿐 아니라 소비자가 정한 제한과 지출 한도인 mandate를 포함한다. Visa는 이 API를 VACP Platform과 파트너 서버 사이의 backend-to-backend 통신으로 설명하며, 현재 가용성은 Restricted다.

같은 월에는 Visa Offers Network의 사용자 동의 생성·조회·삭제 API와 Visa Commercial의 가상카드 인증 outbound event도 추가됐다.

## 왜 중요한가

에이전트 결제를 단순한 카드 credential 전달이 아니라 동의, 지출 제한, 구매 지시 lifecycle과 사후 이벤트로 분리한 공식 API 경계가 드러난다. 자동 구매 시스템을 설계할 때 필요한 최소 통제면을 비교할 수 있는 구체적인 자료다.

## 기술 학습 키워드

- Agentic commerce — 소프트웨어 에이전트가 사용자의 권한 범위에서 탐색과 구매를 수행하는 흐름
- Payment credential — 실제 결제 승인에 쓰이는 카드 또는 토큰화된 결제 정보
- Mandate — 금액, 사용처 등 소비자가 사전에 정한 거래 제약
- Consent lifecycle — 동의의 생성, 조회, 변경과 철회를 관리하는 과정
- Assurance data — 소비자가 특정 행위를 승인했다는 근거 데이터

## 확인할 점

- Restricted API의 이용 대상, onboarding 조건과 정식 공개 일정
- 구매 지시와 실제 authorization 사이의 책임·거절 처리 경계
- mandate 위반, 환불과 부분취소가 이벤트 모델에 반영되는 방식
- `assuranceData`와 `consentData`의 보존 기간 및 감사 요건
