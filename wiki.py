# -*- coding: utf-8 -*-
import xml.sax.handler
import sys,string
from collections import defaultdict
from nltk import PorterStemmer
import Stemmer
import timeit
from string import digits
import re
import itertools
from itertools import product
from string import ascii_lowercase
import math
from bisect import bisect_left
from itertools import islice
import linecache
import bz2

MAX_LIMIT=2000
K=10

Posting_List={}
TF_IDF_WT={}
DocID_Title_dict={}

StopWordFlag={}
StopWordFlag = defaultdict(lambda: 0 , StopWordFlag)
stemmer = Stemmer.Stemmer('english') 

file_pointers={}
filenames=[]

Title_dict={}
Infobox_dict={}
External_link_dict={}
Body_dict={}
Category_dict={}

dt_cnt=0

class wikiContentHandler(xml.sax.handler.ContentHandler):

	Page_flag = 0
	Page_count = 0
	def __init__(self):
		self.Text_Flag = 0	
		self.Text_data = ""	
		self.ID_flag = 0
		self.ID = -999
		self.Title_flag = 0
		self.Title_data= ""

	def startElement(self, name, attr):
		if name == "text":	
			self.Text_Flag = 1
			self.Text_data = ""	
		elif name == "id" and wikiContentHandler.Page_flag == 0:
			self.ID_flag = 1
			wikiContentHandler.Page_flag = 1
		elif name == "title":
			self.Title_flag = 1
			self.Title_data= ""	
		elif name == "page":
			Title_dict.clear()
			Infobox_dict.clear()
			External_link_dict.clear()
			Body_dict.clear()
			Category_dict.clear()

	def endElement(self, name): 
	   	if name == "text":
	   		self.Text_Flag = 0
	   		TextProcessing(self,self.Text_data)
	   	elif name == "id":
			self.ID_flag = 0
		elif name == "page":	
			wikiContentHandler.Page_flag = 0
			DocID_Title_dict[self.ID]=self.Title_data
			Make_Entry_in_index(self.ID)
			wikiContentHandler.Page_count+=1
			if wikiContentHandler.Page_count%MAX_LIMIT==0:
				write_to_file()
				# print "done"
				print "Page_count : "+str(wikiContentHandler.Page_count)
				Posting_List.clear()
				DocID_Title_dict.clear()

		if name == "title":
	   		self.Title_flag = 0
	   		TitleProcessing(self,self.Title_data)

	def characters(self, data):
		if self.Text_Flag:
			data = data.lower().encode('utf-8')
			self.Text_data+=data		
		elif self.ID_flag==1 and wikiContentHandler.Page_flag==1: 
			self.ID = wikiContentHandler.Page_count
		elif self.Title_flag ==1 :
			data = data.lower().encode('utf-8')
			self.Title_data +=data

def Make_Entry_in_index(ID):
	words=list(set(External_link_dict.keys()+Infobox_dict.keys()+Title_dict.keys()+Category_dict.keys()+Body_dict.keys()))
		
	Title_word_cnt=len(Title_dict)
	Body_word_cnt=len(Body_dict)
	Category_word_cnt=len(Category_dict)
	External_link_word_cnt=len(External_link_dict)
	Infobox_word_cnt=len(Infobox_dict)

	for word in words:
		Posting=str(ID)
		if Title_word_cnt!=0 and word in Title_dict:
			Posting+="t"+str(round((float(Title_dict[word])/float(Title_word_cnt))*100,4))
		else:
			Posting+="t"
		if Body_word_cnt!=0 and word in Body_dict:
			Posting+="b"+str(round((float(Body_dict[word])/float(Body_word_cnt))*100,4))
		else:
			Posting+="b"	
		if Category_word_cnt!=0 and word in Category_dict:
			Posting+="c"+str(round((float(Category_dict[word])/float(Category_word_cnt))*100,4))
		else:
			Posting+="c"
		if External_link_word_cnt!=0 and word in External_link_dict:
			Posting+="e"+str(round((float(External_link_dict[word])/float(External_link_word_cnt))*100,4))
		else:
			Posting+="e"
		if Infobox_word_cnt!=0 and word in Infobox_dict:
			Posting+="i"+str(round((float(Infobox_dict[word])/float(Infobox_word_cnt))*100,4))+" "
		else:
			Posting+="i"+" "
		
		if word not in Posting_List:
			Posting_List[word]=""
		# print Posting
		Posting_List[word]=Posting_List[word]+Posting

def write_to_file():
	global dt_cnt
	for key in Posting_List.iterkeys():
		op=file_pointers[key[0:2]]
		op.write(key+":"+Posting_List[key]+'\n')
		file_pointers[key[0:2]]=op
	D_T=open("./index/"+"DocID_Title"+str(dt_cnt),"w")
	for keys in DocID_Title_dict:
		D_T.write(DocID_Title_dict[keys]+"\n")
	dt_cnt+=1
	D_T.close()

def TitleProcessing(self,data):
	for word in data.split(" "):
		word=word.translate(string.maketrans(string.punctuation,' '*len(string.punctuation)))
		if word.isalpha() and word not in StopWordFlag:
			try:
				word=stemmer.stemWord(word)
				if word not in StopWordFlag:
					if word not in Title_dict:
						Title_dict[word]=1
					else:
						Title_dict[word]+=1
			except Exception:
				pass

def Info_Elink_category_Processing(self,data):
	lines = data.split('\n')
	index=0
	while index < len(lines):
		if "{{infobox" in lines[index]:
			Info_data=""
			br_cnt=0
			flag=0
			while index < len(lines):
				if '{{' in lines[index]:
					br_cnt+=lines[index].count('{{')
				if '}}' in lines[index]:
					br_cnt-=lines[index].count('}}')
				if br_cnt==0:
					break
				Info_data+=lines[index]+"\n"
				index+=1	

			Info_data = Info_data[len("{{infobox"):]
			Info_data = re.sub(u"http[^\s]+\s",' ', Info_data)
			Info_data = re.sub(u'<ref.*?>.*?</ref>|</?.*?>',' ',Info_data)
			Info_data = re.sub(u'<!--.*?-->',' ',Info_data)

			for wordList in Info_data.split("|"):
				wordList=wordList.split("=")[-1]
				wordList=wordList.translate(string.maketrans(string.punctuation,' '*len(string.punctuation)))
				for word in wordList.split(" "):
					word=word.strip()
					if word and word not in StopWordFlag and word.isalpha():
						try:
							word=stemmer.stemWord(word)
							if word not in StopWordFlag:
								if word not in Infobox_dict:
									Infobox_dict[word]=1
								else:
									Infobox_dict[word]+=1
						except Exception:
							pass
		elif '* [' in lines[index] or '*[' in lines[index]:
			lines[index] = lines[index].replace("nbsp;"," ").replace("–"," ") 	
			lines[index]=lines[index].translate(string.maketrans(string.punctuation,' '*len(string.punctuation)))			
			link_line =lines[index].replace("*","").split(" ")
			for word in link_line:
				if "http" in word:
					link=word[1:]
				if "http" not in word :
					if word and word not in StopWordFlag and word.isalpha():
						try:
							word=stemmer.stemWord(word)
							if word not in StopWordFlag:
								if word not in External_link_dict:
									External_link_dict[word]=1
								else:
									External_link_dict[word]+=1
						except Exception:
							pass

		elif "[[category:" in lines[index]: 
			for d in lines[index].split("[[category:"):
				d=d.translate(string.maketrans(string.punctuation,' '*len(string.punctuation)))
				for word in d.split(" "):
					if word and word not in StopWordFlag and word.isalpha():
						try:
							word=stemmer.stemWord(word)
							if word not in StopWordFlag:
								if word not in Category_dict:
									Category_dict[word]=1
								else:
									Category_dict[word]+=1
						except Exception:
							pass
		index+=1	

def TextProcessing(self,data):
	
	Info_Elink_category_Processing(self,data)
	data=data.translate(string.maketrans(string.punctuation,' '*len(string.punctuation)))
	for word in data.split():
		if word and word not in StopWordFlag and word.isalpha():
			try:
				word=stemmer.stemWord(word)
				if word not in StopWordFlag:
					if word not in Body_dict:
						Body_dict[word]=1
					else:
						Body_dict[word]+=1
			except Exception:
				pass
			
def stopwords():
	with open('./stopwords.txt','r') as StopWordfile:
		for line in StopWordfile:
				StopWordFlag[line.strip()]=1		

def createfiles():
	filenames = [''.join(i) for i in itertools.product(ascii_lowercase, repeat = 2)]
	for file in filenames:
		file_pointers[file]=bz2.BZ2File("./Tmpindex/"+file+".bz2","wb",compresslevel=9)

def sortFile():
	for filename in file_pointers:
	    inputfile = bz2.BZ2File("./Tmpindex/"+filename+".bz2", "r",compresslevel=9)
	    outputfile = bz2.BZ2File("./index/"+filename+".bz2", "wb",compresslevel=9)
 
	    ip_reader = inputfile.readlines()
	    
	    ip_reader.sort()
	    for row in ip_reader:
	    	outputfile.write(row.strip()+"\n")

	    inputfile.close()
	    outputfile.close()

def close_all_files():
	for filename in file_pointers:
		file_pointers[filename].close()

def prunning_files(Pages):
	for filename in file_pointers:
		new_lines=[]
		with bz2.BZ2File("./index/"+filename+".bz2","r",compresslevel=9) as Edit_file:
			line = Edit_file.readlines()
			n=len(line)
			i=0
			while i < n:
				word=line[i][0:line[i].find(":")]
				j=i+1
				postings=""
				while j < n and word == line[j][0:line[j].find(":")]:
					postings+=" "+line[j][line[j].find(":")+1:-1]
					j+=1
				new_lines.append(line[i][:-1]+postings+"\n")
				i=j

		with bz2.BZ2File("./index/"+filename+".bz2","w",compresslevel=9) as Edit_file:
			Edit_file.writelines( new_lines)
		
def Two_Level_indexing():
	primary_offset=-1
	cnt=0
	secondary_offset=-1
	file_offset=0
	file_offset_dict={}

	Offset_file=open("./index/"+"offset_file","w")
	Secondary_index=open("./index/"+"secondary_index","w")

	Primary_index=open("./index/"+"primary_index","w")
	Primary_index_Entry=[]
	Secondary_index_Entry=[]
	for filename in sorted(file_pointers.iterkeys()):
		file_offset_dict[filename]=primary_offset+1
		with bz2.BZ2File("./index/"+filename+".bz2","r",compresslevel=9) as index_file:
			line = index_file.readlines()
			n=len(line)
			for i in xrange(n):
				word=line[i][0:line[i].find(":")]
				Entry=word+":"+str(primary_offset+1)+"\n"
				Primary_index_Entry.append(Entry)
				# Primary_index.write(Entry)
				primary_offset+=len(line[i])

				if cnt%1000==0:
					Secondary_index_Entry.append(word+":"+str(secondary_offset+1)+"\n")
					# Secondary_index.write(word+":"+str(secondary_offset+1)+"\n")
				secondary_offset+=len(Entry)
				cnt+=1
		cnt=0
		if len(Primary_index_Entry)>=100000:
			for PEntry in Primary_index_Entry:
				Primary_index.write(PEntry)
			Primary_index_Entry[:]=[]

		if len(Secondary_index_Entry)>=100000:
			for SEntry in Secondary_index_Entry:
				Secondary_index.write(SEntry)
			Secondary_index_Entry[:]=[]

	if len(Primary_index_Entry) > 0:
		for PEntry in Primary_index_Entry:
			Primary_index.write(PEntry)
		Primary_index_Entry[:]=[]

	if len(Secondary_index_Entry) > 0:
		for SEntry in Secondary_index_Entry:
			Secondary_index.write(SEntry)
		Secondary_index_Entry[:]=[]

	for filename in sorted(file_pointers.iterkeys()):
		Offset_file.write(filename+":"+str(file_offset_dict[filename])+"\n")

	Offset_file.close()
	Secondary_index.close()
	Primary_index.close()

def binary_search(Arr, key, start, end):  
    pos = bisect_left(Arr, key, start, end)  
    x=Arr[pos][0:Arr[pos].find(":")]

    if pos != end and key == x :
    	return pos+1
    elif pos != end and key < x :
    	return pos
    else:
   		return -1  

def binary_search_numbers(Arr, key, start, end): 
    while (end-start)>1:
        mid = (start + end)/2
        Entry=int(Arr[mid][Arr[mid].find(":")+1:])
        if Entry <= key:
            start = mid         
        elif Entry > key:
            end = mid 
    Entry=int(Arr[end][Arr[end].find(":")+1:])
    if Entry <= key:
        return end
    Entry=int(Arr[start][Arr[start].find(":")+1:])
    if Entry <= key:
        return start
    return -1

def binary_search_exact_match(Arr,key,start,end):  
    while start <= end:
        mid = (start + end)/2
        Entry=Arr[mid][0:Arr[mid].find(":")]
        if Entry > key:
            end = mid - 1
        elif Entry < key:
            start = mid + 1
        else:
            return mid
    return -1

def Get_Top_K_Search(Doc_IDs):
	cnt=1
	for docid in Doc_IDs:
		# print docid
		fileno=docid/MAX_LIMIT
		lineno=docid%MAX_LIMIT
		title_name= linecache.getline("./index/"+"DocID_Title"+str(fileno), lineno+1)
		print str(cnt)+"] "+ title_name[:-1]
		linecache.clearcache()
		if cnt >= K:
			break
		cnt+=1


def Sort_By_Tf_Idf_for_MultiWord(D_ID,Doc_IDs,Pages):	
	TF_IDF_Wt={}
	for d_id in D_ID:
		for Entry in Doc_IDs[d_id]:
			Title_index=Entry.find("t")
			Body_index=Entry.find("b")
			Category_index=Entry.find("c")
			External_link_index=Entry.find("e")
			Infobox_index=Entry.find("i")
			Postings_size_index=Entry.find("p")

			Doc_ID=Entry[0:Title_index]
			Title_cnt=Entry[Title_index+1:Body_index]
			Body_cnt=Entry[Body_index+1:Category_index]
			Category_cnt=Entry[Category_index+1:External_link_index]
			External_link_cnt=Entry[External_link_index+1:Infobox_index]
			Infobox_cnt=Entry[Infobox_index+1:Postings_size_index]
			Postings_size=Entry[Postings_size_index+1:]
			
			if Title_cnt=="":
				Title_cnt=round(float(0),4)
			else:
				Title_cnt=round(float(Title_cnt)*float(400),4)
			
			if Body_cnt=="":
				Body_cnt=round(float(0),4)
			else:
				Body_cnt=round(float(Body_cnt)*float(100),4)

			if Category_cnt=="":
				Category_cnt=round(float(0),4)
			else:
				Category_cnt=round(float(Category_cnt)*float(200),4)

			if External_link_cnt=="":
				External_link_cnt=round(float(0),4)
			else:
				External_link_cnt=round(float(External_link_cnt)*float(200),4)

			if Infobox_cnt=="":
				Infobox_cnt=round(float(0),4)
			else:
				Infobox_cnt=round(float(Infobox_cnt)*float(200),4)

			TF=Title_cnt+Body_cnt+Category_cnt+External_link_cnt+Infobox_cnt
			IDF=round(math.log(float(Pages)/float(Postings_size),10),4)
			TF_IDF_Wt[int(Doc_ID)]=round(float(TF)*float(IDF),4)		
	
	Result=[]
	for doc_id in sorted(TF_IDF_Wt,key=TF_IDF_Wt.get,reverse=True):
		Result.append(doc_id)
	# Get_Top_K_Search(Result)
	return Result

def Word_Query_forMultiQ(Search_word):

	Primary_index=open("./index/"+"primary_index","r")
	Secondary_index=open("./index/"+"secondary_index","r")
	Index_lines=Secondary_index.readlines()
	Search_word.lower()
	index= binary_search(Index_lines,Search_word,0,len(Index_lines)-1)
	
	if index==0:
		x=int(Index_lines[index][Index_lines[index].find(":")+1:])
	else:
		x=int(Index_lines[index-1][Index_lines[index-1].find(":")+1:])
	
	Primary_index.seek(x)
	line=Primary_index.readline()
	offset=int(line[line.find(":")+1:-1])
	
	with open("./index/"+"offset_file","r") as Offset_file:
		Offset_line = Offset_file.readlines()
		addr=binary_search_numbers(Offset_line,offset,0,len(Offset_line)-1)
		offset=offset-int(Offset_line[addr][Offset_line[addr].find(":")+1:-1])
		filename=Offset_line[addr][0:Offset_line[addr].find(":")]

		main_file=bz2.BZ2File("./index/"+filename+".bz2","r",compresslevel=9)
		main_file.seek(offset)
		head = list(islice(main_file, 1000))
		addr=binary_search_exact_match(head,Search_word,0,len(head)-1)
		if addr==-1:
			return ""
		else:
			ans=head[addr]
		 	ans=ans[ans.find(":")+1:].strip().split(" ")
		 	return ans


def MultiWord_Query(Search_words,Pages):
	# Results_dict={}
	Doc_IDs={}
	for Search_word in Search_words:
		Search_word=Search_word.strip().lower()
		if Search_word not in StopWordFlag:
			try:
				Search_word=stemmer.stemWord(Search_word)
			except Exception:
				pass
			Postings=Word_Query_forMultiQ(Search_word)
			if Postings!="":
				Postings_size=len(Postings)
				for Entry in Postings:
					Title_index=Entry.find("t")
					Doc_Id=Entry[0:Title_index]
					if Doc_Id not in Doc_IDs:
						Doc_IDs[Doc_Id]=list()
					Entry+="p"+str(Postings_size)	
					Doc_IDs[Doc_Id].append(Entry)	


	Docmt_Id =list(sorted(Doc_IDs, key=lambda k: len(Doc_IDs[k]), reverse=True))
	length=len(Search_words)
	D_ID=[]
	top_cnt=0
	k_fulfilled=0
	Result_Doc=[]
	for doc_id in Docmt_Id:
		if length!=0 and len(Doc_IDs[doc_id])==length:
			D_ID.append(doc_id)
		else:
			if len(D_ID)!=0:
				Result_Doc.extend(Sort_By_Tf_Idf_for_MultiWord(D_ID,Doc_IDs,Pages))
				top_cnt+=len(D_ID)
			D_ID[:]=[]
			length-=1
		if top_cnt >= K:
			k_fulfilled=1
			break
	if len(D_ID)!=0 and k_fulfilled==0:
		Result_Doc.extend(Sort_By_Tf_Idf_for_MultiWord(D_ID,Doc_IDs,Pages))
	Get_Top_K_Search(Result_Doc)

def Sort_By_Tf_Idf_for_Word(Postings,Pages):
	dN=len(Postings)
	IDF=round(math.log(float(Pages)/float(dN),10),4)
	TF_IDF_WT={}
	for Entry in Postings:

		Title_index=Entry.find("t")
		Body_index=Entry.find("b")
		Category_index=Entry.find("c")
		External_link_index=Entry.find("e")
		Infobox_index=Entry.find("i")

		Doc_ID=Entry[0:Title_index]
		Title_cnt=Entry[Title_index+1:Body_index]
		Body_cnt=Entry[Body_index+1:Category_index]
		Category_cnt=Entry[Category_index+1:External_link_index]
		External_link_cnt=Entry[External_link_index+1:Infobox_index]
		Infobox_cnt=Entry[Infobox_index+1:]
		
		if Title_cnt=="":
			Title_cnt=round(float(0),4)
		else:
			Title_cnt=round(float(Title_cnt)*float(400),4)
		
		if Body_cnt=="":
			Body_cnt=round(float(0),4)
		else:
			Body_cnt=round(float(Body_cnt)*float(100),4)

		if Category_cnt=="":
			Category_cnt=round(float(0),4)
		else:
			Category_cnt=round(float(Category_cnt)*float(200),4)

		if External_link_cnt=="":
			External_link_cnt=round(float(0),4)
		else:
			External_link_cnt=round(float(External_link_cnt)*float(200),4)

		if Infobox_cnt=="":
			Infobox_cnt=round(float(0),4)
		else:
			Infobox_cnt=round(float(Infobox_cnt)*float(200),4)
			
		TF=Title_cnt+Body_cnt+Category_cnt+External_link_cnt+Infobox_cnt
		TF_IDF_WT[int(Doc_ID)]=round(float(TF)*float(IDF),4)		
	
	Result=[]
	for doc_id in sorted(TF_IDF_WT,key=TF_IDF_WT.get,reverse=True):
		Result.append(doc_id)
	return Result

def Word_Query(Search_word,Pages):
	Primary_index=open("./index/"+"primary_index","r")
	Secondary_index=open("./index/"+"secondary_index","r")
	Index_lines=Secondary_index.readlines()
	if Search_word not in StopWordFlag:
		try:
			Search_word=stemmer.stemWord(Search_word)
		except Exception:
			pass

		index= binary_search(Index_lines,Search_word,0,len(Index_lines)-1)
		Secondary_index.close()

		if index==0:
			x=int(Index_lines[index][Index_lines[index].find(":")+1:])
		else:
			x=int(Index_lines[index-1][Index_lines[index-1].find(":")+1:])

		Primary_index.seek(x)
		line=Primary_index.readline()
		Primary_index.close()
	
		offset=int(line[line.find(":")+1:-1])
	
		with open("./index/"+"offset_file","r") as Offset_file:
			Offset_line = Offset_file.readlines()
			addr=binary_search_numbers(Offset_line,offset,0,len(Offset_line)-1)
			offset=offset-int(Offset_line[addr][Offset_line[addr].find(":")+1:-1])
			filename=Offset_line[addr][0:Offset_line[addr].find(":")]

			main_file=bz2.BZ2File("./index/"+filename+".bz2","r",compresslevel=9)
			main_file.seek(offset)
			head = list(islice(main_file, 1000))
			addr=binary_search_exact_match(head,Search_word,0,len(head)-1)
			main_file.close()

			if addr!=-1:
				ans=head[addr]
				ans=ans[ans.find(":")+1:].strip().split(" ")
				Result=Sort_By_Tf_Idf_for_Word(ans,Pages)
				Get_Top_K_Search(Result)

def get_Field(Query_type,Entry):

	Title_index=Entry.find("t")
	Doc_ID=Entry[0:Title_index]
	# print Entry
	if Query_type=="t":
		Body_index=Entry.find("b")
		Title_cnt=Entry[Title_index+1:Body_index]
		if Title_cnt=="":
			Title_cnt=0
		else:
			Title_cnt=round(float(Title_cnt)*float(400),4)
		# print Title_cnt
		return Title_cnt
	elif Query_type=="b":
		Body_index=Entry.find("b")
		Category_index=Entry.find("c")
		Body_cnt=Entry[Body_index+1:Category_index]
		if Body_cnt=="":
			Body_cnt=0
		else:
			Body_cnt=round(float(Body_cnt)*float(100),4)
		# print Body_cnt	
		return Body_cnt
	elif Query_type=="c":
		Category_index=Entry.find("c")
		External_link_index=Entry.find("e")
		Category_cnt=Entry[Category_index+1:External_link_index]
		if Category_cnt=="":
			Category_cnt=0
		else:
			Category_cnt=round(float(Category_cnt)*float(200),4)
		# print Category_cnt	
		return Category_cnt
	elif Query_type=="e":
		External_link_index=Entry.find("e")
		Infobox_index=Entry.find("i")
		External_link_cnt=Entry[External_link_index+1:Infobox_index]
		if External_link_cnt=="":
			External_link_cnt=0
		else:
			External_link_cnt=round(float(External_link_cnt)*float(200),4)
		# print External_link_cnt
		return External_link_cnt	
	elif Query_type=="i":
		Infobox_index=Entry.find("i")
		Infobox_cnt=Entry[Infobox_index+1:]
		if Infobox_cnt=="":
			Infobox_cnt=0
		else:
			Infobox_cnt=round(float(Infobox_cnt)*float(200),4)
		return Infobox_cnt	


def Sort_By_Tf_Idf_for_FieldWord(D_ID,Doc_IDs,Pages):	
	TF_IDF_Wt={}
	for d_id in D_ID:
		TF_IDF_WT_SUM=0
		for Entry in Doc_IDs[d_id]:
			TF_IDF_WT_SUM+=Entry
		TF_IDF_Wt[int(d_id)]=TF_IDF_WT_SUM

	Result=[]
	for doc_id in sorted(TF_IDF_Wt,key=TF_IDF_Wt.get,reverse=True):
		Result.append(doc_id)
	return Result

def FieldQuery(Query,Pages):  # t:Sachin b:Tendulkar c:Sports
	Doc_IDs={}
	count_search_words=0
	for key in Query.iterkeys():
		Search_words=Query[key].split(" ")
		for Search_word in Search_words:
			Search_word=Search_word.strip().lower()
			if Search_word not in StopWordFlag:
				try:
					Search_word=stemmer.stemWord(Search_word)
				except Exception:
					pass
				Postings=Word_Query_forMultiQ(Search_word)
				if Postings!="":
					count_search_words+=1
					Postings_size=len(Postings)
					IDF=round(math.log(float(Pages)/float(Postings_size),10),4)
					for Entry in Postings:
						# print Entry
						Title_index=Entry.find("t")
						Doc_Id=Entry[0:Title_index]
						if Doc_Id not in Doc_IDs:
							Doc_IDs[Doc_Id]=list()
						TF=get_Field(key,Entry)
						# print TF
						if TF!=0.0:
							Doc_IDs[Doc_Id].append(round(float(TF)*float(IDF),4))

	# print Doc_IDs
	Docmt_Id =list(sorted(Doc_IDs, key=lambda k: len(Doc_IDs[k]), reverse=True))
	length=len(Search_words)
	D_ID=[]
	top_cnt=0
	k_fulfilled=0
	Result_Doc=[]
	for doc_id in Docmt_Id:
		if length!=0 and len(Doc_IDs[doc_id])==length :
			D_ID.append(doc_id)
		else:
			if len(D_ID)!=0:
				Result_Doc.extend(Sort_By_Tf_Idf_for_FieldWord(D_ID,Doc_IDs,Pages))
				top_cnt+=len(D_ID)
			D_ID[:]=[]
			length-=1
		if top_cnt >= K:
			k_fulfilled=1
			break
	if len(D_ID)!=0 and k_fulfilled==0:
		Result_Doc.extend(Sort_By_Tf_Idf_for_FieldWord(D_ID,Doc_IDs,Pages))
	Get_Top_K_Search(Result_Doc)

def Start_query(Pages):
	while True:
		start = timeit.default_timer()
		query=raw_input("Enter Query: ")
		start = timeit.default_timer()
		if ":" in query:
			q=query.split(":")
			st=q[0]
			qry={}
			for i in range(1,(len(q)-1)):
				t=q[i].split(" ") 
				a=""
				for z in range(0,len(t)-1):
					a+=t[z]+" "
				qry[st]=a.strip()
			 	st=t[len(t)-1]
			qry[st]=q[-1].strip()	
			# print qry
			FieldQuery(qry,Pages)
		else:
			Query_chunk=query.split(" ")
			n=len(Query_chunk)
			# print n
			if n==1:
				Word_Query(Query_chunk[0].strip().lower(),Pages)
			else:
				MultiWord_Query(Query_chunk,Pages)
		stop = timeit.default_timer()
		print stop - start			

def main():
	start = timeit.default_timer()
	stopwords()
	createfiles()

	parser = xml.sax.make_parser() 
	handler = wikiContentHandler()
	parser.setContentHandler(handler)
	parser.parse(sys.argv[1])
	if len(Posting_List)!=0:
		write_to_file()

	print "Page_count : "+str(wikiContentHandler.Page_count)
	print "done Parsing"	
	
	close_all_files()
	print "all files closed"
	
	sortFile()
	print "all files sorted"
	
	prunning_files(wikiContentHandler.Page_count)
	print "all files prunned"
	
	Two_Level_indexing()
	print "Two_Level_index ready"
	
	stop = timeit.default_timer()
	print stop - start
	
	print "Start Query Engine"
	Start_query(wikiContentHandler.Page_count)
	
	# Start_query(72337)
	
if __name__ == "__main__": 
	main()