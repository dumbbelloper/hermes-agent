---
note_schema_version: "1.0"
record_id: "3fe964e5269ce278870c6d27ac5db85772e37b9bf9ae7d7d6a5735ceac697f47"
source_fingerprint: "3a7fcfd221222430a7aa46567f90331f4c5f75c7566eb4a280a0811449dae140"
source: "EMVCo"
source_id: "emvco-news"
source_type: "official-news"
canonical_url: "https://www.emvco.com/news/emvco-requests-feedback-on-verifiable-digital-credentials-for-card-based-payment-authentication"
original_url: "https://www.emvco.com/news/emvco-requests-feedback-on-verifiable-digital-credentials-for-card-based-payment-authentication/"
published_at: "2026-06-23"
collected_at: "2026-07-28T10:30:24+09:00"
first_collected_at: "2026-07-28T10:30:24+09:00"
last_checked_at: "2026-07-28T10:49:47+09:00"
language: "en"
discovery_method: "official-rss"
verification_status: "official-page-verified"
created_by: "manual"
generator: "manual-review"
generator_version: "1.0"
topics:
  - digital-payment-credential
  - payment-authentication
  - digital-identity
  - interoperability
importance: "high"
status: "draft"
---

# EMVCo Requests Feedback on Verifiable Digital Credentials for Card-Based Payment Authentication

## 원문

- [원문 보기](https://www.emvco.com/news/emvco-requests-feedback-on-verifiable-digital-credentials-for-card-based-payment-authentication/)
- 발행: 2026-06-23
- 출처: EMVCo / News
- 수집·검증: EMVCo 공식 RSS에서 발견하고 공식 원문 확인

## 요약

EMVCo는 카드 결제 인증에 검증 가능한 디지털 자격증명을 상호운용 가능하게 사용하기 위한 `EMV Digital Payment Credential Specification – Schema Framework` 초안을 공개했다. 초기 초점은 Digital Payment Credential(DPC)에 포함되는 데이터와 구조를 정의해 안전하고 개인정보 보호가 가능하며 확장 가능한 인증을 지원하는 것이다.

DPC는 온라인 카드 결제에서 자격증명 발급, 요청과 검증 절차를 네트워크·wallet·검증 시스템 사이에서 일관되게 만드는 것을 목표로 한다. 적용 고려사항에는 device binding, 도메인 간 사용과 dynamic linking이 포함되며, EMVCo는 향후 결제 개시 기능도 검토하고 있다. 최초 공개 의견 수렴 기한은 2026-07-23으로 현재는 종료됐다.

## 왜 중요한가

디지털 신원 wallet의 자격증명을 카드 결제 인증에 연결할 때 네트워크마다 별도 규격을 만들면 생태계가 분절될 수 있다. EMVCo의 공통 schema가 표준으로 발전하면 3-D Secure, passkey, 디지털 신원 wallet과 카드 결제 인증 사이의 역할과 데이터 교환 방식에 영향을 줄 수 있다.

## 기술 학습 키워드

- [[Digital Payment Credential]] — 카드 결제 인증에 특화된 검증 가능한 디지털 자격증명
- Verifiable Digital Credential — 암호학적으로 검증 가능한 디지털 신원·속성 표현
- Device binding — 자격증명이나 인증 수단을 특정 기기와 결합하는 통제
- Dynamic linking — 인증 정보를 특정 거래의 금액·수취인과 연결하는 방식

## 확인할 점

- 공개 의견 반영 후 schema와 필수 데이터 요소의 변경
- EMV 3-D Secure, SRC와 DPC의 구체적인 결합 방식
- FIDO Alliance, OpenID Foundation, W3C 등의 규격과 역할 분담
- 개인정보 최소 공개와 wallet 간 상호운용성 요구사항
