import socket
import threading
import json
from utils import create_metainfo_hashtable
# https://www.geeksforgeeks.org/file-transfer-using-tcp-socket-in-python/

class Tracker:
    def __init__(self, port:int =5050, peer_list:set = {}, header_length = 1024) -> None:
        self.ip = "localhost"# socket.gethostbyname(socket.gethostname())
        self.port = port
        self.header_length = header_length
        self.peer_list = set(peer_list)
        self.semaphore = threading.Semaphore()
        self.socket_tracker = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_tracker.bind((self.ip,self.port))
        self.socket_tracker.listen(1)
        self.metainfo_hashtable = create_metainfo_hashtable("metainfo")
        print(f"[TRACKER] Socket is binded to {self.port}")
    
        
    def start(self):
        print("[STARTING] Server is starting ...")
        while True:
            try:
                connection, address = self.socket_tracker.accept()
                thread = threading.Thread(target=self.handle_peer, args=(connection, address))
                print(f"[ACTIVE CONNECTION] {threading.active_count() - 1}")
                thread.start()    
            except KeyboardInterrupt:
                # connection.close()
                break
            
    def parse_metainfo(self,hash_info) -> dict:
        metainfo_path = self.metainfo_hashtable.get(hash_info)
        if metainfo_path:
            with open(metainfo_path, "r") as torrent:
                metainfo = torrent.read()
                metainfo = json.loads(metainfo)
                return metainfo
        else:
            return None
    
    def add_peer(self, peer: tuple)-> None:
        with self.semaphore:
            try:
                print(f"[TRACKER] Add peer {peer} to list tracking")
                self.peer_list.add(peer)
            except Exception as e:
                print(e)
                
                
    def remove_peer(self,peer: tuple)-> None:
        with self.semaphore:
            try:
                print(f"[TRACKER] remove peer {peer} in list tracking")
            
                self.peer_list.discard(peer)
            except Exception as e:
                print(e)
        
    def send_message(self, connection, mess: dict):
        message = json.dumps(mess)
        message = message.encode("utf-8")
        message_length = str(len(message)).encode("utf-8")
        message_length += b' '*(self.header_length - len(message_length))
        connection.send(message_length)
        connection.send(message)
        
    def recieve_message(self, connection, address=None) -> dict:
        message_length = connection.recv(self.header_length).decode("utf-8")
        message_length = int(message_length)
        message = connection.recv(message_length).decode("utf-8")
        return json.loads(message)
    
    def handle_peer(self, connection, address):
        try:
            print(f"[NEW CONNECTION] {address} connected")
            connected = True
            while connected:
                message = self.recieve_message(connection, address)
                response = self.process_message(message)
                print("processing messeage is finished ")
                connected = self.response_action(connection,address, response)    
            connection.close()
        except:
            pass
     
    def process_message(self, mess)-> str:
        try:
            if mess.get("type") == "join":
                self.add_peer((mess.get("ip"),mess.get("port")))
                response = {
                    "action":"accept join",
                    "result":True
                }
                return response
            if mess.get("type") == "download":
                # if mess.get("event") == "started":
                ip = mess.get("ip")
                port = mess.get("port")
                info_hash = mess.get("info_hash")
                # parse metainfo from hash of metainfo
                meta_info = self.parse_metainfo(info_hash)
                if not meta_info:
                    response = {"action":"error"}
                    return response
                # send broadcast to ask all peer in list to find who is keept pieces of this file
                peer_list_response = self.findPeersGetTorrent(meta_info)
                print(peer_list_response)
                response = {
                    "action":"response download",
                    "peers": peer_list_response
                }
                return response
                
                
            if mess.get("type") == "upload":
                response = {"action":"response upload"}
                return response
            
            if mess.get("type") == "disconnect":
                response = {
                    "action":"disconnect",
                    "id":mess.get("ip"),
                    "ip":mess.get("ip"),
                    "port":mess.get("port")
                }
                return response
        except json.JSONDecodeError as e:
            print("Error: Invalid JSON string")
            print(e)
            response ={
                "action": "error",
                "Error": e
            }
            return response
            
        
    def response_action(self,connection,address,command: dict):
        if (command.get("action") == "response download"):
            print(json.dumps(command.get("peers"), indent=4))
            self.send_message(connection, command)
            return False
        # self.send_message(connection,"oke")
        if command.get("action") == "accept join":
            response = {
                "response": "success" if command.get("result") else "failed"
            }
            self.send_message(connection, response)
            return False
            
        if command.get("action") == "disconnect":
            self.remove_peer(address)
            # connected = False
            return False
            
            
        if command.get("action") == "error":
            self.send_message(connection, command)
            # connected = False
            return False
            
        if command.get("action") == "response upload":
            return False
                
                
                
        
    def findPeersGetTorrent(self,metainfo):
        print("[Broadcast] find peers which obtain Torrent pieces in peer list")
        peer_list_for_client = []
        print(self.peer_list)
        for peer in self.peer_list:
            print(f"[ASK] Peer {peer} for torrent ")
            client_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_connection.connect(peer)
            message = {
                "type": "findTorrent",
                "tracker_id": "1",
                "file_name": metainfo.get("info").get("name")
            }
            
            self.send_message(client_connection, message)
            response = self.recieve_message(client_connection, peer)
            print(json.dumps(response,indent=4))
            if response.get("hit") == True:
                peer_list_for_client.append({"id":response.get("id"),"ip":response.get("ip"), "port":response.get("port")})
            client_connection.close()
        return peer_list_for_client
                        

        
####################################################### test ##############################################################
def test_meta_info():    
    tracker = Tracker()  
    message = {
        "info_hash": "62f518eaaff4903ea10163eee1d98e3c7691d1fe",
        "peer_id": 1,
        "port": 4040,
        "event": "started",
        "ip": "192.168.31.119"
    }  
    tracker.process_message(json.dumps(message))
    
    
def run():
    tracker = Tracker()
    tracker.start()
    
    
    
def test_client_connect():
    tracker = Tracker()
        # tracker.start()
    tracker.add_peer(("192.168.31.199",4041))
    tracker.add_peer(("192.168.31.199",4042))
    
    meta_info = {
        "announce": "http://localhost:8080",
        "info": {
            "name": "meeting_1.mp4",
            "length": 360314102,
            "pieces": [],
            "piece length": 524288 
        }
    }
    
    peer_list_response = tracker.findPeersGetTorrent(meta_info)
    print(peer_list_response)
if __name__ == "__main__":
    # test_client_connect()
    run()
       
        
       
    
        
        
        
    