
def split_lines(string):
    task = ''
    tasks = []
    for i in string:
        if i == ',':
            cleaned = task.replace('\r', '').replace('\n', '').replace('\t', '').strip()
            if cleaned:  
                tasks.append(cleaned)
            task = ''
        else:
            task += i

    if task:
        cleaned = task.replace('\r', '').replace('\n', ' ').replace('\t', '').strip()
        if cleaned:
            tasks.append(cleaned)
            
    return tasks


