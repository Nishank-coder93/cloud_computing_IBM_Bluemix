import swiftclient
import tkinter as tk
from tkinter import filedialog as tkFileDialog
import os
import simplecrypt
import json
import sys

PASSWORD = input("Enter the encryption Key (4 digit): ")


def init():
    '''
    Initializes a connection to the IBM Bluemix service
    :return: connection object
    '''
    # dictionary of credentials to access the service
    # use IBM Bluemix's service dashboard to generate this
    if os.path.isfile('service-creds.json'):
        with open("service-creds.json") as f:
            creds = json.load(f)
            print("Local Credentials File Found")
            key = creds["password"]
            authurl = creds["auth_url"]
            projectid = creds["projectId"]
            userid = creds["userId"]
            region_name = creds["region"]
    else:
        print("Service Creds is required. Exiting.")
        exit(-1)
    if key and authurl and projectid and userid and region_name:
        print("Creating connection")
        # establish a connection to the service
        connection = swiftclient.Connection(key=key,
                                            authurl=authurl + "/v3",
                                            auth_version="3",
                                            os_options={
                                                "project_id": projectid,
                                                "user_id": userid,
                                                "region_name": region_name
                                            })
    else :
        print("Connection cannot be established because service-creds.json not found")

    return connection


def return_home_path():
    """
    Platform-independent way of returning the home directory
    :return: string value, home directory path
    """
    return os.path.expanduser("~")


def check_file(con,filename):
    """
     This checks in the container if the file exists or not and returns True if it does
     else returns False
    """
    check_result = False
    vnum = '0'

    for container in con.get_account()[1]:
        for data in con.get_container(container['name'])[1]:
            print("object: %s, size: %s" % (data["name"], data["bytes"]))
            name_file = data["name"]
            vnum = name_file[-5]
            name_file = name_file[:-5] + name_file[-4:]
            print(name_file)
            print(filename)
            if filename == name_file:
                check_result = True


    return (check_result,vnum)

def show_menu():
    '''
    Shows the user the main menu
    :return: none
    '''
    menuItems = {}
    menuItems["1"] = "List Items of the container"
    menuItems["2"] = "Downloading the file"
    menuItems["3"] = "Upload the file"
    menuItems["4"] = "Delete a file from container"
    menuItems["5"] = "Exit the Program"
    for key, value in sorted(menuItems.items()):
        print("%s: %s" % (key, value))


def enter_container():
    '''
    Asks user for name of container
    :return: name of container
    '''
    container = input("Enter name of container: ")
    return container


def enter_file():
    """
    Asks user for name of file
    :return: filename
    """
    filename = input("Enter name of file: ")
    return filename


def upload_file(con):
    '''
    Uploads a file to the container on IBM Bluemix after encrypting it
    :param con: connection object
    :return: success message
    '''
    # we use the Tkinter library to show a file selection dialog

    threshold = 200
    container = enter_container()
    root = tk.Tk()
    root.withdraw()
    # print a message
    print("Opening file selection dialog")
    # get filepath
    fileopen = tkFileDialog.askopenfile(initialdir=return_home_path(), title="Select file", mode="rb")
    abs_path = os.path.abspath(fileopen.name)


    # get name of file
    filename = os.path.basename(abs_path)
    # filename = filename[:-4] + str(v) + filename[-4:]
    # get contents of file
    filecontents = fileopen.read()

    # Check if the File Exist
    res = check_file(con,filename)
    print(res[0],res[1])

    filename = filename[:-4] + str(res[1]) + filename[-4:]
    if res[0]:
        v = int(res[1]) + 1
        # con.delete_object(container, filename)
        filename = filename[:-5] + str(v) + filename[-4:]
        print("Encrypting file %s" % (filename))
        compressed = simplecrypt.encrypt(PASSWORD, filecontents)
        # print("Size is : ", sys.getsizeof(compressed))
        if container == "imagesmall":
            if sys.getsizeof(compressed) < threshold:
                print("Uploading files to %s container" % (container))
                con.put_object(container, filename, compressed, "text/plain")
            else:
                print("Unable to load because less than 200kb")
        else:
            print("Uploading files to %s container" % (container))
            con.put_object(container, filename, compressed, "text/plain")
    else:
        print("Encrypting file %s" % (filename))
        compressed = simplecrypt.encrypt(PASSWORD, filecontents)
        if container == "imagesmall":
            if sys.getsizeof(compressed) < threshold:
                print("Uploading files to %s container" % (container))
                con.put_object(container, filename, compressed, "text/plain")
            else:
                print("Unable to load because less than 200kb")
        else:
            print("Uploading files to %s container" % (container))
            con.put_object(container, filename, compressed, "text/plain")


        # print("Encrypting file %s" % (filename))
    # compressed = simplecrypt.encrypt(PASSWORD, filecontents)
    #
    # print("Uploading files to %s container" % (container))
    # con.put_object(container, filename, compressed, "text/plain")



def download_file(con):
    '''
    Downloads the given file, if present, and decrypts it from the container from IBM Bluemix
    :param con: connection object
    :return:success message
    '''
    list_files(con)
    container = enter_container()
    filename = enter_file()
    home = return_home_path()
    # since the get_object method raises an exception if the file is not found
    # we check if there was a file or not
    try:
        #Enter the key to Decrypt
        PASSWORD = input("Enter the Key to Decrypt: ")

        # get the contents of the file from the container
        filecontents = con.get_object(container, filename)

        if filecontents:
            print("Got the file Contents !")
        else:
            print("Unable to get the File Contents !")
        # open the save file dialog box
        print("Opening the save file as dialog")
        save = tkFileDialog.asksaveasfile(mode="wb", defaultextension="txt", title="Save file as...", initialdir=home)
        # check if no file was selected or cancel was pressed
        if save is None:
            print("No name entered for file.")
            print("Cancelling download.")
            return
        # if file was selected, decompress the contents of the file
        # and save the file
        print("Decrypting the file contents")

        savetext = simplecrypt.decrypt(PASSWORD, filecontents[1])

        print("Writing to storage")

        save.write(savetext)
        save.close()
        print("File stored at %s" % (save.name))

    except swiftclient.ClientException:
        print("File not found. Excpetion %s" % (swiftclient.ClientException))



def list_files(con):
    '''
    Lists all files present in the container
    :param con: connection object
    :return:list of items, if present
    '''
    for container in con.get_account()[1]:
        print("Container name: %s" % (container["name"]))
        for data in con.get_container(container['name'])[1]:
            print("object: %s, size: %s" % (data["name"], data["bytes"]))


def delete_file(con):
    '''
    Deletes given file, if present, from the container from IBM Bluemix
    :param con: connection object
    :return:success message
    '''
    list_files(con)

    inSize = input("Do you want to inut size ? (y/n)")
    if inSize == 'y':
        delSize = input("Enter the size to delete contents : ")

        #for container in

    container = enter_container()
    filename = enter_file()
    # since delete_object throws an exception if file is not found
    # we handle it
    try:
        con.delete_object(container, filename)
        print("%s deleted successfully" % (filename))
    except swiftclient.ClientException:
        print("No file with %s name found in %s container. Exiting." % (filename, container))


def main():
    '''
    Calls all the functions and provides input output functionality
    :return:
    '''
    cont = True
    connection = init()
    if connection:
        print("Connected successfully")
    else:
        print("There was some error in connecting. Cannot continue")
        exit(-1)
    while cont:
        show_menu()
        selection = input("What do you want to do? ")
        if selection == "1":
            list_files(connection)
        if selection == "2":
            download_file(connection)
        if selection == "3":
            upload_file(connection)
        if selection == "4":
            delete_file(connection)
        if selection == "5":
            exit()
        if input("Continue?(y/n)") == "n":
            cont = False


if __name__ == '__main__':
    main()
