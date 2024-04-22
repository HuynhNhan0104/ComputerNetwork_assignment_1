
import socket 
import json
from utils import create_torrent, create_hash_key_metainfo, get_piece_list_of_file, merge_file_from_pieces

# {
#     "62f518eaaff4903ea10163eee1d98e3c7691d1fe": "my_movie.torrent.json"
# }


s = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
peer = ("169.254.109.192",4041)
s.connect(peer) 

HEADER = 1024
#Nhập vào tên file 
# filename = input("Enter a filename ")


    
#Gửi tên file cho server
def send_message(mess):
    message = ""
    message = json.dumps(mess)
    message = message.encode("utf-8")
    message_length = str(len(message)).encode("utf-8")
    
    message_length += b' '*(HEADER - len(message_length))
    s.send(message_length)
    s.send(message)
    
def recieve_message():
        message_length = s.recv(HEADER).decode("utf-8")
        if not message_length:
            return None
        message_length = int(message_length)
        message = s.recv(message_length).decode("utf-8")
        return json.loads(message)
    
def send_file(file_path,chunk=512*1024):
        with open(file_path,"rb") as item:
            data = item.read(chunk)
            while data:
                s.send(data)
                data = item.read(chunk)
        # message = {
        #     "status":"done"
        # }
        # send_message(s,message)
        print(f"finish send: {file_path}")
        
        
    
def recieve_file(out_path,chunk= 524288):
    with open(out_path,"wb") as item:
        while data:=s.recv(chunk):
            item.write(data)
    #
    print(f"finish receive: {out_path}")
    
    
    
def test_torrent():  
    file_path = "input/meeting_1.mp4"
        
        # file_path = 'input/test.txt'

    tracker_url = 'http://localhost:5050'
    output_file = 'output/my_movie.torrent.json'
    torrent_data = create_torrent(file_path, tracker_url, output_file)
    key = create_hash_key_metainfo("metainfo/my_movie.torrent.json")

    message = {
        "type":"download",
        "info_hash": key,
        "peer_id": 1,
        "port": 4040,
        "event": "started",
        "ip": "192.168.31.119"
    }  
    # send_message("Hello")    
    #Nhận được dữ liệu từ server gửi tới
    # recieve_message(s)
    print(json.dumps(message,indent=4))
    send_message(message)
    # recieve_message(s)


    data = recieve_message()
    print(json.dumps(data,indent= 4))



def test_peer():
        
    metainfo = {
        "announce": "http://localhost:8080",
        "info": {
            "name": "meeting_1.mp4",
            "length": 360314102,
            "pieces": [],
            "piece length": 524288 
        }
    }

    message = {
        "type": "findTorrent",
        "tracker_id": "1",
        "file_name": metainfo.get("info").get("name")
    }
    send_message(message)
    response = recieve_message()
    print(json.dumps(response,indent=4))
    

def test_file_transfer():
    pieces_list = get_piece_list_of_file("meeting_1.mp4")
    message = {
        "type": "downloadPieces",
        "file_name": "meeting_1",
        "pieces":pieces_list,
        "chunk": 524288
    }
    send_message(message)
    # response = recieve_message()
    # print(json.dumps(response,indent=4))
    
    # while not finished:
    for piece in pieces_list:
        recieve_file(f"test/meeting_1/{piece}")
    merge_file_from_pieces("test/meeting_1")
            
# test_peer()
test_file_transfer()


s.close()