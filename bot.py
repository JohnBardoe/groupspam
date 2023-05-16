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

async def main(run_flag, accounts, tasks, groups, settings):
    clients = []
    for account_path in accounts:
        account_id = account_path.split("/")[-1]
        tdesk = TDesktop(account_path+"/tdata")
        assert tdesk.isLoaded()
        client = await tdesk.ToTelethon(session="{}.session".format(account_id), flag=UseCurrentSession)
        client.proxy = settings['proxy']
        print("Loaded account " + account_id)
        clients.append({"client": client, "added": 0, "failed": 0, "id": account_id})
    
    report = [ [0, 0, group] for group in groups ]
    banned_clients = []
    while tasks != [] and clients != [] and run_flag.value:
        try:
            task = tasks.pop()
            user = task[0]
            group = task[1]
            client = random.choice(clients)
            await client['client'].connect()
            await asyncio.sleep(random.uniform(0, 1))
            group_entity = await client['client'].get_entity(group)
            await client['client'](JoinChannelRequest(group_entity.id))
            if isinstance(group_entity, telethon.tl.types.Chat):
                await client['client'](AddChatUserRequest(group_entity.id, user, fwd_limit=0))
            elif isinstance(group_entity, telethon.tl.types.Channel):
                await client['client'](InviteToChannelRequest(group_entity.id, [user]))
            await client['client'].disconnect()
            print("Successfully added " + user + " to " + group)
            for i in range(len(report)):
                if report[i][2] == group:
                    report[i][0] += 1
                    break
            for i in range(len(tasks)):
                if tasks[i][0] == user:
                    del tasks[i]
                    break
            client['added'] += 1
        except Exception as e:
            client['failed'] += 1
            print("Failed to add " + user + " to " + group)
            print(e)

            for i in range(len(report)):
                if report[i][2] == group:
                    report[i][1] += 1
                    break
            if "Too many requests" in str(e):
                print("Too many requests, sleeping for 20 secs")
                await asyncio.sleep(20)
                continue
            if "deleted/deactivated" in str(e):
                print("This account is deleted/deactivated. Don't use it")
                banned_clients.append(me.id)
                for i in range(len(clients)):
                    if clients[i] == client:
                        del clients[i]
                        break
                continue
            if "A wait of" in str(e):
                print("This account is limited. Don't use it")
                for i in range(len(clients)):
                    if clients[i] == client:
                        del clients[i]
                        break
                continue
            await asyncio.sleep(random.randint(1, 3))
            continue
        finally:
            if client['added'] >= settings['maxadd'] or client['failed'] + client['added'] >= settings['maxreq']:
                print("This account has added enough users, don't use it ", client['id'])
                for i in range(len(clients)):
                    if clients[i] == client:
                        del clients[i]
                        break

    print("Report:")
    for r in report:
        print("Group: {}, Success: {}, Failed: {}".format(r[2], r[0], r[1]))
    print("Banned clients: ")
    for client in banned_clients:
        print(client)

def entry(run_flag, tasks, groups, settings):
    accounts = glob.glob("./accounts/*")
    sessions = glob.glob("*.session")
    print("Deleting " + str(len(sessions)) + " sessions")
    for session in sessions:
        os.remove(session)
    
    sys.stdout = open("botlog.out", "w+")
    sys.stderr = open("botlog.err", "w+")
    sys.stdout.reconfigure(line_buffering=True)
    sys.stderr.reconfigure(line_buffering=True)

    loop = asyncio.get_event_loop()
    loop.run_until_complete(main(run_flag, accounts, tasks, groups, settings))
