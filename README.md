# Source Control
A C2 server that uses the [A2S query protocol](https://developer.valvesoftware.com/wiki/Server_queries)

## Building the client
If it's not already installed, install [Nim](https://nim-lang.org/install.html)

Then compile:
```bash
nim c -d:release client/main.nim # Will output to client/main
```

## Running the server
 - In `server/`, modify `config.yml` as needed

 - Install the requirements: `pip install -r requirements.txt`

 - Then you can run the server: `python3 source-control.py`

## Using the CLI
 - In `cli/`, modify `config.yml` as needed

 - Install the requirements: `pip install -r requirements.txt`

 - Then you can run the CLI: `python3 cli.py`