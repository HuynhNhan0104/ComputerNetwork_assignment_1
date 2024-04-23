import os
import hashlib
import bencodepy  # You'll need to install this library: pip install bencodepy
import json
###################################################################3
# 512KB piece size
PIECE_LENGTH = 512*1024
   
def calculate_file_pieces_hash(file_path):
    # Calculate the SHA-1 hash of the file
    sha1 = hashlib.sha1()
    pieces_hash = []
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(PIECE_LENGTH)  # Read in 512KB chunks
            if not data:
                break
            # sha1.update(data)
            sha1 = hashlib.sha1(data).hexdigest()
            pieces_hash.append(sha1)
    return pieces_hash




def create_torrent(file_path, tracker_url, output_file):
    # Calculate file hash
    pieces_hash = calculate_file_pieces_hash(file_path)
    # print (str(file_hash))
    # Calculate file size
    file_size = os.path.getsize(file_path)

    # Generate torrent dictionary
    torrent_data = {
        "announce": tracker_url,
        "info": {
            # "hash": "1",
            "name": os.path.basename(file_path),
            "length": file_size,
            "pieces": str(pieces_hash),
            "piece length": PIECE_LENGTH  # 512KB piece size
        }
    }
    

    # Encode the torrent dictionary using bencode
    encoded_torrent = bencodepy.encode(torrent_data)

    # # Write the encoded torrent data to a file
    with open(output_file, 'w') as f:
        f.write(json.dumps(torrent_data,indent = 4))
        
        
        
################################################################
def write_data_file(data,output_file_name: str):
    # print(str(data))
    with open(output_file_name +".txt", 'wb') as f:
        f.write(data) 

def split_file_to_pieces(file_path:str,output_pieces_directory: str, file_name_index:str):
    with open(file_path, 'rb') as f:
        i: int = 0
        while True:
            data = f.read(PIECE_LENGTH)  # Read in 512KB chunks
            if not data:
                break
            write_data_file(data,output_pieces_directory+"/" + file_name_index+"_"+str(i))
            i+=1

def merge_file_from_pieces(file_paths, output_file_path = "output/outputfile.mp4"):
    if os.path.isdir(file_paths):
        print(f"input folder: {file_paths}")
        file_name_list = os.listdir(file_paths)
        file_name_list = sorted(file_name_list,key = lambda x: int(x.split("_")[0]))
        print(file_name_list)
        
        file_paths = [(file_paths+ "/" + file_name) for file_name in file_name_list]
        # print(file_paths)
    print(f"output file:{output_file_path}")
    with open(output_file_path,"ab") as out:
        for file_path in file_paths:
            with open(file_path,"rb") as item:
                data = item.read(PIECE_LENGTH)
                out.write(data)
                
###################################
def create_hash_key_metainfo(file):
    with open(file, "rb") as torrent:
        data = torrent.read()
        key = hashlib.sha1(data).hexdigest()
        return key
    
def create_metainfo_hashtable(directory):
    hash_table = {}
    if not os.path.isdir(directory):
        raise(f"[UTILS] Cannot create hashtable because {directory} is not a directory")
    
    files_list =  os.listdir(directory)
    if not files_list:
        raise(f"[UTILS] Cannot create hashtable because {directory} is emmpty")
    
    for file_name in files_list:
        # print(file)
        file_path = directory + "/" + file_name
        key = create_hash_key_metainfo(file_path)
        # print(key)
        hash_table.update({key:file_path})
    return hash_table
            
####################################
def get_file_name_pieces_directory(pieces_root = "pieces"):
    return os.listdir(pieces_root)      
        
def get_idx_and_hash_of_piece(piece_path):
    name = os.path.basename(piece_path)
    name = name.split(".")[0]
    name = name.split("_")
    idx= name[0]
    hash_code = name[1]
    return (idx, hash_code)
    
    
def get_piece_list_of_file( filename,pieces_root = "pieces"):
    pieces = os.listdir(f"{pieces_root}/{filename}")
    pieces = sorted(pieces, key=lambda file: int(file.split("_")[0]))
    return pieces
    
    
    
def create_pieces_directory(file_path,pieces_root = "pieces" ):
    directory_path = os.path.basename(file_path)
    directory_path = directory_path.split(".")[0]
    directory_path = pieces_root+ "/"+ directory_path
    print(directory_path)
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
    with open(file_path, 'rb') as f:
        idx: int = 0
        while True:
            # Read in 512KB chunks
            data = f.read(PIECE_LENGTH)
            hex_hash = hashlib.sha1(data).hexdigest()
            hex_hash = str(hex_hash)
            if not data:
                break
            write_data_file(data,f"{directory_path}/{str(idx)}_{hex_hash}")
            idx+=1
        
    
    
    
# Example usage:
def test_torrent():
    # file_path = 'D:/input_for_computer_network/sd-blob-b01.img'
    file_path = "input/meeting_1.mp4"
    
    # file_path = 'input/test.txt'

    tracker_url = 'http://localhost:8080'
    output_file = 'output/my_movie.torrent.json'

    create_torrent(file_path, tracker_url, output_file)
    
    

if __name__ == "__main__":
    # test_split_file_to_pieces(file_path,"pieces/movie","mv_part")
    # merge_file_from_pieces("pieces/movie","metainfo/my_movie.mp4")
    # test_torrent()
    # print(get_file_name_pieces_directory())
    # create_pieces_directory("input/test.mp4")
    
    # print(get_piece_list_of_file("meeting_1.mp4"))
    # create_pieces_directory("input/test.mp4")
    merge_file_from_pieces("pieces/test",output_file_path="output/mv3.mp4")
    
