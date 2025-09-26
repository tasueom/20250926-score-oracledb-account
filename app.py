import oracledb
from flask import Flask, render_template as ren, request, redirect, url_for, session
import hashlib

oracledb.init_oracle_client(
    lib_dir=r"C:\oraclexe\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9"
)

app = Flask(__name__)
app.secret_key = "secret_key_123"

#오라클 DB 연결
def conn_db():
    conn = oracledb.connect(
    user="hr",
    password="1234",
    dsn="localhost:1521/XE"
    )
        
    cur = conn.cursor()
    
    return conn, cur

#DB 생성
def init_db():
    conn, cur = conn_db()
    try:
        #회원 테이블 생성
        cur.execute("""
                    create table students (
                        sno varchar2(20) primary key,
                        ban number(1) not null,
                        sname varchar2(40) not null,
                        password varchar2(200),
                        role varchar2(20) not null
                    )
                    """)
        conn.commit()
    except:
        pass
        
    try:
        #성적 테이블 생성
        cur.execute("""
                    create table scores (
                        sno varchar2(20) primary key,
                        kor number(3) not null,
                        eng number(3) not null,
                        mat number(3) not null,
                        tot number(3),
                        average number(5,2),
                        grade char(1),
                        constraint fk_scores_sno foreign key (sno) references students(sno)
                    )
                    """)
        
        conn.commit()
    except:
        pass
    #관리자 계정 생성
    try:
        cur.execute("""
                    insert into students(sno, sname, ban, password, role) values(
                        'admin', 'admin', 0, :1, 'admin'
                    )
                    """, (hashlib.sha256("1234".encode()).hexdigest(),)
                    )
        
        conn.commit()
    except:
        pass
    finally:
        conn.close()

@app.route("/")
def index():
    return ren("index.html", sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))

#회원가입
@app.route("/signup", methods=['GET','POST'])
def signup():
    if request.method=="POST":
        sno = request.form["sno"]
        ban = request.form["ban"]
        sname = request.form["sname"]
        password = request.form["password"]
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        
        try:
            conn, cur = conn_db()
            cur.execute("""
                        insert into students(sno, ban, sname, password, role) 
                        values(:1, :2, :3, :4, 'student')
                        """,(sno, ban, sname, hashed_pw))
            conn.commit()
        except oracledb.IntegrityError:
            conn.close()
            return ren("signup.html", err = "이미 존재하는 학번입니다.")
        conn.close()
        return redirect(url_for("signin"))
    
    return ren("signup.html")

#로그인
@app.route("/signin", methods=['GET','POST'])
def signin():
    #로그인 요청 받음
    if request.method=="POST":
        sno = request.form["sno"]
        password = request.form["password"]
        hashed_pw = hashlib.sha256(password.encode()).hexdigest()
        
        conn, cur = conn_db()
        #학번에 알맞는 비밀번호를 입력했는지 확인
        cur.execute("select sno, sname, role from students where sno=:1 and password=:2",
                    (sno, hashed_pw))
        student = cur.fetchone()
        conn.close()
        
        #로그인에 성공했다면
        if student:
            #세션에 학생 정보 등록
            session["sno"] = student[0]
            session["sname"] = student[1]
            session["role"] = student[2]
            
            #메인 페이지로 이동
            return redirect(url_for("index"))
        #로그인 실패 시
        else:
            return ren("signin.html", err="로그인 실패. 학번 혹은 비밀번호를 확인하세요.")
    
    #로그인 페이지 이동 요청
    return ren("signin.html")

@app.route("/signout")
def signout():
    session.clear()
    return redirect(url_for("index"))

#관리자용 성적 조회
@app.route("/score_list")
def score_list():
    #관리자가 아니라면 돌려보냄
    if session.get("role") != "admin":
        return ren("index.html", err="잘못된 접근입니다", sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))
    
    conn, cur = conn_db()
    
    cur.execute("select * from scores")
    rows = cur.fetchall()
    
    conn.close()
    return ren("score_list.html", rows=rows, sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)