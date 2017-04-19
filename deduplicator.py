# coding=utf-8
import sys, json, subprocess

# Helper function to pretty print a list or dictionary
def pretty_print(print_me):
    print json.dumps(print_me, indent=4, sort_keys=True)

# Helper function to execute a command on a remote host
def execute_ssh(command, host):
    ssh = subprocess.Popen(['ssh', '-l', ssh_user, host, command],
                           shell=False,
                           stdout=subprocess.PIPE,
                           stderr=subprocess.PIPE)
    result = ssh.stdout.readlines()

    # if no result, something is wrong
    if result == []:
        error = ssh.stderr.readlines()
        print "ERROR: %s" % error
        global exit_code
        exit_code = 1

    return result

# Delete each document individually
def delete_duplicates(to_be_deleted, host, endpoint):
    for document in to_be_deleted:
        delete_command = "curl -XDELETE \'%(es_host)s%(endpoint)s/%(document)s\'" % {'es_host': es_host, 'endpoint': endpoint, 'document': document}
        print "Deleting %s" % document
        ssh_response = execute_ssh(delete_command, host)[0]
        pretty_print(json.loads(ssh_response))

# Prepares a list of document ID's that should be deleted. Each document that has duplicates will be deleted
# such that one document remains.
def identify_duplicates(host, endpoint, es_response):
    to_be_deleted = []
    global exit_code
    try:
        buckets = es_response['aggregations']['duplicateCount']['buckets']
        for bucket in buckets:
            total_docs = bucket['duplicateDocuments']['hits']['total']
            for i in range(0, total_docs):
                to_be_deleted.append(bucket['duplicateDocuments']['hits']['hits'][i]['_id'])
        if to_be_deleted:
            delete_duplicates(to_be_deleted, host, endpoint)
            if exit_code != 1:
                exit_code = 2
        summary[host][endpoint]['documents_with_duplicates'] = len(buckets)
        summary[host][endpoint]['deleted_documents'] = len(to_be_deleted)
    except (KeyError):
        exit_code = 1


# Gathers elasticsearch documents which share a value in their _source. Calls functions to delete duplicates.
def deduplicate():
    for host in ssh_hosts:
        print "Host: %s" % host
        summary[host] = {}
        for endpoint, unique_key in endpoints.iteritems():
            print "Endpoint: %s" % endpoint
            summary[host][endpoint] = {}
            
            query = "curl -XGET \'%(es_host)s%(endpoint)s/_search\'" \
            " -d \'{\"size\":0, \"aggs\": { \"duplicateCount\":{ \"terms\": " \
            "{ \"field\":\"%(unique_key)s\",\"min_doc_count\":2}, \"aggs\":{" \
            "\"duplicateDocuments\":{\"top_hits\":{}}}}}}\'" % {'es_host': es_host, 'endpoint': endpoint, 'unique_key': unique_key}

            result = execute_ssh(query, host)
            try:
                es_response = json.loads(result[0])
                pretty_print(es_response)
                identify_duplicates(host, endpoint, es_response)
            except (IndexError):
                continue

if __name__ == '__main__':
    options_tpl = ('-i', 'config_path')
    del_list = []
    
    for i,config_path in enumerate(sys.argv):
        if config_path in options_tpl:
            del_list.append(i)
            del_list.append(i+1)

    del_list.reverse()

    for i in del_list:
        del sys.argv[i]

    config_data_file = open(config_path)
    config_json = json.load(config_data_file)

    ssh_user = config_json["sshUser"]
    ssh_hosts = config_json["sshHosts"]
    es_host = config_json["esHost"]
    endpoints = config_json["endpoints"]

    exit_code = 0
    summary = {}
    
    deduplicate()
    
    print
    print "Summary:"
    pretty_print(summary)

    sys.exit(exit_code)