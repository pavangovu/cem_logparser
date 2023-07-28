import json
import re
import sqlite3

log_file = 'cem_server.log' 
json_file = 'cem_server.json'
json_list = []

#initial classifier
def getType(message):
    if 'error' in message.lower():
        return 'error'
    elif 'warning' in message.lower():
        return 'warning'
    elif 'clus_req' in message.lower():
        return 'clus_req'
    else:
        return 'default'

#read ahead function
def readAhead(log_data, target_phrase, line_number):
    cache = ''
    while True:
        line_number += 1
        line = log_data[line_number]

        if target_phrase in line:
            break
        else:
            cache += line

    return cache

#clus_req parser
def parseClusReq(log, line):

    #determine type of clus_req
    match = re.search(r'req_type:\s*(\w+)', line)
    if match:
        req_type = match.group(1)

        if req_type == 'REQ_SUBS':

            log['type'] = 'REQ_SUBS'

            #store the current line number
            line_number = log_data.index(line)

            target_phrase = 'Queued the event for subs'

            #call function to temporarily read ahead, function returns string of gathered messages
            cache = readAhead(log_data, target_phrase, line_number)

            #scrape clus_req event information using regex
            serviceNames = re.findall(r'SVC name: (\S+)', cache)
            subIDs = re.findall(r'Subs_id : (\d+)', cache)
            gen_id = re.search(r'Client RQ \d+ Gen id (\d+)', cache).group(1)
            producer = re.search(r'Event.*received.*from.*subs (\S+)', cache).group(1)

            if serviceNames:
                log['subscribers'] = serviceNames
            else:
                log['subscribers'] = 'default subscribers'

            if subIDs:
                log['subscriberIDs'] = subIDs
            else:
                log['subscriberIDs'] = 'default subscriber IDs'

            if gen_id:
                log['event_gen_id'] = gen_id
            else:
                log['event_gen_id'] = 'default event id'

            if producer:
                log['producer_name'] = producer
            else:
                log['producer_name'] = 'default producer'
                
            log['event_name'] = 'Service-UP'

            #Scrape subscriber information


            #Subscriber_list { {subs_Id, subs_name, last_event_posted, birth_gen_id, last_event_rcvd, ctr_reboot_times, ctr_svc_down, subs_status},    }
            #create a temporary subscriber object
            temp_subscriber = Subscriber()
            temp_subscriber.subs_name = log['producer_name']
            temp_subscriber.birth_gen_id = log['event_gen_id']
            temp_subscriber.last_event_posted = log['timestamp']
            temp_subscriber.last_event_rcvd = log['timestamp']
            temp_subscriber.subs_status = 'READY'
            temp_subscriber.ctr_reboot_times = 0
            temp_subscriber.ctr_svc_down = 0

            #write subscriber object to database
            #temp_subscriber.writeSubscriber()

    return log

    

#create a subscriber class
class Subscriber:
    subs_id = ''
    subs_name = ''
    last_event_posted = ''
    birth_gen_id = ''
    last_event_rcvd = ''
    ctr_reboot_times = ''
    ctr_svc_down = ''
    subs_status = ''

    #method to write subscriber object to database
    def writeSubscriber(self):
        conn = sqlite3.connect('cem_server.db')
        c = conn.cursor()

        c.execute("INSERT INTO subscribers VALUES (:subs_id, :subs_name, :last_event_posted, :birth_gen_id, :last_event_rcvd, :ctr_reboot_times, :ctr_svc_down, :subs_status)", 
        {
            'subs_id': self.subs_id,
            'subs_name': self.subs_name,
            'last_event_posted': self.last_event_posted,
            'birth_gen_id': self.birth_gen_id,
            'last_event_rcvd': self.last_event_rcvd,
            'ctr_reboot_times': self.ctr_reboot_times,
            'ctr_svc_down': self.ctr_svc_down,
            'subs_status': self.subs_status
        })

        conn.commit()
        conn.close()

#use sql
conn = sqlite3.connect('cem_server.db')
c = conn.cursor()

#if a table does not exist, create it
c.execute("""CREATE TABLE IF NOT EXISTS subscribers (
            subs_id TEXT,
            subs_name TEXT,
            last_event_posted TEXT,
            birth_gen_id INTEGER,
            last_event_rcvd TEXT,
            ctr_reboot_times INTEGER,
            ctr_svc_down INTEGER,
            subs_status TEXT
            )""")

#clear all existing data
c.execute("DELETE FROM subscribers")

# Insert modified data
c.execute("INSERT INTO subscribers VALUES ('2', 'my-svc-1', '2022-01-01 12:00:00', 1, '2022-01-02 13:00:00', 2, 1, 'READY')")
c.execute("INSERT INTO subscribers VALUES ('3', 'my-svc-2', '2022-01-03 14:00:00', 1, '2022-01-04 15:00:00', 1, 1, 'READY')")
c.execute("INSERT INTO subscribers VALUES ('4', 'my-svc-3', '2022-01-05 16:00:00', 1, '2022-01-06 17:00:00', 1, 1, 'READY')")
conn.commit()
conn.close()   

#MAIN PARSER LOGIC
with open(log_file, 'r') as f:
    log_data = f.readlines()

timestamp = ''
message = ''

for line in log_data:
    if line.startswith('['):
        if timestamp and message:
            log = {
                'timestamp': timestamp,
                'type': getType(message),
                'message': message
            }
            if log['type'] == 'clus_req':

                #pass the line before the current line to the clus_req parser
                log = parseClusReq(log, log_data[log_data.index(line) - 1])
                
            json_list.append(log)
        timestamp = line.split(']', 1)[0].strip('[').strip()
        message = line.split(']', 1)[1].strip()
    else:
        message += ' ' + line.strip()

if timestamp and message:
    log = {
        'timestamp': timestamp,
        'type': getType(message),
        'message': message
    }

    #clus req parsing
    if log['type'] == 'clus_req':
        log = parseClusReq(log, line)
    json_list.append(log)

#write to json file
with open(json_file, 'w') as f:
    json.dump(json_list, f, indent=4)