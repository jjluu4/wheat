[![Review Assignment Due Date](https://classroom.github.com/assets/deadline-readme-button-22041afd0340ce965d47ae6ef1cefeee28c7c493a6346c4f15d667ab976d596c.svg)](https://classroom.github.com/a/bRZK9dqv)
CMPUT404-project-socialdistribution
===================================

CMPUT404-project-socialdistribution

See [the web page](https://uofa-cmput404.github.io/general/project.html) for a description of the project.

Make a distributed social network!

## License

* Choose an OSI approved license, name it here, and copy the license text to a file called `LICENSE`.

## Copyright

The authors claiming copyright, if they wish to be known, can list their names here...

* 
## Project Members

| Name            | CCID          | GitHub                                          |
| --------------- | ------------- | ----------------------------------------------- |
| Johny Luu       | jjluu         | [jjluu4](https://github.com/jjluu4)             |
| Zane Crawford   | zcrawfor      | [Zumzu](https://github.com/Zumzu)            |
| Daniel Vold   | dvold      | [2004Nausicaa](https://github.com/2004nausicaa) |
| Juan Joseph | jsjosep1 | [jsjosep1](https://github.com/jsjosep1)|
| Sanskar Singh | sanskar2 | [S0504](https://github.com/S0504)|

## Remote Node Configuration

Staff users can manage remote node credentials through the web UI at `/staff/nodes/`.

- Required inputs are the remote node URL, username, and password.
- The API URL is optional. If left blank, it defaults to `<remote_url>/api`.
- Nodes can be disabled without being deleted, which keeps the configuration available for later federation work.
- Disabling a node temporarily pauses its use. Deleting a node permanently removes the saved configuration from this node.
- Deleting a node only affects local configuration. It does not send any request to the remote server.
- Configured remote-node credentials are also used for node-to-node HTTP Basic Auth on the inbox API.
- Browser and local web-app traffic continue to use the project’s existing local authentication; remote Basic Auth is only enforced on remote-only surfaces such as the inbox API.
