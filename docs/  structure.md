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