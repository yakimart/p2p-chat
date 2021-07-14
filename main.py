from flask import *
from waitress import serve
import json
import logging
import time as tm
import requests
import configparser


config = configparser.ConfigParser()
config.read("settings.ini")

app = Flask(__name__)

with app.app_context():

    MAX_LEAFS = 5

    my_peer_ip = config["config"]["my_peer_ip"]
    my_user_name = config["config"]["my_user_name"]
    node_peer_ip = my_peer_ip

    received_messages = []
    messages_counter = 0
    peer_list = {}


    def spot_node_ip(peer_list):
        node = ''
        if my_peer_ip in list(peer_list.keys()):
            node = my_peer_ip
        else:
            for i in list(peer_list.keys()):
                if my_peer_ip in peer_list[i]:
                    node = i
                    break
        return node

    def send_message(type, content, sender, time, username = ''):
        offline_peers = []

        if my_peer_ip == node_peer_ip:
                if my_peer_ip != sender:
                    if sender in peer_list[my_peer_ip]: #if peer is a node and message sent from inside
                        send_list = [i for i in list(peer_list.keys()) if i != my_peer_ip] #!!!!#send message to ALL nodes

                    elif sender not in peer_list[my_peer_ip]: #if peer is a node and message sent from outside
                        send_list = peer_list[my_peer_ip] #send message to leafs
                else:
                    send_list = peer_list[my_peer_ip] + [i for i in list(peer_list.keys()) if i != my_peer_ip]


        else:
            send_list = [i for i in peer_list[node_peer_ip] if i != my_peer_ip] + [node_peer_ip] #!!!!!send message to leafs and CURRENT node



        data = json.dumps({"jsonrpc": "2.0", "method": "send_message", "params": {"type": type, "content": content,
                                                                                  "sender": sender, "time": time, "username": username}, "id": 2})

        for peer in send_list:
            try:
                requests.post(f'http://{peer}', data=data)
            except:
                offline_peers.append(peer)

        if offline_peers != []:
            pass



@app.route("/", methods=["GET", "POST"]) #route for receaving messages from outside
def handle_message():
    global my_peer_ip, node_peer_ip, peer_list, messages_counter


    if request.method == 'GET':
        return redirect(url_for('index'))

    data = json.loads(request.data.decode("utf-8"))


    if data["method"] == "connect":

        if peer_list == {}:
            peer_list = {my_peer_ip: [data["params"]["ip"]]}
        else:
            if len(peer_list[node_peer_ip]) < MAX_LEAFS:
                peer_list[node_peer_ip].append(data["params"]["ip"]) #adding to peer list of current node
            else:
                available_node = [node for node in list(peer_list.keys()) if len(peer_list[node]) < MAX_LEAFS]
                if available_node == []: #if no any available node
                    peer_list[data["params"]["ip"]] = []
                else:
                    peer_list[available_node[0]].append(data["params"]["ip"]) #adding to peer list of first available node

        send_message(type='peer_list', content=peer_list, sender=my_peer_ip, time=data["params"]["time"], username=my_user_name)
        received_messages.append(["PEER LIST UPDATED!!!", data["params"]["ip"], my_user_name,
                                  'Delivered in ' + str(abs(round(tm.time() - data["params"]["time"], 2))) + 's'])
        messages_counter += 1


    elif data["method"] == "send_message":

        if data["params"]["type"] == "message":
            received_messages.append([data["params"]["content"], data["params"]["sender"], data["params"]["username"], 'Delivered in ' + str(round(tm.time() - data["params"]["time"], 2)) + 's'])
            messages_counter += 1

            if my_peer_ip in list(peer_list.keys()):
                send_message(type='message', content=data["params"]["content"], sender=data["params"]["sender"], time=data["params"]["time"], username=data["params"]["username"])


        elif data["params"]["type"] == "peer_list":
            if my_peer_ip not in list(peer_list.keys()):
                peer_list = data["params"]["content"]
                node_peer_ip = spot_node_ip(peer_list)

            else:
                send_message(type='peer_list', content=data["params"]["content"], sender=data["params"]["sender"],
                             time=data["params"]["time"], username=data["params"]["username"])

                peer_list = data["params"]["content"]
                node_peer_ip = spot_node_ip(peer_list)


            received_messages.append(["PEER LIST UPDATED!!!", data["params"]["sender"], data["params"]["username"], 'Delivered in ' + str(round(tm.time() - data["params"]["time"], 2)) + 's'])
            messages_counter += 1


    return Response("Success")


#-------------------------------------------------------------------------------

@app.route("/index", methods=["GET"]) #web interface
def index():
    if request.environ.get("HTTP_X_REAL_IP", request.remote_addr) in ['127.0.0.1', config["config"]["host"]]:
        return render_template('index.html', messages=received_messages, 
            username=f'{my_user_name} ({my_peer_ip})', peers=peer_list, host=f'{config["config"]["host"]}:{config["config"]["port"]}')



@app.route("/index/send_message", methods=["POST"]) #send message from web
def send_web():
    global messages_counter, received_messages

    msg = request.data.decode("utf-8")

    send_message(type = 'message', content=msg, sender=my_peer_ip, time=tm.time(), username = my_user_name)
    received_messages.append([msg, my_peer_ip, my_user_name,
                             f"Sent in {tm.localtime()[3]}:{tm.localtime()[4]}:{tm.localtime()[5]}"])

    messages_counter += 1
    return Response("Success")


@app.route("/index/poll_messages", methods=["GET", "POST"]) #poll messages from web
def poll_web():
    global messages_counter, received_messages

    if messages_counter != 0:
        i = messages_counter
        messages_counter = 0
        return json.dumps({"data": received_messages[-i:]})
    else: return Response("No messages")


@app.route("/index/join_chat", methods=["GET", "POST"]) #join chat from web
def join_web():
    data = request.data.decode("utf-8")

    rpc_req = json.dumps({"jsonrpc": "2.0", "method": "connect", "params": {"ip": my_peer_ip, "time": tm.time()}, "id": 3})
    requests.post(f'http://{data}', data=rpc_req)

    return Response("Success")



if __name__ == "__main__":

    #serve(app, host=config["config"]["host"], port=int(config["config"]["port"]), threads=5)  # WAITRESS!
    app.run(debug=True, host=config["config"]["host"], port=int(config["config"]["port"]))





