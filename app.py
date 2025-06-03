from flask import Flask, render_template, request, send_from_directory, redirect, url_for, Response, jsonify
from flask_cors import CORS
import time
import json

app = Flask(__name__, static_folder='static')
CORS(app)

message = ''
temperature = ''
orders = []
confirmOrders = []
order_data = {}

@app.route('/')
def index():
    return render_template('index.html', message=message, temperature=temperature)

@app.route('/staff', methods=['GET', 'POST'])
def staff():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('staff.html')

@app.route('/order', methods=['GET', 'POST'])
def order():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('order.html', orders=orders)

@app.route('/secret', methods=['GET', 'POST'])
def secret():
    if request.method == 'POST':
        return redirect(url_for('index'))
    return render_template('secret.html', orders=orders)

@app.route('/submit', methods=['POST'])
def submit_order():
    data = request.get_json()
    order_number = data.get('orderNumber')
    pizza_name = data.get('pizzaName')

    global submitted_data
    submitted_data = {
        'orderNumber': order_number,
        'pizzaName': pizza_name
    }

    return jsonify({'message': 'Order submitted successfully'})

@app.route('/get_data', methods=['GET'])
def get_data():
    if submitted_data is None:
        return jsonify({'message': 'No data'}), 200
    else:
        return jsonify({'data': submitted_data}), 200

@app.route('/pizzaFinished', methods=['POST'])
def receive_pizza_finished():
    global order_data

    order_data = request.get_json()
    print(order_data)

    return jsonify({'message': 'Data received successfully'})

@app.route('/getJsonData', methods=['GET'])
def get_json_data():
    global order_data
    return jsonify(order_data)

@app.route('/confirm_order', methods=['POST', 'GET'])
def confirm_order():
    global confirmOrders
    if request.method == 'POST':
        data = request.get_json()
        confirmOrders = data
        print(data)
        return jsonify({'status': 'success'}), 200
    elif request.method == 'GET':
        return jsonify(confirmOrders), 200
    
@app.route('/stream')
def stream():
    def event_stream():
        global message
        global temperature
        global orderName
        global orderNumber
        global status

        while True:
            yield 'data: %s\n\n' % json.dumps({'message': message, 'temperature': temperature, 'orderName': orderName, 'orderNumber': orderNumber, 'status': status})
            time.sleep(1)
    return Response(event_stream(), mimetype="text/event-stream")
