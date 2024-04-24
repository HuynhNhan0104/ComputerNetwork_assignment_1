from tracker import Tracker
from peer import Peer
import sys

import argparse

# Tạo một đối tượng ArgumentParser
parser = argparse.ArgumentParser(description="Example of using argparse to handle key-value arguments")

# Thêm các tham số dạng key-value
parser.add_argument('--param1', help='Description of param1')
parser.add_argument('--param2', help='Description of param2')

# Phân tích các tham số dòng lệnh
args = parser.parse_args()

# Truy cập các giá trị của các tham số
if args.param1:
    print("Giá trị của param1:", args.param1)
if args.param2:
    print("Giá trị của param2:", args.param2)

def main():
    print("hello")



if __name__ == "__main__":
    main()