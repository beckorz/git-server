# git server

git server for Python3(on Flask).

## Requirement
- git client
- Python 3.+
    - flask `pip install flask`

## Usage

### Start git server

```sh
mkdir repos
git init --bare repos/aaa
git init --bare repos/bbb
python app.py
```

### From git client

```
git clone http://localhost:5000/aaa
git clone http://localhost:5000/bbb
```

## Thanks
- [stewartpark/git-server.py](https://gist.github.com/stewartpark/1b079dc0481c6213def9)
    - Python2 to Python3.

