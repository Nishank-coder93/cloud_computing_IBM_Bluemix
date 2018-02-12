# BlueMix-Save
## Introduction
As part of our curriculum, we were tasked with creating a file upload/download service that, additionally, encrypts the file before upload
and decrypts it after download. All of the file upload and download functionality had to be achieved through the use of the Object Storage service
provided by IBM on their Bluemix cloud platform. This project achieves the desired result as a command-line application using Python, 
[Swiftclient](https://docs.openstack.org/developer/python-swiftclient/service-api.html),
and [Keystone](https://github.com/openstack/python-keystoneclient) APIs. 
For encryption and decryption, the application uses the [simple-crypty](https://github.com/andrewcooke/simple-crypt).
## Objective
Application allows the user to upload a text-file to the cloud and encrypts it before upload. It also allows the user to download any files
on their cloud account and decrypts it for the user.
## How to use
Do a normal `pip install -r requirements.txt` after cloning the application to a local environment.
In the `init()` method, under `main.py`, the user must enter the correct credentials from the Object Storage service on their IBM Bluemix
account. Not all are required but nonetheless, it is helpful to put them all in. For instructions on creating an IBM Bluemix account,
starting the Object Storage service instance, and generating service credentials, kindly look at 
[Bluemix Cloud Computing](https://www.ibm.com/cloud-computing/bluemix/)
## Future Considerations
Implement a better encryption algorithm (compression is not even close to secure). Separate the file into a more cogent structure.