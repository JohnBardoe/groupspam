from opentele.td import TDesktop
from opentele.tl import TelegramClient
from opentele.api import API, UseCurrentSession
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.functions.channels import InviteToChannelRequest, JoinChannelRequest
import telethon
import asyncio
import glob
import os, sys, random 
import csv
import json

def getTasks(inout_path):
    tasks = []
    with open(inout_path) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            try:
                tasks.append(row[1])
            except:
                pass
    return tasks

async def main(progress_data, run_flag, accounts, tasks, groups, proxy):
    clients = []
    for account_path in accounts:
        account_id = account_path.split("/")[-1]
        tdesk = TDesktop(account_path+"/tdata")
        assert tdesk.isLoaded()
        client = await tdesk.ToTelethon(session="{}.session".format(account_id), flag=UseCurrentSession)
        client.proxy = proxy
        print("Loaded account " + account_id)
        clients.append(client)
    
    report = [ [0, 0, group] for group in groups ]
    banned_clients = []
    while tasks != [] and run_flag.value:
        try:
            task = tasks.pop()
            user = task[0]
            group = task[1]
            client = random.choice(clients)
            await client.connect()
            await asyncio.sleep(random.uniform(0, 1))
            group_entity = await client.get_entity(group)
            await client(JoinChannelRequest(group_entity.id))
            if isinstance(group_entity, telethon.tl.types.Chat):
                await client(AddChatUserRequest(group_entity.id, user, fwd_limit=0))
            elif isinstance(group_entity, telethon.tl.types.Channel):
                await client(InviteToChannelRequest(group_entity.id, [user]))
            await client.disconnect()
            print("Successfully added " + user + " to " + group)
            for i in range(len(report)):
                if report[i][2] == group:
                    report[i][0] += 1
                    break
            for i in range(len(tasks)):
                if tasks[i][0] == user:
                    del tasks[i]
                    break
            progress_data[group]['success'] += 1
        except Exception as e:
            progress_data[group]['failed'] += 1
            for i in range(len(report)):
                if report[i][2] == group:
                    report[i][1] += 1
                    break
            if "Too many requests" in str(e):
                print("Too many requests, sleeping for 20 secs")
                await asyncio.sleep(20)
                continue
            if "A wait of" in str(e):
                print("This account is limited. Don't use it")
                me = await client.get_entity('me')
                banned_clients.append(me.id)
                for i in range(len(clients)):
                    if clients[i] == client:
                        del clients[i]
                        break
                continue
            print("Failed to add " + user + " to " + group)
            print(e)
            await asyncio.sleep(random.randint(1, 3))
            continue
    print("Report:")
    for r in report:
        print("Group: {}, Success: {}, Failed: {}".format(r[2], r[0], r[1]))
    print("Banned clients: ")
    for client in banned_clients:
        print(client)
   
def entry(progress_data, run_flag, tasks, groups, proxy):
    accounts = glob.glob("./accounts/*")
    sessions = glob.glob("*.session")
    print("Deleting " + str(len(sessions)) + " sessions")
    for session in sessions:
        os.remove(session)
    
    sys.stdout = open("botlog.out", "a", buffering=0)
    sys.stderr = open("botlog.err", "a", buffering=0)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(progress_data, run_flag, accounts, tasks, groups, proxy))
