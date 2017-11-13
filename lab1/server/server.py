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
from urlparse import parse_qs # Parse POST data
from httplib import HTTPConnection # Create a HTTP connection, as a client (for POST requests to the other vessels)
from urllib import urlencode # Encode POST content into the HTTP header
from codecs import open # Open a file
from threading import  Thread # Thread Management
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
		self.vessel_id = vessel_id
		# The list of other vessels
		self.vessels = vessel_list
#------------------------------------------------------------------------------------------------------
	# We add a value received to the store
	def add_value_to_store(self, value):
		self.current_key += 1
		self.store[self.current_key] = value

#------------------------------------------------------------------------------------------------------
	# We modify a value received in the store
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
		pass
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
		# We iterate through the vessel list
		for vessel in self.vessels:
			# We should not send it to our own IP, or we would create an infinite loop of updates
			if vessel != ("10.1.0.%s" % self.vessel_id):
				# A good practice would be to try again if the request failed
				# Here, we do it only once
				self.contact_vessel(vessel, path, action, key, value)		
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
		# We should do some real HTML here
		# html_response = "<html><head><title>Basic Skeleton</title></head><body>This is the basic HTML content when receiving a GET</body></html>"
		#In practice, go over the entries list, 
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
		board = boardcontents_template % ("Sample board @ 10.0.1."+str(self.server.vessel_id) + ".",entries)
		return board


#------------------------------------------------------------------------------------------------------
	# we might want some other functions
#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Request handling - POST
#------------------------------------------------------------------------------------------------------
	def do_POST(self):
		print("Receiving a POST on %s" % self.path)
		# Here, we should check which path was requested and call the right logic based on it
		# We should also parse the data received
		# and set the headers for the client

		retransmit = False # Like this, we won't create infinite loops!
		# Var initialization for propagation
		action = ""
		key = -1
		value = ""

		parsed = self.parse_POST_request() # Parsing data
		print(parsed)

		# Self cases
		if self.path == "/entries" and "entry" in parsed: # Adding entry from this server
			retransmit = True # Propagate
			action = "ADD"
			value = parsed['entry'][0]
			self.server.add_value_to_store(value) # Adding entry to server
			self.set_HTTP_headers(200)
		elif "/entries" in self.path and "entry" in parsed and "delete" in parsed and parsed['delete'][0]=='0':
			retransmit = True
			action = "MOD"
			value = parsed['entry'][0]
			key = int(self.path.replace("/entries/",""))
			self.server.modify_value_in_store(key,value)
			self.set_HTTP_headers(200)
		elif "/entries" in self.path and "delete" in parsed and parsed['delete'][0]=='1':
			retransmit = True
			action = "DEL"
			key = int(self.path.replace("/entries/",""))
			self.server.delete_value_in_store(key)
			self.set_HTTP_headers(200)

		# Propagate cases
		elif self.path == "/entries" and "action" in parsed and "value" in parsed and parsed['action'][0] == "ADD" : # Entry added by another server
			print("Adding entry")
			self.server.add_value_to_store(parsed['value'][0]) 
			self.set_HTTP_headers(200)
		elif self.path == "/entries" and "action" in parsed and "key" in parsed and "value" in parsed and parsed['action'][0] == "MOD" :
			print("Modifying entry")
			key = int(parsed['key'][0])
			self.server.modify_value_in_store(key,parsed['value'][0]) 
			self.set_HTTP_headers(200)
		elif self.path == "/entries" and "action" in parsed and "key" in parsed and parsed['action'][0] == "DEL" :
			print("Deleting entry")
			key = int(parsed['key'][0])
			self.server.delete_value_in_store(key) 
			self.set_HTTP_headers(200)
		else:
			self.set_HTTP_headers(400)
		
		# If we want to retransmit what we received to the other vessels
		
		if retransmit:
			# do_POST send the message only when the function finishes
			# We must then create threads if we want to do some heavy computation
			# 
			# Random content
			thread = Thread(target=self.server.propagate_value_to_vessels,args=("/entries", action, key, value) )
			# We kill the process if we kill the server
			thread.daemon = True
			# We start the thread
			thread.start()
#------------------------------------------------------------------------------------------------------
# POST Logic
#------------------------------------------------------------------------------------------------------
	# We might want some functions here as well
#------------------------------------------------------------------------------------------------------





#------------------------------------------------------------------------------------------------------
#------------------------------------------------------------------------------------------------------
# Execute the code
if __name__ == '__main__':

	## read the templates from the corresponding html files
	# .....

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
