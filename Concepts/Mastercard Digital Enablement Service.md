# Mastercard Digital Enablement Service

> 기준일: 2026-08-11
>
> 상태: 공식 공개 문서 기반 개념 정리

Mastercard Digital Enablement Service(MDES)는 Mastercard 카드의 PAN을 디지털 토큰으로 전환하고, 해당 토큰의 발급·활성화·거래·수명주기를 관리하는 통합 플랫폼이다. Mastercard는 issuer, wallet provider, merchant, payment service provider(PSP)와 그 밖의 token requestor가 여러 디지털 결제 채널을 하나의 MDES 연결로 지원할 수 있다고 설명한다.

## 핵심 흐름

1. 카드의 PAN을 MDES 토큰으로 대체한다.
2. 토큰을 특정 플랫폼, wallet application 또는 device의 사용 영역에 연결한다.
3. 생성한 토큰을 대상 플랫폼이나 device에 provision한다.
4. 거래에는 원래 PAN 대신 토큰을 사용한다.

토큰화가 PAN 자체의 모든 위험을 없애는 것은 아니다. 실제 통제 범위는 token domain, cryptogram, issuer 참여, token requestor 설정과 lifecycle 운영에 따라 달라진다.

## 참여자와 책임

- Issuer — digitization 승인, account holder 인증, activation 방법 제공, token 상태와 고객 문의 관리
- Token Requestor — merchant, wallet 또는 commerce platform으로서 토큰 발급을 요청하고 정의된 사용 영역에서 사용
- Merchant — 소비자가 입력하거나 card-on-file로 보관한 PAN을 MDES 토큰으로 교체
- PSP·OBOTR — On-Behalf-Of 모델에서 여러 merchant의 tokenization과 transaction 활동을 대신 수행
- Mastercard MDES — PAN–token mapping, token provisioning, 관련 lifecycle 및 참여자 간 연결 제공

## 공식 서비스 지도

| 대상 | 서비스 | 역할 |
| --- | --- | --- |
| Issuer | [MDES Pre-Digitization](https://developer.mastercard.com/mdes-pre-digitization/documentation/) | digitization 전 승인, account holder 인증, activation method·code와 주요 token update 처리 |
| Issuer | [MDES Customer Service](https://developer.mastercard.com/mdes-customer-service/documentation/) | token 검색, 활성화, suspend·resume·update·delete, 상태 이력과 거래 조회 |
| Issuer | [MDES Token Connect](https://developer.mastercard.com/mdes-token-connect/documentation/) | issuer app과 token requestor 사이의 push·pull provisioning 연결 |
| Issuer | [Authentication Facilitator](https://developer.mastercard.com/authentication-facilitator/documentation/) | 이미 provision된 MDES token의 별도 cardholder authentication 지원 |
| Merchant·PSP | [MDES Digital Enablement API](https://developer.mastercard.com/mdes-digital-enablement/documentation/) | merchant card-on-file tokenization, token transaction과 lifecycle 관리 |
| Merchant·PSP | [MDES Bulk Tokenization](https://developer.mastercard.com/mdes-bulk-tokenization/documentation/) | 대량 card-on-file PAN을 암호화 파일로 일괄 tokenization |
| PSP·OBOTR | [Token Requestor Identifier API](https://developer.mastercard.com/token-requestor-identifier-api/documentation/) | merchant별 token domain을 MDES에 onboarding하고 TRID 생성·갱신 |

## 서비스 간 경계

- Pre-Digitization은 token을 사용할 수 있게 되기 전의 승인·인증 단계다.
- Digital Enablement는 merchant 또는 PSP가 PAN을 token화하고 token을 관리하는 실행 인터페이스다.
- Token Connect는 issuer에서 merchant·wallet로 account를 push하거나, wallet에서 issuer로 이동해 account를 선택하는 provisioning 경험을 연결한다.
- Customer Service는 이미 생성된 token의 조회와 운영 수명주기에 초점을 둔다. 공식 문서는 고용량 batch 대체 수단이 아니며 5 TPS 제한을 명시한다.
- Bulk Tokenization은 개별 Tokenize API 호출 대신 대량 card-on-file 전환에 사용하는 file-based 절차다.
- Authentication Facilitator는 digitization activation code와 다른 서비스다. 이미 provision된 token의 인증에 사용되며, 일부 business context는 Mastercard 승인이 필요하다.
- TRID는 OBOTR이 지원하는 consumer-facing token domain을 식별한다. 같은 merchant의 여러 website나 지역 지점이 항상 별도 TRID를 의미하지는 않는다.

## 보안과 운영 관점

- 여러 inbound REST API는 OAuth 1.0a와 RSA request signing을 사용한다.
- PAN·PII가 포함된 API는 TLS 외에 field-level 또는 payload encryption을 요구한다.
- Authentication Facilitator는 issuer가 제공하는 outbound web service에 mutual TLS와 별도 PCI·PII payload encryption을 적용한다.
- private key, encryption key, certificate와 keystore는 문서 예제와 분리해 최소 권한으로 관리해야 한다.
- Sandbox mock, Mastercard Test Facility(MTF), Production은 기능과 credential 경계가 다르다.
- 공식 문서의 endpoint·cipher·환경 표는 변경될 수 있으므로 구현 시 복사본보다 현재 API Reference와 onboarding 자료를 기준으로 재검증한다.

## 2026년 MTF 변경

Mastercard는 2026-07-15 새 MTF 환경을 도입하고 legacy MTF를 중단했다고 공지했다. 영향을 받는 Customer Service, Digital Enablement, Token Connect와 TRID 통합은 MTF에서 sandbox domain과 sandbox credential을 사용해야 한다. Production endpoint·credential과 API contract에는 영향이 없다고 명시했다.

관련 문서: [[2026-07-15 Mastercard MDES MTF Domain Change Notification]]

## 이 프로젝트에서 확인할 관점

- PAN, token, Token Unique Reference(TUR), Payment Account Reference(PAR)와 TRID의 식별자 경계
- token domain과 device·wallet·merchant별 사용 제한
- token activation, suspend, resume, update, delete의 상태 전이와 권한 주체
- card replacement 시 PAN mapping update와 re-digitization 동작
- issuer-initiated push, wallet-initiated pull과 merchant card-on-file provisioning의 차이
- OAuth signing, mTLS, payload encryption, HSM과 key rotation 책임
- Sandbox·MTF·Production의 endpoint, credential과 test data 분리
- 공식 문서의 release history, effective date, API specification과 PDF hash 변경 추적

## 공식 원문

- [MDES 제품 개요](https://developer.mastercard.com/product/mdes/)
- [MDES for Financial Institutions](https://developer.mastercard.com/mdes/product/mdes-issuers/)
- [Card On File Tokenization](https://developer.mastercard.com/mdes/product/mdes-for-merchants/)
- [MTF Domain Change Notification](https://developer.mastercard.com/mdes/documentation/mtf-domain-change-notification/)
