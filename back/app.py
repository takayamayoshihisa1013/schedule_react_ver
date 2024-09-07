from flask import Flask, jsonify, request, render_template, redirect, session, url_for
from flask_cors import CORS
import mysql.connector
import uuid
from flask_session import Session
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret'
CORS(app, supports_credentials=True, resources={
     r"/*": {"origins": ["http://localhost:3000"]}})


def mysql_conn():
    conn = mysql.connector.connect(
        host="localhost",
        user="root",
        password="",
        db="schedule"
    )
    return conn


@app.route('/api/data', methods=['GET'])
def get_data():
    data = {"message": "Hello from Flask!"}
    return jsonify(data)


@app.route("/check_session")
def dashboard():
    print(session, "dash")
    if "user_id" not in session:
        return jsonify({"login": False})
    else:
        print(session["user_id"])
        return jsonify({"login": True})


@app.route("/login", methods=["POST"])
def login():
    data = request.json
    email = data.get("email")
    password = data.get("password")

    conn = mysql_conn()
    cur = conn.cursor()
    try:
        cur.execute("""
                    SELECT user_id, name
                    FROM user
                    WHERE email = %s AND password = %s
                    """, (email, password))

        user = cur.fetchone()
        if user:  # ユーザーが見つかった場合
            session["user_id"] = user[0]
            print(session, "session")
            time.sleep(1)
            return jsonify({"submit": True, "user": user[1]})
        else:
            return jsonify({"submit": False}), 404

    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"submit": False}), 500


@app.route("/signup", methods=["POST", "GET"])
def signup():
    data = request.json
    name = data["name"]
    email = data["email"]
    password = data["password"]
    conn = mysql_conn()
    cur = conn.cursor()
    cur.execute("""
                CREATE TABLE IF NOT EXISTS user(
                    user_id CHAR(36) PRIMARY KEY,
                    name VARCHAR(100),
                    email VARCHAR(100) UNIQUE,
                    password VARCHAR(255)
                )
                """)
    try:
        cur.execute("INSERT INTO user(user_id, name, email, password) VALUES(UUID(),%s,%s,%s)",
                    (name, email, password))

        conn.commit()
        conn.close()

        return jsonify({"submit": True})
    except:
        return jsonify({"submit": False})


@app.route("/add", methods=["POST"])
def add():
    print("Session before processing /add:", session)  # セッション内容を確認

    # POSTリクエストの処理
    # return jsonify({"message": "Form submitted successfully!"}), 200

    # JSONデータを受け取る
    data = request.get_json()

    # フォームデータから取得
    name = data.get("name")
    detail = data.get("schedule_detail")
    start_date = data.get("start_date")
    start_time = data.get("start_time")
    end_date = data.get("end_date")
    end_time = data.get("end_time")
    important = data.get("important")
    add_button = data.get("add_button")

    if not all([start_date, start_time, end_date, end_time]):
        print("time_error")

    # 日時の組み合わせ

    print("time")
    start_datetime = datetime.strptime(
        f"{start_date} {start_time}", "%Y-%m-%d %H:%M")
    end_datetime = datetime.strptime(
        f"{end_date} {end_time}", "%Y-%m-%d %H:%M")

    # if add_button:
    print("push")
    conn = mysql_conn()
    cur = conn.cursor()
    cur.execute("""
            CREATE TABLE IF NOT EXISTS schedule(
                id VARCHAR(36) PRIMARY KEY,
                user_id VARCHAR(36),
                name TEXT NOT NULL,
                detail TEXT,
                start_datetime DATETIME,
                end_datetime DATETIME,
                importance TEXT,
                FOREIGN KEY (user_id) REFERENCES user(user_id)
            )
        """)
    print("create")
    try:
            cur.execute("INSERT INTO schedule(id,user_id,name,detail,start_datetime,end_datetime,importance) VALUES(UUID(),%s,%s,%s,%s,%s,%s)",
                        (session["user_id"], name, detail, start_datetime, end_datetime, important))
            print("commit")
            conn.commit()
    except Exception as e:
            print(e)

    return jsonify({"message": "Form submitted successfully!"}), 200

@app.route("/activity_data", methods=["POST"])
def calender_data():

    conn = mysql_conn()
    cur = conn.cursor()
    cur.execute("""
                SELECT name, start_datetime, importance
                FROM schedule
                WHERE user_id = %s
                """, (session["user_id"],))
    
    activity_data = cur.fetchall()
    
    # print(data)
    activity = ()
    
    for data in activity_data:
        print(data)
        activity_list = {}
        activity_list["name"] = data[0]
        activity_list["start_date"] = data[1].strftime("%Y-%m-%d")
        activity_list["importance"] = data[2]
        activity.append(activity_list)
        
    return jsonify(activity)


if __name__ == "__main__":
    app.run(debug=True)
