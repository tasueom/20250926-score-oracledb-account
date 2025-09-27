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

#학생 계정용 본인 성적 조회
@app.route("/my_score")
def my_score():
    sno = session.get("sno")
    
    conn, cur = conn_db()
    cur.execute("""
                select s.sno, s.ban, s.sname, c.kor, c.eng, c.mat, c.tot, c.average, c.grade
                from scores c
                join students s on s.sno=c.sno
                where s.sno=:1
                """,(sno,))
    score = cur.fetchone()
    
    conn.close()
    
    return ren("my_score.html", score=score, sno = session.get("sno"), role=session.get("role"))

#관리자용 성적 조회
@app.route("/score_list")
def score_list():
    #관리자가 아니라면 돌려보냄
    if session.get("role") != "admin":
        return ren("index.html", err="잘못된 접근입니다", sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))
    
    conn, cur = conn_db()
    
    #JOIN을 이용하여 학번, 반, 이름, 성적 선택
    cur.execute("""
                select s.sno, s.ban, s.sname, c.kor, c.eng, c.mat, c.tot, c.average, c.grade
                from scores c
                join students s on s.sno=c.sno
                order by sno asc
                """)
    rows = cur.fetchall()
    
    conn.close()
    return ren("score_list.html", rows=rows, sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))

@app.route("/score_list_ban")
def score_list_ban():
    #관리자가 아니라면 돌려보냄
    if session.get("role") != "admin":
        return ren("index.html", err="잘못된 접근입니다", sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))
    
    #조회할 반 받아오기
    ban = request.args.get("ban") or "1"
    
    conn, cur = conn_db()
    
    #JOIN을 이용하여 특정 반 학생들의 학번, 반, 이름, 성적 선택
    cur.execute("""
                select s.sno, s.ban, s.sname, c.kor, c.eng, c.mat, c.tot, c.average, c.grade
                from scores c
                join students s on s.sno=c.sno
                where ban = :1
                order by s.sno asc
                """,(ban,))
    rows = cur.fetchall()
    
    #선택한 반의 통계 선택
    cur.execute("""
                select
                s.ban,
                round(avg(c.average), 2) as avg_average,
                max(c.average)           as max_average,
                min(c.average)           as min_average
                from students s
                join scores   c on c.sno = s.sno
                where s.ban = :1
                group by s.ban
                """, (ban,))
    stats = cur.fetchone()
    
    conn.close()
    return ren("score_list_ban.html", ban=ban, rows=rows, stats=stats, sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))

@app.route("/insert_score",methods=['GET','POST'])
def insert_score():
    #성적 삽입 요청
    if request.method=="POST":
        sno = request.form["sno"]
        kor = int(request.form["kor"])
        eng = int(request.form["eng"])
        mat = int(request.form["mat"])
        tot, avg, grade = calculate(kor, eng, mat)
        
        conn, cur = conn_db()
        cur.execute("""insert into scores(sno, kor, eng, mat, tot, average, grade) 
                    values(:1, :2, :3, :4, :5, :6, :7)""",
                    (sno, kor, eng, mat, tot, avg, grade))
        conn.commit()
        
        #학생이 입력한것이라면
        if session.get("role") == "student":
            cur.execute("""
                select s.sno, s.ban, s.sname, c.kor, c.eng, c.mat, c.tot, c.average, c.grade
                from scores c
                join students s on s.sno=c.sno
                where s.sno=:1
                """,(sno,))
            score = cur.fetchone()
    
            conn.close()
    
            return ren("my_score.html", score=score, sno = session.get("sno"), role=session.get("role"))
        #관리자라면
        #students 테이블에는 존재하지만 scores 테이블에 성적이 입력되지 않은 학번만 선택
        cur.execute("""
                    select sno from students
                    where sno != 'admin'
                    minus
                    select sno from scores
                    order by sno
                    """)
        snos = cur.fetchall()
        conn.close()
        
        return ren("insert_score.html", noti="성적이 입력되었습니다.", snos=snos, sno=session.get("sno"), role=session.get("role"))
    #삽입 폼 이동
    if session.get("role") != "admin":#관리자가 아닌 사람이 성적 입력을 시도할 시
        return ren("index.html", err="잘못된 접근입니다", sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))
    #관리자라면
    conn, cur = conn_db()
    
    #students 테이블에는 존재하지만 scores 테이블에 성적이 입력되지 않은 학번만 선택
    cur.execute("""
                select sno from students
                where sno != 'admin'
                minus
                select sno from scores
                order by sno
                """)
    snos = cur.fetchall()
    conn.close()
    
    #성적 미입력 학번을 같이 넘겨 성적 입력 폼에서 select로 사용할 수 있게 함
    return ren("insert_score.html", snos=snos, sno = session.get("sno"), role=session.get("role"))

@app.route("/update_score/<sno>",methods=['GET','POST'])
def update_score(sno):
    #성적 수정 요청
    if request.method=="POST":
        kor = int(request.form["kor"])
        eng = int(request.form["eng"])
        mat = int(request.form["mat"])
        tot, avg, grade = calculate(kor, eng, mat)
        
        conn, cur = conn_db()
        cur.execute("""
                    update scores set
                    kor = :1,
                    eng = :2,
                    mat = :3,
                    tot = :4,
                    average = :5,
                    grade = :6
                    where sno = :7
                    """,
                    (kor, eng, mat, tot, avg, grade, sno))
        conn.commit()
        
        #누구의 수정 요청인지에 따라 돌아가는 페이지 분기
        if session.get("role")=="admin":
            conn.close()
            return redirect(url_for("score_list"))
        else:
            cur.execute("""
                select s.sno, s.ban, s.sname, c.kor, c.eng, c.mat, c.tot, c.average, c.grade
                from scores c
                join students s on s.sno=c.sno
                where s.sno=:1
                """,(sno,))
            score = cur.fetchone()
    
            conn.close()
            return ren("my_score.html", noti="성적이 수정되었습니다", score=score, sno = session.get("sno"), sname=session.get("sname"), role=session.get("role"))
    #수정 폼 이동 요청
    conn, cur = conn_db()
    cur.execute("select * from scores where sno=:1",(sno,))
    score = cur.fetchone()
    conn.close()
    
    return ren("update_score.html", score=score, sno = session.get("sno"), role=session.get("role"))

def calculate(kor, eng, mat):
    tot = kor+eng+mat
    avg = round(tot/3,2)
    match int(avg//10):
        case 10|9:
            grade = "A"
        case 8:
            grade = "B"
        case 7:
            grade = "C"
        case 6:
            grade = "D"
        case _:
            grade = "F"
    return tot, avg, grade

if __name__ == "__main__":
    init_db()
    app.run(debug=True)