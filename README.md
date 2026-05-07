# wheat

wheat is a fully functional, federated social networking platform built with Django and Django REST Framework. The app supports node-to-node communication, allowing for posts, comments, likes, and follow requests to be seamlessly shared across multiple platforms.

See [the web page](https://uofa-cmput404.github.io/general/project.html) for a description of the project.

![Website Image](https://github.com/jjluu4/wheat/blob/Production/imgs/wbesite.png)

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

## License

This project is licensed under the terms of the MIT open source license. Please refer to the [LICENSE](https://github.com/jjluu4/wheat/blob/Production/LICENSE) for the full terms.

## Copyright

Copyright © 2026 Team wheat
