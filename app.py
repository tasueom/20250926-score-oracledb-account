import oracledb
from flask import Flask, render_template as ren, request, redirect, url_for, session

oracledb.init_oracle_client(
    lib_dir=r"C:\oraclexe\instantclient-basic-windows.x64-23.9.0.25.07\instantclient_23_9"
)

app = Flask(__name__)

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
                        sno number primary key,
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
                        sno number primary key,
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
    finally:
        conn.close()

if __name__ == "__main__":
    init_db()
    app.run(debug=True)