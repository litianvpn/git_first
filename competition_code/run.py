from flask import Flask, render_template, url_for, redirect, request, session
from flask.json import dump
import pymysql
import pymysql.cursors
import os

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(30)

db = pymysql.connect(host='127.0.0.1',
                     user='root',
                     password='shujuku',
                     database='blog2'
                     )


@app.route("/")
def blog():
    # GET 请求处理
    page = request.args.get('page', 1, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    if username:
        return render_template("blog.html", data=username, papers=rows, page=page, total_pages=total_pages)
    else:
        return render_template('blog.html', papers=rows, page=page, total_pages=total_pages)


@app.route('/blog_submit', methods=['GET', 'POST'])
def blog_submit():
    page = request.args.get('page', 1, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 计算总的申请数量
    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')

    if request.method == 'POST':
        result = request.form

        # 判断审核的结果是同意还是不同意
        decision = result.get('decision')  # 1 or 0
        paper_id = result.get('pid')  # 获取申请的 ID
        reason = result.get('reason', '')  # 不同意理由（如果有）

        cursor = db.cursor()
        if decision == 1:
            # 更新为同意状态
            sql = "UPDATE paper SET decision=1 WHERE id=%s"
            cursor.execute(sql, (paper_id,))
        elif decision == 0:
            # 更新为不同意状态并添加理由
            sql = "UPDATE paper SET decision=0, reason=%s WHERE id=%s"
            cursor.execute(sql, (reason, paper_id))

        try:
            db.commit()
            # 获取更新后的申请信息以在 ans.html 中显示
            cursor.execute("SELECT * FROM paper")
            applications = cursor.fetchall()
            # return render_template("ans.html", data=username, papers=applications, page=page, total_pages=total_pages)
        except Exception as e:
            db.rollback()
            return f"发布失败!<a href='/issue'> 点击返回</a> 错误信息: {e}"

    # 返回到申请列表页面
    return render_template("blog.html", data=username, papers=rows, page=page, total_pages=total_pages)


@app.route('/blog2')
def blog2():
    page = request.args.get('page', 1, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    return render_template("blog2.html", papers=rows, page=page, total_pages=total_pages)


@app.route('/login')
def login():
    return render_template("login.html")


@app.route('/regi')
def regi():
    return render_template('regi.html')


@app.route('/regi_submit', methods=['GET', 'POST'])
def regi_submit():
    if request.method == 'POST':
        result = request.form

        cursor = db.cursor()
        sql = " INSERT INTO user(username,password,email) VALUES('%s','%s','%s') " % (
            result['username'], result['password'], result['email'])
        try:
            cursor.execute(sql)
            db.commit()
            return render_template("login2.html")
        except:
            db.rollback()
            return '提交失败'


@app.route('/login_submit', methods=['GET', 'POST'])
def login_submit():
    if request.method == 'POST':
        result = request.form

        cursor = db.cursor(pymysql.cursors.DictCursor)
        sql = " SELECT * FROM user  WHERE username='%s' and password ='%s' " % (result['username'], result['password'])
        try:
            cursor.execute(sql)
            row = cursor.fetchone()
            if row:
                session['username'] = row['username']
                session['userid'] = row['id']
                session['email'] = row['email']
                return redirect(url_for('blog'))
            else:
                return "用户名或密码错误 <a href='/login'>点击返回登录界面</a>"
        except:
            return '查询出错'


@app.route('/issue')
def issue():
    user = {}
    user['username'] = session.get("username", '')
    user['userid'] = session.get("userid", '')
    return render_template("issue.html", user=user)


@app.route('/issue_submit', methods=['GET', 'POST'])
def issue_submit():
    page = request.args.get('page', 1, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    if request.method == 'POST':
        result = request.form
        cursor = db.cursor()
        sql = "INSERT INTO paper(id,username,issue_date,title,content) VALUES('%s','%s','%s','%s','%s')" \
              % (result['userid'], result['username'], result['issue_date'], result['title'], result['content'])
        try:
            cursor.execute(sql)
            db.commit()
            return render_template("blog.html", data=username, papers=rows, page=page, total_pages=total_pages)
        except:
            db.rollback()
            return "发布失败!<a href='/issue'> 点击返回</a>"


@app.route('/manage')
def manage():
    cursor = db.cursor(pymysql.cursors.DictCursor)
    sql = "SELECT * FROM paper"
    cursor.execute(sql)
    papers = cursor.fetchall()
    return render_template("manage.html", papers=papers)


@app.route('/delete/<int:id>', methods=['POST'])
def delete(id):
    cursor = db.cursor()
    sql = "DELETE FROM paper WHERE id = %s"
    try:
        cursor.execute(sql, (id,))
        db.commit()
        return redirect(url_for('manage'))
    except Exception as e:
        db.rollback()
        return f"删除失败! {e} <a href='/manage'> 点击返回</a>"


images = [{'image1': "images/20231109154607.png", 'caption': 'image1'}]


@app.route('/ans')
def ans():
    page = request.args.get('page', 1, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    # 计算总的申请数量
    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    # 返回到申请列表页面
    return render_template("ans.html", papers=rows, page=page, total_pages=total_pages)


@app.route('/intro')
def intro():
    # GET 请求处理
    page = request.args.get('page', 3, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    if username:
        return render_template("intro.html", data=username, papers=rows, page=page, total_pages=total_pages)
    else:
        return render_template('intro.html', papers=rows, page=page, total_pages=total_pages)


@app.route('/fea')
def fea():
    # GET 请求处理
    page = request.args.get('page', 1, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    if username:
        return render_template("fea.html", data=username, papers=rows, page=page, total_pages=total_pages)
    else:
        return render_template('fea.html', papers=rows, page=page, total_pages=total_pages)


@app.route('/knowledge')
def knowledge():
    # GET 请求处理
    page = request.args.get('page', 3, type=int)
    per_page = 3

    cursor = db.cursor(pymysql.cursors.DictCursor)

    cursor.execute("SELECT COUNT(*) as count FROM paper")
    total_papers = cursor.fetchone()['count']
    total_pages = (total_papers + per_page - 1) // per_page

    offset = (page - 1) * per_page
    sql = "SELECT * FROM paper LIMIT %s OFFSET %s"
    cursor.execute(sql, (per_page, offset))
    rows = cursor.fetchall()

    username = session.get('username', '')
    if username:
        return render_template("knowledge.html", data=username, papers=rows, page=page, total_pages=total_pages)
    else:
        return render_template('knowledge.html', papers=rows, page=page, total_pages=total_pages)

if __name__ == '__main__':
    app.run(debug=True)
