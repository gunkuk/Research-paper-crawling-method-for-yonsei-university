# 연세대학교 VPN 기반 Wiley·Elsevier 논문 자동 다운로드

DOI 목록을 입력하면 **Wiley TDM API**와 **Elsevier Article Retrieval API**를 이용해 접근 권한이 있는 논문의 원문 PDF를 자동으로 저장하는 도구입니다.

> 핵심 흐름: **YSVPN 설치·연결 → Wiley/Elsevier API 발급 → API 키 입력 → DOI 목록 준비 → 자동 다운로드**

이 저장소는 출판사 웹페이지를 크롤링하지 않습니다. Wiley와 Elsevier가 제공하는 **공식 API만 사용**하며, 다운로드 가능 여부는 본인의 기관 구독 권한과 각 출판사의 API 정책에 따릅니다.

---

## 1. YSVPN 설치 및 연결

연세대학교 정보통신처는 교외에서 YSVPN을 사용하면 논리적으로 교내 네트워크를 이용하는 것과 같은 환경을 제공한다고 안내합니다.

### 설치

1. 아래 연세대학교 YSVPN 페이지에 접속합니다.
   - https://ysvpn.yonsei.ac.kr
2. 운영체제에 맞는 VPN 클라이언트를 다운로드하여 설치합니다.
3. 자세한 설치 방법은 공식 사용자 매뉴얼을 따릅니다.
   - https://ibook.yonsei.ac.kr/Viewer/ysvpn_user_manual

### 실행

1. YSVPN 클라이언트를 실행합니다.
2. **연세포탈 ID / 비밀번호**로 로그인합니다.
3. VPN 연결이 완료된 상태에서 아래 다운로드 스크립트를 실행합니다.

연세대학교 공식 안내:
- https://ilis2.yonsei.ac.kr/ics/service/PolicyApplyInfo.do

> VPN 프로그램 자체는 연세대학교가 배포하는 소프트웨어이므로 이 저장소에 포함하지 않습니다.

---

## 2. Wiley TDM API 발급

Wiley는 기관 구독자가 TDM(Text and Data Mining) 목적으로 구독 원문을 API로 내려받을 수 있는 공식 서비스를 제공합니다.

1. 아래 Wiley TDM 페이지에 접속합니다.
   - https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
2. Wiley 계정으로 로그인합니다.
3. **Get a Text and Data Mining Token**에서 이용조건에 동의합니다.
4. 발급된 **Wiley TDM Token**을 복사합니다.

Wiley 공식 API 형식:

```text
https://api.wiley.com/onlinelibrary/tdm/v1/articles/<DOI>
```

요청 헤더:

```text
Wiley-TDM-Client-Token: <YOUR_TOKEN>
```

Wiley는 TDM 서비스에 대해 **60 requests / 10 minutes** 제한을 안내하고 있으므로, 이 프로그램은 Wiley 요청 사이에 기본 **10초 간격**을 둡니다.

---

## 3. Elsevier API 발급

1. Elsevier Developer Portal에 접속합니다.
   - https://dev.elsevier.com/
2. 로그인 후 API Key를 생성합니다.
3. 발급된 **Elsevier API Key**를 복사합니다.

Elsevier Article Retrieval API:

```text
https://api.elsevier.com/content/article/doi/<DOI>
```

요청 헤더:

```text
X-ELS-APIKey: <YOUR_API_KEY>
Accept: application/pdf
```

Elsevier는 ScienceDirect 구독 기관 네트워크에서 요청할 경우 기관의 원문 접근 권한을 확인하여 full text를 제공합니다. 따라서 **YSVPN 연결 후 실행**하는 것을 전제로 합니다.

단, YSVPN 연결 상태라도 Elsevier에서 기관 entitlement를 인식하지 못하거나 해당 논문이 구독 대상이 아니면 다운로드가 거부될 수 있습니다.

---

## 4. 저장소 다운로드

```bash
git clone https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university.git
cd Research-paper-crawling-method-for-yonsei-university
```

추가 Python 패키지는 필요하지 않습니다.

권장 Python:

```text
Python 3.10+
```

---

## 5. API 키 입력

예제 설정 파일을 복사합니다.

### Windows PowerShell

```powershell
Copy-Item .env.example .env
```

### macOS / Linux

```bash
cp .env.example .env
```

그다음 `.env` 파일을 열어 발급받은 값을 입력합니다.

```text
WILEY_TDM_TOKEN=발급받은_Wiley_TDM_Token
ELSEVIER_API_KEY=발급받은_Elsevier_API_Key
```

**중요:** `.env`는 Git에 업로드되지 않도록 `.gitignore`에 등록되어 있습니다.

---

## 6. DOI 목록 입력

`doi_list.example.txt`를 복사하여 `doi_list.txt`를 만듭니다.

```text
# 한 줄에 DOI 하나
10.1016/j.enbuild.2024.114000
10.1002/example.12345
10.1111/example.12345
```

다음 형태도 자동으로 정규화합니다.

```text
https://doi.org/10.1016/j.enbuild.2024.114000
doi:10.1002/example.12345
```

빈 줄과 `#`으로 시작하는 주석은 무시합니다.

---

## 7. 자동 다운로드

반드시 **YSVPN을 먼저 연결한 뒤** 실행합니다.

```bash
python download_papers.py --input doi_list.txt --output downloads
```

프로그램은 각 DOI에 대해:

1. Crossref에서 출판사 확인
2. Wiley 또는 Elsevier로 분류
3. 해당 출판사의 공식 API 호출
4. 접근 권한이 확인되면 PDF 저장
5. 처리 결과를 `download_results.csv`에 기록

합니다.

기본 출력 폴더:

```text
downloads/
```

파일 예:

```text
downloads/
├─ 10.1016__j.enbuild.2024.114000.pdf
└─ 10.1002__example.12345.pdf
```

---

## 8. 먼저 소량으로 테스트

처음에는 DOI 1~2개만 테스트하는 것을 권장합니다.

```bash
python download_papers.py --input doi_list.txt --output downloads --max 2
```

실제 다운로드 없이 출판사 분류만 확인:

```bash
python download_papers.py --input doi_list.txt --dry-run
```

이미 다운로드된 PDF는 기본적으로 다시 받지 않습니다.

다시 받으려면:

```bash
python download_papers.py --input doi_list.txt --output downloads --overwrite
```

---

## 9. 결과 확인

실행이 끝나면 `download_results.csv`에 결과가 기록됩니다.

| 항목 | 의미 |
|---|---|
| `downloaded` | 정상 다운로드 |
| `skipped` | 이미 파일이 존재함 |
| `unsupported` | Wiley/Elsevier 논문이 아님 |
| `not_found` | API에서 DOI를 찾지 못함 |
| `forbidden` | 기관 구독/API 권한 없음 |
| `rate_limited` | API 호출 한도 초과 |
| `error` | 기타 오류 |

---

## 10. 자주 발생하는 문제

### Elsevier가 403을 반환함

다음을 확인합니다.

1. YSVPN이 실제로 연결되어 있는지
2. 해당 논문이 연세대학교 ScienceDirect 구독 범위인지
3. Elsevier API Key가 정확한지
4. Elsevier가 현재 접속을 기관 네트워크로 인식하는지

Elsevier 공식 문서에 따르면 full API access는 해당 제품을 구독하는 기관의 네트워크에서 제공됩니다.

### Wiley가 403을 반환함

다음을 확인합니다.

1. 일반 Wiley API Key가 아니라 **Wiley TDM Token**을 사용했는지
2. TDM 약관 동의를 완료했는지
3. 기관이 해당 Wiley 콘텐츠를 구독하는지

### Wiley가 429를 반환함

공식 요청 제한을 초과한 것입니다. 프로그램 기본값은 Wiley 문서에 맞춰 요청 사이에 10초 간격을 둡니다.

---

## 파일 구성

```text
.
├─ README.md
├─ download_papers.py
├─ .env.example
├─ doi_list.example.txt
├─ .gitignore
├─ LICENSE
└─ tests/
   └─ test_downloader.py
```

---

## 테스트

```bash
python -m unittest discover -s tests -v
```

테스트는 실제 API Key 없이 URL 생성, DOI 정규화, 출판사 분류 로직 등을 확인합니다.

---

## 주의사항

- 본인의 연세대학교 계정과 기관 구독 권한 범위에서 사용하십시오.
- API 키와 TDM Token을 GitHub에 업로드하지 마십시오.
- Wiley/Elsevier 웹페이지 자체를 자동 크롤링하지 않습니다.
- 각 출판사의 API 호출 한도와 TDM 이용조건을 준수해야 합니다.
- 다운로드된 원문의 이용·저장·분석·공유 범위는 각 라이선스 조건에 따릅니다.

---

## 공식 문서

### 연세대학교
- YSVPN 안내: https://ilis2.yonsei.ac.kr/ics/service/PolicyApplyInfo.do
- YSVPN 접속: https://ysvpn.yonsei.ac.kr
- YSVPN 사용자 매뉴얼: https://ibook.yonsei.ac.kr/Viewer/ysvpn_user_manual

### Wiley
- Wiley Text and Data Mining: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining

### Elsevier
- Elsevier Developer Portal: https://dev.elsevier.com/
- Article Retrieval API: https://dev.elsevier.com/documentation/ArticleRetrievalAPI.wadl
- Text Mining API 안내: https://dev.elsevier.com/tecdoc_text_mining.html
