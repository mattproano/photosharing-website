To get "photosharing" running, open a terminal and do the following:
	1. 'cd path/to/photosharing'
	2. 'pip install -r requirements.txt'
	3. export flask (Mac, Linux) 'export FLASK_APP=app.py', (Windows) 'set FLASK_APP=app.py'
	4. run schema.sql using MySQL Workbench
	5. open app.py using your favorite editor, change 'cs460' in 'app.config['MYSQL_DATABASE_PASSWORD'] = 'cs460'' to your MySQL root password. You need to keep the quotations around your root password
	6. back to the terminal, run the app 'python -m flask run' (or use python3)
	7. open your browser, and open the local website 'localhost:5000'
