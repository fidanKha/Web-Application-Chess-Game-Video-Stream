from imutils.video import VideoStream
from flask import Response, Flask, render_template, request, jsonify
import threading
import argparse
import datetime
import imutils
import time
import math
import numpy as np
import cv2 # for image processing
import pafy # for reading youtube link
import pyttsx3  # tts library
import pandas as pd

outputFrame = None
lock = threading.Lock()
start_second  = 21
app = Flask(__name__)
stop_flag = 0
play_flag = True

'''
# for getting video from youtube
url = "https://www.youtube.com/watch?v=fLb6zwz235g"
video = pafy.new(url)
best = video.getbest(preftype="mp4")
vs = cv2.VideoCapture()
vs.open(best.url)
'''

path_to_video = r"./kasparov_deepblue.mp4"
vs = cv2.VideoCapture(path_to_video)
fps = vs.get(cv2.CAP_PROP_FPS)   #getting the fps of the video, (the result was 29.97)
fps_int = math.ceil(fps)
time.sleep(2.0)
start_frame  =400
vs.set(cv2.CAP_PROP_POS_FRAMES, start_frame) # start from a certain frame
where_were_we = 0
first = True
DeepBlue = True
Kasparov = False
paused = 0
new_frame_to_go  = False

@app.route('/')
def index():
	global play_flag, new_frame_to_go
	play_flag = True 
	new_frame_to_go = True
	return render_template('index.html')


@app.route('/Play')
def Play():
	global play_flag, first, where_were_we, start_frame 
	if(where_were_we != 0):
		start_frame = where_were_we
	else:
		start_frame = 400
		first = False
	play_flag = True
	video_stream()
	return "Nothing"


@app.route('/Stop')
def Stop():
	global play_flag, start_frame, where_were_we, paused
	paused = 1
	where_were_we = start_frame
	play_flag = False
	return "Nothing"

def end_stream():
	vs.release()
	cv2.destroyAllWindows()


def video_stream():

	global start_frame, new_frame_to_go, counter, engine, false, vs, outputFrame, lock, start_second, first_frame, DeepBlue, Kasparov, stop_flag, play_flag
	total = start_frame
	engine = pyttsx3.init()
	if(new_frame_to_go):
		engine.stop()
		vs.release()
		vs2 = cv2.VideoCapture(path_to_video)
		vs2.set(cv2.CAP_PROP_POS_FRAMES, start_frame) # start from a certain frame
		vs = vs2
		engine2 = pyttsx3.init()
		engine = engine2
		time.sleep(1.0)
		new_frame_to_go = False

	global paused
	data = pd.read_excel (r"./match.xlsx")

	instances = list()
	for ii in data.time:
		instances.append(ii*fps_int)
	text_cv2_kasparov = ' '
	text_cv2_deepblue = ' '
	while play_flag:
		start_frame = total
		if(first):
			play_flag=False
			total += 1
		if(new_frame_to_go):
			break
		a,frame = vs.read()
		if not  a:
			break
		frame = imutils.resize(frame, width=400)
		engine = pyttsx3.init()
		cv2.putText(frame, 'USA - IBM/DeepBlue', (125, frame.shape[0] - 20), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		cv2.putText(frame, 'RUS - Kasparov', (frame.shape[0] - 275, 15), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		position_1 = (375, frame.shape[0] - 200)
		position_2 = (10, frame.shape[0] - 200)
		if(DeepBlue):
			cv2.putText(frame, '->', position_1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
			cv2.putText(frame, ' ', position_2, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		if(Kasparov):
			cv2.putText(frame, '<-', position_2, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
			cv2.putText(frame, ' ', position_1, cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		if len(text_cv2_kasparov)>14:
			cv2.putText(frame, text_cv2_kasparov[:14],(250, frame.shape[0] - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
			cv2.putText(frame, text_cv2_kasparov[14:],(250, frame.shape[0] - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		else :
			cv2.putText(frame, text_cv2_kasparov,(300, frame.shape[0] - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		if len(text_cv2_deepblue)>14:
			cv2.putText(frame, text_cv2_deepblue[:14],(0, frame.shape[0] - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
			cv2.putText(frame, text_cv2_deepblue[14:],(0, frame.shape[0] - 120), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		else :
			cv2.putText(frame, text_cv2_deepblue,(0, frame.shape[0] - 150), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0,0,255), 2)
		if total  in instances:
			engine.say(data.name[instances.index(total)]+ data.Move[instances.index(total)])
			text_cv2= data.Move[instances.index(total)]
			if(new_frame_to_go):
				return
			engine.runAndWait()
			if(new_frame_to_go):
				break
			engine.stop()
			if data.name[instances.index(total)]== 'Kasparov':
				Kasparov = False
				DeepBlue = True
				text_cv2_deepblue = data.Move[instances.index(total)]
				text_cv2_kasparov = ' '
			elif data.name[instances.index(total)]== 'Deep Blue':
				Kasparov = True
				DeepBlue = False
				text_cv2_kasparov = data.Move[instances.index(total)]
				text_cv2_deepblue = ' '
		total += 1
		time.sleep(0.05)
		with lock:
			outputFrame = frame.copy()
		if stop_flag==1:
			cv2.waitKey(1)
			break
		if(paused == 0):
			engine = pyttsx3.init()
			engine.say('Press Play button to start the game.')
			engine.runAndWait()
			paused = 1
			video_stream()


def generate():
	global outputFrame, lock, counter
	while True:
		with lock:
			if outputFrame is None:
				continue
			(flag, encodedImage) = cv2.imencode(".jpg", outputFrame)
			if not flag:
				continue
		yield(b'--frame\r\n' b'Content-Type: image/jpeg\r\n\r\n' + bytearray(encodedImage) + b'\r\n')


@app.route("/video_feed")
def video_feed():
	return Response(generate(),
		mimetype = "multipart/x-mixed-replace; boundary=frame")

@app.route('/stats')
def stats():
	global play_flag, engine, vs, where_were_we, start_frame, paused
	engine.stop()
	vs.release()
	paused = 1
	where_were_we = start_frame
	play_flag = False
	bar_label = ['Russia', 'USA', 'China', 'India','Ukraine', 'Armenia', 'Azerbaijan', 'Hungary','France', 'Poland']
	bar_value = [2739,2714,2706,2666,2661,2652,2651,2643,2640,2638]
	bar_colors = ["#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA","#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1","#C71585", "#FF4500"]
	return render_template('stats.html', title='Country rank by average rating of top 10 players', max=2800, labels=bar_label, values=bar_value, colors = bar_colors)


@app.route('/line_chart')
def line_chart():
	global play_flag, engine, vs, where_were_we, start_frame, paused
	engine.stop()
	vs.release()
	paused = 1
	where_were_we = start_frame
	play_flag = False
	line_labels= ['Magnus Carlsen', 'Garry Kasparov', 'Fabiano Caruana', 'Levon Aronian','Wesley So', 'Shakhriyar Mamedyarov', 'Maxime Vachier-Lagrave', 'Viswanathan Anand','Vladimir Kramnik', 'Veselin Topalov', 'Hikaru Nakamura','Ding Liren']
	line_values = [2882,2851,2844,2830,2822,2820,2819,2817,2817,2816,2816,2816]
	return render_template('line_chart.html', title='Top 20 rated players of all-time', max=2900, labels=line_labels, values=line_values)

@app.route('/pie_chart')
def pie_chart():
	global play_flag, engine, vs, where_were_we, start_frame, paused
	engine.stop()
	vs.release()
	paused = 1
	where_were_we = start_frame
	play_flag = False
	labels = ['Garry Kasparov','Viswanathan Anand','Vladimir Kramnik','Vassily Ivanchuk','Veselin Topalov', 'Gata Kamsky','Boris Gelfand','Alexei Shirov' ,'Nigel Short']
	values =[2795,2765, 2760,2740,2740,2725,2720, 2700,2690,2690]
	colors = ["#F7464A", "#46BFBD", "#FDB45C", "#FEDCBA","#ABCDEF", "#DDDDDD", "#ABCABC", "#4169E1","#C71585", "#FF4500"]
	return render_template('pie_chart.html', title='FIDE top 10 players by Elo rating - January 1997', max=17000, set=zip(values, labels, colors))




@app.route('/about_chess')
def about_chess():
	global play_flag, engine, vs, where_were_we, start_frame, paused
	engine.stop()
	vs.release()
	paused = 1
	where_were_we = start_frame
	play_flag = False
	return render_template('about_chess.html')
    
@app.route('/about_the_game')
def about_the_game():
	global play_flag, engine, vs, where_were_we, start_frame, paused
	engine.stop()
	vs.release()
	paused = 1
	where_were_we = start_frame
	play_flag = False
	return render_template('about_the_game.html')
    
@app.route('/Submit', methods=['POST'])
def Submit():
	global start_frame, new_frame_to_go
	start_frame = ((int(request.form['name_of_slider']))+14)*30
	new_frame_to_go = True
	video_stream()
	return render_template('index.html')

if __name__ == '__main__':
	ap = argparse.ArgumentParser()
	ap.add_argument("-i", "--ip", type=str, default='0.0.0.0',help="ip address of the device")
	ap.add_argument("-o", "--port", type=int, default='8000',help="ephemeral port number of the server (1024 to 65535)")
	args = vars(ap.parse_args())
	t = threading.Thread(target=video_stream)
	t.daemon = True
	t.start()
	app.run(host=args["ip"], port=args["port"], debug=True,threaded=True, use_reloader=False)

vs.release()
cv2.destroyAllWindows()
