from flask import Blueprint, render_template
from flask_login import LoginManager
from flask_login.utils import login_required, login_user, current_user
from flask import current_app, request
from jinja2 import TemplateNotFound
import psycopg2 as dbapi2
import flask

from flask import Flask
from flask import redirect
from flask import render_template
from flask.helpers import url_for

from branch_operations import site

@site.route('/profile', methods=['GET', 'POST'])
@login_required
def profile_page():
    if request.method == 'POST':
        if request.form['action'] == 'sendPost':
            postContent = request.form['postContent']
            username = current_user.userName
            with dbapi2.connect(flask.current_app.config['dsn']) as connection:
                cursor = connection.cursor()

                query = """INSERT INTO POST(USERNAME, CONTENT) VALUES(%s, %s)"""
                cursor.execute(query,(username, postContent))

                query = """SELECT POSTID FROM POST WHERE (USERNAME = %s and CONTENT = %s)"""
                cursor.execute(query,(username, postContent))
                postid = cursor.fetchall()

                query = """SELECT FOLLOWER FROM FOLLOW WHERE (FOLLOWING = %s)"""
                cursor.execute(query,(username,))
                followers = cursor.fetchall()


                query = """INSERT INTO FEED(USERNAME, POSTID) VALUES(%s, %s)"""
                cursor.execute(query,(username, postid[0]))

                for user in followers:
                    query = """INSERT INTO FEED(USERNAME, POSTID) VALUES(%s, %s)"""
                    cursor.execute(query,(user[0], postid[0]))

                connection.commit()
            return redirect(url_for('site.profile_page'))
        elif request.form['action'] == 'sendTitle':
            titleContent = request.form['titleContent']
            username = current_user.userName
            with dbapi2.connect(flask.current_app.config['dsn']) as connection:
                cursor = connection.cursor()

                query = """INSERT INTO HOTTITLES(TOPIC, USERNAME) VALUES(%s, %s)"""
                cursor.execute(query,(titleContent, username))

                connection.commit()
            return redirect(url_for('site.profile_page'))
        elif request.form['action'] == 'updateTitle':
            updateContent = request.form['titleUpdate']
            titleContent = request.form['content']
            username = current_user.userName
            with dbapi2.connect(flask.current_app.config['dsn']) as connection:
                cursor = connection.cursor()

                query = """UPDATE HOTTITLES SET TOPIC = %s WHERE USERNAME = %S AND TOPIC = %s"""
                cursor.execute(query,(updateContent, username, titleContent))

                connection.commit()
            return redirect(url_for('site.profile_page'))
        else:
            return redirect(url_for('site.profile_page'))
    else:
        with dbapi2.connect(flask.current_app.config['dsn']) as connection:
            cursor = connection.cursor()
            username = current_user.userName

            ## posts
            query = """SELECT POSTID FROM FEED WHERE USERNAME = %s ORDER BY POSTID DESC"""
            cursor.execute(query, [username])
            postids = cursor.fetchall()


            posts = []

            for id in postids:
                query = """SELECT * FROM POST NATURAL JOIN USERS  WHERE POSTID = %s ORDER BY POSTID DESC"""
                cursor.execute(query, [id[0]])
                posts.append(cursor.fetchall())


            ## Lectures
            query = """SELECT CRN FROM CLASSES WHERE USERNAME = %s"""
            cursor.execute(query, [username])
            lectures = cursor.fetchall()

            ## Faculty
            query = """SELECT D.NAME FROM DEPARTMENTS AS D INNER JOIN DEPARTMENTLIST AS L ON D.FACULTYNO =L.FACULTYNO  WHERE L.USERNAME = %s"""
            cursor.execute(query, [username])
            faculty = cursor.fetchall()

            ##Student Branches
            query = """SELECT * FROM STUDENTBRANCHES_CASTING WHERE PERSON_NAME = %s"""
            cursor.execute(query, [username])
            ids = cursor.fetchall()

            sbranches = []
            for id in ids:
                query = """SELECT * FROM STUDENTBRANCHES WHERE ID = %s"""
                cursor.execute(query, [id[0]])
                sbranches.append(cursor.fetchall())

            ##Hot Titles
            query = """SELECT * FROM HOTTITLES WHERE (ID <= 10)"""
            cursor.execute(query)
            titles = cursor.fetchall()

            ##My Titles
            query = """SELECT * FROM HOTTITLES WHERE USERNAME = %s"""
            cursor.execute(query, [current_user.userName])
            mytitles = cursor.fetchall()

            connection.commit()
        return render_template('profile_page.html', user = current_user, results = posts, lectures = lectures, branches = sbranches, titles = titles, mytitles = mytitles, faculty = faculty)

@site.route('/post_cfg/<postid>', methods=['GET', 'POST'])
def post_cfg(postid):
    if request.method == 'POST':
        if request.form['action'] == 'updatePost':
            postContent = request.form['postContent']
            with dbapi2.connect(flask.current_app.config['dsn']) as connection:
                cursor = connection.cursor()

                query = """UPDATE POST SET CONTENT= %s WHERE (POSTID= %s)"""

                cursor.execute(query, (postContent, postid))

                connection.commit()
            return redirect(url_for('site.post_cfg', postid = postid))
        elif request.form['action'] == 'deletePost':
            with dbapi2.connect(flask.current_app.config['dsn']) as connection:
                cursor = connection.cursor()

                query = """SELECT * FROM CLASSPOSTS WHERE POSTID = %s"""
                cursor.execute(query, [postid])
                result = cursor.fetchall()

                if len(result) ==0:
                    query = """DELETE FROM POST WHERE (POSTID= %s)"""
                    cursor.execute(query, [postid])
                else:
                    query = """DELETE FROM CLASSPOSTS WHERE (POSTID= %s)"""
                    cursor.execute(query, [postid])
                    query = """DELETE FROM POST WHERE (POSTID= %s)"""
                    cursor.execute(query, [postid])

                connection.commit()
            return render_template('post_cfg.html', message = "Post is successfully deleted")
        elif request.form['action'] == 'searchPost':
            postContent=request.form['search-content']
            with dbapi2.connect(flask.current_app.config['dsn']) as connection:
                cursor = connection.cursor()

                query = """SELECT * FROM POST WHERE CONTENT = %s"""
                cursor.execute(query, [postContent])

                datas=cursor.fetchall()
                connection.commit()
            return render_template('post_cfg.html', result=datas)
        else:
            return render_template('post_cfg.html')
    else:
        with dbapi2.connect(flask.current_app.config['dsn']) as connection:
            cursor = connection.cursor()

            query = """SELECT * FROM POST WHERE POSTID = %s"""

            cursor.execute(query, [postid])
            post = cursor.fetchall()

            query = """SELECT NAME FROM USERS WHERE USERNAME = %s"""

            cursor.execute(query, (post[0][1],))
            fullname = cursor.fetchall()

            connection.commit()
        return render_template('post_cfg.html', post = post, fullname = fullname)

@site.route('/follow_cfg', methods=['GET', 'POST'])
def follow_cfg():
    with dbapi2.connect(flask.current_app.config['dsn']) as connection:
        cursor = connection.cursor()
        if request.method == 'POST':
            query = """SELECT FOLLOWER FROM FOLLOW WHERE FOLLOWING = %s"""
            cursor.execute(query, (current_user.userName,))

            followers=cursor.fetchall()
            follower_data = []
            for follower in followers:
                query = """SELECT * FROM USERS WHERE USERNAME = %s"""
                cursor.execute(query, (follower[0],))
                follower_data.append(cursor.fetchall())

                followings=cursor.fetchall()
                following_data = []
                for following in followings:
                    query = """SELECT * FROM USERS WHERE USERNAME = %s"""
                cursor.execute(query, (following[0],))
                following_data.append(cursor.fetchall())

            connection.commit()
            return render_template('follow_cfg.html', followers = follower_data, followings = following_data)
        if request.method == 'GET':

            return render_template('follow_cfg.html', followers = follower_data, followings = following_data)