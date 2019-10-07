# gmail-inbox-cleaner
Automatically archive and mark as read the e-mails on your inbox


## How to use
1. Clone this repository and `cd` into it.
1. Run `pip install -r requirements.txt` (virtualenv is recommended)
1. Run `python cleaner.py`

```
usage: cleaner.py [-h] [--age AGE] [--starred] [--verbose] [--no_archive]
                  [--no_read]

optional arguments:
  -h, --help    show this help message and exit
  --age AGE     Act on e-mails older than x days. Defaults to 30.
  --starred     Keep starred e-mails.
  --verbose     More output of the actions done by the cleaner.
  --no_archive  Don't archive e-mails that met the criteria.
  --no_read     Don't mark e-mails that met the criteria as read.
```