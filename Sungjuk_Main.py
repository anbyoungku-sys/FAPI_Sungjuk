from fastapi import FastAPI, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
import sqlite3
from datetime import datetime

app = FastAPI()
templates = Jinja2Templates(directory="templates")

# DB 초기화: student_id(학번) 컬럼 추가
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    # 테이블이 이미 있으면 지우고 새로 생성 (개발 단계에서 편리함)
    # cursor.execute("DROP TABLE IF EXISTS sungjuk")

    cursor.execute("""
       CREATE TABLE IF NOT EXISTS sungjuk (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT,  -- 이 부분이 없어서 에러가 났던 것입니다.
          name TEXT,
          kor INTEGER,
          eng INTEGER,
          mat INTEGER,
          total INTEGER,
          avg REAL,
          grade TEXT
       )
       """)
    conn.commit()
    conn.close()

init_db()

# 1. 메인 화면
@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    # 이제 문자열 대신 'index.html' 파일을 불러옵니다!
    return templates.TemplateResponse("index.html", {"request": request})


# 2. 학생 등록 화면 보기
@app.get("/student")
async def get_form(request: Request):
    return templates.TemplateResponse("student.html", {"request": request})

# 3. 학생 정보 처리 및 DB 저장

@app.post("/student_info")
async def post_info(
        name: str = Form(...),
        kor: int = Form(...),
        eng: int = Form(...),
        mat: int = Form(...)
):
    # 1. 성적 및 학점 계산
    total = kor + eng + mat
    avg = round(total / 3, 2)
    if avg >= 90: grade = "A"
    elif avg >= 80: grade = "B"
    elif avg >= 70: grade = "C"
    elif avg >= 60: grade = "D"
    else: grade = "F"

    # 2. DB 연결
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    # 3. [핵심] 학번 자동 생성 로직
    # 현재 연도 가져오기 (예: 2026)
    current_year = datetime.now().year

    # DB에 저장된 현재 총 학생 수 조회
    cursor.execute("SELECT COUNT(*) FROM sungjuk")
    count = cursor.fetchone()[0]

    # 새로운 학번 생성: 연도 + (현재인원+1)을 3자리 숫자로 (예: 2026001)
    new_student_id = f"{current_year}{(count + 1):03d}"

    # 4. DB에 저장 (생성된 학번 new_student_id 포함)
    cursor.execute(
        "INSERT INTO sungjuk (student_id, name, kor, eng, mat, total, avg, grade) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (new_student_id, name, kor, eng, mat, total, avg, grade)
    )
    conn.commit()
    conn.close()

    # 저장 완료 후 리스트 페이지로 이동 (조회 화면에서 바로 확인 가능)
    return HTMLResponse(f"""
        <script>
            alert('학번 [{new_student_id}]번으로 등록되었습니다!');
            location.href = '/list';
        </script>
    """)

# 4. 전체 학생 데이터 조회하기
@app.get("/list")
async def get_student_list(request: Request, page: int = 1):
    # 한 페이지에 보여줄 개수
    limit = 20
    # 건너뛸 개수 계산 (예: 2페이지면 앞의 20개를 건너뜀)
    offset = (page - 1) * limit

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    # 1. 전체 데이터 개수 구하기 (다음 페이지 존재 여부 확인용)
    cursor.execute("SELECT COUNT(*) FROM sungjuk")
    total_count = cursor.fetchone()[0]

    # 2. 20개만 가져오기 (LIMIT: 가져올 개수, OFFSET: 시작점)
    cursor.execute(
        "SELECT * FROM sungjuk ORDER BY id DESC LIMIT ? OFFSET ?",
        (limit, offset)
    )
    rows = cursor.fetchall()
    conn.close()

    # 다음/이전 페이지 계산
    has_next = total_count > (page * limit)
    has_prev = page > 1

    return templates.TemplateResponse("list.html", {
        "request": request,
        "students": rows,
        "page": page,
        "has_next": has_next,
        "has_prev": has_prev
    })

# [추가] 4-1. 수정용 검색 페이지 띄우기
@app.get("/edit_list") # 메인 메뉴 4번 링크와 일치시킴
async def edit_search_page(request: Request):
    return templates.TemplateResponse("edit_search.html", {"request": request})

# [추가] 4-2. 입력받은 학번으로 실제 수정 페이지(/edit/학번)로 리다이렉트
@app.get("/edit_redirect")
async def edit_redirect(student_id: str):
    from fastapi.responses import RedirectResponse
    # 입력한 학번을 주소 뒤에 붙여서 /edit/2026001 형태로 보냅니다.
    return RedirectResponse(url=f"/edit/{student_id}")



# 5. 상세조회 입력 페이지로 이동
@app.get("/search")
async def search_page(request: Request):
    return templates.TemplateResponse("search.html", {"request": request})

# 6. 학번으로 데이터 조회 처리
@app.get("/search_result")
async def search_result(request: Request, student_id: str):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    # 학번(student_id)이 일치하는 행 하나만 가져오기
    cursor.execute("SELECT * FROM sungjuk WHERE student_id = ?", (student_id,))
    student = cursor.fetchone() # 하나만 가져올 때는 fetchone()
    conn.close()

    return templates.TemplateResponse("view.html", {"request": request, "student": student})

# [추가] 7. 성적 수정 화면 (기존 데이터 불러오기)
@app.get("/edit/{student_id}")
async def edit_page(request: Request, student_id: str):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    # 수정할 학생의 기존 정보를 가져옵니다.
    cursor.execute("SELECT * FROM sungjuk WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()
    conn.close()

    if not student:
        return HTMLResponse("<script>alert('학생을 찾을 수 없습니다.'); history.back();</script>")

    return templates.TemplateResponse("edit.html", {"request": request, "student": student})

# [추가] 8. 성적 수정 처리 (DB 업데이트)
@app.post("/update_info")
async def update_info(
        student_id: str = Form(...),
        name: str = Form(...),
        kor: int = Form(...),
        eng: int = Form(...),
        mat: int = Form(...)
):
    # 새로운 점수로 다시 계산
    total = kor + eng + mat
    avg = round(total / 3, 2)

    if avg >= 90: grade = "A"
    elif avg >= 80: grade = "B"
    elif avg >= 70: grade = "C"
    elif avg >= 60: grade = "D"
    else: grade = "F"

    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    # SQL UPDATE문을 사용하여 정보 변경
    cursor.execute("""
                   UPDATE sungjuk
                   SET name=?, kor=?, eng=?, mat=?, total=?, avg=?, grade=?
                   WHERE student_id=?
                   """, (name, kor, eng, mat, total, avg, grade, student_id))

    conn.commit()
    conn.close()

    return HTMLResponse(f"""
        <script>
            alert('학번 [{student_id}]의 정보가 수정되었습니다.');
            location.href = '/list';
        </script>
    """)

# [추가] 5-1. 삭제 검색 페이지 이동
@app.get("/delete_list")
async def delete_search_page(request: Request):
    return templates.TemplateResponse("delete_search.html", {"request": request})

# [추가] 5-2. 실제 데이터 삭제 처리
@app.post("/delete_process")
async def delete_process(student_id: str = Form(...)):
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()

    # 해당 학번이 존재하는지 먼저 확인
    cursor.execute("SELECT name FROM sungjuk WHERE student_id = ?", (student_id,))
    student = cursor.fetchone()

    if not student:
        conn.close()
        return HTMLResponse("<script>alert('해당 학번을 찾을 수 없습니다.'); history.back();</script>")

    # 데이터 삭제 실행
    cursor.execute("DELETE FROM sungjuk WHERE student_id = ?", (student_id,))
    conn.commit()
    conn.close()

    return HTMLResponse(f"""
        <script>
            alert('학번 [{student_id}] {student[0]} 학생의 정보가 삭제되었습니다.');
            location.href = '/';
        </script>
    """)




if __name__ == "__main__":
    import uvicorn
    # 파일명이 Sungjuk_Main.py인지 다시 한번 확인하세요!
    uvicorn.run('Sungjuk_Main:app', host="0.0.0.0", port=8000, reload=True)