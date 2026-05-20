import os  # Create Directioies 

# Each website you crawl is a separare project (folder) 
def create_project_dir(directory):
    if not os.path.exists(directory):
        print('Creating project ' + directory)
        os.makedirs(directory)
        
# Create queue and crawled files (if not created)
def create_data_files(project_name, base_url):
    queue = project_name + '/queue.txt'
    alreadyCrawled = project_name + '/crawled.txt'
    if not os.path.isfile(queue): 
        write_file(queue,base_url) 
    if not os.path.isfile(alreadyCrawled): 
        write_file(alreadyCrawled, '')

# Create a new file 

def write_file(path, data):
    with open(path, 'w', encoding='utf-8') as f:
      f.write(data) 


# Add data onto an existing file 
def append_to_file(path, data): 
    with open(path, 'a', encoding='utf-8') as file: 
        file.write(data + '\n')


# Delete the conents of a file 
def delete_file_contents(path): 
    with open(path, 'w'): 
        pass  # DO NOTHING. 


# Read a file and convert each line to set items 
def file_to_set(file_name): 
    results = set() 
    with open (file_name, 'rt', encoding='utf-8') as f: 
        for line in f: 
            results.add(line.replace('\n', ''))
    return results

# Iterate through a set, each item in the set will be a new line in the file 
def set_to_file(links, file): 
    delete_file_contents(file)
    for link in sorted(links): 
        append_to_file(file, link) 
        
