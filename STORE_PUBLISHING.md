# Microsoft Store 배포 가이드

이 문서는 Yonsei Paper Downloader를 Microsoft Store에 게시하기 위한 실제 절차입니다.

일반 사용자는 이 문서를 따라 할 필요가 없습니다.

## 1. Microsoft Store 개발자 계정 만들기

신규 개인 개발자는 Microsoft의 새 온보딩 흐름을 통해 등록비 없이 계정을 만들 수 있습니다.

반드시 다음 주소에서 시작합니다.

https://storedeveloper.microsoft.com/

순서:

1. Get started for free 선택
2. Individual developer 선택
3. 개인 Microsoft 계정으로 로그인
4. 신분증 및 셀피를 이용한 본인 확인
5. 개발자 프로필 작성
6. Partner Center로 이동

개인 개발자 계정은 개인 Microsoft 계정을 사용합니다.

## 2. 앱 이름 예약

Partner Center에서 다음 순서로 진행합니다.

1. Apps & Games
2. New product
3. MSIX or PWA app
4. 원하는 앱 이름 입력
5. 사용 가능 여부 확인
6. Reserve product name

우선 시도할 이름:

Yonsei Paper Downloader

Microsoft Store의 앱 이름은 고유해야 하므로 이미 예약된 이름이면 다른 이름을 선택해야 합니다.

## 3. Product identity 값 확인

앱 이름을 예약한 뒤 해당 제품의 Product identity 정보를 확인합니다.

MSIX 생성에 필요한 값은 정확히 다음 두 개입니다.

- Package/Identity/Name
- Package/Identity/Publisher

예시 모양:

Package/Identity/Name = 12345Publisher.YonseiPaperDownloader

Package/Identity/Publisher = CN=XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXX

예시를 복사하면 안 됩니다. Partner Center에 실제로 표시되는 값을 사용해야 합니다.

## 4. GitHub에서 Store용 MSIX 생성

GitHub 저장소에서 다음 순서로 이동합니다.

1. Actions
2. Build Store MSIX
3. Run workflow

입력값:

- identity_name: Partner Center의 Package/Identity/Name
- publisher: Partner Center의 Package/Identity/Publisher
- publisher_display_name: Store에 표시할 게시자 이름
- version: 처음에는 1.0.0.0

Run workflow를 실행합니다.

작업이 완료되면 해당 workflow 실행 화면 아래의 Artifacts에서 Yonsei-Paper-Downloader-Store-MSIX를 다운로드합니다.

압축을 풀면 Microsoft Store에 제출할 .msix 파일이 들어 있습니다.

이 MSIX는 Store 제출용입니다. 공인 코드서명 인증서를 직접 구매할 필요가 없으며, Store 인증을 통과하면 Microsoft Store가 패키지를 다시 서명합니다.

## 5. Store 제출 정보 준비

Partner Center에서 새 submission을 만들고 다음 항목을 채웁니다.

### Pricing and availability

무료 앱이면 Free로 설정합니다.

### Properties

앱의 실제 기능에 맞는 카테고리와 속성을 선택합니다.

### Age ratings

연구 도구의 실제 콘텐츠에 맞춰 설문에 사실대로 응답합니다.

### Packages

4단계에서 생성한 .msix를 업로드합니다.

### Store listing

일반적으로 다음 항목을 준비합니다.

- 앱 이름
- 짧은 설명
- 상세 설명
- 앱 아이콘
- 최소 1개 이상의 스크린샷
- 지원 URL
- 개인정보 처리방침 URL

개인정보 처리방침:

https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university/blob/main/PRIVACY.md

지원 URL:

https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university/issues

## 6. 권장 Store 문구

짧은 설명:

DOI 목록을 붙여넣어 Wiley 및 Elsevier의 공식 API를 통해 접근 권한이 있는 학술논문 PDF를 간편하게 다운로드합니다.

주요 기능:

- DOI 여러 개 일괄 입력
- Wiley TDM API 지원
- Elsevier API 지원
- 기관 구독 환경에서 접근 가능한 논문 다운로드
- 중복 다운로드 자동 건너뛰기
- 다운로드 진행 상태 표시
- 저장 폴더 바로 열기
- Python, VS Code 또는 Git 설치 불필요

## 7. 제출

필수 항목을 모두 입력한 뒤 Submit for certification을 선택합니다.

문제가 발견되면 Partner Center에 인증 실패 사유가 표시됩니다. 해당 항목을 수정한 뒤 다시 제출하면 됩니다.

## 8. GitHub EXE와 Store MSIX의 차이

GitHub에서 직접 배포하는 미서명 EXE는 Windows SmartScreen 경고가 나타날 수 있습니다.

Microsoft Store에 제출한 MSIX는 인증을 통과한 뒤 Store가 Microsoft 인증서로 서명하므로 일반 사용자가 SmartScreen 경고를 우회하는 방식으로 설치할 필요가 없습니다.

따라서 최종 일반 사용자 배포는 Microsoft Store 링크를 사용하는 것을 권장합니다.
