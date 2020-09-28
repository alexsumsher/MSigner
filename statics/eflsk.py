# empty flask
 
from flask import Flask, request, send_from_directory, send_file
import os

app = Flask(__name__)
mainpath = os.getcwd()


@app.route("/index")
def index():
	return 'ok'

@app.route("/html/<fn>")
def html(fn=""):
	if "." in fn:
		ext = fn.split(".")[-1]
		if ext == 'js':
			mimetype = "application/x-javascript"
		elif ext == 'html':
			mimetype = "text/html"
		else:
			mimetype = ""
		return send_file(os.path.join(mainpath, 'htmls', fn), mimetype=mimetype)
	return send_file(os.path.join(mainpath, 'htmls', fn + '.html'), mimetype="text/html")

@app.route("/js/<fn>")
def js(fn=""):
	return send_file(os.path.join(mainpath, 'js', fn), mimetype="application/x-javascript")

@app.route("/css/<fn>")
def css(fn=""):
	return send_file(os.path.join(mainpath, 'css', fn), mimetype="text/css")

@app.route("/local/<page>")
def local(page=""):
	ext = page.split(".")[-1]
	if  ext == "html":
		return send_file(os.path.join(mainpath, page), mimetype="text/html")
	elif ext == 'js':
		return send_file(os.path.join(mainpath, page), mimetype="application/x-javascript")
	else:
		return send_from_directory(mainpath, page)

@app.route("/file/<file>")
def file(file=""):
	return send_from_directory(mainpath, file)

@app.route("/js/<file>")
def file2(file=""):
	#return send_from_directory(os.path.join(mainpath, 'js'), file)
	return send_file(os.path.join(mainpath, 'js', file), mimetype="application/x-javascript")


if __name__ == '__main__':
	app.debug = True
	app.run()