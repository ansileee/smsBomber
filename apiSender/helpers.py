import random
import string
import uuid

def randomEmail():
    name=''.join(random.choices(string.ascii_lowercase+string.digits,k=10))
    return f"{name}@example.com"

def randomName():
    first=''.join(random.choices(string.ascii_lowercase,k=6)).capitalize()
    last=''.join(random.choices(string.ascii_lowercase,k=5)).capitalize()
    return f"{first} {last}"

def randomPassword():
    chars=string.ascii_letters+string.digits
    return ''.join(random.choices(chars,k=12))

def replacePlaceholders(obj,phone):
    if obj is None:return None
    if isinstance(obj,dict):return{k:replacePlaceholders(v,phone)for k,v in obj.items()}
    if isinstance(obj,list):return[replacePlaceholders(v,phone)for v in obj]
    if isinstance(obj,str):
        obj=obj.replace("{phone}",phone)
        obj=obj.replace("{uuid}",str(uuid.uuid4()))
        if "{random_email}" in obj:obj=randomEmail()
        if "{random_name}" in obj:obj=randomName()
        if "{random_password}" in obj:obj=randomPassword()
        return obj
    return obj