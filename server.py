import asyncio
import websockets

USERS = {}
ROOMS = {}
R = {}
DATA_FILENAME = "chat_data.json"

async def addUser(websocket, user_name):
    USERS[websocket] = user_name

async def removeUser(websocket):
    USERS.pop(websocket)


async def createRoom(room_name):
    ROOMS[room_name] = set()


async def addUserToRoom(websocket, room_name):
    ROOMS[room_name].add(websocket)


async def removeUserFromRoom(websocket, room_name):
    ROOMS[room_name].remove(websocket)

async def saveRoomData(room_name, room_messages):
    with open(f"{room_name}.txt", "a") as room_file:
        for message in room_messages:
            room_file.write(message + "\n")

async def sendSavedMessagesToUser(websocket, room_name):
    room_messages = []
    try:
        with open(f"{room_name}.txt", "r") as room_file:
            room_messages = room_file.read().splitlines()
    except FileNotFoundError:
        pass
    for message in room_messages:
        await websocket.send(message)

async def socket(websocket, path):
    await addUser(websocket, "")

    try:
        room_name = 'hub'
        if room_name not in ROOMS:
            await createRoom(room_name)
        await addUserToRoom(websocket, room_name)
        await sendSavedMessagesToUser(websocket, room_name)
        while True:
            message = await websocket.recv()
            print(message)
            if message.startswith('/setUserName '):
                user_name = message.split(' ')[1]
                USERS[websocket] = user_name
            elif message.startswith('/create '):
                for room in ROOMS:
                    if websocket in ROOMS[room]:
                        await removeUserFromRoom(websocket, room)

                room_name = message.split(' ')[1]
                if room_name not in ROOMS:
                    await createRoom(room_name)
                    await addUserToRoom(websocket, room_name)
                    await websocket.send(f'You created and entered room: {room_name}')
                else:
                    await websocket.send(f'Room already exist')

            elif message.startswith('/enter '):
                room_name = message.split(' ')[1]
                if room_name in ROOMS:
                    for room in ROOMS:
                        if websocket in ROOMS[room]:
                            await removeUserFromRoom(websocket, room)
                    await addUserToRoom(websocket, room_name)
                    await websocket.send(f'You entered room: {room_name}')
                    await sendSavedMessagesToUser(websocket, room_name)
                else:
                    await websocket.send(f'Room {room_name} does not exist.')
            elif message.startswith('/leave '):
                room_name = message.split(' ')[1]
                if room_name in ROOMS:
                    await removeUserFromRoom(websocket, room_name)
                    await websocket.send(f'You left room: {room_name}')
                else:
                    await websocket.send(f'Room {room_name} does not exist.')
            elif message.startswith('/listRooms'):
                for room in ROOMS:
                    users = [USERS[us] for us in USERS if us in ROOMS[room]]
                    await websocket.send(f'Room: {room}, Users: {users}')
            else:
                for user in ROOMS.get(room_name, set()):
                    await user.send(message)
                room_messages = []
                room_messages.append(str(message))
                R[room_name] = room_messages
                await saveRoomData(room_name, room_messages)

    finally:
        for room_name in ROOMS:
            if websocket in ROOMS[room_name]:
                await removeUserFromRoom(websocket, room_name)
        await removeUser(websocket)


start_server = websockets.serve(socket, '127.0.0.1', 5678)

asyncio.get_event_loop().run_until_complete(start_server)
asyncio.get_event_loop().run_forever()
