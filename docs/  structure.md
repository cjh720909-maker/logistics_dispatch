master/                 # 기초정보관리
    routes.py           # 화면(URL) 연결
    service.py          # 업무 처리
    templates/          # 화면(html)

dispatch/              # 배차관리
    routes.py
    service.py
    templates/

print/                 # 출력물관리
    routes.py
    service.py
    templates/

inventory/             # 재고관리
    routes.py
    service.py
    templates/

static/                # 공통 리소스
    css/
    js/
    images/

system/
    routes.py
    service.py          # SQL 조회(910)
    sync.py             # 920 동기화
    sync_log.py         # (나중)    

원본 MySQL
  - SELECT만 허용
  - CREATE / INSERT / UPDATE / DELETE 절대 금지

        ↓ 읽기

로컬 DB
  - CREATE 가능
  - INSERT 가능
  - UPDATE 가능
  - 우리 프로그램 전용

100 기초관리
 ├─120 거래처
 ├─121 가상 거래처 생성
 ├─130 제품
 ├─140 차량
 ├─151 업로드 자동변환(분리)
 └─152 업로드 자동변환(합치기)

200 배차
 ├─211 엑셀 업로드
 ├─220 배차 사전작업
 ├─230 배차조정
 └─240 진행현황