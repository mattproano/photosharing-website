from getpass import getuser
import flask
from flask import Flask, Response, request, render_template, redirect, url_for, flash
from flaskext.mysql import MySQL
import flask_login
from werkzeug.utils import secure_filename

#for image uploading
import os, base64

import time

mysql = MySQL()
app = Flask(__name__)
app.secret_key = 'super secret string'  # Change this!

#These will need to be changed according to your creditionals
app.config['MYSQL_DATABASE_USER'] = 'root'
app.config['MYSQL_DATABASE_PASSWORD'] = 'OgufjpKj1232!'
app.config['MYSQL_DATABASE_DB'] = 'photosharedemo'
app.config['MYSQL_DATABASE_HOST'] = 'localhost'
mysql.init_app(app)

#begin code used for login
login_manager = flask_login.LoginManager()
login_manager.init_app(app)

conn = mysql.connect()
cursor = conn.cursor()
cursor.execute("SELECT email from Users")
users = cursor.fetchall()

def getUserList():
	cursor = conn.cursor()
	cursor.execute("SELECT email from Users")
	return cursor.fetchall()

class User(flask_login.UserMixin):
	pass

@login_manager.user_loader
def user_loader(email):
	users = getUserList()
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	return user

@login_manager.request_loader
def request_loader(request):
	users = getUserList()
	email = request.form.get('email')
	if not(email) or email not in str(users):
		return
	user = User()
	user.id = email
	cursor = mysql.connect().cursor()
	cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email))
	data = cursor.fetchall()
	pwd = str(data[0][0] )
	user.is_authenticated = request.form['password'] == pwd
	return user

'''
A new page looks like this:
@app.route('new_page_name')
def new_page_function():
	return new_page_html
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
	if flask.request.method == 'GET':
		return '''
			   <form action='login' method='POST'>
				<input type='text' name='email' id='email' placeholder='email'></input>
				<input type='password' name='password' id='password' placeholder='password'></input>
				<input type='submit' name='submit'></input>
			   </form></br>
		   <a href='/'>Home</a>
			   '''
	#The request method is POST (page is recieving data)
	email = flask.request.form['email']
	cursor = conn.cursor()
	#check if email is registered
	if cursor.execute("SELECT password FROM Users WHERE email = '{0}'".format(email)):
		data = cursor.fetchall()
		pwd = str(data[0][0] )
		if flask.request.form['password'] == pwd:
			user = User()
			user.id = email
			flask_login.login_user(user) #okay login in user
			return flask.redirect(flask.url_for('protected')) #protected is a function defined in this file

	#information did not match
	return "<a href='/login'>Try again</a>\
			</br><a href='/register'>or make an account</a>"

@app.route('/logout')
def logout():
	flask_login.logout_user()
	return render_template('hello.html', message='Logged out')

@login_manager.unauthorized_handler
def unauthorized_handler():
	return render_template('unauth.html')

#you can specify specific methods (GET/POST) in function header instead of inside the functions as seen earlier
@app.route("/register", methods=['GET'])
def register():
	return render_template('register.html', supress='True')

@app.route("/register", methods=['POST'])
def register_user():
	try:
		email=request.form.get('email')
		password=request.form.get('password')
		first_name=request.form.get('first_name')
		last_name=request.form.get('last_name')
		dob=request.form.get('dob')
		hometown=request.form.get('hometown')
		gender=request.form.get('gender')
		activity = 0
	except:
		print("couldn't find all tokens") #this prints to shell, end users will not see this (all print statements go to shell)
		return flask.redirect(flask.url_for('register'))
	cursor = conn.cursor()
	test =  isEmailUnique(email)
	if test:
		print(cursor.execute("INSERT INTO Users (email, password, first_name, last_name, dob, hometown, gender, activity) VALUES ('{0}', '{1}', '{2}', '{3}', '{4}', '{5}', '{6}', '{7}')".format(email, password, first_name, last_name, dob, hometown, gender, activity)))
		conn.commit()
		#log user in
		user = User()
		user.id = email
		flask_login.login_user(user)
		return render_template('hello.html', name=email, message='Account Created!')
	else:
		print("couldn't find all tokens")
		return flask.redirect(flask.url_for('register'))

def getUsersPhotos(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT imgdata, picture_id, caption FROM Pictures WHERE user_id = '{0}'".format(uid))
	return cursor.fetchall() #NOTE return a list of tuples, [(imgdata, pid, caption), ...]

def getUserIdFromEmail(email):
	cursor = conn.cursor()
	cursor.execute("SELECT user_id FROM Users WHERE email = '{0}'".format(email))
	return cursor.fetchone()[0]

def isEmailUnique(email):
	#use this to check if a email has already been registered
	cursor = conn.cursor()
	if cursor.execute("SELECT email  FROM Users WHERE email = '{0}'".format(email)):
		#this means there are greater than zero entries with that email
		return False
	else:
		return True
#end login code

#add friends by email
@app.route('/addfriend', methods=['GET', 'POST'])
@flask_login.login_required
def addfriend():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		friend_email = request.form.get('friend_email')
		fid = getUserIdFromEmail(friend_email)

		cursor = conn.cursor()
		cursor.execute("INSERT INTO Friends(user_id, friend_id) VALUES ('{0}', '{1}')".format(uid, fid))
		conn.commit()
		return render_template('addfriend.html', message='Friend added successfully')
	else:
		return render_template('addfriend.html')

#view your friends list
@app.route('/viewfriendslist', methods=['GET'])
@flask_login.login_required
def viewfriendslist():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, email FROM Users WHERE user_id IN (SELECT friend_id FROM Friends WHERE user_id = '{0}')".format(uid))
	friends_list = cursor.fetchall()
	
	return render_template('viewfriendslist.html', yourfriends=friends_list)

@app.route('/profile')
@flask_login.login_required
def protected():
	return render_template('hello.html', name=flask_login.current_user.id, message="Here's your profile")

#begin photo uploading code
# photos uploaded using base64 encoding so they can be directly embeded in HTML
ALLOWED_EXTENSIONS = set(['png', 'jpg', 'jpeg', 'gif'])
def allowed_file(filename):
	return '.' in filename and filename.rsplit('.', 1)[1] in ALLOWED_EXTENSIONS


@app.route('/upload', methods=['GET', 'POST'])
@flask_login.login_required
def upload_file():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		cursor= conn.cursor()
		cursor.execute("UPDATE Users SET activity = activity + 1 WHERE user_id = '{0}'".format(uid))
		conn.commit()
		imgfile = request.files['photo']
		caption = request.form.get('caption')
		tags = request.form.get('tag')
		album_name = request.form.get('album_name')
		photo_data =imgfile.read()
		likecount = 0
		cursor = conn.cursor()
		
		cursor.execute("SELECT album_name FROM Albums WHERE user_id = '{0}'".format(uid))
		albums = cursor.fetchall()
		album_exists = False
		for i in range(len(albums)):
			if album_name == str(albums[i][0]):
				album_exists = True
		if album_exists == False:
			return render_template('upload.html', message='Album must exist and you must own it before photo uploaded. Please try again.')

		cursor.execute("SELECT album_id FROM Albums WHERE user_id = '{0}' AND album_name = '{1}'".format(uid,album_name))
		album_id = cursor.fetchone()[0]
		cursor.execute('''INSERT INTO Pictures (imgdata, user_id, caption, album_id, likecount) VALUES (%s, %s, %s, %s, %s)''', (photo_data, uid, caption, album_id, likecount))
		conn.commit()
		pic_id = cursor.lastrowid

		tags = tags.split()
		num_tag = len(tags) - 1 
		cursor = conn.cursor()

		while num_tag >= 0:
			cursor.execute("INSERT INTO Tags(tag_text) VALUES ('{0}')".format(tags[num_tag]))
			conn.commit()
			tag_id = cursor.lastrowid
			cursor.execute("INSERT INTO PictureTags(picture_id, tag_id) VALUES ('{0}', '{1}')".format(pic_id, tag_id))
			conn.commit()
			num_tag -= 1

		return render_template('hello.html', name=flask_login.current_user.id, message='Photo uploaded!', photos=getUsersPhotos(uid), base64=base64)
	#The method is GET so we return a  HTML form to upload the a photo.
	else:
		return render_template('upload.html')
#end photo uploading code

@app.route('/make_album', methods=['GET', 'POST'])
@flask_login.login_required
def makeAlbum():
	if request.method == 'POST':
		album_name = request.form.get('album_name')
		uid = getUserIdFromEmail(flask_login.current_user.id)
		start_date = time.strftime('%Y-%m-%d')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Albums(album_name, user_id, start_date) VALUES ('{0}', '{1}', '{2}')".format(album_name, uid, start_date))
		conn.commit()
		return render_template('hello.html', message='Album created.')
	else:
		return render_template('make_album.html')

@app.route('/deletephoto', methods=['GET', 'POST'])
@flask_login.login_required
def deletePhoto():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = request.form.get('pid')
		cursor = conn.cursor()
		cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
		owner = cursor.fetchone()[0]
		if owner == uid:
			cursor.execute("DELETE FROM Comments WHERE picture_id = '{0}'".format(pid))
			conn.commit()
			cursor.execute("DELETE FROM PictureTags WHERE picture_id = '{0}'".format(pid))
			conn.commit()
			cursor.execute("DELETE FROM UserLikes WHERE picture_id = '{0}'".format(pid))
			conn.commit()
			cursor.execute("DELETE FROM Pictures WHERE picture_id = '{0}'".format(pid))
			conn.commit()
			return render_template('deletephoto.html', message='Photo deleted')
		else:
			return render_template('deletephoto.html', message='You dont own this photo')
	else:
		return render_template('deletephoto.html')

@app.route('/deletealbum', methods=['GET', 'POST'])
@flask_login.login_required
def deleteAlbum():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		aname = request.form.get('aname')
		cursor = conn.cursor()
		cursor.execute("SELECT user_id FROM Albums WHERE album_name = '{0}'".format(aname))
		owner = cursor.fetchone()[0]
		if owner == uid:
			cursor.execute("SELECT album_id FROM Albums WHERE album_name = '{0}'".format(aname))
			aid = cursor.fetchone()[0]

			cursor.execute("DELETE FROM Pictures WHERE album_id = '{0}'".format(aid))
			conn.commit()
			cursor.execute("DELETE FROM Albums WHERE album_id = '{0}'".format(aid))
			conn.commit()
			return render_template('deletealbum.html', message='Album deleted')
		else:
			return render_template('deletealbum.html', message='You dont own this album')
	else:
		return render_template('deletealbum.html')

@app.route('/viewyourphotos', methods=['GET'])
@flask_login.login_required
def viewyourphotos():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.caption, A.album_name, P.picture_id, P.likecount FROM Pictures P, Albums A WHERE P.album_id = A.album_id AND P.user_id = '{0}'".format(uid))
	pictures = cursor.fetchall()
	return render_template('hello.html', message='Here are all your photos', yourphotos=pictures, base64=base64)

@app.route('/viewallphotos', methods=['GET'])
def viewallphotos():
	cursor = conn.cursor()
	cursor.execute("SELECT P.imgdata, P.caption, U.first_name, U.last_name, A.album_name, P.picture_id, P.likecount FROM Pictures P, Users U, Albums A WHERE P.user_id = U.user_id AND P.album_id = A.album_id ORDER BY P.picture_id DESC")
	pictures = cursor.fetchall()

	cursor = conn.cursor()
	cursor.execute("SELECT COUNT(DISTINCT user_id) FROM UserLikes GROUP BY picture_id")
	picture_like_counts = cursor.fetchall()

	return render_template('hello.html', message='Here are all photos posted to Photoshare', allphotos=pictures, picture_like_counts = picture_like_counts, base64=base64)

@app.route('/searchbyalbum', methods=['GET', 'POST'])
def searchbyalbum():
	if request.method == 'POST':
		album_names = request.form.get('album_names')
		album_names = album_names.split()
		return render_template('searchbyalbum.html', photos=photobyalbum(album_names), base64=base64)
	else:
		return render_template('searchbyalbum.html')

def photobyalbum(albums):
	photos = []
	cursor = conn.cursor()
	for x in range(len(albums)):
		cursor.execute("SELECT P.imgdata, P.caption, A.album_name FROM Pictures P, Albums A WHERE P.album_id = A.album_id AND A.album_name = '{0}'".format(albums[x]))
		photos += cursor.fetchall()
	return photos

@app.route('/searchbytag', methods=['GET', 'POST'])
@flask_login.login_required
def searchbytag():
	if request.method == 'POST':
		tags = request.form.get('tags')
		tags = tags.split()
		return render_template('searchbytag.html', photos=photobytag(tags), yourphotos=yourphotobytag(tags), toptags = getTopTags(), base64=base64)
	else:
		return render_template('searchbytag.html', toptags = getTopTags())

def unique(array):
	temp = []
	for x in array:
		if x not in temp:
			temp.append(x)
	return temp

def photobytag(tags):
	photos = []
	cursor = conn.cursor()
	for x in range(len(tags)):
		cursor.execute("SELECT DISTINCT P.imgdata, P.caption, T.tag_text, P.picture_id FROM Users U, Pictures P, PictureTags PT, Tags T WHERE U.user_id = P.user_id AND P.picture_id = PT.picture_id AND PT.tag_id = T.tag_id AND T.tag_text = '{0}'".format(tags[x]))
		photo = cursor.fetchall()
		if photo not in photos:
			photos += photo
	return unique(photos)

def yourphotobytag(tags):
	yourphotos = []
	cursor = conn.cursor()
	uid = getUserIdFromEmail(flask_login.current_user.id)
	for x in range(len(tags)):
		cursor.execute("SELECT DISTINCT P.imgdata, P.caption, T.tag_text, P.picture_id FROM Users U, Pictures P, PictureTags PT, Tags T WHERE U.user_id = P.user_id AND P.picture_id = PT.picture_id AND PT.tag_id = T.tag_id AND T.tag_text = '{0}' AND U.user_id = '{1}'".format(tags[x], uid))
		yourphoto = cursor.fetchall()
		if yourphoto not in yourphotos:
			yourphotos += yourphoto
	return unique(yourphotos)

@app.route("/makecomment", methods=['GET', 'POST'])
@flask_login.login_required
def makecomment():
	if request.method == 'POST':
		comment_text = request.form.get('comment_text')
		if getUserIdFromEmail(flask_login.current_user.id): 
			uid = getUserIdFromEmail(flask_login.current_user.id)
		else:
			uid = -1
		pid = request.form.get('pid')
		
		cursor = conn.cursor()
		cursor.execute("SELECT user_id FROM Pictures WHERE picture_id = '{0}'".format(pid))
		owner = cursor.fetchone()[0]
		if owner == uid:
			return render_template('makecomment.html', message="cannot comment on your own photo!")
		cursor = conn.cursor()
		cursor.execute("UPDATE Users SET activity = activity + 1 WHERE user_id = '{0}'".format(uid))
		conn.commit()
		comment_date = time.strftime('%Y-%m-%d')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO Comments (comment_text, user_id, picture_id, comment_date) VALUES ('{0}', '{1}', '{2}', '{3}')".format(comment_text, uid, pid, comment_date))
		conn.commit()
		return render_template('makecomment.html', message="comment posted!")
	else:
		return render_template('makecomment.html')

@app.route("/viewcomments", methods=['GET', 'POST'])
def viewcomments():
	if request.method == 'POST':
		pid = request.form.get('pid')
		cursor = conn.cursor()
		cursor.execute("SELECT C.comment_text, U.first_name, U.last_name FROM Comments C, Users U WHERE U.user_id = C.user_id AND C.picture_id = '{0}'".format(pid))
		comments = cursor.fetchall()
		return render_template('viewcomments.html', message="comments on post", comments=comments, pid=pid)
	else:
		return render_template('viewcomments.html')

@app.route("/likepost", methods=['GET', 'POST'])
@flask_login.login_required
def likepost():
	if request.method == 'POST':
		uid = getUserIdFromEmail(flask_login.current_user.id)
		pid = request.form.get('pid')
		cursor = conn.cursor()
		cursor.execute("INSERT INTO UserLikes (user_id, picture_id) VALUES ('{0}', '{1}')".format(uid, pid))
		conn.commit()
		cursor.execute("UPDATE Pictures SET likecount = likecount + 1 WHERE picture_id = '{0}'".format(pid))
		conn.commit()
		return render_template('likepost.html', message="post liked!")
	else:
		return render_template('likepost.html')

@app.route("/topten", methods=['GET'])
def topten():
	cursor = conn.cursor()
	cursor.execute("SELECT first_name, last_name, activity FROM Users ORDER BY activity DESC LIMIT 10")
	topten = cursor.fetchall()
	return render_template('hello.html', topten=topten, message='Top ten users listed by photo and comment count')

def getTopTags():
	cursor = conn.cursor()
	cursor.execute("SELECT T.tag_text, COUNT(T.tag_text) FROM Tags T GROUP BY T.tag_text")
	tags_and_counts = cursor.fetchall()
	return tags_and_counts

@app.route("/usercommentsearch", methods=['GET', 'POST'])
def usercommentsearch():
	if request.method == 'POST':
		comment_text = request.form.get('comment_text')
		cursor = conn.cursor()
		cursor.execute("SELECT DISTINCT U.email, U.first_name, U.last_name FROM Users U, Comments C WHERE U.user_id = C.user_id AND C.comment_text = '{0}' ORDER BY U.user_id DESC".format(comment_text))
		results = cursor.fetchall()
		return render_template('usercommentsearch.html', results=results)
	else:
		return render_template('usercommentsearch.html')

@app.route("/recfriend", methods=['GET'])
@flask_login.login_required
def recfriend():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	cursor = conn.cursor()
	cursor.execute("SELECT email FROM Users WHERE user_id IN (SELECT B.friend_id FROM Friends A, Friends B WHERE A.friend_id = B.user_id AND A.user_id = '{0}')".format(uid))
	friendrecs = cursor.fetchall()
	return render_template('hello.html', friendrecs = friendrecs, message="here are your friend recommendations")

def getUserTop5Tags(uid):
	cursor = conn.cursor()
	cursor.execute("SELECT T.tag_text FROM Users U, Tags T, PictureTags PT, Pictures P WHERE P.picture_id = PT.picture_id AND PT.tag_id = T.tag_id AND P.user_id = U.user_id AND U.user_id = '{0}' GROUP BY T.tag_text ORDER BY COUNT(T.tag_text) DESC LIMIT 5".format(uid))
	usertop5 = cursor.fetchall()
	return usertop5

@app.route("/umayalsolike", methods=['GET'])
@flask_login.login_required
def umayalsolike():
	uid = getUserIdFromEmail(flask_login.current_user.id)
	top5 = getUserTop5Tags(uid)
	cursor = conn.cursor()
	unordered = []
	for x in range(len(top5)):
		cursor.execute("SELECT P.imgdata FROM Users U, Pictures P, PictureTags PT, Tags T WHERE U.user_id = P.user_id AND P.picture_id = PT.picture_id AND PT.tag_id = T.tag_id AND T.tag_text = ('{0}') AND U.user_id <> ('{1}')".format(top5[x], uid))
		unordered += cursor.fetchall()
	unordered = unique(unordered)
	# this recommender doesnt tie break or select best recommendations
	# but it DOES recommender photos with matching tags that other users have posted
	
	return render_template('hello.html', umayalsolike = unordered, message="you may like these pictures!", base64=base64)


#default page
@app.route("/", methods=['GET'])
def hello():
	return render_template('hello.html', message='Welecome to Photoshare')


if __name__ == "__main__":
	#this is invoked when in the shell  you run
	#$ python app.py
	app.run(port=5000, debug=True)
