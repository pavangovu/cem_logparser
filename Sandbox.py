import json

test = '{ req_type: REQ_RCV_EVENT req_info { event_info { subs_id: 4 cur_exe_pri: 1 cur_id: 3 gen_id { global_seq_id: 3 subs_id: 4 } event_type: K8S_SERVICE_EVENT event_pld { k8s_event { name: "my-svc-3" event_status: READY ip: "127.0.0.4" } } } } req_data { } old_mem_i { mems { name: "my-svc-1" Cluster_IP: "127.0.0.2" state: 3 global_gen_id: 1 } mems { name: "my-svc-2" Cluster_IP: "127.0.0.3" state: 3 global_gen_id: 2 } } new_mem_i { mems { name: "my-svc-1" Cluster_IP: "127.0.0.2" state: 3 global_gen_id: 1 } mems { name: "my-svc-2" Cluster_IP: "127.0.0.3" state: 3 global_gen_id: 2 } mems { name: "my-svc-3" Cluster_IP: "127.0.0.4" state: 3 global_gen_id: 3 } } }'

data = json.loads(test)

print(data)
