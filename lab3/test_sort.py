# Sorting algorithm to re-order store
def sort_store(store):
	store_seq_num = {}
	for key in store:
		entry = store[key]
		if entry['seq'] not in store_seq_num:
			store_seq_num[entry['seq']]=[]
		#print(entry)
		details = {'seq':entry['seq'],'node':entry['node'],'msg':entry['msg']}
		store_seq_num[entry['seq']].append(details)

	current_key = -1
	consistent_store = {}
	for key in sorted(store_seq_num.keys()):
		for entry in sorted(store_seq_num[key], key=lambda i:i['node'], reverse=True):
			current_key+=1
			consistent_store[current_key]=entry	
	#self.current_key=current_key
	#self.store = consistent_store
	return consistent_store

store={
	5:{'seq':1,'node':1,'msg':"2"},
	4:{'seq':1,'node':3,'msg':"1"},
	2:{'seq':2,'node':1,'msg':"3"},
	3:{'seq':3,'node':1,'msg':"4"},
	1:{'seq':4,'node':1,'msg':"6"},
	0:{'seq':4,'node':9,'msg':"5"}
}

print(sort_store(store))