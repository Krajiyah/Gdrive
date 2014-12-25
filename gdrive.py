import colorama, hashlib, os, datetime
from colorama import Fore, Back, Style

class DirectoryTree:

	def __init__(self, name, file_type, file_size, modified, inp_path, inp_branches=[]):
		self.entry = name
		self.size = file_size
		self.date_modified = modified
		self.type_file = file_type
		self.branches = inp_branches
		self.md5_val = None
		self.path = inp_path

	def displayTree(self, tab):

		colorama.init()

		if(len(self.entry) > 20):
			print(tab + Fore.RED + "(" + self.index + ") " + Fore.GREEN + "[" + self.type_file + "] " + \
				Fore.CYAN + "#" + str(self.md5) + "# " + \
				Fore.BLUE + "~" + self.size + "~ " + Fore.YELLOW + "@" + str(self.date_modified) + "@ " + \
				Style.RESET_ALL + self.entry[:30] + "...");
		else:
			print(tab + Fore.RED + "(" + self.index + ") " + Fore.GREEN + "[" + self.type_file + "] " + \
				Fore.CYAN + "#" + str(self.md5) + "# " + \
				Fore.BLUE + "~" + self.size + "~ " + Fore.YELLOW + "@" + str(self.date_modified) + "@ " + \
				Style.RESET_ALL + self.entry);
		
		tab = "----" + tab;
		for branch in self.branches:
			DirectoryTree.displayTree(branch, tab)

	def setIndeces(self, rootentry, prev_index, curr_index):
		if(self.entry == rootentry):
			self.index = "1"
		else:
			self.index = prev_index + "." + str(curr_index)
		
		i = 1
		for branch in self.branches:
			DirectoryTree.setIndeces(branch, rootentry, self.index, i)
			i += 1

#local directory tree
class LTree(DirectoryTree):
		
	@property       
	def md5(self):
		if self.md5_val == None and self.type_file == "file":
			
			p = self.path
			p = p.split("/")
			for i in range(len(p)):
				if(len(p[i]) > 0 and p[i][0] == "'" and p[i][len(p[i])-1] == "'"):
					p[i] = p[i][1:len(p[i])-1] 
			p = '/'.join(p)
			self.md5_val = hashlib.md5(open(p, 'rb').read()).hexdigest()
			return self.md5_val
		elif self.type_file == "folder":
			return None
		else:
			return self.md5_val

#google drive tree
class GTree(DirectoryTree):

	@property       
	def md5(self):
		return self.md5_val

	def writeInfo(self):
		for key in info:
			if info[key][0] == self.entry:
				self.ID = key
				self.ParentID = info[key][3]
				if(self.type_file == "file"):
					self.md5_val = info[key][4]
				else:
					self.md5_val = None
		for branch in self.branches:
			GTree.writeInfo(branch)

#URL to gdrive command (GitHub Repository): https://github.com/prasmussen/gdrive
#I made an alias to gdrive as drive
def list_command():
	return "drive list"
def info_command(idtag):
	return "drive info -i " + idtag
def file_type_command(name):
	return "file " + name
def file_contents_command(name):
	return "ls " + name
def delete_file_command(name):
	return "rm " + name
def file_download_command(md5):
	for key in info:
		if info[key][4] == md5:
			return "drive download -i " + key
	raise Exception("MD5 SIG DOES NOT EXIST: ",  md5)
def file_remote_delete_command(md5):
	for key in info:
		if info[key][4] == md5:
			return "drive delete -i " + key
	raise Exception("MD5 SIG DOES NOT EXIST: ",  md5)
def file_local_delete_command(filepath):
	return "rm -r " + filepath
def file_upload_command(filepath, parentID):
	return "drive upload -p " + parentID + " -f " + filepath
def create_local_folder(filepath):
	return "mkdir " + filepath
def create_remote_folder(name, parentID):
	return "drive folder -p " + parentID + " -t " + name


#special bash function for dictionaries
def bash_dict(command):
	result = os.popen(command).readlines()
	i = 0
	while i < len(result):
		result[i] = result[i].replace("\n", "")
		result[i] = result[i].replace(" ", "*")
		c = 0
		while(c < len(result[i])):
			if(c == len(result[i]) - 1):
				None
			elif(result[i][c] == "*" and result[i][c+1] != "*" and result[i][c-1] != "*"):
				result[i] = result[i][:c] + " " + result[i][c+1:]
			c+=1
		i += 1
	return result

#bash function for all other commands
def bash(command):
	result = os.popen(command).readlines()
	i = 0
	while i < len(result):
		result[i] = result[i].replace("\n", "")
		i += 1
	return result 

def buildGTree(rootid, prevpath):
	
	dt = None

	if(rootid in info):
		dt = info[rootid][2]
	else:
		dt = bash_dict(info_command(rootid))[4]
		dt = dt.replace("Modified: ", "")

	dt = datetime.datetime.strptime(dt, "%Y-%m-%d %H:%M:%S")

	if(rootid not in info):
		name = "My Drive"
		path = "/home/krishnan/My Drive"
	else:
		name = info[rootid][0]
		path = prevpath + "/" + name

	if(rootid not in info or info[rootid][1] == "0 B"):
		children = []
		for idtag in info:
			if rootid == info[idtag][3]:
				children.append(idtag)
		if(len(children) == 0):
			return GTree(name, "folder", "0 B", dt, path)
		else:
			b = [buildGTree(child, path) for child in children]
			return GTree(name, "folder", "0 B", dt, path, b)
	else:
		return GTree(name, "file", info[rootid][1], dt, path)

def buildLTree(name):
	children = bash(file_contents_command(name))
	i = 0
	while i < len(children):            
		if " " in children[i] or "(" in children[i] or ")" in children[i]:
			children[i] = name + "/'" + children[i] + "'"           
		else:
			children[i] = name + "/" + children[i]
		i += 1

	entry_name = name.split("/")[-1]
	if " " in entry_name or "(" in entry_name or ")" in entry_name:
		entry_name = entry_name[1:len(entry_name)-1]

	n = name.replace("~", "/home/krishnan")
	path = n
	n = n.split("/")
	k = 0
	while k < len(n):
		if " " in n[k] or "(" in n[k] or ")" in n[k]:
			n[k] = n[k][1:len(n[k])-1]
		k += 1
	n = '/'.join(n)
	
	dt = os.path.getmtime(n)
	dt = datetime.datetime.fromtimestamp(dt)
	dt = dt.replace(microsecond=0)

	if("directory" not in bash(file_type_command(name))[0]):
		nam = name.replace("~", "/home/krishnan")
		nam = nam.split("/")
		k = 0
		while k < len(nam):
			if " " in nam[k] or "(" in nam[k] or ")" in nam[k]:
				nam[k] = nam[k][1:len(nam[k])-1]
			k += 1
		nam = '/'.join(nam)
		size = os.path.getsize(nam)
		units = ["B", "KB", "MB", "GB"]
		curr_unit = 0
		while(size >= 1000):
			curr_unit += 1
			size = size / 1000
		if "." in str(size):
			r = int(str(size).split(".")[1][0])
			if(r >= 5):
				size = int(size + 1)
			else:
				size = int(size)
		size = str(size) + " " + units[curr_unit]
		return LTree(entry_name, "file", size, dt, path)
	elif(len(children) == 0):
		return LTree(entry_name, "folder", "0 B", dt, path)
	else:
		b = [buildLTree(childname) for childname in children]
		return LTree(entry_name, "folder", "0 B", dt, path, b)

remote_tree = None
local_tree = None
info = None
rootid = None

def construct():
	global remote_tree, local_tree, info, rootid
	print("")
	
	info = {}
	input_list = bash_dict(list_command())[1:]
	for line in input_list:
		not_trimmed_vals = line.split("*")
		vals = []
		for val in not_trimmed_vals:
			if val != '':
				vals.append(val)
		info_key = bash_dict(info_command(vals[0]))
		parentID = info_key[-1]
		parentID = parentID.replace("Parents: ", "")
		dt = info_key[4]
		dt = dt.replace("Modified: ", "")
		md5 = info_key[6]
		md5 = md5.replace("Md5sum: ", "")
		info[vals[0]] = [vals[1], vals[2], dt, parentID, md5]
		#Key: Value for INFO dictionary
		#ID: [Title, Size, DateMod, ParentID, md5]

	i = 0;
	rootid = "";
	for key in info:
		if(info[key][1] == "0 B"):
			parent = info[key][3]
			if parent not in info: 
				rootid = parent
		i += 1

	print("******************Contructing GTree******************")
	print("")

	remote_tree = buildGTree(rootid, "")
	remote_tree.setIndeces("My Drive", "", 1)
	remote_tree.writeInfo()
	remote_tree.displayTree(">")
	print("")

	print("******************Contructing LTree******************")
	print("")

	local_tree = buildLTree("~/'My Drive'")
	local_tree.setIndeces("My Drive", "", 1)
	local_tree.displayTree(">")
	print("")

def sync(local, remote):
	"""
	(I have set folder checksums to be lists containing checksums of its children,
	only files have md5 checksum strings instead of lists)

	Go through whole local tree and compare each node to all remote nodes 
	according to these rules:

		if the local file and a remote file have same md5 sum
		and one of those files is closer to today's date,
			if the one file is local,
				then delete remote file and upload local file.
			else
				then delete local file and download remote file.
		
		if the local folder and a remote folder have same checksum
		and one of those folders is closer to today's date,
			if the one folder is local,
				then ....
			else
				then ....

		else the local file/folder does not match any remote file/folder checksum,
			then ....

	Go through whole remote tree and compare each node to all local nodes 
	according to these rules:

		if the remote file/folder does not match any local file/folder checksum,
			then ....
	"""
	pass