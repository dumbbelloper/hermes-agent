# 데이터 수집 검증 보고서

> 기준일: 2026-07-24  
> 상태: 초기 범위 품질 게이트 통과 · 수집기 구현 전  
> 대상: Visa, Mastercard, American Express, UnionPay, JCB, EMVCo, PCI Security Standards Council

## 1. 문서 목적

이 문서는 Hermes Agent의 첫 번째 데이터 수집 실험에서 무엇을 실제로 확인했고, 어떤 방식이 안정적이었으며, 무엇을 아직 자동화하면 안 되는지 기록한다.

이번 검증에서는 Obsidian 문서 생성을 먼저 자동화하지 않았다. 양질의 원문을 지속적으로 발견하고, 정확한 메타데이터와 본문을 보존하며, 실패 시 기존 데이터를 잃지 않는 수집 체계를 우선 검증했다.

따라서 이 문서에서 말하는 `품질 게이트 통과`는 다음 의미로 한정한다.

- 초기 핵심 조직의 공식 출처를 빠짐없이 감시할 수 있다.
- 제목, 원문 URL, 게시일, 분류 등 필수 메타데이터를 안정적으로 추출할 수 있다.
- 관련 자료를 자동 제외하여 잃을 위험을 정량적으로 통제할 수 있다.
- 재실행, 중복, 원문 수정, 접근 차단, 파싱 실패 상황에서도 이전 정상 데이터를 보존할 수 있다.

다음 항목까지 완성됐다는 의미는 아니다.

- 모든 출처가 동일한 방식으로 직접 자동 수집된다.
- `collect`, `review`, `exclude` 세 등급을 규칙만으로 정확히 자동 분류한다.
- 확장 범위인 디지털 월렛, 블록체인, 스테이블코인, 국내 카드사를 이미 수집한다.
- 수집 결과가 최종 Obsidian 노트로 자동 발행된다.

## 2. 최종 검증 결과

| 검증 항목 | 결과 | 판정 |
| --- | ---: | --- |
| Source Registry 등록 출처 | 18개 | 목표 범위 15~25개 충족 |
| 활성화되고 검증된 출처 | 15개 | 통과 |
| 글로벌 결제 네트워크 뉴스 | 5/5개 조직 | 통과 |
| EMVCo·PCI SSC 뉴스 및 문서 채널 | 4/4개 | 통과 |
| 정규화한 목록 레코드 | 590건 | 필수 메타데이터 누락 없음 |
| 교차 출처 원문 추출 표본 | 9/9건 | 통과 |
| JCB 2019~2023 원문 추출 | 127/127건 | 통과 |
| 공식 기술 출처 변경 감지 | 6/6개 | 통과 |
| 독립 관련성 검증 표본 | 76건 | 통과 |
| 독립 검증 최소 정밀도 | 94.7% | 기준 90% 이상 |
| 독립 검증 최소 재현율 | 96.4% | 기준 90% 이상 |
| 중복·증분·장애 복구 검사 | 전체 통과 | 통과 |

590건은 다음 세 실험 결과의 합이다.

- Visa, JCB, UnionPay, EMVCo, PCI SSC 구조화 표본: 36건
- American Express 공식 뉴스룸 카테고리: 544건
- Mastercard 최신 보도자료 폴백 표본: 10건

## 3. 초기 출처 범위

### 3.1 글로벌 결제 네트워크

| 조직 | 뉴스·보도자료 | 기술 채널 | GitHub·YouTube | 현재 판단 |
| --- | --- | --- | --- | --- |
| Visa | [공식 Press Releases](https://usa.visa.com/about-visa/newsroom/press-releases-listing.html) | [Developer Release Notes](https://developer.visa.com/site/release_notes), [Use Cases](https://developer.visa.com/use-cases) | [Visa GitHub](https://github.com/visa) | 직접 수집 가능 |
| Mastercard | [공식 Press Releases](https://www.mastercard.com/us/en/news-and-trends/press.html) | [Developer Products](https://developer.mastercard.com/products) | [Mastercard GitHub](https://github.com/Mastercard) | 뉴스는 통제된 폴백 필요 |
| American Express | [공식 Newsroom](https://www.americanexpress.com/en-us/newsroom/) | [Developer Documentation](https://developer.americanexpress.com/documentation) | [American Express GitHub](https://github.com/americanexpress) | 뉴스 모델과 브라우저 스냅샷 사용 가능 |
| UnionPay International | [공식 Media Center](https://www.unionpayintl.com/en/mediaCenter/) | [공식 홈페이지 기술 제품 영역](https://www.unionpayintl.com/en/) | 현재 초기 활성 채널 없음 | 뉴스는 가능, 공개 개발자 URI 미확정 |
| JCB | [공식 Press](https://www.global.jcb/en/press/), [공식 Press JSON](https://www.global.jcb/en/press/news_file.json) | Press JSON의 `PRODUCTS & TECHNOLOGIES` 분류 | [공식 소셜 계정 안내](https://www.global.jcb/ja/policy/social-media/account.html)에서 연결된 YouTube | 구조화 수집 가능, 별도 개발자 허브 미확정 |

### 3.2 결제 표준과 보안

| 조직 | 뉴스 채널 | 기술 문서 | 현재 판단 |
| --- | --- | --- | --- |
| EMVCo | [공식 News RSS](https://www.emvco.com/news/feed/) | [Specifications](https://www.emvco.com/specifications/) | RSS 수집과 문서 변경 감지 가능 |
| PCI Security Standards Council | [공식 Blog RSS](https://blog.pcisecuritystandards.org/rss.xml) | [Document Library](https://www.pcisecuritystandards.org/document_library/) | RSS 수집과 문서 변경 감지 가능 |

## 4. 출처별 수집 방식과 검증 결과

### 4.1 Visa

Visa 보도자료 목록은 정적 HTML에서 최근 항목의 제목, URL, 게시일을 추출할 수 있었다.

개발자 Release Notes와 Use Cases도 정적 스냅샷을 만들 수 있었다. 특히 Release Notes는 API, 인증, 토큰화, HCE, passkey, agentic commerce처럼 기술 변화가 직접 기록되므로 뉴스룸과 별도로 높은 우선순위로 추적할 가치가 있다.

GitHub 조직 전체를 그대로 수집하면 결제와 무관한 저장소가 섞일 수 있다. 따라서 다음처럼 결제·보안·agentic commerce 관련 저장소만 명시적으로 선별하는 방식이 적합하다.

- `visa/trusted-agent-protocol`
- `visa/ai`
- `visa/vic-reference-agent`
- `visa/visa-vulnerability-agentic-harness`
- `visa/mpos.sdk.ios.pods`
- `visa/acceptance-devices-ios-sdk`

### 4.2 Mastercard

Mastercard 보도자료 목록과 개별 원문은 일반 HTTP 클라이언트와 격리된 헤드리스 브라우저에서 Akamai `Access Denied`가 발생했다. 공격적인 우회는 시도하지 않았다.

대신 다음과 같은 통제된 폴백을 검증했다.

1. 검색 인덱스에 노출된 Mastercard 공식 보도자료 목록에서 제목, 게시일, 공식 URL을 발견한다.
2. 각 항목의 Mastercard 공식 원문을 별도로 연다.
3. 뉴스룸 원문이 일시적으로 열리지 않으면 Mastercard Investor Relations의 동일 공식 발표로 교차검증한다.
4. 검색 인덱스 기반 발견이라는 사실과 검증 상태를 레코드에 명시한다.
5. 검색 결과의 최신성이 기준을 넘으면 출처 상태를 `degraded`로 바꾸고 경고한다.

최신 10건 표본에서 다음 결과를 얻었다.

- 제목, URL, 게시일 완전성: 10/10
- Mastercard 뉴스룸 원문 확인: 9/10
- 뉴스룸 타임아웃 후 Mastercard Investor Relations 교차검증: 1/10
- 공식 내용 최종 확인: 10/10

이 방식은 직접 어댑터와 동급으로 간주하지 않는다. 상태는 `validated_controlled_fallback_direct_adapter_blocked`로 분리한다.

Mastercard Developer Products는 HTTP 응답만 보면 JavaScript 셸이지만, 격리된 브라우저에서 89개 제품과 Payments, Security, Open Finance 등의 분류를 확인했다. 정규화한 가시 텍스트 해시도 두 번의 실행에서 동일했다.

### 4.3 American Express

American Express 뉴스룸 홈페이지는 일부 추천 카드만 보여주므로 전체 수집 원본으로 사용하기 어렵다.

공식 AEM 카테고리 모델을 조사한 결과 다음 패턴으로 구조화된 데이터를 받을 수 있었다.

```text
https://www.americanexpress.com/en-us/newsroom/articles/{category}/index.model.json
```

17개 공식 카테고리를 수집한 결과는 다음과 같다.

- 카테고리 성공: 17/17
- 전체 항목: 544건
- 제목 누락: 0건
- URL 누락: 0건
- 게시일 누락: 0건
- 카테고리 누락: 0건
- 검증용으로 미리 정한 필수 기사 발견: 3/3
- 두 번의 정규화 실행 결과 해시 동일

AEM의 `firstPublishDate`는 UTC 기준 날짜이고, 브라우저 표시 날짜는 지역 시간대에 따라 하루 차이가 날 수 있다. 최종 문서화 단계에서는 개별 원문 페이지의 표시 날짜를 다시 확인하고, 차이가 있으면 원문 페이지 날짜를 우선해야 한다.

American Express Developer Documentation도 JavaScript 셸이지만 브라우저 렌더링으로 다음 공개 영역을 확인했다.

- Amex Token Service
- Enhanced Authorization
- Open Banking
- Amex Agentic Commerce Experiences
- API Security
- OAuth와 인증서 관련 문서

American Express GitHub는 공식 조직임을 확인했지만 최근 저장소의 상당수가 범용 엔지니어링 라이브러리였다. 결제 특화 저장소를 선별하기 전까지 초기 자동 수집에서는 비활성화한다.

### 4.4 UnionPay International

UnionPay Media Center의 정적 목록에서 최근 보도자료를 수집할 수 있었다. 표본 4건은 제목, URL, 게시일, 카테고리가 모두 존재했고 선택한 개별 원문도 정상 추출됐다.

공식 홈페이지에는 기술 제품 영역이 존재하지만 현재 사용 가능한 공개 개발자 포털 URI는 확인하지 못했다. 과거 공식 발표에서 UPI Developer가 언급됐다는 사실만으로 현재 엔드포인트를 추정하거나 등록하지 않는다.

따라서 초기 운영은 다음과 같이 제한한다.

- Media Center는 활성화한다.
- 공식 홈페이지의 기술 영역은 페이지 변경 감지만 수행한다.
- 공개 개발자 URI가 확인되기 전에는 API 문서 수집이 가능하다고 표시하지 않는다.

### 4.5 JCB

JCB는 공식 Press JSON이 가장 안정적인 목록 원본이었다.

```text
https://www.global.jcb/en/press/news_file.json
```

JSON에는 연도별 제목, 게시일, 카테고리, 파일명이 포함되어 있어 증분 수집과 시간축 검증에 적합하다.

2019년부터 2023년까지 127건의 공식 원문을 가져온 결과:

- HTTP 200: 127/127
- 본문 추출 가능: 127/127
- 제목 핵심어 원문 포함률: 127/127
- HTML과 PDF 모두 처리 가능
- 가장 짧은 정상 본문도 품질 기준을 충족

PDF 원문은 HTML처럼 디코딩하지 않고 `pdftotext` 계열의 별도 추출기를 사용해야 한다.

JCB 공식 YouTube 채널은 공식 소셜 계정 안내 페이지에서 연결 관계를 확인했다. 그러나 실험 당시 최근 피드가 2025-05-28에서 멈췄고 콘텐츠도 마케팅 중심이어서 초기 수집에서는 비활성화한다.

### 4.6 EMVCo와 PCI SSC

EMVCo와 PCI SSC는 공식 RSS가 있어 신규 뉴스 탐지에 가장 적합한 형태였다.

규격과 문서 라이브러리는 목록의 정규화된 텍스트, 문서 URL, 버전, 수정일, 파일 해시를 비교하는 방식이 적합하다. 단순히 페이지 전체 해시만 비교하면 메뉴나 배너 변경도 기술 변경으로 오인할 수 있으므로, 실제 구현에서는 항목 단위 파서가 추가로 필요하다.

## 5. 메타데이터와 원문 품질

### 5.1 공통 필수 필드

수집 레코드에는 최소한 다음 필드가 필요하다.

```yaml
source_id: "visa-press"
organization: "Visa"
channel: "press"
title: "원문 제목"
url: "https://official.example/article"
published_at: "2026-07-24"
official: true
discovery_method: "official_static_listing"
discovered_at: "2026-07-24T09:00:00+09:00"
```

폴백이나 브라우저 렌더링을 사용했다면 다음 정보도 남긴다.

```yaml
discovery_confidence: "controlled_fallback"
verification_status: "official_page_verified"
verification_url: "https://official.example/mirror"
```

### 5.2 URL 정규화

검증한 정규화 규칙은 다음과 같다.

- scheme과 host는 소문자로 변환한다.
- 기본 포트와 fragment를 제거한다.
- 경로 끝의 불필요한 `/`를 정리한다.
- `utm_*`, `fbclid`, `gclid` 같은 추적 파라미터만 제거한다.
- 의미 있는 query parameter는 삭제하지 않고 정렬한다.
- 같은 입력을 여러 번 정규화해도 결과가 달라지지 않아야 한다.

모든 query parameter를 제거하면 서로 다른 문서를 하나로 합칠 수 있으므로 금지한다.

### 5.3 중복 판정

중복은 한 가지 기준으로 판단하지 않는다.

1. 정규화한 canonical URL
2. 출처가 제공하는 외부 ID
3. 원문 URL 기반 안정 ID
4. 본문 해시
5. 필요할 때만 제목 유사도

동일 본문이 다른 URL로 노출되면 `duplicate_content`로 분리하고, 먼저 수집한 정상 레코드를 보존한다.

## 6. 관련성 분류 검증

### 6.1 분류 목적

관련성 분류의 첫 번째 목적은 중요한 자료를 자동으로 버리지 않는 것이다. 초기 단계에서는 문서 수를 줄이는 것보다 데이터 손실을 막는 것이 우선이다.

세 등급은 다음 의미로 사용한다.

- `collect`: 결제 인프라, 수용망, 처리, 인증, 보안, 표준, 디지털 화폐 등 학습 가치가 명확하다.
- `review`: 사업·시장·상품 동향 가치가 있지만 기술 학습 우선순위는 사람 또는 의미 모델의 판단이 필요하다.
- `exclude`: 행사, 기부, 단순 프로모션, 브랜드 홍보처럼 현재 목적과의 관련성이 낮다.

### 6.2 규칙 기반 분류의 한계

처음에는 제목 키워드 규칙으로 세 등급을 자동화하려 했다. 보정 데이터에서는 높은 정확도를 만들 수 있었지만, 과거 연도의 미사용 데이터에 적용할 때 표현 방식이 달라지면서 `collect` 항목이 대량으로 `review`로 이동했다.

시간축 독립 검증 결과는 다음과 같다.

| 검증셋 | 표본 | 관련 항목 정밀도 | 관련 항목 재현율 | 세 등급 정확도 | 검토 큐 비율 |
| --- | ---: | ---: | ---: | ---: | ---: |
| 2021년 E | 26건 | 96.2% | 100.0% | 76.9% | 50.0% |
| 2020년 F | 29건 | 96.4% | 96.4% | 48.3% | 62.1% |
| 2019년 G | 21건 | 94.7% | 100.0% | 47.6% | 61.9% |

여기서 `관련 항목`은 `collect + review`를 하나로 묶은 값이다.

이 결과는 다음 두 가지를 동시에 보여준다.

1. 관련 데이터를 보존하고 명백히 무관한 자료만 제외하는 안전성은 90% 기준을 통과했다.
2. `collect`와 `review`를 규칙만으로 정확히 나누는 자동 우선순위 기능은 운영에 사용할 수준이 아니다.

### 6.3 초기 운영 결정

- `collect`와 `review`는 모두 저장한다.
- 자동 제외는 제목에 명시적인 고신뢰 근거가 있는 경우로 제한한다.
- 알 수 없는 항목은 제외하지 않고 `review`로 보낸다.
- 카테고리 이름만으로 제외하지 않는다.
- `collect/review` 자동 우선순위는 본문 기반 의미 모델과 별도 정답셋을 검증한 후 도입한다.
- 의미 모델을 도입하더라도 판단 라벨, 근거 문장, 모델 버전, 신뢰도와 검토 여부를 함께 저장한다.

규칙을 계속 추가해 과거 검증셋 점수만 높이는 방식은 중단한다. 보정셋 성능과 미사용 시간축 검증 성능을 반드시 구분해야 한다.

## 7. 증분 실행과 장애 대응

### 7.1 증분 처리 검증

36건의 구조화 표본으로 다음 시나리오를 확인했다.

| 시나리오 | 결과 |
| --- | ---: |
| 최초 실행 | 신규 36건 |
| 동일 입력 재실행 | 변경 없음 36건 |
| 한 항목 제목 변경 | 수정 1건, 변경 없음 35건 |
| 잘못된 날짜 | 격리 |
| 허용되지 않은 도메인 | 격리 |
| 동일 실행 내 ID 충돌 | 격리 |
| 다른 URL의 동일 본문 | `duplicate_content` |
| 실패 이후 기존 상태 | 36건 보존 |

### 7.2 실패 분류

| 실패 | 처리 |
| --- | --- |
| HTTP 403 | `access_blocked`, 공격적 재시도 금지, 승인된 폴백 검토 |
| HTTP 429 | `transient`, `Retry-After` 존중 |
| HTTP 5xx | `transient`, 제한된 지수 백오프와 jitter |
| HTTP 404·410 | 기존 레코드 보존 후 `unavailable` 표시 |
| DNS·timeout | `transient`, 제한 재시도 |
| 파싱 실패 | `adapter_degraded`, 응답 격리, 이전 정상 상태 보존 |
| 예상치 못한 빈 목록 | 성공으로 덮어쓰지 않고 `degraded` |

같은 출처에서 일시 오류가 연속 세 번 발생하면 `unhealthy`로 전환한다. 접근 차단과 어댑터 파손은 첫 발생부터 경고한다. 이후 정상 실행이 확인되면 실패 카운터를 초기화한다.

## 8. Source Registry 운영 기준

각 출처는 최소한 다음 정보를 가져야 한다.

```yaml
id: "mastercard-press"
organization: "Mastercard"
channel: "press"
uri: "https://www.mastercard.com/us/en/news-and-trends/press.html"
method: "search_index_of_official_listing_with_official_page_verification"
status: "validated_controlled_fallback_direct_adapter_blocked"
enabled: true
priority: 1
freshness_days: 14
```

`status`는 단순한 완료 체크가 아니다. 다음 차이를 보존해야 한다.

- 직접 구조화 수집 검증 완료
- 정적 스냅샷 변경 감지 검증 완료
- 브라우저 스냅샷 검증 완료
- 통제된 폴백만 검증 완료
- 공식 URI만 확인
- 낮은 가치 또는 비활성으로 제외
- 어댑터 파손 또는 접근 차단

출처마다 발행 주기가 다르므로 동일한 freshness 기준을 적용하지 않는다.

## 9. 초기 운영 안전 원칙

1. 공식 원문을 우선한다.
2. 원문 전체를 Vault에 복제하지 않고 링크, 메타데이터, 자체 요약과 학습 키워드를 저장한다.
3. `collect`와 `review`는 모두 보존한다.
4. 자동 제외는 고신뢰 규칙으로 제한한다.
5. 빈 응답이나 파싱 실패로 이전 정상 데이터를 덮어쓰지 않는다.
6. 브라우저와 검색 인덱스 방식은 일반 수집기가 아니라 격리된 폴백으로 운영한다.
7. 모든 폴백 레코드에 발견 방식과 검증 상태를 남긴다.
8. 원문 수정은 새 문서 생성보다 변경 이력 보존을 우선한다.
9. 샘플 보정 성능과 미사용 검증 성능을 분리해 보고한다.
10. 검증되지 않은 확장 범위를 초기 품질 게이트에 포함된 것처럼 표시하지 않는다.

## 10. 알려진 한계

### 운영상 허용한 한계

- Mastercard 뉴스룸은 직접 자동 수집이 차단되어 공식 검색 인덱스 폴백이 필요하다.
- `collect/review` 세부 우선순위는 아직 자동화하지 않는다.
- UnionPay의 현재 공개 개발자 포털 URI는 확인되지 않았다.
- JCB는 공개 개발자 문서 허브 대신 공식 기술 보도 카테고리로 보완한다.
- YouTube는 초기 핵심 데이터에 비해 신호 대비 잡음이 커서 비활성화했다.
- GitHub는 조직 전체가 아니라 결제 관련 저장소만 선별한다.

### 아직 검증하지 않은 확장 범위

- Apple Pay
- Samsung Wallet·Samsung Pay
- Google Pay·Google Wallet
- HCE, NFC, Passkey 등 기술 주제별 독립 출처
- Ethereum
- Solana
- 스테이블코인 발행사와 인프라
- 국내 카드사, VAN, PG, 간편결제 사업자
- 규제기관과 전문 뉴스

## 11. 구현 권장 순서

### 다음 단계 1 — 재현 가능한 수집기

- Source Registry를 프로젝트 파일로 확정한다.
- Visa, JCB, EMVCo, PCI SSC 직접 어댑터를 먼저 구현한다.
- American Express AEM 어댑터를 추가한다.
- Mastercard 검색 인덱스 폴백은 별도 모듈과 상태 경고로 격리한다.
- 원시 응답 해시, 체크포인트, 마지막 정상 상태를 저장한다.

### 다음 단계 2 — Inbox 초안

- `collect`와 `review`를 모두 `Inbox/`에 생성한다.
- 제목은 원문 제목을 그대로 사용한다.
- 원문 링크, 게시일, 출처, 수집 방식, 검증 상태를 필수로 기록한다.
- 요약과 기술 키워드는 원문 근거를 인용할 수 있을 때만 생성한다.

### 다음 단계 3 — 의미 기반 우선순위

- 서로 다른 조직과 연도를 포함한 독립 정답셋을 만든다.
- 제목뿐 아니라 본문, 카테고리, 출처 신뢰도를 함께 사용한다.
- `collect`, `review`, `exclude`별 정밀도와 재현율을 따로 측정한다.
- 미확실 항목을 자동 제외하지 않는 abstention 정책을 유지한다.
- 모델 변경 때마다 시간축 회귀 테스트를 실행한다.

### 다음 단계 4 — 범위 확장

초기 수집기를 안정화한 후 [SOURCE_SCOPE_CHECKLIST.md](./SOURCE_SCOPE_CHECKLIST.md)의 확장 후보를 한 묶음씩 추가한다. 각 묶음은 기존과 동일하게 공식 출처 확인, 메타데이터 검증, 원문 추출, 중복, 관련성, 장애 복구 게이트를 통과해야 한다.

## 12. 이번 검증에서 내린 핵심 결정

1. 초기 Source Registry는 18개 출처로 시작한다.
2. 뉴스와 기술 문서를 같은 어댑터로 처리하지 않는다.
3. 직접 HTTP, 공식 JSON·RSS, 정적 HTML, 브라우저, 검색 인덱스 폴백을 명시적으로 구분한다.
4. 데이터 보존과 자동 우선순위 정확도를 서로 다른 품질 지표로 관리한다.
5. `collect/review`는 모두 보존하고 자동 제외만 보수적으로 허용한다.
6. 이전 정상 상태 보존을 신규 스냅샷 저장보다 우선한다.
7. YouTube와 범용 GitHub 활동량보다 공식 기술 문서와 표준 변경을 먼저 추적한다.
8. 확장 범위는 초기 수집기의 운영 품질이 확인된 후 추가한다.

이 결정은 [PROJECT_PLAN.md](./PROJECT_PLAN.md)의 Phase 0 설계를 실제 데이터로 검증한 결과이며, 다음 구현 단계의 기준선으로 사용한다.
