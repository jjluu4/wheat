# Overview

<p>The Wheat Social Distribution API allows for easy communication with the Wheat Social Distribution Web App. Using the Django Rest Framework, one can send and receive simple HTTP requests and responses to and from the Wheat Social Distribution Web App’s server. All of the information one needs to interact with this API can be found in the following document.</p>

<p>All API object <code>id</code> fields are FQIDs: full URLs that uniquely identify the object on its home node.</p>

# Where to Start

<p>The Wheat Social Distribution API supports both local client usage and a limited set of remote node-to-node requests. Local browser and API clients use the project’s existing local authentication flow. Remote node-to-node requests currently use HTTP Basic Auth with credentials configured through the staff-only remote node management UI at <code>/staff/nodes/</code>.</p>

<p>However, certain requests made at specific endpoints may require signing up to successfully complete. The ability to make GET requests towards friends-only entries, as well as POST, PUT and DELETE requests are dependent upon specific user permissions, and will be denied in all cases where the user is not logged in. To sign up, one must only go to the address where their local node is currently running, press the “Sign up” button in the top right corner, and enter whatever username and password one finds appealing. This username and password can then be utilized when making requests to the API (how to achieve this is discussed below). </p>

## Remote Node Authentication

<p>Node-to-node inbox requests require HTTP Basic Auth. The username and password must match an active remote node configured in the target server’s <code>/staff/nodes/</code> page. Requests with missing, malformed, or invalid Basic Auth headers receive a <code>401 Unauthorized</code> response and a <code>WWW-Authenticate: Basic realm="Node to Node API"</code> challenge.</p>

<p>Example header:</p>

> Authorization: Basic &lt;base64(username:password)&gt;

# HTTP Requests and Responses

<p>One can interact with the Wheat Social Distribution API by making HTTP requests at specific API endpoints. This section goes over the general procedures when making requests and receiving responses with the API.</p>

## Requests

<p>There are a number of methods one can use to send an HTTP request. One of the most common methods is through CURL requests. An example of a simple GET request with CURL can be seen below.</p>

> curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors/8d77aa07-b5ab-4532-8367-9973d287b36e/entries/5d65a728-df4e-44b7-a7f2-653fc73f2b14/ 

<p>As mentioned previously, some HTTP requests will require login in order to be successfully carried out. To achieve this, the format in the example GET request below can be applied to any type of CURL request. </p>

> curl --user example_username:example_password -X GET http<nolink>:\//127.0.0.1:8000/api/authors/8d77aa07-b5ab-4532-8367-9973d287b36e/entries/1ff24238-e302-40a9-b20c-96e6b32b23b1/

<p>There are various types of HTTP requests that one can make. For the Wheat Social Distribution API there are up to four types of API requests that can be made depending on the particular endpoint. A summary of these different types with example CURL requests can be viewed below. </p>

___
#### Request Types
| Request Type | Usage | Example Curl |
| --------------- | --------------- | --------------- |
| GET | Retrieves data from the server. For this API, data is retrieved in the form of a JSON. | curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors/8d77aa07-b5ab-4532-8367-9973d287b36e/entries/5d65a728-df4e-44b7-a7f2-653fc73f2b14/  |
| PUT | Modifies data in the server. For this API, sent data should be in the form of a JSON object. Correct JSON representations for specific API endpoints can be found further down. | curl --user example_username:example_password -X PUT http<nolink>:\//127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/812ceb53-c4fe-4897-861c-9e672bf366f8/ -H "Content-Type: application/json" -d @/example/path.json |
| POST | Sends data to the server. For this API, sent data should be in the form of a JSON object. Correct JSON representations for specific API endpoints can be found further down. | curl --user example_username:example_password -X POST http<nolink>:\//127.0.0.1:8000/api/authors/02309c0a-b28d-457d-815c-2ce5722bad13/entries/ -H "Content-Type: application/json" -d @/example/path.json |
| DELETE | Deletes data from the server. With this API, data is typically not deleted, but rather marked as “Deleted” such that it won’t ever show up in the UI, but can still technically be accessed later | curl -X DELETE http<nolink>:\//127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/812ceb53-c4fe-4897-861c-9e672bf366f8/ |

___
#### Pagination

Pagination, where a request will return the **x** th page of results with **y** results per page, can be used with certain endpoints by using the format seen in the example below. One can find which endpoints do and do not support pagination further down in this documentation, in the section on API Endpoints.

> curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors?page=**x**&size=**y**

___
## Responses

<p>Once an HTTP request has been made, the API user will receive a response code concerning their request’s status (and possibly some data alongside it). If the response code comes back in the format 2XX, it means the request was processed successfully. If a response code with format 4XX is returned, it means that something went wrong while processing the request. In the table below, one can find a complete list of response codes one will encounter while using this API, as well as more specific meanings for each one. </p>

| Response | Meaning |
| --------------- | --------------- |
| 200 Ok | The request has succeeded. |
| 201 Created | A new object has been successfully created. Typically appears after successful PUT or POST requests. |
| 204 No Content | The request has been successfully completed, but no content was returned. Typically appears after successful DELETE requests. |
| 400 Bad Request | The request is invalid in some way. Typically suggests incorrect syntax within the request. |
| 401 Unauthorized | The user making this request has not been authenticated to make the specified http request (In other words, logging in is probably required to make this request). |
| 403 Forbidden | The user making this request does not have sufficient permissions to view the requested content. |
| 404 Not Found | The requested content could not be found. |

___
## Browser-Safe Media Routes

<p>The web UI only embeds same-node image URLs. Author avatars, entry images, and allowlisted remote markdown images are loaded through the routes below so the browser never needs to request configured remote-node media directly.</p>

**GET /api/authors/{author_serial}/profile-image/**
> curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/profile-image/

**Description:** Retrieve an author avatar through this node. Same-node avatar URLs are redirected locally. Configured remote-node avatars are fetched server-side with the stored Basic Auth credentials. Missing or disallowed avatars fall back to the local placeholder image.

**GET /api/media/image-proxy/?url={absolute_image_url}**
> curl -X GET "http<nolink>:\//127.0.0.1:8000/api/media/image-proxy/?url=https%3A%2F%2Fpartner.example.com%2Fmedia%2Fexample.png"

**Description:** Proxy an image through this node. Only same-node image URLs and URLs belonging to active configured remote nodes are allowed.

**Proxy Error Codes:** <br>400 [Occurs if the URL is missing or not allowlisted], <br>404 [Occurs if the remote image does not exist], <br>502 [Occurs if the upstream response is not a successful image response], <br>503 [Occurs if the remote node cannot be reached]

**Entry Image Routes**

Existing image-entry routes also honor this same-origin behavior:

- `GET /api/authors/{author_serial}/entries/{entry_serial}/image/`
- `GET /api/entries/{entry_fqid}/image/`

These routes now serve local uploads, local base64 image entries, and stored remote image-backed entries through this node.

___
## Inbox API - Receive remote objects for a local author

___
#### Endpoint Pattern

> &lt;Node Address&gt;/api/authors/&lt;Author Serial&gt;/inbox

___
#### Authentication

<p>This endpoint is intended for remote node-to-node traffic. It requires HTTP Basic Auth using an active remote node credential pair configured on the receiving server.</p>

___
#### POST Request with curl

> curl -X POST http<nolink>:\//127.0.0.1:8000/api/authors/02309c0a-b28d-457d-815c-2ce5722bad13/inbox -H "Authorization: Basic &lt;base64(username:password)&gt;" -H "Content-Type: application/json" -d @/example/path/remote-entry.json

> **CREATES or UPDATES the received object with Code=200 or Code=201**

<p>The incoming object must belong to the same remote node as the authenticated Basic Auth credential pair. Currently, entry create/update/delete traffic is enforced on this endpoint.</p>

Possible Error Codes: <br>400 [Occurs if the payload is malformed], <br>401 [Occurs if Basic Auth is missing or invalid], <br>403 [Occurs if the payload author does not match the authenticated remote node], <br>404 [Occurs if the inbox owner does not exist]

# Objects

<p>The following section goes over the numerous JSON “Objects” that represent different parts of the Wheat Social Distribution Web App. These objects are utilized when interacting with API endpoints, both as data being sent to the server, and data being received from the server. This section covers the major endpoints that are associated with each object type, the requests and responses associated with those endpoints, and the make-up of each object, providing examples for reference. </p>

# API Endpoints and Their Objects

<p>The following section covers each of the API Endpoints that one can interact with while using this API. For each endpoint a template is provided for the general layout of each endpoint. An example curl command is also provided for each viable request type at each endpoint, as well as the response behavior that comes about from that command. A list of possible error response codes is also provided for each example. </p>

___
## Authors API - Retrieve a list of authors

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors

Paginated:
> \<Node Address\>/api/authors?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

**GET /api/authors**
> curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors

**Description:** Retrieve a list of all authors.

#### Queries
page_number (int): page number of results
size (int): # of results per page

#### Example with Query Keywords
GET /api/authors?page={page_number}&size={size}

#### Response Body

```
{
    "type": string,
    "authors": List<Author>
}
```

#### Example Response

```
{
    "type": "authors",
    "authors": [
        {
            "type": "author",
            "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
            "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount",
            "github": "https://github.com/NewAccount",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
        },
        {
            "type": "author",
            "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "Johnson",
            "github": "https://github.com/Johnson",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
        }
    ]
}
```

#### Status Codes
200 - Success<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/**
> curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/

**Description:** Retrieve one specific author.

#### Parameters
author_serial (string): The UUID of an author.

#### Response Body

```
{
    "type": string,
    "serial": string,
    "id": string,
    "host": string,
    "displayName": string,
    "github": string,
    "profileImage": string,
    "web": string
}
```

#### Example Response

```
{
    "type": "author",
    "serial": "02309c0a-b28d-457d-815c-2ce5722bad13",
    "id": "http://127.0.0.1:8000/api/authors/02309c0a-b28d-457d-815c-2ce5722bad13",
    "host": "http://127.0.0.1:8000/api/",
    "displayName": "NewAccount2",
    "github": "https://github.com/NewAccount2",
    "profileImage": "https://placehold.co/150x150.png",
    "web": "http://127.0.0.1:8000/authors/02309c0a-b28d-457d-815c-2ce5722bad13/"
}
```

#### Status Codes
200 - Success<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**PUT /api/authors/{author_serial}/**
> curl --user <example_username>:<example_password> -X PUT http<nolink>:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/

**Description:** Edit a specific author.

#### Auth
<example_username>: username of author connected to <author_serial>
<example_password>: password for author connected to <author_serial>

#### Parameters
author_serial (string): The UUID of an author.

#### Request Body

```
{
    "type": string,
    "serial": string,
    "id": string,
    "host": string,
    "displayName": string,
    "github": string,
    "profileImage": string,
    "web": string
}
```

#### Example Request

```
{
    "type": "author",
    "serial": "02309c0a-b28d-457d-815c-2ce5722bad13",
    "id": "http://127.0.0.1:8000/api/authors/02309c0a-b28d-457d-815c-2ce5722bad13",
    "host": "http://127.0.0.1:8000/api/",
    "displayName": "NewAccount2",
    "github": "https://github.com/NewAccount2",
    "profileImage": "https://placehold.co/150x150.png",
    "web": "http://127.0.0.1:8000/authors/02309c0a-b28d-457d-815c-2ce5722bad13/"
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_fqid}/**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_fqid}

**Description:** Retrieve one specific author.

#### Auth
<example_username>: username of remote node <author_fqid> originates from
<example_password>: password  for remote node <author_fqid> originates from

#### Parameters
author_fqid (string): The FQID of an author

#### Response Body

```
{
    "type": string,
    "serial": string,
    "id": string,
    "host": string,
    "displayName": string,
    "github": string,
    "profileImage": string,
    "web": string
}
```

#### Example Response

```
{
    "type": "author",
    "serial": "02309c0a-b28d-457d-815c-2ce5722bad13",
    "id": "http://127.0.0.1:8000/api/authors/02309c0a-b28d-457d-815c-2ce5722bad13",
    "host": "http://127.0.0.1:8000/api/",
    "displayName": "NewAccount2",
    "github": "https://github.com/NewAccount2",
    "profileImage": "https://placehold.co/150x150.png",
    "web": "http://127.0.0.1:8000/authors/02309c0a-b28d-457d-815c-2ce5722bad13/"
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
500 - Internal Server Error<br>

## Following API

**GET /api/authors/{author_serial}/following**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/following

**Description:** Retrieve a list of authors that an author is following

#### Auth
<example_username>: username of author
<example_password>: password for author

#### Parameters
author_serial (string): The UUID of an author

#### Response Body

```
{
    "type": string,
    "following”: List<Author>
}
```

#### Example Response

```
{
    "type": "following",
    "following": [
        {
            "type": "author",
            "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
            "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount",
            "github": "https://github.com/NewAccount",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
        }
    ]
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/following/{foreign_author_fqid}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/following/{foreign_author_fqid}

**Description:** Check if a local author is following a remote author.

#### Auth
<example_username>: username of author connected with author_serial
<example_password>: password for author connected with author_serial

#### Parameters
author_serial (string): The UUID of an author
foreign_author_fqid (string): The FQID of a remote author

#### Response Body

```
{"is_following": Boolean}
```

#### Example Response

```
{"is_following": True}
```


#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**PUT /api/authors/{author_serial}/following/{foreign_author_fqid}**
> curl --user <example_username>:<example_password> -X PUT http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/following/{foreign_author_fqid}

**Description:** Generates a follow request by a local author for a remote author.

#### Auth
<example_username>: username of author connected with author_serial
<example_password>: password for author connected with author_serial

#### Parameters
author_serial (string): The UUID of an author
foreign_author_fqid (string): The FQID of a remote author

#### Status Codes
204 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>
502 - Delivery Error<br>

**DELETE /api/authors/{author_serial}/following/{foreign_author_fqid}**
> curl --user <example_username>:<example_password> -X DELETE http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/following/{foreign_author_fqid}

**Description:** Unfollows local author from remote author.

#### Auth
<example_username>: username of author connected with author_serial
<example_password>: password for author connected with author_serial

#### Parameters
author_serial (string): The UUID of an author
foreign_author_fqid (string): The FQID of a remote author

#### Status Codes
204 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>

## Followers API

**GET /api/authors/{author_serial}/followers**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/followers

**Description:** Retrieve a list of authors who are followers of an author

#### Auth
<example_username>: username of author
<example_password>: password for author

#### Parameters
author_serial (string): The UUID of an author

#### Response Body

```
{
    "type": string,
    "following”: List<Author>
}
```

#### Example Response

```
{
    "type": "followers",
    "followers": [
        {
            "type": "author",
            "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "Johnson",
            "github": "https://github.com/Johnson",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
        }

    ]
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/followers/{foreign_author_fqid}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/followers/{foreign_author_fqid}

**Description:** Check if a remote author follows a local author.

#### Auth
<example_username>: username of author connected with author_serial *or* username of remote node of author_fqid
<example_password>: password for author connected with author_serial *or* password for remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author
foreign_author_fqid (string): The FQID of a remote author

#### Response Body

```
{"is_follower": Boolean}
```

#### Example Response

```
{"is_follower": True}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**PUT /api/authors/{author_serial}/followers/{foreign_author_fqid}**
> curl --user <example_username>:<example_password> -X PUT http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/followers/{foreign_author_fqid}

**Description:** Accept a follow request from a remote author

#### Auth
<example_username>: username of author connected with author_serial
<example_password>: password for author connected with author_serial

#### Parameters
author_serial (string): The UUID of an author
foreign_author_fqid (string): The FQID of a remote author

#### Status Codes
204 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>
502 - Delivery Error<br>

**DELETE /api/authors/{author_serial}/followers/{foreign_author_fqid}**
> curl --user <example_username>:<example_password> -X DELETE http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/followers/{foreign_author_fqid}

**Description:** Remove a remote author as a follower of a local author.

#### Auth
<example_username>: username of author connected with author_serial
<example_password>: password for author connected with author_serial

#### Parameters
author_serial (string): The UUID of an author
foreign_author_fqid (string): The FQID of a remote author

#### Status Codes
204 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

## Follow Request API

**GET /api/authors/{author_serial}/follow_requests**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/follow_requests

**Description:** Retrieve a list of authors that have made follow requests to an author.

#### Auth
<example_username>: username of author
<example_password>: password for author

#### Parameters
author_serial (string): The UUID of an author

#### Response Body

```
{
    "type": string,
    "summary”: string,
    "actor”: Author,
    "object”: Author
}
```

#### Example Response

```
[
    {
        "type": "follow",
        "summary": "NewAccount1 wants to follow NewAccount2",
        "actor": {
            "type": "author",
            "serial": "a1c2ddb7-f5a1-4854-a79e-b04113c33c39",
            "id": "http://127.0.0.1:8000/api/authors/da1638bc-2f5a-4ef9-9531-2d090c6eac16",
            "host": "http://127.0.0.1:8000/api",
            "displayName": "NewAccount1",
            "github": "https://github.com/NewAccount1",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/da1638bc-2f5a-4ef9-9531-2d090c6eac16/"
        },
        "object": {
            "type": "author",
            "serial": "1c910cfb-348c-407d-9ad5-f6859b74d308",
            "id": "http://127.0.0.1:8002/api/authors/1c910cfb-348c-407d-9ad5-f6859b74d308",
            "host": "http://127.0.0.1:8002/api",
            "displayName": "NewAccount2",
            "github": "https://github.com/NewAccount2",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8002/authors/1c910cfb-348c-407d-9ad5-f6859b74d308/"
        }
    }
]
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

## Entries API

**GET /api/authors/{author_serial}/entries/{entry_serial}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}

**Description:** Retrieve an entry

#### Auth
<example_username>: username of an author (should be friend to access friends-only entries locally) *or* username of remote node of author_serial
<example_password>: password for an author (should be friend to access friends-only entries locally) *or* password for remote node of author_serial

#### Parameters
author_serial (string): The UUID of an author
entry_serial (string): The UUID of an entry

#### Response Body

```
{
    "type": string,
    "title”: string,
    "id": string,
    "web”: string,
    "description": string,
    "contentType”: string,
    "imageUrl": string,
    "author”: Author,
    "published": Date,
    "visibility”: Author,
    "likes": List<Like>,
    "comments”: List<Comment>,
}
```

#### Example Response

```
{
    "type": "entry",
    "title": "A New Entry",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e",
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
    "description": "this is a new entry....",
    "contentType": "text/plain",
    "content": "this is a new entry....",
    "imageUrl": "",
    "author": {
        "type": "author",
        "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
    },
    "published": "2026-03-16T10:39:13.948852Z",
    "visibility": "PUBLIC",
    "likes": {
        "type": "likes",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/likes/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/likes/",
        "page_number": 1,
        "size": 50,
        "count": 1,
        "src": [
            {
                "type": "like",
                "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/liked/03c9e0d5-c3f9-4b78-9858-7a07d83dca58/",
                "author": {
                    "type": "author",
                    "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
                    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
                    "host": "http://127.0.0.1:8000/api/",
                    "displayName": "NewAccount",
                    "github": "https://github.com/NewAccount",
                    "profileImage": "https://placehold.co/150x150.png",
                    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
                },
                "published": "2026-03-16T10:39:32.837116Z",
                "object": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e"
            }
        ]
    },
    "comments": {
        "type": "comments",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
        "page_number": 1,
        "size": 5,
        "count": 1,
        "src": [
            {
                "type": "comment",
                "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/1df6381f-1ecb-42b4-8ad1-2ad4a66207d0/",
                "url": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/1df6381f-1ecb-42b4-8ad1-2ad4a66207d0/",
                "author": {
                    "type": "author",
                    "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
                    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
                    "host": "http://127.0.0.1:8000/api/",
                    "displayName": "NewAccount",
                    "github": "https://github.com/NewAccount",
                    "profileImage": "https://placehold.co/150x150.png",
                    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
                },
                "content": "This is a comment.",
                "contentType": "text/plain",
                "published": "2026-03-16T10:39:24.867354Z",
                "entry": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
                "likes": {
                    "type": "likes",
                    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/1df6381f-1ecb-42b4-8ad1-2ad4a66207d0/likes/",
                    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/1df6381f-1ecb-42b4-8ad1-2ad4a66207d0/likes/",
                    "page_number": 1,
                    "size": 50,
                    "count": 0,
                    "src": []
                }
            }
        ]
    }
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**PUT /api/authors/{author_serial}/entries/{entry_serial}**
> curl --user <example_username>:<example_password> -X PUT http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}

**Description:** Edit an entry

#### Auth
<example_username>: username of an author connected to author_serial
<example_password>: password for an author connected to author_serial

#### Parameters
author_serial (string): The UUID of an author
entry_serial (string): The UUID of an entry

#### Request Body

```
{
    "type": string,
    "title”: string,
    "id": string,
    "web”: string,
    "description": string,
    "contentType”: string,
    "imageUrl": string,
    "author”: Author,
    "published": Date,
    "visibility”: Author,
    "likes": List<Like>,
    "comments”: List<Comment>,
}
```

#### Example Request

```
{
            "type": "entry",
            "title": "Typing",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588",
            "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "description": "I am typing on the computer. :)",
            "contentType": "text/markdown",
            "content": "I am typing on the computer. :)",
            "imageUrl": "",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T12:45:27.099220Z",
            "visibility": "PUBLIC",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
}
```

#### Status Codes
200 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**DELETE /api/authors/{author_serial}/entries/{entry_serial}**
> curl --user <example_username>:<example_password> -X DELETE http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}

**Description:** Delete an entry

#### Auth
<example_username>: username of author connected to author_serial
<example_password>: password for author connected to author_serial

#### Parameters
author_serial (string): The UUID of an author
entry_serial (string): The UUID of an entry

#### Status Codes
204 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/entries/{entry_fqid}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/entries/{entry_fqid}

**Description:** Retrieve an entry with the fqid

#### Auth
<example_username>: username of an author (should be friend to access friends-only entries locally)
<example_password>: password for an author (should be friend to access friends-only entries locally)

#### Parameters
entry_fqid (string): The FQID of an entry

#### Response Body

```
{
    "type": string,
    "title”: string,
    "id": string,
    "web”: string,
    "description": string,
    "contentType”: string,
    "imageUrl": string,
    "author”: Author,
    "published": Date,
    "visibility”: Author,
    "likes": List<Like>,
    "comments”: List<Comment>,
}
```

#### Example Response

```
{
            "type": "entry",
            "title": "Typing",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588",
            "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "description": "I am typing on the computer. :)",
            "contentType": "text/markdown",
            "content": "I am typing on the computer. :)",
            "imageUrl": "",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T12:45:27.099220Z",
            "visibility": "PUBLIC",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/entries/**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/

**Description:** Retrieve a list of entries from an author

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries)
<example_password>: password for author (should be friend of author_serial for friends-only entries)

#### Parameters
author_serial (string): The UUID of an author.

#### Queries
page_number (int): page number of results
size (int): # of results per page

#### Example with Query Keywords
GET /api/authors/{author_serial}/entries/?page={page_number}&size={size}

#### Response Body

```
{
    "type": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Entry>
}
```

#### Example Response

```
{
{
    "type": "entries",
    "page_number": 1,
    "size": 5,
    "count": 1,
    "src": [
        {
            "type": "entry",
            "title": "Typing",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588",
            "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "description": "I am typing on the computer. :)",
            "contentType": "text/markdown",
            "content": "I am typing on the computer. :)",
            "imageUrl": "",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T12:45:27.099220Z",
            "visibility": "PUBLIC",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
    ],
    }
}
```

#### Status Codes
200 - Success<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**POST /api/authors/{author_serial}/entries/**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/

**Description:** Retrieve a list of entries from an author

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries)
<example_password>: password for author (should be friend of author_serial for friends-only entries)

#### Parameters
author_serial (string): The UUID of an author.

#### Request Body

```
{
    "type": string,
    "title”: string,
    "id": string,
    "web”: string,
    "description": string,
    "contentType”: string,
    "imageUrl": string,
    "author”: Author,
    "published": Date,
    "visibility”: Author,
    "likes": List<Like>,
    "comments”: List<Comment>,
}
```

#### Example Request

```
{
            "type": "entry",
            "title": "Entry",
            "description": "Example.",
            "contentType": "text/markdown",
            "content": "This is an example entry.",
            "imageUrl": "",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T12:45:27.099220Z",
            "visibility": "PUBLIC",
}
```

#### Status Codes
201 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/entries/{entry_serial}/image**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}/image

**Description:** Retrieve an image from an image entry

#### Auth
<example_username>: username of an author (should be friend to access friends-only entries locally) *or* username of remote node of author_serial
<example_password>: password for an author (should be friend to access friends-only entries locally) *or* password for remote node of author_serial

#### Parameters
author_serial (string): The UUID of an author.
entry_serial (string): The UUID of an entry.

#### Response Body
```
{Image Encoded As Binary Data}
```

#### Example Response
```
{b'\xff\xd8\xff\xe0\x00\x10JFI………’}
```

#### Status Codes
200 - Success<br>
400 - Invalid Request<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>
503 - Failure to Connect to Remote Node<br>

**GET /api//entries/{entry_fqid}/image**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api//entries/{entry_fqid}/image

**Description:** Retrieve an image from an image entry using fqid

#### Auth
<example_username>: username of an author (should be friend to access friends-only entries locally) *or* username of remote node of author_serial
<example_password>: password for an author (should be friend to access friends-only entries locally) *or* password for remote node of author_serial

#### Parameters
entry_fqid (string): The FQID of an entry.

#### Response Body
```
{Image Encoded As Binary Data}
```

#### Example Response
```
{b'\xff\xd8\xff\xe0\x00\x10JFI………’}
```

#### Status Codes
200 - Success<br>
400 - Invalid Request<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>
502 - Remote Node Error<br>
503 - Failure to Connect to Remote Node<br>

## Comments API

**GET /api/authors/{author_serial}/entries/{entry_serial}/comments**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}/comments

**Description:** Retrieve a list of comments on an entry

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries) *or* username of remote node of author_fqid
<example_password>: password for author (should be friend of author_serial for friends-only entries) *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author.
entry_serial (string): The UUID of an entry.

#### Queries
page_number (int): page number of results
size (int): # of results per page

#### Example with Query Keywords
GET /api/authors/{author_serial}/entries/{entry_serial}/comments?page={page_number}&size={size}

#### Response Body

```
{
    "type": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Comment>
}
```

#### Example Response

```
{
    "type": "comments",
    "page_number": 1,
    "size": 5,
    "count": 1,
    "src": [
        {
            "type": "comment",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "url": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "content": "making a comment.",
            "contentType": "text/plain",
            "published": "2026-03-16T12:56:43.768883Z",
            "entry": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
    ]
}
```

#### Status Codes
200 - Success<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/entries/{entry_fqid}/comments**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/entries/{entry_fqid}/comments

**Description:** Retrieve a list of comments on an entry with an fqid

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries) *or* username of remote node of author_fqid
<example_password>: password for author (should be friend of author_serial for friends-only entries) *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author.
entry_serial (string): The UUID of an entry.

#### Queries
page_number (int): page number of results
size (int): # of results per page

#### Example with Query Keywords
GET /api/entries/{entry_fqid}/comments?page={page_number}&size={size}

#### Response Body

```
{
    "type": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Comment>
}
```

#### Example Response

```
{
    "type": "comments",
    "page_number": 1,
    "size": 5,
    "count": 1,
    "src": [
        {
            "type": "comment",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "url": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "content": "making a comment.",
            "contentType": "text/plain",
            "published": "2026-03-16T12:56:43.768883Z",
            "entry": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
    ]
}
```

#### Status Codes
200 - Success<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/entries/{entry_serial}/comments/{remote_comment_fqid}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}/comments

**Description:** Retrieve a list of comments on an entry

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries) *or* username of remote node of author_fqid
<example_password>: password for author (should be friend of author_serial for friends-only entries) *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author.
entry_serial (string): The UUID of an entry.
remote_comment_fqid (string): the FQID of a remote comment on a local entry.

#### Response Body

```
{
    "type": string
    "id": string
    "url": string
    "author": Author
    "content": string
    "contentType": string
    "published": Date
    "entry": string
    "likes": List<Like>
}
```

#### Example Response

```
{
    "type": "comment",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "url": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "author": {
        "type": "author",
        "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
    },
    "content": "I am commenting on this post",
    "contentType": "text/plain",
    "published": "2026-03-16T10:47:57.796752Z",
    "entry": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
    "likes": {
        "type": "likes",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
    },
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331"
}
```

#### Status Codes
200 - Success<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

## Commented API

**GET /api/authors/{author_serial}/commented**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/commented

**Description:** Retrieve a list of comments an author has made

#### Auth
<example_username>: username of author corresponding to author_serial *or* username of remote node of author_fqid
<example_password>: password for author corresponding to author_serial *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author.

#### Queries
page_number (int): page number of results
size (int): # of results per page

#### Example with Query Keywords
GET /api/authors/{author_serial}/commented?page={page_number}&size={size}

#### Response Body

```
{
    "type": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Comment>
}
```

#### Example Response

```
{
    "type": "comments",
    "page_number": 1,
    "size": 5,
    "count": 1,
    "src": [
        {
            "type": "comment",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "url": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "content": "making a comment.",
            "contentType": "text/plain",
            "published": "2026-03-16T12:56:43.768883Z",
            "entry": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
    ]
}
```

#### Status Codes
200 - Success<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**POST /api/authors/{author_serial}/commented**
> curl --user <example_username>:<example_password> -X POST http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/commented

**Description:** Create a comment for an author

#### Auth
<example_username>: username of author corresponding to author_serial
<example_password>: password for author corresponding to author_serial

#### Parameters
author_serial (string): The UUID of an author.

#### Request Body

```
{
    "type": string
    "id": string
    "url": string
    "author": Author
    "content": string
    "contentType": string
    "published": Date
    "entry": string
    "likes": List<Like>
}
```

#### Example Request

```
{
    "type": "comment",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "url": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "author": {
        "type": "author",
        "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
    },
    "content": "I am commenting on this post",
    "contentType": "text/plain",
    "published": "2026-03-16T10:47:57.796752Z",
    "entry": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
    "likes": {
        "type": "likes",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
    },
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331"
}
```

#### Status Codes
201 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_fqid}/commented**
> curl -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_fqid}/commented

**Description:** Retrieve a list of comments an author has made

#### Parameters
author_fqid (string): The FQID of an author.

#### Queries
page_number (int): page number of results
size (int): # of results per page

#### Example with Query Keywords
GET /api/authors/{author_fqid}/commented?page={page_number}&size={size}

#### Response Body

```
{
    "type": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Comments>
}
```

#### Example Response

```
{
    "type": "comments",
    "page_number": 1,
    "size": 5,
    "count": 1,
    "src": [
        {
            "type": "comment",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "url": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/c26d6dff-f240-40d1-9a19-60d1b464f478/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "content": "making a comment.",
            "contentType": "text/plain",
            "published": "2026-03-16T12:56:43.768883Z",
            "entry": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/",
            "likes": {
                "type": "likes",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/c26d6dff-f240-40d1-9a19-60d1b464f478/likes/",
                "page_number": 1,
                "size": 50,
                "count": 0,
                "src": []
            }
        }
    ]
}
```

#### Status Codes
200 - Success<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/commented/{comment_serial}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/commented/{comment_serial}

**Description:** Retrieve a comment an author has made

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries) *or* username of remote node of author_fqid
<example_password>: password for author (should be friend of author_serial for friends-only entries) *or* password of remote node of author_fqid


#### Parameters
author_serial (string): The UUID of an author.
entry_serial (string): The UUID of an entry.
comment_serial (string): The UUID of a comment.

#### Response Body

```
{
    "type": string
    "id": string
    "url": string
    "author": Author
    "content": string
    "contentType": string
    "published": Date
    "entry": string
    "likes": List<Like>
}
```

#### Example Response

```
{
    "type": "comment",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "url": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "author": {
        "type": "author",
        "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
    },
    "content": "I am commenting on this post",
    "contentType": "text/plain",
    "published": "2026-03-16T10:47:57.796752Z",
    "entry": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
    "likes": {
        "type": "likes",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
    },
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331"
}
```

#### Status Codes
200 - Success<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/commented/{comment_fqid}**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/commented/{comment_fqid}

**Description:** Retrieve a comment based on its fqid

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries)
<example_password>: password for author (should be friend of author_serial for friends-only entries)

#### Parameters
comment_fqid (string): The FQID of a comment.

#### Response Body

```
{
    "type": string
    "id": string
    "url": string
    "author": Author
    "content": string
    "contentType": string
    "published": Date
    "entry": string
    "likes": List<Like>
}
```

#### Example Response

```
{
    "type": "comment",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "url": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "author": {
        "type": "author",
        "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
    },
    "content": "I am commenting on this post",
    "contentType": "text/plain",
    "published": "2026-03-16T10:47:57.796752Z",
    "entry": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
    "likes": {
        "type": "likes",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
    },
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331"
}
```

#### Status Codes
200 - Success<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

## Likes API

**GET /api/authors/{author_serial}/entries/{entry_serial}/likes*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}/likes

**Description:** Retrieve a list of likes on an entry

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries) *or* username of remote node of author_fqid
<example_password>: password for author (should be friend of author_serial for friends-only entries) *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author
entry_serial (string): The UUID of an entry

#### Response Body

```
{
    "type": string
    "id": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Like>
}
```


#### Example Response

```
{
    "type": "likes",
    "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/",
    "page_number": 1,
    "size": 50,
    "count": 1,
    "src": [
        {
            "type": "like",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/5433d6c1-6f2e-413c-88bc-32224da15be5/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T15:30:10.768432Z",
            "object": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588"
        }
    ]
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_fqid}/likes*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/entries/{entry_serial}/comments/{comment_fqid}/likes

**Description:** Retrieve a list of likes on a comment

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries) *or* username of remote node of author_fqid
<example_password>: password for author (should be friend of author_serial for friends-only entries) *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author
entry_serial (string): The UUID of an entry
comment_fqid (string): The FQID of a comment

#### Response Body

```
{
    "type": string
    "id": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Like>
}
```


#### Example Response

```
{
    "type": "likes",
    "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/",
    "page_number": 1,
    "size": 50,
    "count": 1,
    "src": [
        {
            "type": "like",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/5433d6c1-6f2e-413c-88bc-32224da15be5/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T15:30:10.768432Z",
            "object": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588"
        }
    ]
}
```

#### Status Codes
200 - Success<br>
401 - Unauthorized<br>
403 - Forbidden<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

## Liked API

**GET /api/authors/{author_serial}/likes*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/likes

**Description:** Retrieve a list of all likes an author has made

#### Auth
<example_username>: username of an author *or* username of remote node of author_fqid
<example_password>: password for an author *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author

#### Response Body

```
{
    "type": string
    "id": string
    "page_number": int
    "size": int
    "count": int
    "src": List<Like>
}
```


#### Example Response

```
{
    "type": "likes",
    "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/",
    "page_number": 1,
    "size": 50,
    "count": 1,
    "src": [
        {
            "type": "like",
            "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/5433d6c1-6f2e-413c-88bc-32224da15be5/",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T15:30:10.768432Z",
            "object": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588"
        }
    ]
}
```

#### Status Codes
200 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/authors/{author_serial}/liked/{like_serial}*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/liked/{like_serial}

**Description:** Retrieve a like

#### Auth
<example_username>: username of an author *or* username of remote node of author_fqid
<example_password>: password for an author *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author
like_serial (string): The UUID of a like

#### Response Body

```
{
    "type": string
    "id": string
    "author": Author
    "published": Date
    "object": string
}
```

#### Example Response

```
{
    "type": "like",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/liked/03c9e0d5-c3f9-4b78-9858-7a07d83dca58/",
    "author": {
      "type": "author",
      "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
      "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
      "host": "http://127.0.0.1:8000/api/",
      "displayName": "NewAccount",
      "github": "https://github.com/NewAccount",
      "profileImage": "https://placehold.co/150x150.png",
      "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
      },
    "published": "2026-03-16T10:39:32.837116Z",
    "object": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e"
}
```

#### Status Codes
200 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

## Inbox API

**POST /api/authors/{author_serial}/inbox**
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/inbox

**Description:** Post an object to a remote author’s inbox

#### Auth
<example_username>: username of remote node of author_serial
<example_password>: password for remote node of author_serial

#### Parameters
author_serial (string): The UUID of an author.

#### Request Body [Entry]

```
{
    "type": string,
    "title”: string,
    "id": string,
    "web”: string,
    "description": string,
    "contentType”: string,
    "imageUrl": string,
    "author”: Author,
    "published": Date,
    "visibility”: Author,
    "likes": List<Like>,
    "comments”: List<Comment>,
}
```

#### Example Request [Entry]

```
{
            "type": "entry",
            "title": "Entry",
            "description": "Example.",
            "contentType": "text/markdown",
            "content": "This is an example entry.",
            "imageUrl": "",
            "author": {
                "type": "author",
                "serial": "d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "id": "http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "Johnson",
                "github": "https://github.com/Johnson",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/"
            },
            "published": "2026-03-16T12:45:27.099220Z",
            "visibility": "PUBLIC",
}
```

#### Request Body [Follow Request]

```
{
    "type": string,
    "summary”: string,
    "actor”: Author,
    "object”: Author
}
```

#### Example Request [Follow Request]

```
{
        "type": "follow",
        "summary": "NewAccount1 wants to follow NewAccount2",
        "actor": {
            "type": "author",
            "serial": "a1c2ddb7-f5a1-4854-a79e-b04113c33c39",
            "id": "http://127.0.0.1:8000/api/authors/da1638bc-2f5a-4ef9-9531-2d090c6eac16",
            "host": "http://127.0.0.1:8000/api",
            "displayName": "NewAccount1",
            "github": "https://github.com/NewAccount1",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/da1638bc-2f5a-4ef9-9531-2d090c6eac16/"
        },
        "object": {
            "type": "author",
            "serial": "1c910cfb-348c-407d-9ad5-f6859b74d308",
            "id": "http://127.0.0.1:8002/api/authors/1c910cfb-348c-407d-9ad5-f6859b74d308",
            "host": "http://127.0.0.1:8002/api",
            "displayName": "NewAccount2",
            "github": "https://github.com/NewAccount2",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8002/authors/1c910cfb-348c-407d-9ad5-f6859b74d308/"
        }
    }
```

#### Request Body [Like]

```
{
    "type": string
    "id": string
    "author": Author
    "published": Date
    "object": string
}
```

#### Example Request [Like]

```
{
    "type": "like",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/liked/03c9e0d5-c3f9-4b78-9858-7a07d83dca58/",
    "author": {
      "type": "author",
      "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
      "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
      "host": "http://127.0.0.1:8000/api/",
      "displayName": "NewAccount",
      "github": "https://github.com/NewAccount",
      "profileImage": "https://placehold.co/150x150.png",
      "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
      },
    "published": "2026-03-16T10:39:32.837116Z",
    "object": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e"
}
```

#### Request Body [Comment]

```
{
    "type": string
    "id": string
    "url": string
    "author": Author
    "content": string
    "contentType": string
    "published": Date
    "entry": string
    "likes": List<Like>
}
```

#### Example Request [Comment]

```
{
    "type": "comment",
    "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "url": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/",
    "author": {
        "type": "author",
        "serial": "27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/"
    },
    "content": "I am commenting on this post",
    "contentType": "text/plain",
    "published": "2026-03-16T10:47:57.796752Z",
    "entry": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/",
    "likes": {
        "type": "likes",
        "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/3aa686db-034b-4c8b-9dc2-b54ba1b3a12e/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/likes/",
        "page_number": 1,
        "size": 50,
        "count": 0,
        "src": []
    },
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331"
}
```

#### Status Codes
201 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

<br><br><br>
