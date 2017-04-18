# Elastic Deduplicator

Have you ever had duplicate documents in Elastic Search but didn't want delete an entire index and repopulate the data just to get rid of the duplicates? Look no further.

## How it Works

Deduplicator works by finding documents that share a value for a field in their \_source. It's recommended that the field used is numeric, not a string. Using a field that contains text might require extra Elastic Search configuration. [See this article on field data in Elastic Search for more details.](https://www.elastic.co/guide/en/elasticsearch/reference/current/fielddata.html)

If more than one document shares the same field ([specified in configuration-example.json](configuration-example.json)), n-1 documents are deleted where "n" equals all instances of the document. Thus, one document is left over.

Deduplicator uses SSH to execute curl commands on a remote host running an Elastic Search instance. You can specify multiple hosts and ES indicies.

## Exit Codes
0: No duplicates were found, all commands ran successfully.
1: There was a problem executing a command. Duplicates may have been found and deleted on one or more hosts.
2: Duplicates were found and deleted, all commands ran successfully. 

## Instructions
1. Save configuration-example.json as configuration.json and modify it to suit your environment. 
"endpoints" is an object where each key is an Elastic Search type and index, and its value is the unique key that will be used to check whether a document is a duplicate. 
If a document shares the value of the unique key with one or more documents, all documents will be deleted except for one of them.
2. Run the python script and pass configuration.json as an argument.
```
cd elastic-deduplicator
python deduplicator.py -i configuration.json
```

## Improvements
* Could be smarter about deleting a batch of documents but some versions of Elastic Search don't support \_delete\_by\_query. 
Some versions do support this functionality (or even as a plugin), but the query syntax, HTTP method, and URI can differ.