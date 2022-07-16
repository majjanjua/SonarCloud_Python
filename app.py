from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_bootstrap import Bootstrap
from flask_session import Session
from datetime import datetime, timedelta
import os , requests, random, json ,io , sys
import urllib.request
import urllib.parse
from flask_paginate import Pagination, get_page_parameter
from models import requestdetails, message, images
from models import users
import PIL.Image as Image

'''Libraries required for connection of postgreSQL database Need to install sqlalchemy and psycopg2
Command : pip install sqlalchemy psycopg2'''

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

# Method to have an authenticated connection to the database
#template : engine = create_engine('postgresql+psycopg2://user:password@hostname/database_name')
#Connectionto the Local Database
#os.environ['DATABASE_URL'] = "postgresql+psycopg2://postgres:mutemath@localhost:5433/flask"
#Connection to Heroku database



# #for establising connection to the DB
engine = create_engine(os.getenv('DATABASE_URL'))
# #For creating a session with the DB
db = scoped_session(sessionmaker(bind=engine))

app = Flask(__name__)
Bootstrap(app)
app.config['SECRET_KEY'] = os.urandom(24)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
# Session parameters
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

#db.init_app(app)

# Variables to be used in the page

request_parameters = ["name", "email", "problem", "language", "deadline", "secretkey"]
db_secret_key = ""
query_existsStatus = False
db_id=0
popupStatus = True
login_Status = False
description = "- Helping Code | student coding | Assignments Coding Exercises"
laguages_list = ["Bash", "Python", "JavaScript", "Java", "C", "C++", "Others"]


def create_session(username):
	if 'logged_user' not in session:
		session['logged_user'] = ''
	session['logged_user'] = username
	session['login_status'] = True

def check_session(username):
	if 'login_status' in session:
		if session['login_status']:
			if session['logged_user'] == username:
				return True
	else:
		return False

def get_session():
	if 'logged_user' in session:
		return session['logged_user']
	else:
		return False

def delete_session():
	session.pop('logged_user', None)
	session['login_status'] = False
	print(session)

def get_message_count():
	messages_length = message.query.all()
	# db.commit()
	return messages_length

@app.route('/logout', methods=["GET","POST"])
def logout():
	global login_Status
	delete_session()
	login_Status=False
	return redirect(url_for('homepage'))

@app.route('/login', methods=["GET","POST"])
def login():
	global login_Status
	if request.method == "POST":
		username=request.form.get('username')
		password=request.form.get('password')
		user_status=False
		#fetch from the DB all the users and password
		#users = db.execute("SELECT * FROM users").fetchall()
		users_list = users.query.all()
		#For the case in which no user exists in the DB
		if len(users_list) == 0:
			return render_template('error.html', error_message="No user currently active. Please register a user First.") 	
		#For any other user.
		else:
			#First a check if the user exists or not.
			for user in users_list:
				if username == user.username:
					user_status = True
					userId = user.id			
			#If the user exists, then redirect it to homepage for the user after fetching the password for the user, based on id in the db.								
			if user_status:
				user_password = users.query.get(userId)
				#Matching for the password entered and password fetched from the DB.
				if password == user_password.password:
					create_session(username)
					print(session)
					return redirect(url_for('homepage'))
				else:
					return render_template('login.html', title="Login" + description, error_message="Invalid username or password.",login_status=False)	
			else:
				return render_template('login.html', title="Login" + description, error_message="Invalid username or password.",login_status=False)
	else:
		return render_template('login.html', title="Login")

@app.route('/register', methods=["GET","POST"])
def register():
	if request.method == "POST":
		username=request.form.get('username')
		email=request.form.get('email')
		password=request.form.get('password')
		repeat_password=request.form.get('password-repeat')
		#For matching both the password entered.
		if password != repeat_password:
			return render_template('register.html', title = "Register" + description, message="Password's dont match", error_message_status=True)
		#For adding the newly added user in the DB.
		else:
			#Before adding in the Db , check if the username already exists
			users = db.execute("SELECT * FROM users").fetchall()
			for user in users:
				#User already exists display output
				if username == user.username:
					return render_template('register.html', title = "Register"+ description, message="User already exists. Please enter a different username.", error_message_status=True) 		
			#Addign the user in the DB.
			db.execute("INSERT INTO users (username, password, email) VALUES (:username, :password, :email)", {"username": username, "password": password, "email":email})
			db.commit()					
		#For validation of the actual addition of the user
		users = db.execute("SELECT * FROM users").fetchall()
		if len(users) == 0:
			return render_template('error.html', error_message="User not added successfully in the DB.")
		else:
			for user in users:
				#To check for the username in the complete arrray of users and then update the matchStatus flag.
				if user.username == username:
					matchStatus = True
				else:
					matchStatus=False	
		#Final check for the validation of the user in the DB.			
		if matchStatus:
			return render_template('register.html', title = "Register"+ description, message="User successfully added.", message_status=True)
		else:
			return render_template('register.html', title = "Register" + description, message="Error while user addition", error_message_status=True)
		return render_template('register.html', title = "Register" + description)
	else:
		return render_template('register.html', title="Register" + description)

'''
	This is for the homepage of a  user 
'''
@app.route("/", methods=["GET", "POST"])
def homepage():
	global popupStatus
	if 'login_status' not in session:
		session['login_status'] = False	

		
	#today_quote= random.choice(quotes)
	today_quote = { "q" : "Jarvis, sometimes you got to run, before you can walk","a":"Robert Downey Jr."}
	#problemQuestions = db.execute("SELECT * FROM requestdetails")
	page = request.args.get('page', type=int, default=1)
	problemQuestions = requestdetails.query.order_by(requestdetails.id.desc()).paginate(per_page=3, page=page)
	if len(problemQuestions.items) > 0:
		if popupStatus:
			popupStatus=False
			if session['login_status']:
				username = get_session()
				return render_template('home_new.html', title="Home" + description, popup=True, today_quote=today_quote, loginStatus=session['login_status'], user=username,problemQuestions=problemQuestions,queryPresent=True)
			else:
				return render_template('home_new.html', title="Home" + description, popup=True, today_quote=today_quote,problemQuestions=problemQuestions,queryPresent=True)
		else:
			if session['login_status']:
				username= get_session()
				return render_template('home_new.html', title="Home" + description, popup=False,today_quote=today_quote, loginStatus=session['login_status'], user=username, problemQuestions=problemQuestions,queryPresent=True)
			else:
				return render_template('home_new.html', title="Home" + description, popup=False,today_quote=today_quote, problemQuestions=problemQuestions,queryPresent=True)
	else:
		return render_template('home_new.html', title="Home" + description, popup=False, today_quote=today_quote, queryPresent=False)

#This is for the about page
@app.route('/about', methods=["GET","POST"])
def about():
    if 'login_status' not in session:
        session['login_status'] = False	
    message_length=get_message_count()
    if session['login_status']:
        username= get_session()
        return render_template('about.html', title="About" + description,length=len(message_length),user=username,loginStatus=session['login_status'])
    else:
    	return render_template('about.html', title="About" + description,length=len(message_length))

#This is for the contact page
@app.route('/contact',methods=['GET','POST'])
def contact():
	message_length=get_message_count()
	if request.method == "POST":
		if session['login_status']:
			username = get_session()      
			name_details = request.form.get('name')
			email_detials = request.form.get('email')
			message = request.form.get('message')
			db.execute("INSERT INTO message (name, email, message) VALUES (:name_details, :email_detials, :message )", {"name_details": name_details, "email_detials": email_detials, "message": message}) 
			db.commit()
			return render_template('contact.html' ,message_written=True,title="Contact" + description,length=len(message_length),loginStatus=session['login_status'], user=username)
		else:
			return render_template('contact.html' ,message_written=True,title="Contact" + description,length=len(message_length),)
	else:
		if session['login_status']:
			username = get_session()
			return render_template('contact.html',message_written=False,title="Contact" + description,length=len(message_length),loginStatus=session['login_status'], user=username)
		else:
			return render_template('contact.html',message_written=False,title="Contact" + description,length=len(message_length))

#This is for the page , to add a query
@app.route('/addrequest', methods=["GET","POST"])
def addrequest():
	global query_existsStatus
	message_length=get_message_count()
	if request.method == "POST":	
		buttonRequest =  request.form.get('buttonrequest')
		fetched_request_parameters=[]
		for item in request_parameters:
			fetched_request_parameters.append(request.form.get(item))
			time = datetime.now().strftime("%d %b, %Y")	
		if buttonRequest == 'update':	
			queryDetails = requestdetails.query.filter_by(secretkey=fetched_request_parameters[5]).first()
			db.session.delete(queryDetails)
		secreyKeyList = requestdetails.query.order_by(requestdetails.secretkey).all()
		for query in secreyKeyList:
			if fetched_request_parameters[5] == query.secretkey :
				return render_template('addrequest.html', title="Add Request" + description,length=len(message_length),laguages_list=laguages_list,secreyKeystatus=True)
		requestObj = requestdetails(name=fetched_request_parameters[0], email=fetched_request_parameters[1], problem=fetched_request_parameters[2], language=fetched_request_parameters[3], updatedate=time, deadline=fetched_request_parameters[4], secretkey=fetched_request_parameters[5], solution='Will be updated.')
		db.session.add(requestObj)
		db.session.commit()	
		return redirect(url_for('homepage'))
	else:
		if session['login_status']:
			username = get_session()
			return render_template('addrequest.html', title="Add Request" + description,length=len(message_length),laguages_list=laguages_list,loginStatus=session['login_status'], user=username)
		else:
			return render_template('addrequest.html', title="Add Request" + description,length=len(message_length),laguages_list=laguages_list)	

#This is for the messages page
@app.route('/messages', methods=["GET","POST"])
def messages():
	message_length=get_message_count()
	if len(message_length) > 0:
		return render_template('messages.html', message=message_length, title="Messages" + description, message_status=True,length=len(message_length))
	else:
		return render_template('messages.html', title="Messages" + description,message_status=False,length=len(message_length))

#This is if you want o modify any query already present on the home page
@app.route('/modify/<int:id>', methods=["GET","POST"])
def modify(id):
	message_length=get_message_count()
	global query_existsStatus, db_secret_key, fetchedData, db_id
	fetchedData=db.execute("SELECT * FROM requestdetails WHERE id=:id", { "id" : id}).fetchone()
	db.commit()
	db_secret_key=fetchedData["secretkey"]
	db_id=fetchedData["id"]
	query_existsStatus=True
	return render_template('addrequest.html', title="Add Request" + description, fetchedData=fetchedData, modification=True ,secretMatching=True,length=len(message_length))

@app.route('/search',methods=["GET","POST"])
def search():
	search_results=[]
	message_length=get_message_count()
	search_parameter=request.form.get('searchtext')
	all_query=requestdetails.query.all()
	for item in all_query:
		query=item
		if search_parameter.lower() in str(item.problem).lower():
			search_results.append(query)
	if len(search_results) > 0:
		if session['login_status']:
			username = get_session()
			return render_template('search.html', title="Search Results" + description,length=len(message_length), search_text=search_parameter, search_results=search_results, result_status=True,loginStatus=session['login_status'], user=username)
		else:
			return render_template('search.html', title="Search Results" + description,length=len(message_length), search_text=search_parameter, search_results=search_results, result_status=True)			
	else:
		if session['login_status']:
			username = get_session()
			return render_template('search.html', title="Search Results" + description,length=len(message_length), search_text=search_parameter,result_status=False,loginStatus=session['login_status'], user=username)
		else:
  			return render_template('search.html', title="Search Results" + description,length=len(message_length), search_text=search_parameter,result_status=False)

@app.route('/language/<string:lang>', methods=["GET","POST"])
def lang(lang):
	image_list = os.listdir(os.getcwd()+"/static/images/languages")
	message_length=get_message_count()
	return render_template('languages/'+lang+'.html', title=lang.capitalize() ,length=len(message_length))

@app.route('/news',methods=["GET","POST"])
def getnews():
	key=request.form.get('key')
	date_N_days_ago = datetime.now() - timedelta(days=10)
	date_N_days_ago = date_N_days_ago.strftime("%Y-%m-%d")
	if key is not None:
		main_url = " http://newsapi.org/v2/everything?q="+key+"&from="+date_N_days_ago+"&sortBy=publishedAt&apiKey=49213237c2684589859959522b51848f&language=en&pageSize=10"
		keyword_search=True		
	else:
		main_url = " http://newsapi.org/v2/everything?q=coding-languages&from="+date_N_days_ago+"&sortBy=publishedAt&apiKey=49213237c2684589859959522b51848f&language=en&pageSize=10"	
		keyword_search=False	
	news_fetched = requests.get(main_url).json()
	if session['login_status']:
		username = get_session()
		return render_template('news.html', title="News" + description, news=news_fetched, key=key, keyword_search_status=keyword_search,loginStatus=session['login_status'], user=username)
	else:
		return render_template('news.html', title="News" + description, news=news_fetched, key=key, keyword_search_status=keyword_search)

@app.route('/recover',methods=["GET","POST"])
def recover_password():
	if request.method == "POST":
		userStatus=False
		response="failure"
		username=request.form.get('username')
		mobile_number=request.form.get('number')
		users=db.execute("SELECT * FROM users").fetchall()
		db.commit()
		for user in users:
			user_id=user[0]
			if user[1] == username:
				password=db.execute("SELECT password FROM users WHERE id=:id",{"id":user_id}).fetchone()[0]
				db.commit()
				userStatus=True
				message="Hello " + username+"\n"+"Your password is: "+password+"\n"+"Have a nice day."+"\n"+"CodeForYouu."		
				response=send_text_message('ooj5eMPQ+LI-yvpgbK1u4tL36iRaZP6ItJ7LVZ8Wu2',mobile_number,message)
		print(response)
		if response == "success":		
			return render_template('recover.html',title="Recovery" + description, userStatus=userStatus, success_message="Message sent successfully on the number provided.")
		else:
			return render_template('recover.html',title="Recovery" + description, userStatus=userStatus, error_message="No such user exists. Please check the username and try again.")
	else:		
		return render_template('recover.html',title="Recovery" + description, userStatus=True)

#To send text messages using the TextLocal messaing gateway.
def send_text_message(apikey, numbers, message):
	data =  urllib.parse.urlencode({'apikey': apikey, 'numbers': numbers,'message' : message})
	data = data.encode('utf-8')
	request = urllib.request.Request("https://api.textlocal.in/send/?")
	f = urllib.request.urlopen(request, data)
	fr = f.read()
	dict_str = fr.decode("UTF-8")
	res = json.loads(dict_str)
	print (res)
	return (res["status"])


@app.route('/blog',methods=["GET","POST"])
def blog():
    image_list = os.listdir(os.getcwd()+"/static/images/languages")
    if session['login_status']:
        username = get_session()
        
        return render_template('blog.html',title="Blog" + description,images=image_list, loginStatus=session['login_status'], user=username)
    else:
        return render_template('blog.html',title="Blog" + description,images=image_list)


@app.route('/problemquery/<int:id>',methods=['GET','POST'])
def problemquery(id):
	querydetails = db.execute("SELECT * FROM requestdetails WHERE id=:id", { "id" : id}).fetchone()
	print(querydetails)
	if request.method == "POST":
		new_comment = request.form.get("newComment")
		commentsList = querydetails["comments"]
		commentsList.append(new_comment)
		cssProperties = db.execute("UPDATE requestdetails SET comments=:new_comments WHERE id=:id",{"new_comments":commentsList, "id":id})
		db.commit()
	return render_template('query.html', title="Query" + description, query=querydetails)


@app.route('/pagination', methods=['GET','POST'])
def pagination():
	page = request.args.get('page', type=int, default=1)
	querydetails = requestdetails.query.order_by(requestdetails.id).paginate(per_page=3, page=page)
	# querydetails = requestdetails.query.all()
	# return jsonify({
	# 	"name": querydetails[0].name,
	# 	"email": querydetails[0].email,
	# 	"problem": querydetails[0].problem
	# })
	return render_template('pagination.html', title="Pagination", queries=querydetails)

@app.route('/update', methods=["GET","POST"])
def updaterequest():
    if request.method == "POST":
        secretKey = request.form.get('secretKey')
        queryDetails = requestdetails.query.filter_by(secretkey=secretKey).first()
        if queryDetails is None:
            return render_template('update.html', title="Update" + description, update=False, secretKey=secretKey, queryStatus=False)
        else:
            return render_template('update.html', title="Update" + description, update=False, secretKey=secretKey,queryDetails=queryDetails, laguages_list=laguages_list, queryStatus=True)
    else:
        if session['login_status']:
            username= get_session()
            return render_template('update.html', title="Update" + description, update=True, loginStatus=session['login_status'], user=username)
        else:
            return render_template('update.html', title="Update" + description, update=True)

@app.route('/userdetails', methods=['GET','POST'])
def userdetails():    
    username=get_session()    
    if request.method == "POST":
        file_name = str(username) +'.jpg'
        button_value= request.form.get('button_value')
        if button_value == "update_bio":
            return "Update bio details invoked"
        elif button_value == "Update Profile Pic":
            if (os.getcwd() + '/static/images/profile-pictures/' + file_name) == True :
                os.remove(os.getcwd() + '/static/images/profile-pictures/' + file_name)
            file = request.files['file']
            img_array = file.read()
            # To check if an entry already exists for a username 
            existing_profile_images = images.query.all()
            for entry in existing_profile_images:
                if entry.username == username:
                    db.session.delete(entry)
            userObj = images(username=username, img=img_array, filename=file_name)      
            db.session.add(userObj)
            db.session.commit()
            return redirect(url_for('userdetails'))
        else:
            return "Update user details invoked"
    else:
        if 'login_status' not in session:
            session['login_status'] = False
        userProfilePicStatus=False
        picture_name = "avatar2.png"
        profile_images = images.query.all()
        # This is for decoding the byyteArrayy and stroing it in the location. 
        for i in profile_images:
            image_converter(i.img, i.filename, '/profile-pictures/')
        # This is for checking whether there is an image in the name of the logged user.
        for filename in profile_images:
            if filename.filename.split(".")[0] == username :
                userProfilePicStatus=True
                picture_name = filename.filename			   
        return render_template('user.html', title= str(username).capitalize() + description,loginStatus=session['login_status'], user=username, profile_images = picture_name )

def image_converter(img_array, file_name, path):
    image = Image.open(io.BytesIO(img_array))
    image = image.resize((300, 300), Image.ANTIALIAS)
    dp_name = os.getcwd() + "/static/images" + path  + file_name
    image.save(dp_name, optimize=True, quality=95)

if __name__ == "__main__":
    app.run(debug=True)
