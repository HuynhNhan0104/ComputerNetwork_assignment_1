import os
import hashlib
import bencodepy  # You'll need to install this library: pip install bencodepy

# 512KB piece size
PIECE_LENGTH = 512*1024




def write_data_file(data,output_file_name: str):
    # print(str(data))
    with open(output_file_name +".txt", 'wb') as f:
        f.write(data)
        
def calculate_file_hash(file_path):
    # Calculate the SHA-1 hash of the file
    sha1 = hashlib.sha1()
    with open(file_path, 'rb') as f:
        while True:
            data = f.read(PIECE_LENGTH)  # Read in 512KB chunks
            if not data:
                break
            sha1.update(data)
    return sha1.digest()




def create_torrent(file_path, tracker_url, output_file):
    # Calculate file hash
    file_hash = calculate_file_hash(file_path)
    print (str(file_hash))
    # Calculate file size
    file_size = os.path.getsize(file_path)

    # Generate torrent dictionary
    torrent_data = {
        'announce': tracker_url,
        'info': {
            'name': os.path.basename(file_path),
            'length': file_size,
            'pieces': [file_hash],
            'piece length': PIECE_LENGTH  # 512KB piece size
        }
    }

    # Encode the torrent dictionary using bencode
    encoded_torrent = bencodepy.encode(torrent_data)

    # # Write the encoded torrent data to a file
    # with open(output_file, 'wb') as f:
    #     f.write(encoded_torrent)
        
        

def split_file_to_pieces(file_path:str,output_pieces_directory: str, file_name_index:str):
    with open(file_path, 'rb') as f:
        i: int = 0
        while True:
            data = f.read(PIECE_LENGTH)  # Read in 512KB chunks
            if not data:
                break
            write_data_file(data,output_pieces_directory+"/" + file_name_index+"_"+str(i))
            i+=1

def merge_file_from_pieces(file_paths, output_file_path = "output/outputfile.txt"):
    if os.path.isdir(file_paths):
        print("Đây là một thư mục.")
        file_name_list = os.listdir(file_paths)
        file_name_list = sorted(file_name_list,key = lambda x: int(x.split("_")[-1].split(".")[0]))
        print(file_name_list)
        
        file_paths = [(file_paths+ "/" + file_name) for file_name in file_name_list]
        print(file_paths)
    print("merge file time:")
    with open(output_file_path,"ab") as out:
        for file_path in file_paths:
            with open(file_path,"rb") as item:
                data = item.read(PIECE_LENGTH)
                out.write(data)
                

# Example usage:
def test_torrent():
    file_path = 'D:/input_for_computer_network/sd-blob-b01.img'
    # file_path = 'input/test.txt'

    tracker_url = 'http://localhost:8080'
    output_file = 'output/file.torrent'

    create_torrent(file_path, tracker_url, output_file)
    
    
if __name__ == "__main__":
    print("hello 1" )
    file_path = 'input/meeting_1.mp4'
    # test_split_file_to_pieces(file_path,"pieces/movie","mv_part")
    merge_file_from_pieces("pieces/movie","output/my_movie.mp4")
    
    print("bye 1" )
    
