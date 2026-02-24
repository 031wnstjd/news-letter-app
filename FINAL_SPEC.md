# Final Specification (Interview Consolidated)

- Date: 2026-02-24
- Scope: AI/개발 트렌드 일간 뉴스레터 MVP

## 1) PRD 요약

### 1.1 제품 1문장 정의
빠르게 뜨는 AI/개발 이슈를 놓치지 않게 압축 전달하는 데일리 브리핑.

### 1.2 타깃 사용자
- 기준 페르소나: 실무 개발자(중급)
- 경력 범위: 3~7년

### 1.3 핵심 가치
- 빠른 파악: 5분 내 핵심 흐름 이해
- 실무 연결: 각 아이템에 적용 맥락 제공
- 신뢰 가능한 선별: 소스/랭킹/검증 정책 기반 큐레이션

### 1.4 MVP 포함/제외
- 포함
  - 평일 09:00(KST) 발송, 8개 고정
  - 수집(RSS 우선, HTML 보조), 중복 제거, 점수 기반 선정
  - 요약 생성 + 중간 검증(핵심 주장 대조)
  - Multipart 이메일(HTML+Text), 더블 옵트인
  - 클릭 추적, 90일 보관
- 제외
  - 행동 기반 개인화 랭킹
  - 운영자 수동 승인/편집
  - List-Unsubscribe/One-Click 헤더

## 2) 확정 정책 (결정사항)

### 2.1 뉴스레터 UX/콘텐츠
- 에디션: 단일 에디션(비개인화)
- 카테고리: 6개
  - LLM/Agent, Backend, Frontend, Infra/MLOps, Data, Security
- 1회 아이템 수: 8개 고정
- 배치 규칙
  - 상단 2개: 핫이슈, 서로 다른 카테고리 강제
  - 하단 6개: 최소 4개 카테고리 커버 강제, 나머지 점수순
- 월요일 규칙: 8개 유지 + 주말 브리프 2개 슬롯
- 요약 포맷(기본): TL;DR 2줄 + 왜 중요한가 1줄 + 실무 적용 1줄
- 언어: 한국어 본문 + 원문 용어 병기
- 링크 표기: source 도메인 배지
- 링크 동작: `go.<root>` 즉시 302 리다이렉트 추적
- 아이템 부족 시: 상단 간단 배지로 통과 개수 고지

### 2.2 발송/구독
- 발송 시간/빈도: 평일 09:00(KST)
- 정시 원칙: 09:00 무조건 발송(완전 정시), 미완료 아이템 즉시 제외
- 가입: 더블 옵트인 필수
- 구독 설정 UI: 최소 제공(관심 카테고리 저장만, 랭킹 미반영)
- 추적: 클릭만 수집, 90일 보관
- 프로바이더: Resend(단일)
- 도메인 분리: `verify.<root>`, `newsletter.<root>`
- 한도 초과 시: 기존 구독자 우선, 신규는 대기열
  - 대기열 순서: 더블 옵트인 완료 시각 FIFO
  - 대기열 안내: 즉시 안내 메일 + 예상 활성화 시점은 상대시간

### 2.3 소스/신뢰/정책
- 소스 철학: 공식 소스 + 커뮤니티/큐레이션 병행
- 다양성 제약: 동일 조직 최대 3개, 초과는 추가 읽을거리로 강등
- 공신력 운영: 유형 무관 포함 가능(영향도 기반), 신뢰 표시는 중노출
- 상업성 패널티: 강 적용
  - 예외 완화: 공식 기술 문서 + 재현 코드 동시 충족 시 패널티 50% 완화
- 커뮤니티 신호 반영: Impact에 소량 가산
  - 총점 가산 상한: +15%
  - 1차 소스 미존재 시: 커뮤니티 가산 50% 감쇠
  - 시간 감쇠: 48시간 반감
- 커뮤니티 링크: 메인 링크 허용

### 2.4 수집/정제/중복
- 수집 우선순위: RSS/Atom 우선 + HTML 보조
- 중복 제거: 혼합
  - canonical URL 동일 시 즉시 병합
  - 그 외 임베딩 유사도 + 엔터티 일치로 병합
  - 유사도 임계치: 0.86
- 링크 내구성: 발송 전 전체 링크 HEAD/GET 검증, 실패 시 자동 대체

### 2.5 랭킹/선정
- 시간 모델: 이중 창
  - 속보 창(0~24h) : 검증 창(24~96h) = 6 : 4
- 후보 부족 시: 하이브리드 정책, 최소 보장 3개까지 하한 완화
- 초기 가중치(신뢰형)
  - Recency 0.20
  - Authority 0.40
  - Impact 0.30
  - CommercialPenalty 0.10

### 2.6 요약/검증
- 검증 수준: 중간 검증
  - 핵심 주장 문장 대조
  - 불일치 문장 제거
- 모델 전략: 단일 상용 API
- 장애 시: 요약 실패 아이템 엄격 제외

### 2.7 기술 아키텍처/운영
- 실행 방식: 큐 기반 워커
- 백엔드 스택: Python(FastAPI) + Celery + Redis
- DB: Postgres
- 배포: 단일 VM + Docker Compose
- 발송 멱등성: `campaign_id + subscriber_id` 유니크 키 강제
- 이메일 포맷: Multipart(HTML + Text)
- 반송 정책
  - 하드바운스 1회 즉시 중단
  - 소프트바운스 3회 누적 중단
- 피드백: 메일 하단 전체 만족도 1개
- 해지 데이터: 30일 유예 보관 후 삭제

## 3) 소스 리스트/정책

상세 구조는 [sources.yaml](/home/junsung/vibe_coding/news-letter/sources.yaml)에 반영.

### 3.1 공식 블로그/공식 소스 (10)
- openai.com
- research.google
- anthropic.com
- ai.meta.com
- news.microsoft.com
- aws.amazon.com
- github.blog
- kubernetes.io
- developer.chrome.com
- arxiv.org

### 3.2 커뮤니티/큐레이션 (11)
- news.ycombinator.com
- lobste.rs
- reddit.com/r/programming
- reddit.com/r/MachineLearning
- reddit.com/r/devops
- techmeme.com
- slashdot.org
- dev.to
- daily.dev
- producthunt.com/topics/developer-tools
- yozm.wishket.com

## 4) 이메일 템플릿 샘플

### 샘플 A: 평일 일반판
- Subject
  - `[AI/Dev Daily] 2026-02-24 09:00 KST - 오늘의 핵심 8개`
- Body 구조
  - 상단 배지: `오늘은 검증 통과 8개 발행`
  - Hot Issue 2개(서로 다른 카테고리)
  - 카테고리 균형 6개(최소 4카테고리)
  - 각 아이템: TL;DR 2줄 + 왜 중요한가 + 실무 적용 + source 도메인
  - 하단: 만족도 1문항, 해지 링크

### 샘플 B: 월요일 압축판
- Subject
  - `[AI/Dev Daily] 2026-02-29 09:00 KST - 주말 브리프 포함 8개`
- Body 구조
  - 상단 배지: `오늘은 주말 브리프 2개 포함`
  - Hot Issue 2개
  - Weekend Brief 2개
  - 나머지 4개는 점수/카테고리 준균형 규칙 적용
  - 하단 동일

## 5) 시스템 아키텍처 (텍스트 다이어그램)

### 5.1 수집 파이프라인
`Source Registry(sources.yaml) -> RSS Fetcher -> HTML Fallback Fetcher -> Normalizer -> Canonicalizer -> Language/Metadata Extractor -> Raw Item Store`

### 5.2 랭킹/요약 파이프라인
`Raw Item -> Dedup Engine(URL + Similarity 0.86 + Entity) -> Scoring Engine(Recency/Authority/Impact/Penalty) -> Slot Allocator(Top2 + Bottom6 Rules) -> Summarizer -> Claim Verifier -> Candidate Set`

### 5.3 발송 파이프라인
`Candidate Set -> Link Validator(HEAD/GET) -> Campaign Composer(HTML+Text) -> Delivery Queue -> Resend API -> Delivery/Bounce Tracker -> Metrics Store`

## 6) 데이터 모델 초안

- Source(id, name, domain, trust_tier, fetch_type, rss_url, enabled, tags, lang)
- Item(id, source_id, url, canonical_url, title, author, published_at, fetched_at, raw_content_ref, lang, category, keywords, hash, dedup_group_id)
- RankedItem(id, item_id, score, score_breakdown_json, day)
- Summary(id, item_id, tldr, bullets_json, caveats, model_info, created_at)
- Subscriber(id, email, status, preferences_json, created_at, verified_at, unsub_token)
- Campaign(id, day, subject, html_body_ref, text_body_ref, created_at)
- Delivery(id, campaign_id, subscriber_id, status, provider_message_id, sent_at, bounce_at, complaint_at, open_count, click_count)

## 7) MVP 백로그 (우선순위/일정 단위)

### P0 (필수, 2주)
- 소스 레지스트리 + RSS 수집기 + HTML 보조 수집기
- canonicalize + dedup(혼합, 0.86)
- 점수 엔진 + 슬롯 할당(Top2/Bottom6 규칙)
- 요약 생성 + 중간 검증
- 링크 사전 검증 + 자동 대체
- 캠페인 생성(HTML+Text) + Resend 발송
- 더블 옵트인 + 해지 링크
- 클릭 추적 + 90일 보관
- 반송 억제 정책 적용

### P1 (다음, 1~2주)
- 월요일 압축판 로직
- 대기열 운영(무료 티어 초과 대응) + 안내 메일
- 만족도 1문항 수집 대시보드
- 리포팅(발송성공률/클릭률/바운스율/스팸율)

### P2 (고도화)
- 개인화 랭킹 활성화(저장된 관심 카테고리 반영)
- List-Unsubscribe/One-Click 헤더 지원
- 다중 모델/다중 프로바이더 페일오버
- 어드민 큐레이션 도구

## 8) 우려 사항/트레이드오프

- 커뮤니티 링크 메인 허용
  - 장점: 속도/화제성
  - 리스크: 원문 부재/변질 가능성
  - 완화: 링크 사전 검증, 커뮤니티 가산 상한/감쇠
- 완전 정시(09:00 고정)
  - 장점: 신뢰 가능한 습관
  - 리스크: 일부 고품질 아이템 누락
  - 완화: 간단 배지로 투명 고지
- 단일 프로바이더(Resend)
  - 장점: 초기 단순화
  - 리스크: 공급자 장애/한도
  - 완화: 신규 대기열 정책, 발송 멱등성, 도메인 분리

## 9) 미결사항/가정

### 미결사항
- 단일 상용 요약 API의 구체 벤더/모델명
- 약관/개인정보처리방침 페이지 공개 시점
- 금칙 키워드/제외 소스 세부 목록

### 가정
- 초기 MVP 구독자 규모는 Resend 무료/저비용 구간 내에서 시작
- 소스 다수는 RSS 제공, 미제공 소스는 HTML 보조 수집으로 대응 가능
