import streamlit as st
import sqlite3
from datetime import datetime
import pandas as pd

# --- 1. DB 설정 및 초기화 ---
def init_db():
    conn = sqlite3.connect("students.db")
    cursor = conn.cursor()
    cursor.execute("""
       CREATE TABLE IF NOT EXISTS sungjuk (
          id INTEGER PRIMARY KEY AUTOINCREMENT,
          student_id TEXT,
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

# --- 2. 사이드바 메뉴 구성 ---
st.set_page_config(page_title="성적 관리 시스템", layout="wide")
menu = ["홈", "학생 등록", "전체 명단 조회", "학생 정보 수정", "학생 정보 삭제"]
choice = st.sidebar.radio(
    "이동할 메뉴를 선택하세요",
    ["홈", "학생 등록", "전체 명단 조회", "학생 정보 수정", "학생 정보 삭제"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.info("학번은 등록 시 자동 생성됩니다.")
# --- 3. 기능별 화면 구현 ---

# (1) 홈 화면
if choice == "홈":
    st.title("🎓 성적 관리 시스템")
    st.write("왼쪽 메뉴를 선택하여 학생 등록 및 성적 관리를 시작하세요.")

# (2) 학생 등록
elif choice == "학생 등록":
    st.title("📝 신규 학생 등록")
    with st.form("register_form"):
        name = st.text_input("이름")
        kor = st.number_input("국어 점수", 0, 100, 0)
        eng = st.number_input("영어 점수", 0, 100, 0)
        mat = st.number_input("수학 점수", 0, 100, 0)
        submitted = st.form_submit_button("등록하기")

        if submitted:
            total = kor + eng + mat
            avg = round(total / 3, 2)
            grade = "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "D" if avg >= 60 else "F"
            
            conn = sqlite3.connect("students.db")
            cur = conn.cursor()
            
            # 학번 생성
            current_year = datetime.now().year
            cur.execute("SELECT COUNT(*) FROM sungjuk")
            count = cur.fetchone()[0]
            new_id = f"{current_year}{(count + 1):03d}"
            
            cur.execute("INSERT INTO sungjuk (student_id, name, kor, eng, mat, total, avg, grade) VALUES (?,?,?,?,?,?,?,?)",
                        (new_id, name, kor, eng, mat, total, avg, grade))
            conn.commit()
            conn.close()
            st.success(f"학번 [{new_id}] {name} 학생이 등록되었습니다!")

# (3) 전체 명단 조회
elif choice == "전체 명단 조회":
    st.title("📋 전체 학생 명단")
    conn = sqlite3.connect("students.db")
    df = pd.read_sql_query("SELECT * FROM sungjuk ORDER BY id DESC", conn)
    conn.close()
    
    if not df.empty:
        st.dataframe(df, use_container_width=True)
    else:
        st.info("등록된 학생 데이터가 없습니다.")

# (4) 학생 정보 수정
elif choice == "학생 정보 수정":
    st.title("🔄 성적 정보 수정")
    search_id = st.text_input("수정할 학생의 학번을 입력하세요")
    
    if search_id:
        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        cur.execute("SELECT * FROM sungjuk WHERE student_id = ?", (search_id,))
        student = cur.fetchone()
        
        if student:
            with st.form("edit_form"):
                new_name = st.text_input("이름", value=student[2])
                new_kor = st.number_input("국어", 0, 100, int(student[3]))
                new_eng = st.number_input("영어", 0, 100, int(student[4]))
                new_mat = st.number_input("수학", 0, 100, int(student[5]))
                update_btn = st.form_submit_button("수정 완료")
                
                if update_btn:
                    total = new_kor + new_eng + new_mat
                    avg = round(total / 3, 2)
                    grade = "A" if avg >= 90 else "B" if avg >= 80 else "C" if avg >= 70 else "D" if avg >= 60 else "F"
                    
                    cur.execute("UPDATE sungjuk SET name=?, kor=?, eng=?, mat=?, total=?, avg=?, grade=? WHERE student_id=?",
                                (new_name, new_kor, new_eng, new_mat, total, avg, grade, search_id))
                    conn.commit()
                    st.success(f"학번 [{search_id}] 정보가 수정되었습니다.")
        else:
            st.error("해당 학번을 찾을 수 없습니다.")
        conn.close()

# (5) 학생 정보 삭제
elif choice == "학생 정보 삭제":
    st.title("🗑️ 데이터 삭제")
    del_id = st.text_input("삭제할 학생의 학번을 입력하세요")
    if st.button("삭제하기"):
        conn = sqlite3.connect("students.db")
        cur = conn.cursor()
        cur.execute("SELECT name FROM sungjuk WHERE student_id = ?", (del_id,))
        student = cur.fetchone()
        
        if student:
            cur.execute("DELETE FROM sungjuk WHERE student_id = ?", (del_id,))
            conn.commit()
            st.warning(f"학번 [{del_id}] {student[0]} 학생의 정보가 삭제되었습니다.")
        else:
            st.error("학번을 다시 확인해 주세요.")
        conn.close()
