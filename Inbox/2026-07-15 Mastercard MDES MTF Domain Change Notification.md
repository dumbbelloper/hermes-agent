---
note_schema_version: "1.0"
record_id: "c6277f2a54326bc644a1056a8213d778e338c218ad200870f8aa1ee37ffb5f5c"
source_fingerprint: "c621bce8942cf96e13fc14a3a76a1bba670a634d3307102179c90779f87501e4"
source: "Mastercard"
source_id: "mastercard-mdes-documentation"
source_type: "official-technical-documentation"
canonical_url: "https://developer.mastercard.com/mdes/documentation/mtf-domain-change-notification"
original_url: "https://developer.mastercard.com/mdes/documentation/mtf-domain-change-notification/"
published_at: "2026-07-15"
collected_at: "2026-08-11T10:34:42+09:00"
first_collected_at: "2026-08-11T10:34:42+09:00"
last_checked_at: "2026-08-11T10:34:42+09:00"
language: "en"
discovery_method: "official-documentation"
verification_status: "official-page-verified"
created_by: "manual"
generator: "manual-review"
generator_version: "1.0"
topics:
  - mdes
  - tokenization
  - api-environment
  - credential-separation
  - migration
importance: "high"
status: "draft"
---

# Mastercard MDES MTF Domain Change Notification

## 원문

- [공식 공지](https://developer.mastercard.com/mdes/documentation/mtf-domain-change-notification/)
- [MDES 제품 개요](https://developer.mastercard.com/product/mdes/)
- 발효: 2026-07-15
- 출처: Mastercard Developers / MDES Documentation
- 수집·검증: 현재 Chrome의 Mastercard MDES 공식 제품 페이지에서 문서 구조를 확인하고, Mastercard Developers의 공지와 각 영향 서비스의 API Basics를 대조

## 요약

Mastercard는 2026년 7월 15일부터 새로운 Mastercard Test Facility(MTF) 환경을 제공하고 legacy MTF 환경을 중단했다. 변경 대상은 MDES Customer Service API, MDES Digital Enablement API, MDES Token Connect API와 Token Requestor Identifier(TRID) API다.

새 MTF는 `sandbox.api.mastercard.com` 계열 domain과 Sandbox credential을 사용한다. 기존 MTF 전용 service를 프로젝트에서 제거하고, 대상 MDES service의 test environment를 MTF로 선택한 뒤 Sandbox Client ID, OAuth key와 필요한 encryption key를 생성·적용해야 한다. Production endpoint와 credential, API contract 및 gateway certificate에는 영향이 없다고 공식 문서는 명시한다.

## 왜 중요한가

이번 변경은 단순 DNS 교체가 아니라 test와 production의 credential 경계를 분리하는 운영 migration이다. production credential로 MTF를 호출하던 기존 통합은 2026년 7월 15일 이후 동작하지 않으므로, endpoint만 바꾸고 key·Client ID·project service 구성을 그대로 두면 인증 실패가 발생할 수 있다.

MDES는 PAN·PII를 다루므로 OAuth signing key, payload encryption key와 환경별 Client ID를 함께 교체·검증해야 한다. migration 검증도 단순 network 연결이 아니라 각 API의 서명, 암호화·복호화와 실제 MTF test call 성공까지 포함해야 한다.

## 영향 서비스

| 서비스 | 확인할 변경 |
| --- | --- |
| MDES Customer Service | MTF endpoint, Sandbox Client ID·OAuth·encryption key, Search API encryption test 환경 |
| MDES Digital Enablement | digitization·remote transaction·asset·token lifecycle MTF endpoint와 Sandbox credential |
| MDES Token Connect | eligible token requestor·asset·push provisioning endpoint와 payload encryption |
| Token Requestor Identifier | batch onboarding·search endpoint와 OAuth 1.0a signing credential |

## 기술 학습 키워드

- [[Mastercard Digital Enablement Service]] — 영향을 받는 tokenization 서비스와 참여자·API 경계
- Mastercard Test Facility(MTF) — 실제 production 전 통합을 검증하는 pre-production 환경
- Environment credential separation — Sandbox·MTF와 Production의 Client ID·signing·encryption key를 분리하는 통제
- OAuth 1.0a body hash — request body 무결성과 RSA signature를 함께 검증하는 Mastercard API 인증 방식
- Payload encryption — TLS와 별도로 PAN·PII field를 application layer에서 암호화하는 방식

## 확인할 점

- 모든 영향 API의 현재 MTF URL을 각 API Reference에서 다시 확인했는가
- legacy MTF service와 production credential 의존성이 구성·secret store·배포 pipeline에 남아 있지 않은가
- Sandbox OAuth key와 encryption/decryption key를 MTF runtime에만 주입했는가
- Customer Service의 Search API encryption은 mock Sandbox가 아니라 MTF에서 검증했는가
- migration 후 서명, payload 암호화·복호화와 대표 API call을 end-to-end로 통과했는가
- rollback이 legacy MTF 복귀를 전제로 하지 않도록 장애 대응 절차를 갱신했는가

## 한계

- 공개 문서만 검토했으며 Mastercard project, credential, Sandbox·MTF 또는 Production API를 실제 호출하지 않았다.
- 공지의 endpoint 표는 시점에 따라 바뀔 수 있으므로 구현 기준은 현재 각 서비스의 API Reference와 Mastercard onboarding 안내다.
- 공지 페이지의 발행일 표시는 별도로 노출되지 않아 `published_at`은 공식 공지에 명시된 새 MTF 발효일 2026-07-15로 기록했다.
