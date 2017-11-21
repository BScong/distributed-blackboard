# coding=utf-8
#------------------------------------------------------------------------------------------------------
# TDA596 Labs - Server Skeleton
# server/server.py
# Input: Node_ID total_number_of_ID
# Student Group: Group 13
# Student names: Ludovic Giry & Benoit Zhong
#------------------------------------------------------------------------------------------------------
# We import various libraries
from BaseHTTPServer import HTTPServer, BaseHTTPRequestHandler # Socket specifically designed to handle HTTP requests
import sys # Retrieve arguments
import os # Paths to HTML files
import ast
import random
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management
import time
#------------------------------------------------------------------------------------------------------

# Global variables for HTML templates
script_dir = os.path.dirname(__file__)
if script_dir == "": script_dir="."
board_frontpage_footer_template = open(script_dir + "/board_frontpage_footer_template.html","r").read() % "Ludovic Giry & Benoit Zhong (benoitz@student.chalmers.se) - Group 13"
board_frontpage_header_template = open(script_dir + "/board_frontpage_header_template.html","r").read()
boardcontents_template = open(script_dir + "/boardcontents_template.html","r").read()
entry_template = open(script_dir + "/entry_template.html","r").read()

#------------------------------------------------------------------------------------------------------
# Static variables definitions
PORT_NUMBER = 80
#------------------------------------------------------------------------------------------------------



#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
class BlackboardServer(HTTPServer):
#------------------------------------------------------------------------------------------------------
	def __init__(self, server_address, handler, vessel_id, vessel_list):
	# We call the super init
		HTTPServer.__init__(self,server_address, handler)
		# we create the dictionary of values
		self.store = {}
		# We keep a variable of the next id to insert
		self.current_key = -1
		# our own ID (IP is 10.1.0.ID)
		self.vessel_id = vessel_id #"10.1.0."+vessel_id
		# The list of other vessels
		self.vessels = vessel_list
		# The leader id
		self.leader_id = -1
		# Random number generated
		self.random = random.randint(0,1000)

		# Neighbor in the ring
		number_of_vessels=len(vessel_list)
	 	self.neighbor_id = ((self.vessel_id)%number_of_vessels)+1

	 	#Starting Leader Election
		thread = Thread(target=self.start_leader_election )
		# We kill the process if we kill the server
		thread.daemon = True
		# We start the thread
		thread.start()

#------------------------------------------------------------------------------------------------------
	# We add a value received to the store - This function is only used by the leader
	def add_value_to_store(self, value):
		self.current_key += 1
		self.store[self.current_key] = value
		return self.current_key
#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store - This function is only used by the leader
	def modify_value_in_store(self,key,value):
		# we modify a value in the store if it exists
		if key in self.store:
			self.store[key]=value
#------------------------------------------------------------------------------------------------------
	# We delete a value received from the store
	def delete_value_in_store(self,key):
		# we delete a value in the store if it exists
		if key in self.store:
			del self.store[key]
		
#------------------------------------------------------------------------------------------------------
	# We set a value that the leader gave us - This function is only used by the slaves
	def set_value_in_local_store(self, key, value):
		if key not in self.store:
			self.store[key]=""
		self.store[key]=value

		# we update the current key
		if key > self.current_key:
			self.current_key = key

#------------------------------------------------------------------------------------------------------
# Contact a specific vessel with a set of variables to transmit to it
	def contact_vessel(self, vessel_ip, path, action, key, value):
		# the Boolean variable we will return
		success = False
		# The variables must be encoded in the URL format, through urllib.urlencode
		post_content = urlencode({'action': action, 'key': key, 'value': value})
		# the HTTP header must contain the type of data we are transmitting, here URL encoded
		headers = {"Content-type": "application/x-www-form-urlencoded"}
		# We should try to catch errors when contacting the vessel
		try:
			# We contact vessel:PORT_NUMBER since we all use the same port
			# We can set a timeout, after which the connection fails if nothing happened
			connection = HTTPConnection("%s:%d" % (vessel_ip, PORT_NUMBER), timeout = 30)
			# We only use POST to send data (PUT and DELETE not supported)
			action_type = "POST"
			# We send the HTTP request
			connection.request(action_type, path, post_content, headers)
			# We retrieve the response
			response = connection.getresponse()
			# We want to check the status, the body should be empty
			status = response.status
			# If we receive a HTTP 200 - OK
			if status == 200:
				success = True
		# We catch every possible exceptions
		except Exception as e:
			print "Error while contacting %s" % vessel_ip
			# printing the error given by Python
			print(e)

		# we return if we succeeded or not
		return success
#------------------------------------------------------------------------------------------------------
	# We send a received value to all the other vessels of the system
	def propagate_value_to_vessels(self, path, action, key, value):
		retry_list = [] # we will store the vessels without success
		# We iterate through the vessel list
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				success = self.contact_vessel(vessel, path, action, key, value)
				if not success:
					retry_list.append(vessel)

		# for the vessels who failed, we retry
		try_count = 0
		while len(retry_list)>0 and try_count < 15:
			try_count += 1
			for vessel in retry_list:
				success = self.contact_vessel(vessel, path, action, key, value)
				if success : retry_list.remove(vessel)
		if len(retry_list)>0:
			print("Problem occured with " + ", ".join(retry_list) + " : Unable to connect after multiple attempts.")

	# Function to forward the request to the leader
	def forward_request_to_leader(self, path, action, key, value):
		leader_ip = "10.1.0."+str(self.leader_id)
		success = False
		try_count = 0
		while success == False and try_count < 10: 
			try_count += 1 # If the request fails, we retry (10 retry max)
			success = self.contact_vessel(leader_ip,path,action,key,value)
		if success == False:
			print("Problem occured with " + leader_ip + " : Unable to join after multiple attempts.")
		
#------------------------------------------------------------------------------------------------------
	def start_leader_election (self):
		time.sleep(1)
		data_gathering={}
		data_gathering[self.vessel_id]=self.random
	  	#self.current_key+=1
		print "trying to contact"+str(self.neighbor_id)	
		self.contact_vessel("10.1.0."+str(self.neighbor_id), "/election", "ELE", self.vessel_id, data_gathering)


#------------------------------------------------------------------------------------------------------
	def end_leader_election (self, parsed_value):
		parsed_value=str(parsed_value)
		time.sleep(5)
		data_gathering=ast.literal_eval(parsed_value)#  Convert a string to a dictionnary
		leader_id=0
		for key in data_gathering :
			if data_gathering[key] > leader_id :
				leader_id=data_gathering[key]
				leader_id=key
		self.leader_id=leader_id#find the key of the highest value
		print ("Choosing the leader ",self.leader_id)
		#I start warning my neighbors about my choice	
		self.contact_vessel("10.1.0."+str(self.neighbor_id), "/election", "COO", self.vessel_id,self.leader_id)
#------------------------------------------------------------------------------------------------------


#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# This class implements the logic when a server receives a GET or POST request
# It can access to the server data through self.server.*
# i.e. the store is accessible through self.server.store
# Attributes of the server are SHARED accross all request hqndling/ threads!
class BlackboardRequestHandler(BaseHTTPRequestHandler):
#------------------------------------------------------------------------------------------------------
	# We fill the HTTP headers
	def set_HTTP_headers(self, status_code = 200):
		 # We set the response status code (200 if OK, something else otherwise)
		self.send_response(status_code)
		# We set the content type to HTML
		self.send_header("Content-type","text/html")
		# No more important headers, we can close them
		self.end_headers()
#------------------------------------------------------------------------------------------------------
	# a POST request must be parsed through urlparse.parse_QS, since the content is URL encoded
	def parse_POST_request(self):
		post_data = self.path
		# We need to parse the response, so we must know the length of the content
		length = int(self.headers['Content-Length'])
		# we can now parse the content using parse_qs
		post_data = parse_qs(self.rfile.read(length), keep_blank_values=1)
		# we return the data
		return post_data
#------------------------------------------------------------------------------------------------------	
#------------------------------------------------------------------------------------------------------
# Request handling - GET
#------------------------------------------------------------------------------------------------------
	# This function contains the logic executed when this server receives a GET request
	# This function is called AUTOMATICALLY upon reception and is executed as a thread!
	def do_GET(self):
		print("Receiving a GET on path %s" % self.path)
		# Here, we should check which path was requested and call the right logic based on it
		if self.path == "/board":
			self.do_GET_Board()
		else:
			self.do_GET_Index()
#------------------------------------------------------------------------------------------------------
# GET logic - specific path
#------------------------------------------------------------------------------------------------------
	def do_GET_Index(self):
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)
	
		#We go over the entries list, 
		#produce the boardcontents part, 
		#then construct the full page by combining all the parts ...

		html_response = board_frontpage_header_template + self.generate_entries() + board_frontpage_footer_template
		
		self.wfile.write(html_response)

	def do_GET_Board(self):
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)

		# We send back the entries
		self.wfile.write(self.generate_entries())

	def generate_entries(self):
		entries = ""
		for entryId in self.server.store.keys():
			entries += entry_template % ("entries/"+str(entryId),entryId,self.server.store[entryId])
		board = boardcontents_template % ("Sample board @ 10.0.1."+str(self.server.vessel_id) + ". Leader : 10.1.0."+str(self.server.leader_id) + ", my random number : " +str(self.server.random),entries)
		return board


#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
		print("Receiving a POST on %s" % self.path)

		parsed = self.parse_POST_request() # Parsing data
		print(parsed)

		# Check if the path is correct
		valid_path_entries = True if "/entries" in self.path else False
		valid_path_election = True if "/election" in self.path else False
		
		if valid_path_entries:
			self.do_POST_entries(parsed)
		elif valid_path_election:
			self.do_POST_election(parsed)
		else:
			self.set_HTTP_headers(400)
#------------------------------------------------------------------------------------------------------
# POST Logic
#------------------------------------------------------------------------------------------------------
	
	# POST Logic for entries (slave/leader)
	def do_POST_entries(self, parsed):
		# Fetch parameters
		action, key, value, propagate = self.get_entries_parameters(parsed)
		# action is in ["ADD","DEL","MOD","SET"].
		# We added the action "SET" that sets a value for a specific key
		# propagate is true if the request comes from me.
		# (If the request is received from someone else, then propagate is false)

		# Validate parameters
		isValid = self.are_parameters_valid(action, key, value)

		if isValid:
			self.set_HTTP_headers(200)

			# self.do_POST_entries_vessel(action,key,value,propagate) # This was used in propagate version (task 1)
			
			if self.server.vessel_id == self.server.leader_id : # If I am the leader
				self.do_POST_entries_leader(action, key, value) # Directly do the action
			elif not propagate : # If the request comes from the leader
				self.do_POST_entries_slave(action, key, value)
			else: # We forward the request we received to the leader
				# do_POST send the message only when the function finishes
				# We must then create threads if we want to do some heavy computation
				thread = Thread(target=self.server.forward_request_to_leader,args=("/entries", action, key, value) )
				# We kill the process if we kill the server
				thread.daemon = True
				# We start the thread
				thread.start()

		else:
			self.set_HTTP_headers(400)

	# Specific POST Logic for leader (centralized version)
	def do_POST_entries_leader(self, action, key, value):
		if action == "ADD" : # Entry added by another server
			print("Adding entry")
			action="SET"
			key = self.server.add_value_to_store(value) 
		elif action == "MOD" :
			print("Modifying entry")
			action="SET"
			self.server.modify_value_in_store(key,value) 
		elif action == "DEL" :
			print("Deleting entry")
			self.server.delete_value_in_store(key) 

		thread = Thread(target=self.server.propagate_value_to_vessels,args=("/entries", action, key, value) )
		# We kill the process if we kill the server
		thread.daemon = True
		# We start the thread
		thread.start()

	# Slave POST Logic in centralized version
	def do_POST_entries_slave(self, action, key, value):
		if action == "SET" :
			forward = False # but don't forward if the order is from the leader
			print("Entry from leader received")
			self.server.set_value_in_local_store(key, value)
		elif action =="DEL": 
			forward = False # but don't forward if the order is from the leader
			print("Delete order from leader received")
			self.server.delete_value_in_store(key)


	# Vessel POST Logic (Task 1 - propagate version)
	def do_POST_entries_vessel(self, action, key, value, propagate):
		if action == "ADD" : # Entry added by another server
			print("Adding entry")
			key = self.server.add_value_to_store(value) 
		elif action == "MOD" :
			print("Modifying entry")
			self.server.modify_value_in_store(key,value) 
		elif action == "DEL" :
			print("Deleting entry")
			self.server.delete_value_in_store(key)
		# If we want to propagate the request to other vessels
		if propagate:
			# do_POST send the message only when the function finishes
			# We must then create threads if we want to do some heavy computation
			thread = Thread(target=self.server.propagate_value_to_vessels,args=("/entries", action, key, value) )
			# We kill the process if we kill the server
			thread.daemon = True
			# We start the thread
			thread.start() 

	def do_POST_election(self, parsed):
		# POST ELECTION LOGIC
		if self.path=="/election" and "action" in parsed and parsed['action'][0] == "ELE" and str(parsed['key'][0])!=str(self.server.vessel_id):
			print("Data request received, forwarding.")
			data_gathering=ast.literal_eval(parsed['value'][0])#  Convert a string to a dictionnary
			data_gathering[self.server.vessel_id]=self.server.random#int(float(self.server.random))
			
			thread = Thread(target=self.server.contact_vessel,args=("10.1.0."+str(self.server.neighbor_id),"/election","ELE",parsed['key'][0],data_gathering ))
			thread.daemon = True
			thread.start()
			self.set_HTTP_headers(200)
				
		elif self.path=="/election" and "action" in parsed and parsed['action'][0] == "ELE" and str(parsed['key'][0])==str(self.server.vessel_id):
			print( "[DONE]Completed gathering data turn.")	
			thread = Thread(target=self.server.end_leader_election,args=(parsed['value'][0],))
			thread.daemon = True
			thread.start()
			
			self.set_HTTP_headers(200)

		elif self.path=="/election" and "action" in parsed and parsed['action'][0] == "COO" and str(parsed['key'][0])!=str(self.server.vessel_id):
			if self.server.leader_id==-1:
				print "Error, not ready to choose a leader"
				self.set_HTTP_headers(200)
			elif str(self.server.leader_id)!=parsed['value'][0] :
				print "Error while choosing the leader"
				print self.server.leader_id 
				print parsed['value'][0] 
				self.set_HTTP_headers(400)
			else :
				print('OK')
				self.set_HTTP_headers(200)
		
			thread = Thread(target=self.server.contact_vessel,args=("10.1.0."+str(self.server.neighbor_id),"/election","COO",parsed['key'][0],parsed['value'][0] ))
			thread.daemon = True
			thread.start()

		elif self.path=="/election" and "action" in parsed and parsed['action'][0] == "COO" and str(parsed['key'][0])==str(self.server.vessel_id):
			print("[DONE]End of Leader Election: LEADER",self.server.leader_id)
			self.set_HTTP_headers(200)
		else:
			self.set_HTTP_headers(200)

	# Extracting parameters from the parsed structure
	def get_entries_parameters(self, params):
		action, key, value, propagate = "",-1,"",True

		if "action" in params: # Propagate cases
			propagate = False
			action = params['action'][0]
			key = int(params['key'][0]) if "key" in params else ""
			value = params['value'][0] if "value" in params else ""
		else: # Self cases
			key = int(self.path.replace("/entries/","")) if "/entries/" in self.path else -1
			value = params['entry'][0] if "entry" in params else ""
			if "delete" in params and params['delete'][0]=='1':
				action = "DEL"
			elif "delete" in params and params['delete'][0]=='0':
				action = "MOD"
			else:
				action = "ADD"

		return action, key, value, propagate


	# Test the parameters to see if they are valid (No incorrect values or incorrect combinations)
	def are_parameters_valid(self, action, key, value):
		if action=="ADD" and value!="":
			return True
		elif action == "DEL" and key!=-1:
			return True
		elif action in ["MOD","SET"] and key!=-1 and value!="":
			return True
		else:
			return False

#------------------------------------------------------------------------------------------------------





#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Execute the code
if __name__ == '__main__':

	## read the templates from the corresponding html files

	vessel_list = []
	vessel_id = 0
	# Checking the arguments
	if len(sys.argv) != 3: # 2 args, the script and the vessel name
		print("Arguments: vessel_ID number_of_vessels")
	else:
		# We need to know the vessel IP
		vessel_id = int(sys.argv[1])
		# We need to write the other vessels IP, based on the knowledge of their number
		for i in range(1, int(sys.argv[2])+1):
			vessel_list.append("10.1.0.%d" % i) # We can add ourselves, we have a test in the propagation

	# We launch a server
	server = BlackboardServer(('', PORT_NUMBER), BlackboardRequestHandler, vessel_id, vessel_list)
	print("Starting the server on port %d" % PORT_NUMBER)

	try:
		server.serve_forever()
	except KeyboardInterrupt:
		server.server_close()
		print("Stopping Server")
#------------------------------------------------------------------------------------------------------
