# ComputerNetwork_Assignment1
## Requirement
```bash
python >= 3.7
```
## Installation

```bash
pip install bencode.py
```

## Command line interface
### tracker.py
```bash
python tracker.py --ip your_ip --port your_port --metainfo-storage your_folder_metainfo --header-length bytes
```

### peer.py
```bash
python peer.py --ip your_ip --port your_port --tracker-ip your_tracker_ip --tracker-port your_tracker_port  --header-length bytes\
--metainfo-storage your_folder_metainfo\
--pieces-storage your_folder_hold_pieces\
--ouput-storage your_folder_output\
--download file1.torrent file2.torrent ....
--become-seeder\   # upload after complete download
--upload input1.mp4 input2.pdf ....
```