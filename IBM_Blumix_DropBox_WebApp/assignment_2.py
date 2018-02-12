from __future__ import unicode_literals, print_function
from flask import Flask, request, url_for, redirect,render_template, make_response
import os
from werkzeug.utils import secure_filename
from cloudant import Cloudant
import cloudant
import cf_deployment_tracker
import json
#import simplecrypt
from base64 import b64encode
import hashlib

# for bluemix deployment
cf_deployment_tracker.track()

app = Flask(__name__)

# database configuration
db_name = 'filedb'
client = None
db = None


def check_item(dict, item):
    """
    Checks if the item is present in a dictionary or not
    :param dict: dictionary of items; made for cloudant
    :param item: name of item to find in the dictionary
    :return: tuple with boolean and cloudant document or None-type object
    """
    print(len(dict.items()))
    count = 0
    item_present = False
    for row in dict:
        name = row["name"]
        if name == item:
            item_present = True
            row_item = row
        count += 1
    if count == len(dict.items()) and item_present:
        return (True, row_item)
    else:
        return (False, None)


# check for configuration file
# NOTE: if statement checks for environment variable
# NOTE: DO NOT REMOVE (USED BY BLUEMIX)
if 'VCAP_SERVICES' in os.environ:
    vcap = json.loads(os.getenv('VCAP_SERVICES'))
    print('Found VCAP_SERVICES')
    if 'cloudantNoSQLDB' in vcap:
        creds = vcap['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)
elif os.path.isfile('vcap-local.json'):
    with open('vcap-local.json') as f:
        vcap = json.load(f)
        print('Found local VCAP_SERVICES')
        creds = vcap['services']['cloudantNoSQLDB'][0]['credentials']
        user = creds['username']
        password = creds['password']
        url = 'https://' + creds['host']
        client = Cloudant(user, password, url=url, connect=True)
        db = client.create_database(db_name, throw_on_exists=False)

if db != None:
    print("Connected to DB")
else:
    print("Not Connected to DB")


@app.route('/', methods=['GET','POST'])
@app.route('/index', methods=['GET','POST'])
def upload_file():
    # check if request method is post or not
    if client:
        if request.method == 'POST':
            # check if a file select dialog box popped up
            if 'file' not in request.files:
                print('No file part')
                return redirect(request.url)
            uploadfile = request.files['file']
            # this means that the dialog box was present
            # check if user pressed cancel
            if uploadfile.filename == '':
                print('No file selected')
                return redirect(request.url)
            # make sure that the file is present
            if uploadfile:
                filename = secure_filename(uploadfile.filename).strip()
                filecontents = b64encode(uploadfile.read())
                # getting the size of the file
                oldfilepos = uploadfile.stream.tell()
                uploadfile.stream.seek(0, os.SEEK_END)
                filesize = uploadfile.stream.tell()
                uploadfile.stream.seek(oldfilepos, os.SEEK_SET)
                # add a version number
                version = 1
                # check versions using hashing
                hash_num = hashlib.sha1()
                hash_num.update(filecontents)
                hashed = hash_num.hexdigest()
                if len(db.items()) == 0:
                    # no items in the database
                    data = {'name': filename,
                            '_attachments': {
                                filename: {
                                    'data': filecontents
                                }
                            },
                            'size': str(filesize),
                            'version': version,
                            'hash': hashed}
                    db.create_document(data)
                    return redirect(url_for("upload_file"))
                else:
                    # there are items in the database
                    # check if any items match the row
                    present, row = check_item(db, filename)
                    if present:
                        # file found
                        if hashed != row["hash"]:
                            # hash numbers do not match
                            # file was updated
                            version = int(row["version"])
                            version += 1
                            data = {'name': filename,
                                    '_attachments': {
                                        filename: {
                                            'data': filecontents
                                        }
                                    },
                                    'size': str(filesize),
                                    'version': version,
                                    'hash': hashed}
                            row.delete()
                            db.create_document(data)
                        else:
                            # hashes are the same
                            # file shows no change
                            # simply render a message
                            infocenter = {'info': 'File Exists !!'}
                            return render_template("index.html", infocenter=infocenter)
                    else:
                        # file was not found in the database
                        # create a new file
                        data = {'name': filename,
                                '_attachments': {
                                  filename: {
                                      'data': filecontents
                                  }
                                },
                               'size': str(filesize),
                               'version': version,
                               'hash': hashed}
                        db.create_document(data)
                        return redirect(url_for("upload_file"))

        infocenter = {'info': 'Information will go here'}
        return render_template('index.html', infocenter=infocenter)
    else:
        infocenter = {'info':'Information will go here'}
        return render_template('index.html', infocenter=infocenter)


@app.route('/uploads', methods=['GET','POST'])
def show_uploads():
    if client:
        data = db
        infocenter = {'info': 'File Uploaded'}
        return render_template("index.html", infocenter=infocenter, data_dict=data)
    else:
        infocenter = {'info': 'Information will go here'}
        return render_template('index.html', infocenter=infocenter)


@app.route('/download', methods=['GET', 'POST'])
def download():
    if client:
        if request.method == 'POST':
            # check if filename field is present
            # in form
            if 'filename' not in request.form:
                print("filename field not present in form")
                return redirect(url_for('download'))
            filename = request.form['filename'].strip()
            # check if user entered a filename
            if not filename:
                # filename attribute not present
                print("No filename entered")
                return redirect(url_for('download'))
            # iterate over all documents in the database
            for doc in db:
                # check if any document name matches the filename
                if doc['name'] == filename:
                    downloadfile = doc.get_attachment(filename, attachment_type='binary')
                    response = make_response(downloadfile)
                    response.headers["Content-Disposition"] = "attachment; filename=%s" % (filename)
                    return response
                #else:
            # no document with that name
            return render_template('not_found.html', filename=filename)

        return render_template('download.html')
    else:
        return render_template('no_uploads.html')

@app.route('/delete_file', methods=['GET', 'POST'])
def delete_file():
    if client:
        if request.method == 'POST':
            # check if filename field is present
            # in form
            if 'filename' not in request.form:
                print('filename field not present in form')
                return redirect(url_for('delete_file'))
            filename = request.form['filename'].strip()
            # check if user entered a filename
            if not filename:
                print("No filename entered")
                return redirect(url_for('delete_file'))
            # iterate over all documents in the database
            for doc in db:
                # check if any document name matches the filename
                if (doc['name'] == filename):
                    doc.delete()
                    return render_template("delete_success.html", filename=filename)
            return render_template("not_found.html", filename=filename)
        return render_template('delete_file.html')
    else:
        return render_template('no_uploads.html')


# port number configuration
port = int(os.getenv('PORT', 8080))

if __name__ == '__main__':
    # change the host to localhost before using locally
    app.run(host='0.0.0.0', port=port, debug=True)
