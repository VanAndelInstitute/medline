# medline

The pubmed/medline database contains a wealth of information ripe for analysis by 
natural language and/or machine learning tools to infer new relationships between 
diseases, molecules, and chemicals.  However, accessing this data via the ncbi 
e-utils requires throttling queries to about 3 per second (although queries can 
be batched to some extent).

A local instance of the database allows higher throughput for data mining.  
Furthermore, use of an in-memory database allows for very efficient querying and 
data extraction. 

Here we use the redissearch module available from RedisLabs to index the medline 
data.

## Pre-requisites

### Hardware

You will need a server with at least 30GB of RAM, and about 250GB of disk space. 
On AWS, the r4.2xlarge instance is a good bet, and is available for $0.10 - $0.20 per 
hour as a spot instance.  Your server should also have Python available, and 
a recent version of redis.  (In fact, the RediSearch docs suggest the latest, 
unstable version of redis: https://github.com/antirez/redis/archive/unstable.tar.gz)

It is a good idea to download the data to a separate volume that will not 
disappear when your spot instance terminates.  You will, of course, need to keep 
paying for that storage but that only runs a few dollars per month.

By storing your data and index (see below) on a separate volume, you can stop 
and start your server at will, thereby minimizing costs.

### RediSearch

You will need to build and install the latest version of the RediSearch module:
```
git clone https://github.com/RedisLabsModules/RediSearch.git
cd RediSearch/src
make all
```
You may wish to move the resulting `redisearch.so` to somewhere memorable.  If you 
have root access, `/var/lib/redis/redisearch.so` would be a good spot.  Then, 
you need to tell redis to load it by editing your `redis.conf` file.  This file 
typically resides in /etc/redis, or you can have your own local redis.conf.  Add the 
following line to your redis.conf:

```
loadmodule /var/lib/redis/redisearch.so
```
Also, if you created a separate volume to hold your data and you are using spot 
instances, it is a good idea to keep the index there as well so you can quickly 
restart in case your spot instance is terminated.  Adjust this line in `redis.conf` 
accordingly

```
dir /mnt/your/ebs/volume
```

Then restart your redis server:

```
/etc/init.d/redis restart
```
### RediSearch Python module


To allow redisearch to play nicely with python requires the module:
```
pip install redisearch
```

Make sure everything is right by trying a few of the examples via `redis-cli` as 
shown here: http://redisearch.io/Quick_Start/#building

### Medline data files

You will need the Medline data files.  Here we fetch the annual baseline files by
first fetching a list of the files we need and then downloading those files:

```
# fetch the file list (not all the files in this directory are the xml files)
ROOT=ftp.ncbi.nlm.nih.gov/pubmed/baseline
wget $ROOT
grep -o '>pubmed.*gz' baseline | uniq |  grep -o pubmed.* | \
    xargs -n1 -I% echo $ROOT/% > filelist

# fetch files 
wget -i filelist
```

And then we add the update files that add documents indexed since the last annual 
baseline:

```
# fetch the file list (not all the files in this directory are the xml files)
ROOT=ftp.ncbi.nlm.nih.gov/pubmed/updatefiles
wget $ROOT
grep -o '>pubmed.*gz' updatefiles | uniq |  grep -o pubmed.* | \
    xargs -n1 -I% echo $ROOT/% > filelist

# fetch files 
wget -i filelist

```
And finally decompress everything

```
gunzip *.gz
```

## Indexing the files

Indexing the medline XML files is achieved with the parse_redis.py script in this repository.
The slowest part is reading the data from disk, so moderating multi-threading speeds 
things up.  You can use `xargs` to spawn multiple jobs, each processing a different XML 
file.  Adjust the number of cores (the `P` argument below) to something less than
the number of cores available on your server.  Note that the multithreading gains seem to 
max out around 10 cores, since redis itself is single threaded. 

```
ls *.xml | xargs -n1 -P4 parse_redis.py 
```
This takes a while (likely 24-36 hours) to complete.  You can monitor progress by looking at 
the log file.  For example,

```
tail parse.log
```

## Querying

Sample queries will be added here soon.  



```





