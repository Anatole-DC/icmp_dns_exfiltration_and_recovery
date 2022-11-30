import binascii
import sys
import re


method = sys.argv[2]


with open(sys.argv[1], 'r') as file:
    print(">>> Performing extraction on {}".format(file.name))
    if method == "dns":
        matches = re.findall(r'\"dns\.qry\.name\".*:.*\".*\"', file.read())
    elif method == "icmp":
        matches = re.findall(r'\"data\.data\".*:.*\".*\"', file.read())

    print(">>> Foundt content :")
    contents = ""
    for match in matches:
        _, content = match.split(" ")
        content = "".join(content.split(":")).strip('"')
        contents = contents + binascii.unhexlify(content)

    string_elements = {}

    for content in contents:
        matches = re.findall(r"[0-9]*;?[\D]*", contents)
        for match in matches:
            id, content = match.split(";")
            string_elements[id] = content

    base_string = ""
    index = 0
    while string_elements != {}:
        base_string += string_elements[index]
        string_elements.pop(index)
        index += 1


    with open("exfiltrated_file", "w") as file:
        file.write(base_string)
        file.close()
