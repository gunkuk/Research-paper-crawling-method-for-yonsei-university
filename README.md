# 연세대학교 VPN 기반 학술논문 자동 다운로드

**Yonsei Paper Downloader**는 DOI 목록을 붙여넣으면 Wiley와 Elsevier의 공식 API를 통해 접근 권한이 있는 논문 PDF를 자동으로 내려받는 Windows 앱입니다.

---

## 준비물

처음 한 번만 아래 설명에 따라 세 가지를 준비합니다.

1. 연세대학교 **YSVPN**
2. **Wiley TDM Token**
3. **Elsevier API Key**


---

## 1. YSVPN 설치 및 연결

교외에서 사용할 경우 먼저 연세대학교 VPN에 연결합니다.

1. 아래 페이지에 접속합니다.
   - https://ysvpn.yonsei.ac.kr
2. 운영체제에 맞는 VPN 프로그램을 설치합니다.
3. YSVPN을 실행합니다.
4. **연세포탈 ID / 비밀번호**로 로그인합니다.
5. VPN 연결을 유지합니다.

설치 방법:
- YSVPN 사용자 매뉴얼: https://ibook.yonsei.ac.kr/Viewer/ysvpn_user_manual
- 연세대학교 공식 안내: https://ilis2.yonsei.ac.kr/ics/service/PolicyApplyInfo.do

---

## 2. Wiley TDM Token 발급

1. 아래 Wiley 페이지에 접속합니다.
   - https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
2. Wiley 계정으로 로그인합니다.
3. **Get a Text and Data Mining Token**을 선택하고 이용조건에 동의합니다.
4. 발급된 **Wiley TDM Token**을 복사해 둡니다.

이 값은 앱을 처음 실행할 때 한 번 입력합니다.

---

## 3. Elsevier API Key 발급

1. 아래 Elsevier Developer Portal에 접속합니다.
   - https://dev.elsevier.com/
2. 로그인합니다.
3. API Key를 생성합니다.
4. 발급된 **Elsevier API Key**를 복사해 둡니다.

이 값도 앱을 처음 실행할 때 한 번 입력합니다.

---

## 4. 앱 설치

### 현재 개발 테스트 단계

현재 GitHub Releases의 설치파일은 기능 확인을 위한 **개발 테스트용 빌드**입니다.

- https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university/releases/latest

공인 코드서명이 없는 테스트 빌드이므로 Windows SmartScreen 경고가 표시될 수 있습니다. 따라서 일반 사용자에게는 이 방식을 최종 배포 경로로 사용하지 않습니다.

### 최종 공개 배포

최종 버전은 **Microsoft Store의 서명된 MSIX 패키지**로 배포하는 것을 목표로 합니다.

Store 게시가 완료되면 이 섹션을 Microsoft Store 설치 링크로 교체합니다.

개발 테스트용 설치를 완료한 경우 바탕화면에 다음 바로가기가 만들어집니다.

```text
Yonsei Paper Downloader
```

---

## 5. 처음 한 번만 API 키 입력

바탕화면의 **Yonsei Paper Downloader**를 더블클릭합니다.

처음 실행하면 **API 키 설정** 창이 자동으로 열립니다.

### Wiley TDM Token

2단계에서 발급받은 **Wiley TDM Token 값만** 붙여넣습니다.

### Elsevier API Key

3단계에서 발급받은 **Elsevier API Key 값만** 붙여넣습니다.

두 값을 모두 넣은 뒤:

```text
저장
```

버튼을 누릅니다.

이 설정은 해당 Windows 사용자 계정에 저장되므로 다음 실행부터 다시 입력할 필요가 없습니다.

API 키를 변경하려면 앱 오른쪽 위의 **API 키 설정** 버튼을 누르면 됩니다.

---

## 6. DOI 붙여넣기

다운로드할 DOI를 한 줄에 하나씩 준비합니다.

예:

```text
10.1016/j.ibusrev.2010.09.002
10.1002/asi.10389
```

필요한 DOI는 일반적으로 GPT와 같은 자연어 모델에 아래의 명령을 입력하여 쉽게 구할 수 있습니다.

"아래 논문들의 DOI를 다음과 같은 형식으로 list-up 해줘.
10.1016/j.ibusrev.2010.09.002
10.1002/asi.10389
(다운 받고자 하는 논문들의 설명)"

이렇게 GPT, Excel, 메모장, 논문 목록 등에서 DOI 여러 개를 복사한 뒤 앱에서:

```text
클립보드에서 붙여넣기
```

버튼을 누르면 됩니다.
중복 DOI는 한 번만 처리됩니다.

---

## 7. 논문 다운로드

다운로드 전에 **YSVPN이 연결되어 있는지 확인**합니다.

앱에서:

```text
다운로드 시작
```

버튼을 누릅니다.

앱이 DOI를 순서대로 확인하고 Wiley 또는 Elsevier의 공식 API를 통해 다운로드합니다.

진행 상황은 앱 아래쪽에 표시됩니다.

예:

```text
[1/20] 10.xxxx/xxxxx
  다운로드 완료: 정상 다운로드
```

---

## 8. 다운로드된 PDF 확인

기본 저장 위치는 Windows의 다운로드 폴더 안입니다.

```text
Downloads\Yonsei Paper Downloader
```

앱에서:

```text
다운로드 폴더 열기
```

버튼을 누르면 바로 열립니다.

저장 위치를 바꾸고 싶으면 앱의 **변경** 버튼을 누릅니다.

---

## 9. 다음부터 사용할 때

처음 설정을 끝낸 뒤에는 아래 세 단계만 반복하면 됩니다.

1. **YSVPN 연결**
2. 바탕화면의 **Yonsei Paper Downloader** 실행
3. DOI 붙여넣기 → **다운로드 시작**

API Token/Key 발급, 프로그램 설치, 설정 작업은 다시 할 필요가 없습니다.

---

## 상태 메시지 의미

| 상태 | 의미 |
|---|---|
| 다운로드 완료 | PDF 다운로드 성공 |
| 이미 받은 파일 | 같은 PDF가 이미 있어서 건너뜀 |
| 지원하지 않는 출판사 | Wiley 또는 Elsevier 논문이 아님 |
| DOI를 찾지 못함 | DOI가 잘못되었거나 조회되지 않음 |
| 접근 권한 확인 필요 | API Key, 기관 구독 또는 접근 권한 문제 |
| API 요청 제한 | 출판사가 허용한 요청 횟수 제한에 걸림 |
| 오류 | 네트워크 등 기타 오류 |

---

## 문제가 생겼을 때

### Wiley 403

Wiley TDM API가 `403`을 반환하면 Wiley가 현재 TDM Token을 유효한 등록 Token으로 인정하지 않은 경우입니다.

1. 앱의 **API 키 설정**에서 Wiley TDM Token이 최신 값인지 확인합니다.
2. Wiley TDM 페이지에서 Token을 재발급한 경우 앱에도 새 Token을 다시 저장합니다.
3. 이전 Token이 Windows 환경변수 등에 남아 있더라도 앱/로컬 설정의 최신 값을 사용하도록 구현되어 있습니다.

### Wiley 404

Wiley TDM API가 `404`를 반환하면 DOI 또는 해당 콘텐츠의 접근 권한을 확인합니다.

기관 구독 콘텐츠라면 **YSVPN/교내 네트워크 연결 상태**도 확인합니다.

### Elsevier 403

Elsevier Article Retrieval API가 `403`을 반환한다고 해서 곧바로 "연세대학교가 해당 논문을 구독하지 않는다"는 뜻은 아닙니다.

API Key 자체가 유효해도 **developer account, Article Retrieval resource 설정, TDM entitlement 또는 institutional authorization** 문제로 403이 발생할 수 있습니다.

앱은 가능한 경우 Elsevier가 반환한 원문 오류 메시지도 함께 표시합니다.

### API 요청 제한

출판사의 API 요청 횟수 제한에 걸린 경우입니다.

잠시 후 다시 **다운로드 시작**을 누르면 됩니다.

이미 받은 PDF는 자동으로 건너뜁니다.

### 일부 DOI만 다시 받고 싶음

입력창을 **전체 지우기**한 뒤 필요한 DOI만 다시 붙여넣고 실행하면 됩니다.

---

## 보안 및 이용 주의

- Wiley TDM Token과 Elsevier API Key는 다른 사람과 공유하지 마십시오.
- 앱에 저장한 키는 현재 Windows 사용자 계정의 설정 폴더에 저장됩니다.
- 본인의 연세대학교 계정과 기관 구독 권한 범위에서 사용하십시오.
- 다운로드된 원문의 이용·저장·분석·공유는 해당 출판사와 기관의 라이선스 조건을 따라야 합니다.
- 이 프로그램은 Wiley와 Elsevier의 공식 API를 사용하며 출판사 웹페이지 자체를 크롤링하지 않습니다.

---

## 개발자용

일반 사용자는 이 부분을 볼 필요가 없습니다.

주요 파일:

```text
paper_downloader_app.py    Windows GUI
download_papers.py         다운로드 엔진
installer.iss              Windows 설치파일 설정
tests/                     단위 테스트
.github/workflows/         Windows 자동 빌드
```

GitHub Actions가 Windows에서 테스트 후 실행파일과 설치파일을 자동으로 빌드합니다.

Microsoft Store 배포 절차는 [STORE_PUBLISHING.md](STORE_PUBLISHING.md)를 참고합니다.

개인정보 처리방침은 [PRIVACY.md](PRIVACY.md)에 정리되어 있습니다.

---

## 공식 링크

### 연세대학교
- YSVPN: https://ysvpn.yonsei.ac.kr
- YSVPN 사용자 매뉴얼: https://ibook.yonsei.ac.kr/Viewer/ysvpn_user_manual
- YSVPN 공식 안내: https://ilis2.yonsei.ac.kr/ics/service/PolicyApplyInfo.do

### Wiley
- Wiley Text and Data Mining: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining

### Elsevier
- Elsevier Developer Portal: https://dev.elsevier.com/
