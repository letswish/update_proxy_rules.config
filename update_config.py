import base64
import re
import yaml
import urllib3
import sys

urls = [
    'https://raw.githubusercontent.com/gfwlist/gfwlist/master/gfwlist.txt',
    'https://gitlab.com/gfwlist/gfwlist/raw/master/gfwlist.txt',
    'https://bitbucket.org/gfwlist/gfwlist/raw/HEAD/gfwlist.txt',
    'http://repo.or.cz/gfwlist.git/blob_plain/HEAD:/gfwlist.txt',
    'https://pagure.io/gfwlist/raw/master/f/gfwlist.txt'
]   

def download_rules(urls=urls):
    print("Downloading new rules...")
    http = urllib3.PoolManager() 
    for url in urls:
        try:
            response = http.request('GET', url, preload_content=False)
            if response.status == 200:
                file_content = b""
                for chunk in response.stream(8192):
                    file_content += chunk
                response.release_conn()
                return file_content
            
            else:
                response.release_conn()
                
        except Exception as e:
            None
    
    return None 


def generate_rules(rules, domains):
    for domain in domains:
        if domain == '': None
        elif domain[0] == '@':
            rules.insert(0,'DOMAIN,'+domain[4:]+',DIRECT')
        elif domain[0] == '|':
            
            if domain[1] == '|':
                rules.append('DOMAIN-SUFFIX,'+domain[2:]+',Abroad') 
            
            else:
                if re.search('https', domain):
                    rules.append('DOMAIN-SUFFIX,'+domain[9:]+',Abroad')
                elif re.search('http', domain):
                    rules.append('DOMAIN-SUFFIX,'+domain[8:]+',Abroad')
                else:
                    rules.append('DOMAIN-SUFFIX,'+domain[1:]+',Abroad')


def process(master_path, proxies_path, output_path):
    new_rules = []
    domains = []

    data = download_rules()
    if data is None:
        print("Network Error")
        return
     
    content = str(base64.b64decode(data), encoding='utf-8')
    domains = content.split('\n')

    generate_rules(new_rules, domains)

    try:
        with open(proxies_path,'r') as f:
            proxies_file = f.read()
        new_proxies = yaml.load(proxies_file, yaml.FullLoader)['proxies']
    except Exception as e:
        print("Error: "+proxies_path+" not available")
    new_name = []
    for proxy in new_proxies:
        new_name.append(proxy['name'])
    
    try:
        with open(master_path,'r') as f:
            master_file = f.read()
        master = yaml.load(master_file, yaml.FullLoader)
    except Exception as e:
        print("Error: "+master_path+" not available")
    
    master['rules'].extend(new_rules)
    master['rules'].append('GEOIP,CN,DIRECT')
    master['rules'].append('MATCH,Others')


    master['proxies'].extend(new_proxies)

    master['proxy-groups'][3]['proxies'].extend(new_name)
    master['proxy-groups'][4]['proxies'].extend(new_name)
    master['proxy-groups'][5]['proxies'].extend(new_name)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            yaml.dump(master, stream=f, allow_unicode=True)
    except Exception as e:
        print("Error: "+output_path+" not available")

if __name__ == "__main__":
    try:
        if len(sys.argv) < 3:
            print("Usage: python update_config.py <master> <new_proxies> <output_path(default ./new_config.yaml)>")
            sys.exit(1)
        master_path = sys.argv[1]
        proxies_path = sys.argv[2]
        if(len(sys.argv) == 4):
            output_path = sys.argv[3]
        else:
            output_path = "./new_config.yaml"
        process(master_path, proxies_path, output_path)
        print(f"Update config success on {output_path} !")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")