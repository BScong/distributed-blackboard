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
template = open(script_dir + "/../lab4-html/vote_frontpage_template.html").read()
result_template = open(script_dir + "/../lab4-html/vote_result_template.html").read()

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
		# our own ID (IP is 10.1.0.ID)
		self.vessel_id = vessel_id #"10.1.0."+vessel_id
		# The list of other vessels
		self.vessels = vessel_list

		# votes
		self.votes = ["unknown" for i in range(len(self.vessels))]
		self.count_votes = 0

		# vectors
		self.vectors_votes = [[] for i in range(len(self.vessels))]
		self.count_vectors = 0

		self.results_vector = []

		#state of the general
		self.honest=False
		#action chosen
		self.action=""

		#byzantine parameters
		self.no_loyal=3
		self.no_total=4
		self.on_tie=True

		self.result = ""
		
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

	def propagate_byzantine_action(self, path, action, key, value):
		retry_list = [] # we will store the vessels without success
		# We iterate through the vessel list
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				#print(int(vessel[7:])-1)
				success = self.contact_vessel(vessel, path, action, key, value[int(vessel[7:])-1])
				if not success:
					retry_list.append(vessel)

		# for the vessels who failed, we retry
		try_count = 0
		while len(retry_list)>0 and try_count < 15:
			try_count += 1
			for vessel in retry_list:
				success = self.contact_vessel(vessel, path, action, key, value[int(vessel[7:])-1])
				if success : retry_list.remove(vessel)
		if len(retry_list)>0:
			print("Problem occured with " + ", ".join(retry_list) + " : Unable to connect after multiple attempts.")

	def reset_votes(self):
		# votes
		self.votes = ["unknown" for i in range(len(self.vessels))]
		self.count_votes = 0

		# vectors
		self.vectors_votes = [[] for i in range(len(self.vessels))]
		self.count_vectors = 0

		self.results_vector = []

		#action chosen
		self.action=""

		self.result = ""
		
#------------------------------------------------------------------------------------------------------
	#Compute byzantine votes for round 1, by trying to create
	#a split decision.
	#input: 
	#	number of loyal nodes,
	#	number of total nodes,
	#	Decision on a tie: True or False 
	#output:
	#	A list with votes to send to the loyal nodes
	#	in the form [True,False,True,.....]
	def compute_byzantine_vote_round1(self, no_loyal,no_total,on_tie):

	  result_vote = []
	  for i in range(0,no_total):
	    if i%2==0:
	      result_vote.append(not on_tie)
	    else:
	      result_vote.append(on_tie)
	  print("Round 1 byz : " + str(result_vote))
	  return result_vote

	#Compute byzantine votes for round 2, trying to swing the decision
	#on different directions for different nodes.
	#input: 
	#	number of loyal nodes,
	#	number of total nodes,
	#	Decision on a tie: True or False
	#output:
	#	A list where every element is a the vector that the 
	#	byzantine node will send to every one of the loyal ones
	#	in the form [[True,...],[False,...],...]
	def compute_byzantine_vote_round2(self, no_loyal,no_total,on_tie):
	  
	  result_vectors=[]
	  for i in range(0,no_total):
	    if i%2==0:
	      result_vectors.append([on_tie]*no_total)
	    else:
	      result_vectors.append([not on_tie]*no_total)
	  return result_vectors

	#convert True/False values to attack/retreat
	def convert_result_vote_round1 (self, result_vote):
		convert_result=result_vote[:]
		for i in range(len(result_vote)):
			if result_vote[i]==True:
				convert_result[i]="attack"
			else:
				convert_result[i]="retreat"
		return convert_result

	def convert_result_vote_round2 (self, result_vote):
		convert_result=result_vote[:]
		for i in range(len(result_vote)):
			for j in range(len(result_vote[i])):
				if result_vote[i][j]==True:
					convert_result[i][j]="attack"
				else:
					convert_result[i][j]="retreat"
		return convert_result

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
		#print("Receiving a GET on path %s" % self.path)
		# Here, we should check which path was requested and call the right logic based on it
		if self.path == "/vote/result":
			self.do_GET_Result()
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

		html_response = template
		
		self.wfile.write(html_response)

	def do_GET_Result(self):
		# We set the response status code to 200 (OK)
		self.set_HTTP_headers(200)



		# We send back the entries
		self.wfile.write(self.get_results())

	def get_results(self):
		if self.server.result == "":
			return result_template%("No results yet.")
		else:
			return result_template%(self.server.result)



#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
		print("Receiving a POST on %s" % self.path)

		parsed = self.parse_POST_request() # Parsing data
		print(parsed)

		# Check if the path is correct
		valid_path_vote = True if "/vote/attack" == self.path\
		or "/vote/retreat" == self.path\
		or "/vote/byzantine" == self.path else False

		if self.path=="/reset":
			self.server.reset_votes()
		
		if valid_path_vote and "/vote/byzantine" not in self.path :
			self.set_HTTP_headers(200)
			self.server.honest=True
			self.do_POST_vote_honest_round1(self.path[6:])
		elif valid_path_vote:
			self.set_HTTP_headers(200)
			self.server.honest=False
			self.do_POST_vote_byzantine_round1(self.path[6:])
		elif self.path=="/vote/round1":
			self.set_HTTP_headers(200)
			self.do_POST_vote_round2(parsed)
		elif self.path=="/vote/round2":
			self.set_HTTP_headers(200)
			self.do_POST_vote_end_round2(parsed)
		else:
			self.set_HTTP_headers(400)
#------------------------------------------------------------------------------------------------------
# POST Logic
#------------------------------------------------------------------------------------------------------
	def do_POST_vote_honest_round1(self, value):
		print("Honest")
		#Set the value of the vote as an action
		self.server.action=value

		self.server.count_votes+=1
		self.server.votes[self.server.vessel_id-1]=value

		#Propagation the chosen action
		#self.server.propagate_value_to_vessels("/vote/round1", "", self.server.vessel_id, str(self.server.action))
		thread = Thread(target=self.server.propagate_value_to_vessels,args=("/vote/round1", "", self.server.vessel_id, str(self.server.action)) )
		# We kill the process if we kill the server
		thread.daemon = True
		# We start the thread
		thread.start()

		if self.server.count_votes==len(self.server.vessels):
			self.begin_round2()


	def do_POST_vote_byzantine_round1(self,value):
		#Set the value of the vote as an action
		byzantine_action=self.server.compute_byzantine_vote_round1(self.server.no_loyal,self.server.no_total,self.server.on_tie)
		byzantine_action=self.server.convert_result_vote_round1 (byzantine_action)
		self.server.votes[self.server.vessel_id-1]=byzantine_action[self.server.vessel_id-1]
		self.server.count_votes+=1

		#Propagation of different value to each node
		#self.server.propagate_byzantine_action("/vote/round1", "", self.server.vessel_id, byzantine_action)
		thread = Thread(target=self.server.propagate_byzantine_action,args=("/vote/round1", "", self.server.vessel_id, byzantine_action) )
		# We kill the process if we kill the server
		thread.daemon = True
		# We start the thread
		thread.start()

		if self.server.count_votes==len(self.server.vessels):
			self.begin_round2()

	def do_POST_vote_round2(self, parsed):
		action, key, value = self.get_entries_parameters(parsed)
		self.server.votes[key-1]=value
		self.server.count_votes+=1

		if self.server.count_votes==len(self.server.vessels):
			self.begin_round2()

	def begin_round2(self):
		if not self.server.honest:
			value = self.server.compute_byzantine_vote_round2(self.server.no_loyal,self.server.no_total,self.server.on_tie)
			value = self.server.convert_result_vote_round2 (value)
			self.server.vectors_votes[self.server.vessel_id-1]=value[self.server.vessel_id-1]
			self.server.count_vectors+=1


			#propagate_byzantine_action("/vote/round2","",self.server.vessel_id,value)
			thread = Thread(target=self.server.propagate_byzantine_action,args=("/vote/round2","",self.server.vessel_id,value) )
			# We kill the process if we kill the server
			thread.daemon = True
			# We start the thread
			thread.start()
		else:
			self.server.vectors_votes[self.server.vessel_id-1]=self.server.votes
			self.server.count_vectors+=1
			# propagate
			thread = Thread(target=self.server.propagate_value_to_vessels,args=("/vote/round2", "", self.server.vessel_id, self.server.votes) )
			# We kill the process if we kill the server
			thread.daemon = True
			# We start the thread
			thread.start()

		if self.server.count_vectors == len(self.server.vessels):
			self.end_vote()

	def do_POST_vote_end_round2(self,parsed):
		action, key, value = self.get_entries_parameters(parsed)
		self.server.vectors_votes[key-1]=value
		self.server.count_vectors += 1
		print(self.server.count_vectors)
		if self.server.count_vectors == len(self.server.vessels):
			self.end_vote()

	def end_vote(self):
		print("End")
		result_vector = ['' for i in range(len(self.server.vessels))]

		# Fill a results vector
		for i in range(len(self.server.vectors_votes)):
			print(self.server.vectors_votes[i])
			self.server.vectors_votes[i]=ast.literal_eval(str(self.server.vectors_votes[i]))
			
		for i in range(len(self.server.vessels)):
			count = {"attack":0,"retreat":0,"unknown":0}
			#print(self.server.vectors_votes)
			#print(len(self.server.vectors_votes))
			for vect in self.server.vectors_votes:
				#print(vect)
				#print(vect[i])
				#print(type(vect[i]))
				if vect[i]=="attack" or vect[i]=="retreat":
					count[vect[i]]+=1
				else:
					count["unknown"]+=1
			result_vector[i] = self.compute_vote(count)

			

		self.server.results_vector = result_vector
		print(self.server.results_vector)
		# compute result from the result_vector
		count = {"attack":0,"retreat":0,"unknown":0}
		for el in self.server.results_vector:
			count[el]+=1
		self.server.result = self.compute_vote(count)
		print(self.server.result)

	def compute_vote(self, count):
		result = ""
		if count["attack"]>count["retreat"] and count["attack"]>count["unknown"]:
			result="attack"
		elif count["retreat"]>count["attack"] and count["retreat"]>count["unknown"]:
			result="retreat"
		elif count["retreat"]>count["unknown"] and count["retreat"]==count["attack"]:
			# ON TIE WE ATTACK
			result="attack"
		else:
			result="unknown"
		return result

	# Extracting parameters from the parsed structure
	def get_entries_parameters(self, params):
		action, key, value = "",-1,""
		key = int(params['key'][0]) if "key" in params else ""
		value = params['value'][0] if "value" in params else ""

		return action, key, value

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
