# patch level features

Fri Aug 24 15:47:56 2018

## MongoDB Server Check

There are several ways to check if a MongoDB instance is running on a server:

1. Check the MongoDB process: You can use the following command to check if the MongoDB process is running on the server:

```sh
ps -ef | grep mongod
```

This command will show you if there are any running MongoDB processes on the server.

2. Check the MongoDB service: If MongoDB is installed as a service on the server, you can use the following command to check if the service is running:

```sh
# Might not work!
systemctl status mongod
```

This command will show you the status of the MongoDB service.

3. Check the MongoDB log files: You can check the MongoDB log files to see if there are any recent entries indicating that the server is running. The log files are typically located in the `/var/log/mongodb` directory.

4. Connect to the MongoDB instance: You can use the MongoDB shell to connect to the instance and check if it is running. Use the following command to start the MongoDB shell:

```sh
mongo
```

If the shell connects successfully, the MongoDB instance is running.

<br>
