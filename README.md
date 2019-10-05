# gmail-inbox-cleaner
Automatically archive and mark as read the e-mails on your inbox


## How to use
1. Clone this repository and `cd` into it.
1. Run `pip install -r requirements.txt` (virtualenv is recommended)
1. Run `python cleaner.py`


    usage: cleaner.py [-h] [--age AGE] [--starred]
    
    optional arguments:
      -h, --help  show this help message and exit
      --age AGE   Archive e-mails older than x days.
      --starred   Keep starred e-mails.