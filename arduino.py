import time
import sys
from datetime import datetime
from fhict_cb_01.custom_telemetrix import CustomTelemetrix
import httpx
import asyncio
import json
import random

board = CustomTelemetrix()

DHTPIN = 12

def setup():
    board.displayOn()
    board.set_pin_mode_dht(DHTPIN, dht_type=11)
    board.set_pin_mode_digital_input_pullup(8)
    board.set_pin_mode_digital_input_pullup(9)
    board.set_pin_mode_digital_input(16)
    
    board.set_pin_mode_analog_output(4)
    board.set_pin_mode_analog_output(5)
    board.set_pin_mode_analog_output(6)
    board.set_pin_mode_analog_output(7)

    time.sleep(1)

measurements = []
order_list = []
countdown = 12
current_order_index = 0
current_key_index = 0
tasks = []
index = 0
firstShowVar = True

async def loop():
    global measurements
    global countdown
    global client
    global order_list
    global current_order_index
    global current_key_index
    global display_state
    global tasks
    global board
    global firstShowVar
    
    humidity, temperature, timestamp = board.dht_read(DHTPIN)
    level1, time_stamp1 = board.digital_read(8)
    level2, time_stamp1 = board.digital_read(9)
    brightnes = board.digital_read(16)

    #temperature = round(temperature, 3)
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

    async def get_data():
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get('http://localhost:8080/get_data')
                data = response.json()["data"]
                order_number = data["orderNumber"]
                pizza_name = data["pizzaName"]
                
                order_temp = random.randint(1, 60)
                cntdwn = random.randint(10, 20)
                
                return {"orderNumber": order_number, "pizzaName": pizza_name, "status": "Cooking", "countdown": 15 + cntdwn, "temp": temperature + order_temp}
            except json.decoder.JSONDecodeError:
                print("Error decoding JSON response. Retrying...")
                await asyncio.sleep(5)
                return None

    async def send_pizza_finished(order_list):
        async with httpx.AsyncClient() as client:
            print(order_list)
            await client.post('http://localhost:8080/pizzaFinished', json=order_list)

    async def cnt(order):
        global order_list
        order_number = order["orderNumber"]
        if order["status"] == "Cooking":
            await asyncio.sleep(1)

            if order["countdown"] > 0:
                print(f"Order {order_number}: {order['countdown']} seconds")
                order["countdown"] -= 1
                #order["countdown"] = round(order["countdown"], 3)


                start_time = time.perf_counter()
                await send_pizza_finished(order_list)
                lag_time = time.perf_counter() - start_time
                print("Request sent. Lag time:", lag_time)
                order["countdown"] -= lag_time
                #order["countdown"] = round(order["countdown"], 3)


                if order["countdown"] <= 0 and order["status"] == "Cooking":
                    print(f"Order {order_number}: Pizza is finished")
                    order["countdown"] = 0
                    order["status"] = "Ready"

                    await send_pizza_finished(order_list)
                    return

    new_order = await get_data()
    if new_order is not None and new_order['orderNumber'] not in [order['orderNumber'] for order in order_list]:
        order_list.append(new_order)
        print("New order received:", new_order)

    for order in order_list:
        task = asyncio.create_task(cnt(order))
        tasks.append(task)

    # 0 = 0 + 1 % duljinata
    def orderFn(arg):
        global current_order_index
        global order_list
        current_order_index = (current_order_index) % len(order_list)
        order_number = order_list[current_order_index]["orderNumber"]
        order_countdown = order_list[current_order_index]["countdown"]
        order_temp = order_list[current_order_index]["temp"]
        if arg == 'order_number':
            return order_number
        if arg == 'order_countdown':
            return order_countdown
        if arg == 'order_temp':
            return order_temp
        return

    async def aaa():
        global current_order_index
        current_order_index += 1
        return current_order_index
    

    async def displayLightShow(countdown):
        global board
        if countdown > 0:
            board.digital_write(5, 0)
            board.digital_write(4, 1)
        else:
            board.digital_write(5, 1)
            board.digital_write(4, 0)
        return

    global index
    if level1 == 0:
        index = 0
        await aaa()
        board.displayShow(orderFn('order_number'))

    if level2 == 0:
        index += 1

    if level2 == 0 and index > 2:
        index = 1

    if index == 1:
        board.displayShow(orderFn("order_countdown"))

    if index == 2:
        board.displayShow(orderFn("order_temp"))
    
    async def firstShow():
        global firstShowVar
        board.displayShow(orderFn('order_number'))
        firstShowVar = False
        return

    if firstShowVar == True:
        await firstShow()
        
    await displayLightShow(orderFn("order_countdown"))
    await asyncio.gather(*tasks)
    return

# [{'orderNumber': '0006', 'pizzaName': '€8 Veggie', 'status': 'Ready', 'countdown': 0, 'temp': 55.5}, {'orderNumber': '0007', 'pizzaName': '€12 Pepperoni', 'status': 'Ready', 'countdown': 0, 'temp': 58.6}]

async def main():
    setup()
    while True:
        try:
            await loop()
        except KeyboardInterrupt:
            print('shutdown')
            board.shutdown()
            sys.exit(0)

asyncio.run(main())