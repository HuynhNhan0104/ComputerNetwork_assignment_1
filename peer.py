import socket
import threading
import json
import os
import time
from utils import merge_file_from_pieces, split_file_to_pieces, create_hash_key_metainfo ,get_file_name_pieces_directory, get_piece_list_of_file

class Peer():
    def __init__(self, id, port:int= 4040, peer_list:list = [], header_length = 1024,pieces_storage="pieces") -> None:
        self.tracker_ip = "localhost"
        self.tracker_port= 5050
        self.id = id
        self.ip = socket.gethostbyname(socket.gethostname())
        self.port = port
        self.peer_list = peer_list
        self.header_length = header_length
        self.pieces_storage = pieces_storage
        self.upload = 0
        self.download = 0
        self.semaphore = threading.Semaphore()
        self.semaphore_download = threading.Semaphore()
        
        self.socket_peer = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        self.socket_peer.bind((self.ip,self.port))
        self.socket_peer.listen(1)
        print(f"[PEER] Socket is binded to {self.port}")
    
    
    def connect_to_tracker(self):
        """
        send signal to join network, tracker will add this address to list
        """
        request = {
            "type":"join",
            "id": self.id,
            "ip": self.ip,
            "port": self.port,
            "upload": 0,
            "download":0
        }
        connection = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        connection.connect((self.tracker_ip,self.tracker_port))
        self.send_message(connection,request)
        response = self.recieve_message(connection)
        print(json.dumps(response,indent=4))
        connection.close()
          
    def start(self):
        """
        Stating listen, if recieve connecttion request then creating thread handle peer
        """
        print("[STARTING] PEER is starting ...")
        while True:
           connection, address = self.socket_peer.accept()
           thread = threading.Thread(target=self.handle_peer, args=(connection, address))
           print(f"[ACTIVE CONNECTION] {threading.active_count() - 1}")
           thread.start()  
           
    def isObtainedPieces(self,file_path:str):
        """
        check peer is hold pieces of this file or not
        Args:
            file_path (str): file_name (exp: helleo.mp4)

        Returns:
            Bool: True if hold this file and False if not
        """
        file_path = file_path.split(".")
        extension = file_path[1]
        file_name = file_path[0]
        file_name_list = get_file_name_pieces_directory(self.pieces_storage)
        return (file_name in file_name_list)
        
    def is_choking(self):
        return False
    
    def is_interested(self):
        return True
      
    def parse_metainfo(self,metainfo) -> dict:
        with open(metainfo,"r") as torrent:
            data = torrent.read()
            data = json.loads(data)
            return data 
                
    def add_peer(self, peer: tuple)-> None:
        """
        add peer to list contact
        Args:
            peer (ip,port): tuple(ip, port ) of peer
        """
        with self.semaphore:
            print(f"[TRACKER] Add peer {peer} to list tracking")
            self.peer_list.append(peer)
            
    def remove_peer(self,peer: tuple)-> None:
        """
        remove peer from list contact

        Args:
    
            peer (ip,port): tuple(ip, port ) of peer
        """
        with self.semaphore:
            print(f"[TRACKER] remove peer {peer} in list tracking")
            self.peer_list.remove(peer)
        
    def send_message(self,connection,mess: dict):
        """
        send message on connection to another peer

        Args:
            connection (socket): socket connection
            mess (dict): message need send 
        """
        message = json.dumps(mess)
        message = message.encode("utf-8")
        message_length = str(len(message)).encode("utf-8")
        message_length += b' '*(self.header_length - len(message_length))
        connection.send(message_length)
        connection.send(message)
        
    def recieve_message(self, connection, address= None) -> dict:
        """
        recieve message on connection from another peer

        Args:
            connection (socket): socket connection
            address ((ip, port), optional): address of this connection host. Defaults to None.

        Returns:
            dict: message need recieve
        """
        message_length = connection.recv(self.header_length).decode("utf-8")
        if not message_length:
            return None
        message_length = int(message_length)
        message = connection.recv(message_length).decode("utf-8")
        return json.loads(message)
    
    def send_pieces_file(self, connection,file_path,chunk= 512*1024):
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
                        break
                    connection.sendall(data)
                connection.sendall(b'done')

            except Exception as e:
                print(e)

        print(f"finish send: {file_path}")
       
    def recieve_pieces_file(self,connection, out_path,chunk=512*1024):
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
        print(f"finish receive: {out_path}")
        
    def handle_peer(self, connection, address):
        """
        to handle request of another host(tracker or peer)
        recieve -> process message -> action
        """
        print(f"[NEW CONNECTION] {address} connected")
        connected = True
        self.add_peer(peer = address)
        while connected:
            message =  self.recieve_message(connection,address)
            response = self.process_message(message)
            self.response_action(connection,address, response),
            connected = False
        connection.close()
            
    def process_message(self, mess):
        """
        process message from request and create action 

        Args:
            mess (dict): request message

        Returns:
            dict: action message 
        """
        # print(json.dumps(mess,indent=4))
        type_message = mess.get("type")
        
        if type_message == "findTorrent":
            file_name = mess.get("file_name")
            response = {
                "action": "response findTorrent",
                "id": self.id,
                "ip": self.ip,
                "port": self.port,
                "hit": self.isObtainedPieces(file_name)
            }
            return response
        
        elif type_message =="getPieces":
            print("here")
            am_choking = self.is_choking()
            am_interested = self.is_interested()
            if not am_choking:
                file_name = mess.get("file_name")
                pieces = get_piece_list_of_file(file_name,self.pieces_storage)   
                response = {
                    "action":"response download pieces",
                    "am_choking":am_choking,
                    "am_interested":am_interested,
                    "pieces": pieces
                }
                return response
            else:
                
                response = {
                    "action":"response download pieces",
                    "am_choking":am_choking,
                }
                
                return response
            
        elif type_message =="downloadPieces":
            pieces = mess.get("pieces")
            chunk_size = mess.get("chunk")
            name = mess.get("file_name") 
            response = {
                "action":"upload pieces",
                "pieces_dicrectory": "pieces",
                "file_name":name,
                "pieces": pieces,
                "chunk": chunk_size
            }
            return response
        else:
            pass
    
    def response_action(self, connection, address, command):
        """
        make action from command send from process message

        Args:
            connection (socket): connnection  of peer which is connected with
            address (ip,port):  address  of peer which is connected with
            command (dict): action message created from process_message
        """
        if command.get("action") == "response findTorrent":
            self.send_message(connection,command)
        if command.get("action") == "response download pieces":
            self.send_message(connection,command)
        if command.get("action") == "upload pieces":
            pieces = command.get("pieces")
            chunk = command.get("chunk")
            name = command.get("file_name")
            for piece in pieces:
                print(piece)
                self.send_pieces_file(connection,f"{self.pieces_storage}/{name}/{piece}")
            print("download done")
                 
        
    def get_peer_list_from_tracker(self, metainfo_path, tracker_ip, tracker_port):
        key =  create_hash_key_metainfo(metainfo_path)
        message = {
            "type":"download",
            "info_hash": key,
            "peer_id": self.id,
            "ip": self.ip,
            "port": self.port,
            "event": "started",            
        } 
        tracker_connection = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
        tracker_connection.connect((tracker_ip,tracker_port))
        self.send_message(tracker_connection,message)
        response = self.recieve_message(tracker_connection)
        print(response)
        peer_list = response.get("peers")
        tracker_connection.close()
        return peer_list

    def getPiecesFromPeers(self,peer_list,file_name):
        piece_hold_by_peers = []
        for peer in peer_list:
            peer_connnection = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_connnection.connect((peer.get("ip"),peer.get("port")))
            message = {
                "type": "getPieces",
                "file_name" : file_name
            }
            self.send_message(peer_connnection,message)
            response = self.recieve_message(peer_connnection)
            pieces_of_peer = response.get("pieces")
            element = {
                "id":peer.get("id"),
                "ip":peer.get("ip"),
                "port":peer.get("port"),
                "pieces":pieces_of_peer
            }
            piece_hold_by_peers.append(element)
            peer_connnection.close()
        return piece_hold_by_peers
    
        
    def optimalToDownload(self,piece_hold_by_peers):
        for i,peer in enumerate(piece_hold_by_peers):
            pass
    
    
    def download_pieces(self,address, pieces_list, file_name):
        with self.semaphore_download:
            peer_connection =  socket.socket(socket.AF_INET,socket.SOCK_STREAM)
            peer_connection.connect(address)
            message = {
                "type": "downloadPieces",
                "file_name": file_name,
                "pieces":pieces_list,
                "chunk": 524288
            }
            self.send_message(peer_connection, message)
            for piece in pieces_list:
                self.recieve_pieces_file(peer_connection,f"{self.pieces_storage}/{file_name}/{piece}")
                
    def download_torrent(self,metainfo_path):
        metainfo = self.parse_metainfo(metainfo_path)
        annouce = metainfo.get("announce")
        annouce = annouce.split(":")
        tracker_ip = annouce[0]
        tracker_port = int(annouce[1])
        file_path = metainfo.get("info").get("name").split(".")
        file_name = file_path[0]
        extension = file_path[1]
        
        total_length = metainfo.get("info").get("length")
        peice_list = metainfo.get("info").get("pieces")
        peice_length = metainfo.get("info").get("piece length")
        # create directory of file pieces
        if not os.path.exists(f"{self.pieces_storage}/{file_name}"):
            os.makedirs(f"{self.pieces_storage}/{file_name}")
        peer_list = self.get_peer_list_from_tracker(metainfo_path,tracker_ip,tracker_port)
        # print(peer_list)
        piece_hold_by_peers = self.getPiecesFromPeers(peer_list,file_name)
        # print(piece_hold_by_peers)    
        
        # piece_hold_by_peers = self.optimalToDownload()
        
        # for peer in piece_hold_by_peers:
        #     self.download_pieces((peer.get("ip"),peer.get("port")),peer.get("pieces"),file_name)
        
        thread_list = []
        for peer in piece_hold_by_peers:
            thread_item = threading.Thread(target=self.download_pieces,args=((peer.get("ip"),peer.get("port")),peer.get("pieces"),file_name))
            thread_list.append(thread_item)
            thread_item.start()
        
        for thread in thread_list:
            thread.join()
            
        # time.sleep(10)
        merge_file_from_pieces(f"{self.pieces_storage}/{file_name}",f"output/mv3.{extension}")
        print(f"{self.pieces_storage}/{file_name}")    
        


    def upload_torrent(self,metainfo = None):
        # create meta info file
        # + splite file to multiple pieces
        # + create meta info file
        # upload meta info file to tracker. 
        self.connect_to_tracker()
        


#####################################################
def download_peer_test():
    peer = Peer(id=3,port = 4043,pieces_storage="pieces3")
    peer.download_torrent("metainfo/test.torrent.json")
    # peer.start()
    
    
def upload_peer_test():
    peer = Peer(id=2,port = 4042,pieces_storage="pieces2")
    peer.upload_torrent()
    peer.start()

# def test_split_file():
    # peer = Peer(id=1,port = 4041)


if __name__ == "__main__":
    # upload_peer_test()
    download_peer_test()