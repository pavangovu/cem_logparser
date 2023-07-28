import json
import re

# CLUS REQ CUSTOM PARSER
# Pavan_Govu
# 10/15/2020
def get_clusreq_json(message, birthGenID, services):
    #parse timestamp normally
    timestamp_start = message.find('[') + 1
    timestamp_end = message.find(']')
    timestamp = message[timestamp_start:timestamp_end].strip()

    #type is clus_req
    type = "clus_req"

    #parse message normally
    message_start = message.find(']') + 1
    message = message[message_start:].strip()

    #event_name can be found after "req_type: ". For example, in clus_req { req_type: REQ_ACK req_info { ack_info { subs_id: 2 gen_id { } for_req: REQ_SUBS } } req_data { } old_mem_i { } new_mem_i { } }, the event_name would be "REQ_ACK"
    event_name_start = message.find("req_type: ") + 10
    event_name_end = message.find("req_info")
    event_name = message[event_name_start:event_name_end].strip()

    #If the event name is "REQ_SUBS", then the producer name is what comes after "svc_name: ". For example, in clus_req { req_type: REQ_SUBS req_info { sub_info { svc_name: "my-svc-1" clus_ip: "127.0.0.2" high_priority_list { high_svc_pri: 2 } conn_client_rq: 1 } } req_data { } old_mem_i { } new_mem_i { } } the producer name would be "my-svc-1"
    if event_name == "REQ_SUBS":
        producer_name_start = message.find("svc_name: ") + 10
        producer_name_end = message.find("clus_ip")
        producer_name = message[producer_name_start:producer_name_end].strip()
    else:
        producer_name = "client ==> CEM"

    #construct json
    log = {
        'timestamp': timestamp,
        'type': type,
        'message': message,
        'event_name': event_name,
        'producer_name': producer_name,
        'birthGenID': birthGenID,
        'services': services
    }

    return log





def extract_services(message):
    pattern = r'SVC name: (\S+)'
    matches = re.findall(pattern, message)
    return matches

# Load the last processed log position if available
last_log_position = None
try:
    with open('log_position.txt', 'r') as position_file:
        last_log_position = position_file.read().strip()
except FileNotFoundError:
    # Log position file doesn't exist, start from the beginning
    print("Log position file not found. Parsing log from the beginning.")

    last_log_position = None
    pass

# Read the log file
with open('cem_server.log', 'r') as file:
    # Skip lines that have already been processed
    if last_log_position is not None:
        line_number, saved_log_entry = last_log_position.split(':')
        line_number = int(line_number)

        try:
            # Verify the starting log entry
            current_log_entry = next(file).strip()
            if current_log_entry != saved_log_entry:
                print("Verification failed. Starting position may be incorrect.")
                exit()

            # Skip remaining lines
            for _ in range(line_number):
                next(file)
        except StopIteration:
            # End of log file reached
            print("Verification failed. Log position is invalid.")
            exit()

    else:
        # Start from the beginning of the log file
        line_number = -1 

    # Process and write log entries to the output file
    with open('cem_loganalysis.txt', 'a') as output_file:
        output_file.write("[\n")
        birthID = False
        serviceList = False
        clusStorage = ""
        logOverride = False

        for line_number, entry in enumerate(file, start=line_number + 1):
            entry = entry.strip()
            if entry:
                # Extract timestamp, type, and message
                timestamp_start = entry.find('[') + 1
                timestamp_end = entry.find(']')
                timestamp = entry[timestamp_start:timestamp_end].strip()

                message_start = entry.find(']') + 1
                message = entry[message_start:].strip()

                if(birthID or serviceList):
                    if("Birth Gen Id" in message):
                        #extract number from this message using regex (eg. REQ_SUBS: Birth Gen Id 1)
                        birthGenID = re.search(r'\d+', message).group()
                        birthID = False
                    elif("Service List" in message):  
                        services = extract_services(message)
                        serviceList = False
                        logOverride = True


                # If "clus_req" is found in the message, call a function to parse the message
                if "clus_req" in message:
                    clusStorage = message
                    birthID = True
                    serviceList = True

                # Create JSON object
                log = {
                    'timestamp': timestamp,
                    'type': 'default',
                    'message': message
                }

                if(logOverride):
                    log = get_clusreq_json(clusStorage, birthGenID, services)
                    logOverride = False

                # Write log entry to the output file
                json.dump(log, output_file, indent=2)
                output_file.write(',\n')

                # Update the last processed log position
                last_log_position = f"{line_number}:{entry}"

        # Remove the trailing comma from the last entry
        output_file.seek(output_file.tell() - 2, 0)
        output_file.truncate()
        

        output_file.write("\n]")

# Save the current log position for resuming
if last_log_position is not None:
    try:
        with open('log_position.txt', 'w') as position_file:
            position_file.write(last_log_position)
    except IOError:
        print("Error occurred while saving log position.")

    

