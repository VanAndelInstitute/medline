#!/usr/bin/python

from redis import ResponseError
from redisearch import Client, TextField, NumericField
import sys
import re
from datetime import datetime
import json
import logging
from random import randint
from time import sleep

#stagger reading and indexing for parallel
sleep(randint(1, 10))

logging.basicConfig(filename='parse.log',level=logging.INFO)

client = Client('medline')

try:
        client.create_index([TextField('abstract')])

except ResponseError:
        pass

with open(sys.argv[1], 'r') as f:
        data=f.read()

recs = data.split("<PubmedArticle>");
recs = recs[1:]

indexer = client.batch_indexer(chunk_size=500)

count = 0

for r in recs:
        pmid = re.findall('<PMID Version="[12]">(.*?)</PMID>', r)
        if pmid:
                pmid = pmid[0]
        else:
                logging.error(datetime.now().isoformat() + " no pmid found for a record in  " + sys.argv[1])
                continue

        count = count+1
        
        title = re.findall('<ArticleTitle>(.*?)</ArticleTitle>', r)
        if title:
                title = title[0]
        else:
                title = ""
                
        abstract = re.findall('<Abstract>([\s\S]*?)</Abstract>', r)
        if abstract:
                abstract = re.sub("\n\s*", "", abstract[0])
                abstract = re.sub('<AbstractText Label="(.*?)".*?>', " \\1: ", abstract)
                abstract = re.sub("<\/*Abstract.*?>", "", abstract)
                abstract = re.sub("<Copyright.*?>.*</Copyright.*?>", "", abstract)
                abstract = re.sub("\(PsycINFO Database Record", "", abstract)
        else:
                abstract = ""

        # type is ignored for now, but for future reference...
        type = re.findall("<PublicationType UI=.*?>(.*?)</PublicationType>", r)
        if type:
                type = str(type)
        else:
                type = str([])
                
        indexer.add_document(pmid, replace=True, abstract=abstract, title=title, type=type)

# flush any remaining documents
indexer.commit()        

docs = client.info()['num_docs']

logging.info(datetime.now().isoformat() + " imported " + str(count) + " records from " + sys.argv[1] + "(" + docs + " total)")
