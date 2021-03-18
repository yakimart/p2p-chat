from flask import *
from waitress import serve
import json


app = Flask(__name__)

with app.app_context():

    # service methods
    def check_valid(data):
        try:
            data = json.loads(data)
        except:
            return jsonify(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32700, "message": "Parse error"},
                    "id": None,
                }
            )

        for key in ["jsonrpc", "method", "id"]:
            if key not in data.keys():
                return jsonify(
                    {
                        "jsonrpc": "2.0",
                        "error": {"code": -32600, "message": "Invalid Request"},
                        "id": data["id"] or None,
                    }
                )

        if data["jsonrpc"] != "2.0":
            return jsonify(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32600, "message": "Invalid Request"},
                    "id": data["id"],
                }
            )

        if data["method"] not in endpoint_methods.keys():
            return jsonify(
                {
                    "jsonrpc": "2.0",
                    "error": {"code": -32601, "message": "Method not found"},
                    "id": data["id"],
                }
            )



        return "OK"
        #!!!!!!!!!!Checkimg for invalid method params

    def listing_peers():
        with open("peers.json") as json_file:
            peer_list = json.load(json_file)

        visitor_ip = request.environ.get("HTTP_X_REAL_IP", request.remote_addr)

        if visitor_ip not in peer_list["peers"]:

            peer_list["peers"].append(visitor_ip)

            with open("peers.json", "w") as json_file:
                json.dump(peer_list, json_file)

    def response(method, id):
        result = endpoint_methods[method]
        return jsonify({"jsonrpc": "2.0", "result": result, "id": id})




    # endpoint methods
    def get_version():
        return {"version": "0.1"}

    def get_peer_list():
        with open("peers.json") as json_file:
            return {"peer_list": json.load(json_file)["peers"]}

    endpoint_methods = {"get_version": get_version(), "get_peer_list": get_peer_list()}



@app.route("/endpoint", methods=["POST"])
def post_response():

    status = check_valid(data=request.data.decode("utf-8"))

    if status == "OK":
        listing_peers()

        data = json.loads(request.data.decode("utf-8"))

        return response(method=data["method"], id=data["id"])

    else:
        return status


@app.route("/")
def greetings():
    return "WTF development is in progress"


if __name__ == "__main__":

    #serve(app, host="192.168.0.101", port=100, threads=5)  # WAITRESS!
    app.run(debug=True, host='192.168.0.101', port=100)
