# 연세대학교 VPN 기반 학술논문 자동 다운로드

DOI 목록을 준비한 뒤 몇 개의 명령어만 복사해서 붙여넣으면, **Wiley**와 **Elsevier**의 공식 API를 통해 접근 권한이 있는 논문의 PDF를 자동으로 내려받는 도구입니다.

> 처음 사용하는 사람은 아래 **1번부터 7번까지 순서대로** 따라 하면 됩니다. 코드를 수정할 필요는 없습니다.

---

## 1. YSVPN 설치 및 연결

교외에서 실행할 경우 먼저 연세대학교 VPN에 연결합니다.

1. 아래 페이지에 접속합니다.
   - https://ysvpn.yonsei.ac.kr
2. 운영체제에 맞는 VPN 프로그램을 설치합니다.
3. YSVPN을 실행합니다.
4. **연세포탈 ID / 비밀번호**로 로그인합니다.
5. VPN 연결을 유지한 상태로 다음 단계로 이동합니다.

설치 방법이 필요한 경우:
- YSVPN 사용자 매뉴얼: https://ibook.yonsei.ac.kr/Viewer/ysvpn_user_manual
- 연세대학교 공식 안내: https://ilis2.yonsei.ac.kr/ics/service/PolicyApplyInfo.do

---

## 2. Wiley TDM Token 발급

1. 아래 Wiley 페이지에 접속합니다.
   - https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining
2. Wiley 계정으로 로그인합니다.
3. **Get a Text and Data Mining Token**을 선택하고 이용조건에 동의합니다.
4. 발급된 **Wiley TDM Token**을 복사해 둡니다.

발급된 Token은 아래 5단계에서 그대로 붙여넣으면 됩니다.

---

## 3. Elsevier API Key 발급

1. 아래 Elsevier Developer Portal에 접속합니다.
   - https://dev.elsevier.com/
2. 로그인합니다.
3. API Key를 생성합니다.
4. 발급된 **Elsevier API Key**를 복사해 둡니다.

발급된 API Key는 아래 5단계에서 그대로 붙여넣으면 됩니다.

---

## 4. 저장소 다운로드

### 4-1. CMD 열기

1. 키보드에서 **Windows 키**를 누릅니다.
2. `cmd`를 입력합니다.
3. **명령 프롬프트**를 실행합니다.

### 4-2. 저장소 다운로드

아래 두 줄을 **한 줄씩 복사해서 CMD에 붙여넣고 Enter**를 누릅니다.

```cmd
git clone https://github.com/gunkuk/Research-paper-crawling-method-for-yonsei-university.git
cd Research-paper-crawling-method-for-yonsei-university
```

정상적으로 실행되면 현재 위치가 이 저장소 폴더로 바뀝니다.

### 4-3. Python 확인

아래 명령을 입력합니다.

```cmd
python --version
```

`Python 3.10` 이상이 표시되면 그대로 진행합니다.

#### "python을 찾을 수 없습니다"라고 나오면

아래 명령을 CMD에 붙여넣습니다.

```cmd
winget install -e --id Python.Python.3.12
```

설치가 끝나면 **CMD를 닫았다가 다시 열고**, 다시 저장소 폴더로 이동한 뒤 진행합니다.

#### "git을 찾을 수 없습니다"라고 나오면

아래 명령을 CMD에 붙여넣습니다.

```cmd
winget install -e --id Git.Git
```

설치가 끝나면 **CMD를 닫았다가 다시 열고 4-2부터 다시 진행**합니다.

---

## 5. API 키 입력

파일을 직접 열어 수정할 필요가 없습니다.

### 5-1. CMD에서 PowerShell로 전환

방금 사용하던 CMD 창에 아래 명령을 입력하고 Enter를 누릅니다.

```cmd
powershell
```

명령줄 앞부분이 `PS`로 시작하면 정상입니다.

### 5-2. 설정 파일 생성

아래 명령을 붙여넣고 Enter를 누릅니다.

```powershell
Copy-Item .env.example .env
```

### 5-3. Wiley Token 입력

**중요: 아래 명령은 한 번에 여러 줄을 붙여넣지 말고, 한 줄씩 실행합니다.**

또한 **아래 명령문 자체에 Wiley Token을 직접 붙여 넣는 것이 아닙니다.**  
먼저 명령문을 그대로 실행한 뒤, PowerShell이 입력을 요청할 때 **그때 Token 값만 붙여넣습니다.**

먼저 아래 한 줄을 PowerShell에 붙여넣고 Enter를 누릅니다.

```powershell
$wiley = Read-Host "Wiley TDM Token을 붙여넣고 Enter"
```

다음 문구가 나타나면:

```text
Wiley TDM Token을 붙여넣고 Enter:
```

→ **2단계에서 발급받은 Wiley TDM Token 값만 붙여넣고 Enter**를 누릅니다.

> `Read-Host "..."`의 따옴표 안에는 Token을 넣는 것이 아닙니다. 안내 문구는 그대로 두고, Enter 후 나타나는 입력란에 Token을 붙여넣습니다.

### 5-4. Elsevier API Key 입력

아래 한 줄을 붙여넣고 Enter를 누릅니다.

```powershell
$elsevier = Read-Host "Elsevier API Key를 붙여넣고 Enter"
```

다음 문구가 나타나면:

```text
Elsevier API Key를 붙여넣고 Enter:
```

→ **3단계에서 발급받은 Elsevier API Key 값만 붙여넣고 Enter**를 누릅니다.

### 5-5. 입력한 값을 .env 파일에 저장

마지막으로 아래 **한 줄만** 붙여넣고 Enter를 누릅니다.

```powershell
@("WILEY_TDM_TOKEN=$wiley","ELSEVIER_API_KEY=$elsevier") | Set-Content .env -Encoding UTF8
```

설정이 정상적으로 저장됐는지 **키 이름만** 확인하려면 아래 명령을 실행합니다.

```powershell
Get-Content .env | ForEach-Object { ($_ -split '=')[0] }
```

아래 두 줄이 나오면 정상입니다.

```text
WILEY_TDM_TOKEN
ELSEVIER_API_KEY
```

> Token과 API Key는 비밀번호처럼 취급하십시오. 생성된 `.env` 파일은 GitHub에 올라가지 않도록 설정되어 있습니다.

---

## 6. DOI 목록 넣기

DOI는 **한 줄에 하나씩** 준비합니다.

예:

```text
10.1016/j.ibusrev.2010.09.002
10.1002/asi.10389
```

### 가장 쉬운 방법

1. Excel, 메모장 등에서 DOI 목록을 **한 줄에 하나씩** 준비합니다.
2. DOI 목록 전체를 선택해서 **Ctrl+C**로 복사합니다.
3. 다시 PowerShell 창으로 돌아옵니다.
4. 아래 한 줄을 붙여넣고 Enter를 누릅니다.

```powershell
Get-Clipboard | Set-Content doi_list.txt -Encoding UTF8
```

끝입니다. 복사해 둔 DOI 목록이 자동으로 `doi_list.txt`에 저장됩니다.

> DOI 앞에 `https://doi.org/`가 붙어 있어도 프로그램이 자동으로 처리합니다.

---

## 7. 논문 자동 다운로드

### 7-1. YSVPN 연결 확인

다운로드를 시작하기 전에 **YSVPN이 연결되어 있는지 다시 확인**합니다.

### 7-2. 실행

PowerShell에 아래 한 줄만 입력합니다.

```powershell
python download_papers.py
```

이제 프로그램이 DOI 목록을 순서대로 확인하고 Wiley 또는 Elsevier의 공식 API를 통해 다운로드를 진행합니다.

화면에는 다음처럼 진행 상황이 표시됩니다.

```text
[1/20] 10.xxxx/xxxxx
  출판사: elsevier
  -> downloaded: 정상 다운로드
```

### 7-3. 다운로드된 PDF 열기

작업이 끝나면 아래 명령을 입력합니다.

```powershell
explorer downloads
```

`downloads` 폴더가 열리고 다운로드된 PDF를 확인할 수 있습니다.

---

## 8. 결과가 제대로 내려받아졌는지 확인

PDF는 다음 폴더에 저장됩니다.

```text
downloads
```

전체 처리 결과는 다음 파일에도 기록됩니다.

```text
download_results.csv
```

주요 결과는 다음과 같습니다.

| 화면에 표시되는 상태 | 의미 |
|---|---|
| `downloaded` | PDF 다운로드 성공 |
| `skipped` | 이미 받은 PDF라서 건너뜀 |
| `unsupported` | Wiley 또는 Elsevier 논문이 아님 |
| `not_found` | DOI를 찾지 못함 |
| `forbidden` | API Key, 기관 구독 또는 접근 권한 문제 |
| `rate_limited` | 출판사 API의 요청 횟수 제한에 걸림 |
| `error` | 그 밖의 오류 |

---

## 9. 문제가 생겼을 때

### `forbidden`이 나오는 경우

다음을 차례로 확인합니다.

1. **YSVPN이 연결되어 있는지**
2. Wiley TDM Token 또는 Elsevier API Key를 정확히 입력했는지
3. 해당 논문이 연세대학교 구독 범위에 포함되는지

VPN을 다시 연결한 뒤 `python download_papers.py`를 다시 실행해도 됩니다.

이미 성공적으로 받은 PDF는 자동으로 건너뜁니다.

### `rate_limited`가 나오는 경우

출판사에서 허용한 API 요청 횟수를 초과한 것입니다.

잠시 후 아래 명령을 다시 실행하면 됩니다.

```powershell
python download_papers.py
```

이미 받은 파일은 다시 다운로드하지 않습니다.

### DOI 목록을 바꾸고 싶은 경우

새 DOI 목록을 한 줄씩 준비해 **Ctrl+C**로 복사한 뒤 다시 아래 명령을 실행합니다.

```powershell
Get-Clipboard | Set-Content doi_list.txt -Encoding UTF8
```

그다음 다시:

```powershell
python download_papers.py
```

---

## 10. 다음부터 다시 사용할 때

처음 설치를 모두 끝낸 뒤에는 **2~5단계를 다시 할 필요가 없습니다.**

다음부터는 아래 순서만 반복하면 됩니다.

1. **YSVPN 연결**
2. Windows 키를 누르고 `cmd`를 검색해 **명령 프롬프트** 실행
3. 아래 두 줄을 CMD에 한 줄씩 입력

```cmd
cd %USERPROFILE%\Research-paper-crawling-method-for-yonsei-university
powershell
```

4. Excel·메모장 등에서 새 DOI 목록 전체를 **Ctrl+C**로 복사
5. 아래 두 줄을 PowerShell에 한 줄씩 입력

```powershell
Get-Clipboard | Set-Content doi_list.txt -Encoding UTF8
python download_papers.py
```

다운로드 폴더 열기:

```powershell
explorer downloads
```

---

## 주의사항

- 본인의 연세대학교 계정과 기관 구독 권한 범위에서 사용하십시오.
- Wiley TDM Token과 Elsevier API Key를 다른 사람과 공유하지 마십시오.
- 다운로드된 원문의 이용·저장·분석·공유 범위는 해당 출판사와 기관의 라이선스 조건을 따라야 합니다.
- 프로그램은 Wiley와 Elsevier의 공식 API를 사용하며, 출판사 웹페이지 자체를 크롤링하지 않습니다.

---

## 공식 링크

### 연세대학교
- YSVPN 접속: https://ysvpn.yonsei.ac.kr
- YSVPN 사용자 매뉴얼: https://ibook.yonsei.ac.kr/Viewer/ysvpn_user_manual
- YSVPN 공식 안내: https://ilis2.yonsei.ac.kr/ics/service/PolicyApplyInfo.do

### Wiley
- Wiley Text and Data Mining: https://onlinelibrary.wiley.com/library-info/resources/text-and-datamining

### Elsevier
- Elsevier Developer Portal: https://dev.elsevier.com/
