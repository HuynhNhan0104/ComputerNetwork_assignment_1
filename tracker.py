import socket
import threading
import json
import os
from utils import create_metainfo_hashtable
import argparse
# https://www.geeksforgeeks.org/file-transfer-using-tcp-socket-in-python/

class Tracker:
    def __init__(self, id = 0, port:int =5050, peer_list:set = {}, header_length = 1024,metainfo_storage="metainfo") -> None:
        self.id = id
        self.ip = "localhost"# socket.gethostbyname(socket.gethostname())
        self.port = port
        self.header_length = header_length
        self.peer_list = set(peer_list)
        self.metainfo_storage = metainfo_storage
        if not os.path.exists(self.metainfo_storage):
            os.makedirs(self.metainfo_storage)
            
        self.peer_list_semaphore = threading.Semaphore()
        self.socket_tracker = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_tracker.bind((self.ip,self.port))
        self.socket_tracker.listen(10)
        self.metainfo_hashtable = create_metainfo_hashtable(self.metainfo_storage)
        self.metainfo_hashtable_semaphore = threading.Semaphore()
        print(f"[TRACKER] Socket is binded to {self.port}")
        self.running = True
    
        
    def start(self):
        print("[STARTING] Server is starting ...")
        while self.running:
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
        with self.peer_list_semaphore:
            try:
                print(f"[TRACKER] Add peer {peer} to list tracking")
                self.peer_list.add(peer)
            except Exception as e:
                print(e)
                
                
    def remove_peer(self,peer: tuple)-> None:
        with self.peer_list_semaphore:
            try:
                print(f"[TRACKER] remove peer {peer} in list tracking")
            
                self.peer_list.discard(peer)
            except Exception as e:
                print(e)
    
    def update_metaifo_hash_table(self,key: str,metainfo_path: str):
        with self.metainfo_hashtable_semaphore:
            self.metainfo_hashtable.update({key:metainfo_path})
        
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
   
    def send_metainfo_file(self, connection,file_path,chunk= 4*1024):
        """
        send all data of file to other peer which is connected with

        Args:
            connection (socket): connnection to other peer
            file_path (string): file path of file which need to send
            chunk (int, optional): chunk size. Defaults to 512*1024 (521kB)
        """
        with open(file_path,"rb") as item:
            try:
                while True:
                    data = item.read(chunk)
                    if not data: 
                        connection.sendall(b'done')
                        break
                    connection.sendall(data)
                    

            except Exception as e:
                print(e)

        print(f"finish send: {file_path}")
       
    def recieve_metainfo_file(self,connection, out_path,chunk=4*1024):
        """
        recieve file from other peer which is connected with

        Args:
            connection (socket):connnection to other peer
            out_path (str): file output path
            chunk (int, optional): chunk size. Defaults to 512*1024 (521kB)
            
        """
        with open(out_path,"wb") as item:
            while True:
                data = connection.recv(chunk)
                if data == b'done':
                    break
                item.write(data)
                # print(sys.getsizeof(data))
                
        print(f"finish receive: {out_path}")
    
    def handle_peer(self, connection, address):
        try:
            print(f"[NEW CONNECTION] {address} connected")
            connected = True
            while connected:
                message = self.recieve_message(connection, address)
                response = self.process_message(message)
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
                metainfo_hash = mess.get("metainfo_hash")
                # parse metainfo from hash of metainfo
                meta_info = self.parse_metainfo(metainfo_hash)
                if not meta_info:
                    response = {"action":"error"}
                    return response
                # send broadcast to ask all peer in list to find who is keept pieces of this file
                peer_list_response = self.findPeersGetTorrent(meta_info)
                response = {
                    "action":"response download",
                    "peers": peer_list_response
                }
                return response
                
                
            if mess.get("type") == "upload":
                self.add_peer((mess.get("ip"),mess.get("port")))
                response = {
                    "action":"response upload",
                    "metainfo_hash": mess.get("metainfo_hash"),
                    "metainfo_name":mess.get("metainfo_name")
                }
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
            # print(json.dumps(command.get("peers"), indent=4))
            self.send_message(connection, command)
            return False
        # self.send_message(connection,"oke")
        if command.get("action") == "accept join":
            response = {
                "notification": "success" if command.get("result") else "failed"
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
            metainfo_hash = command.get("metainfo_hash")
            metainfo_name = command.get("metainfo_name")
            if metainfo_hash in self.metainfo_hashtable:
                response = {
                    "notification": "track was contain this metainfo file",
                    "hit": True
                }
                self.send_message(connection, response)
            else:
                response ={
                    "notification":"tracker want to get this metainfo file",
                    "hit": False
                }
                self.send_message(connection, response)
                self.recieve_metainfo_file(connection,f"{self.metainfo_storage}/{metainfo_name}",chunk=1024)
                self.update_metaifo_hash_table(metainfo_hash,f"{self.metainfo_storage}/{metainfo_name}")
            return False
                
                
                
        
    def findPeersGetTorrent(self,metainfo):
        print("[Broadcast] find peers which obtain Torrent pieces in peer list")
        peer_list_for_client = []
        # print(self.peer_list)
        for peer in self.peer_list:
            print(f"[ASK] Peer {peer} for torrent ")
            client_connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            client_connection.connect(peer)
            message = {
                "type": "findTorrent",
                "tracker_id": self.id,
                "file_name": metainfo.get("info").get("name")
            }
            
            self.send_message(client_connection, message)
            response = self.recieve_message(client_connection, peer)
            # print(json.dumps(response,indent=4))
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
    
    


# Viết mã argparse ở đây




# parser.add_argument('filenames', nargs='+', help='Danh sách tên file')
# print(args.Namespace)

# # Mã logic chính của script ở đây
# for arg in args:
#     # Xử lý từng file
#     print(f"Processing file: {arg}")

def main():
    parser = argparse.ArgumentParser(description='Tracker script')
    parser.add_argument("--id", type=int, help="traker id",default=0)
    parser.add_argument("--port",type=int,help="tracker port", default=5050 )
    parser.add_argument("--metainfo-storage",type=str, help="directory hold metainfo", default="metainfo" )
    parser.add_argument("--header-length",type=int, help="header length of message", default=1024 )
    args = parser.parse_args()
    # for key, value in vars(args).items():
    #     print(f"{key}: {value}")
    id = args.id
    port = args.port
    metainfo_storage = args.metainfo_storage
    header_length = args.header_length
    
    
    tracker = Tracker(id=id,port = port, metainfo_storage=metainfo_storage,header_length= header_length)
    tracker.start()
    
if __name__ == "__main__":
    main()
       
        
       
    
        
        
        
    