#prefix based blocking

def blocking_key(name: str):
    name = name.lower()

    if len(name) < 4:
        return name

    return name[:4]  
