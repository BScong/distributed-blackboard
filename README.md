# Distributed Blackboard

Distributed Systems (TDA596) project - Chalmers University of Technology

## Lab 1
Every node propagates its data to the other nodes.

### Task 1 : Adding values
To add values, we simply define ```action="ADD"``` with the value we would like to add. Then we propagate this request to the other nodes. Of course, a node only propagate only its own requests (else we will have infinite loops).

### Task 2 : Modifying and deleting values
Same principle as in task 1. We defined ```action="MOD"``` for modifications and ```action="DEL"``` for deletions. "MOD" must have a key and a value, "DEL" must have a key. We then propagate the request to the other nodes.

### Task 3 : Consistency
We can show that this system is not consistent through the script ```consistency.sh```. By executing ```curl```commands to add values to multiple servers at almost the same time (i.e. the delay between the commands is too short compared to the propagation time). Hence we can have different boards with different key/values.

### Communication
We also implemented re-	attempts on communications in case of non-success (HTTP Response different than 200 or no response).

## Lab 2
Centralized version where the nodes elect a leader.

### Forwarding requests
When a node wants to ADD, MOD or DEL a value, the request is forwarded to the leader.
If the request is ADD or MOD, the leader then sends a ```action="SET"```request to all nodes, with a key and a value. Every node then sets its local store according to the key/value.
If the request is DEL, the leader sends a ```action="DEL"``` request, with a key. Every nodes then delete this key from its store.
 
#### Communication cost
Let's define a request as an action, a key and a value. Let's define N as the number of nodes.
The payload for each message is one request so the overall cost is 1.

For one request, the initiator sends it to the leader. Then the leaders sends it to all the nodes (i.e. to (N-1) nodes because he doesn't send the request to himself).
So the overall cost per request is N (or N-1 if the initiator is the leader).

Obviously, this cost increases if we have re-attempts on the requests.

(Another solution we thought of was to simply forward the GET request to the leader, but it is too costly.)
