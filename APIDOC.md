<br><br><br>
# Overview

<p>The Wheat Social Distribution API allows for easy communication with the Wheat Social Distribution Web App. Using the Django Rest Framework, one can send and receive simple HTTP requests and responses to and from the Wheat Social Distribution Web App’s server. All of the information one needs to interact with this API can be found in the following document.</p>

# Where to Start

<p>For the time being, the Wheat Social Distribution API is only available for use locally. As such, all one must technically do in order to begin making requests towards the API is be on the local server that the target node is currently running on, and know what the hostname of the local node is. </p>

<p>However, certain requests made at specific endpoints may require signing up to successfully complete. The ability to make GET requests towards friends-only entries, as well as POST, PUT and DELETE requests are dependent upon specific user permissions, and will be denied in all cases where the user is not logged in. To sign up, one must only go to the address where their local node is currently running, press the “Sign up” button in the top right corner, and enter whatever username and password one finds appealing. This username and password can then be utilized when making requests to the API (how to achieve this is discussed below). </p>

# HTTP Requests and Responses

<p>One can interact with the Wheat Social Distribution API by making HTTP requests at specific API endpoints. This section goes over the general procedures when making requests and receiving responses with the API.</p>

## Requests

<p>There are a number of methods one can use to send an HTTP request. One of the most common methods is through CURL requests. An example of a simple GET request with CURL can be seen below.</p>

> curl -X GET http:\//127.0.0.1:8000/api/authors/8d77aa07-b5ab-4532-8367-9973d287b36e/entries/5d65a728-df4e-44b7-a7f2-653fc73f2b14/ 

<p>As mentioned previously, some HTTP requests will require login in order to be successfully carried out. To achieve this, the format in the example GET request below can be applied to any type of CURL request. </p>

> curl --user example_username:example_password -X GET http:\//127.0.0.1:8000/api/authors/8d77aa07-b5ab-4532-8367-9973d287b36e/entries/1ff24238-e302-40a9-b20c-96e6b32b23b1/

<p>There are various types of HTTP requests that one can make. For the Wheat Social Distribution API there are up to four types of API requests that can be made depending on the particular endpoint. A summary of these different types with example CURL requests can be viewed below. </p>

___
#### Request Types
| Request Type | Usage | Example Curl |
| --------------- | --------------- | --------------- |
| GET | Retrieves data from the server. For this API, data is retrieved in the form of a JSON. | curl -X GET http:\//127.0.0.1:8000/api/authors/8d77aa07-b5ab-4532-8367-9973d287b36e/entries/5d65a728-df4e-44b7-a7f2-653fc73f2b14/  |
| PUT | Modifies data in the server. For this API, sent data should be in the form of a JSON object. Correct JSON representations for specific API endpoints can be found further down. | curl --user example_username:example_password -X PUT http:\//127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/812ceb53-c4fe-4897-861c-9e672bf366f8/ -H "Content-Type: application/json" -d @/example/path.json |
| POST | Sends data to the server. For this API, sent data should be in the form of a JSON object. Correct JSON representations for specific API endpoints can be found further down. | curl --user example_username:example_password -X POST http:\//127.0.0.1:8000/api/authors/02309c0a-b28d-457d-815c-2ce5722bad13/entries/ -H "Content-Type: application/json" -d @/example/path.json |
| DELETE | Deletes data from the server. With this API, data is typically not deleted, but rather marked as “Deleted” such that it won’t ever show up in the UI, but can still technically be accessed later | curl -X DELETE /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/812ceb53-c4fe-4897-861c-9e672bf366f8/ |

___
#### Pagination

Pagination, where a request will return the **x** th page of results with **y** results per page, can be used with certain endpoints by using the format seen in the example below. One can find which endpoints do and do not support pagination further down in this documentation, in the section on API Endpoints.

> curl -X GET http:\//127.0.0.1:8000/api/authors?page=**x**&size=**y**

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

# Objects

<p>The following section goes over the numerous JSON “Objects” that represent different parts of the Wheat Social Distribution Web App. These objects are utilized when interacting with API endpoints, both as data being sent to the server, and data being received from the server. This section covers the major endpoints that are associated with each object type, the requests and responses associated with those endpoints, and the make-up of each object, providing examples for reference. </p>

___
## Author Object

Represents a single user on the Wheat Social Distribution Web App.

#### Associated Endpoint Pattern

> \<Node Address\>/api/authors/\<Author Serial\>/

#### Associated HTTP Requests and Responses

> GET returns 200, 404<br>
> PUT returns 200, 401, 403, 404<br>

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For an author object this will always be set as “author” |
| “serial” | String | A unique identifier that is associated with a single author on a particular node. |
| “id” | URL | The API endpoint associated with this particular author object. |
| “host” | URL | The url of the host node that the author exists on. |
| “displayName” | String | The author’s display name on the Wheat social distribution platform. |
| “github” | URL | The link to the author’s connected github account. |
| “profileImage” | URL | A link to the author’s chosen profile picture. |
| “web” | URL | The web link to the author’s profile page. |

#### Example of Author Object

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

___
## Entry Object

Represents a single entry on the Wheat Social Distribution Web App. Entry Objects with visibility as “Friends” can only be requested by users who are friends with the associated author. Objects listed as “Deleted” can only be requested by the Admin of the Node.

#### Associated Endpoint Pattern(s)

> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/

#### Associated HTTP Requests and Responses

> GET returns 200, 401, 404<br>
> PUT returns 200, 400, 401, 403, 404<br>
> DELETE returns 204, 401, 403 <br>

#### Object Fields

| Key | Value Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For an Entry object this will always be set as “entry” |
| “title” | String | The title of the entry as it shows up on the web app. |
| “id” | URL | The API endpoint associated with this particular entry object. |
| “web” | URL | The link to the entry’s web page. |
| “description” | String | The description of the entry as it shows up on the web app. |
| “contentType” | String | Denotes the type of content contained within the entry. Can be either “text/plain”, “text/markdown”, or “image” |
| “content” | String | The content of the entry as it shows up on the web app. |
| “imageUrl” | URL | The url for the entry’s image. Used only when the content type of the post is “image”. This field is an empty string when the content type is anything other than “image”. |
| “author” | Author Object | An Author Object which corresponds to the Author of the given Entry. See above for more information on Author Objects. |
| “published” | Date and Time | The date and time when the given Entry was published. |
| “visibility” | String | Denotes the visibility of the post to others based on the Author’s preferences while posting. Will show up as either “Public”, “Unlisted”, “Friends”, or “Deleted”. |
| “likes” | Likes Object | A Likes Object which shows a page of up to fifty likes received by the given Entry on the web app. See below for more information on Likes Objects. |
| “comments” | Comments Object | A Comments Object which shows a page of up to five comments made under the given Entry on the web app. See below for more information on Comments Objects. |

#### Example of Entry Object

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

___
## Comment Object

Represents a single comment on the Wheat Social Distribution Web App. 

#### Associated Endpoint Pattern(s)

> \<Node Address\>/api/authors/\<Author Serial\>/commented/\<Comment Serial\>/

#### Associated HTTP Requests and Responses

> GET returns 200, 403, 404

#### Object Fields

| Key | Value Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For a comment object this will always be set as “comment” |
| “id” | URL | The API endpoint associated with this particular comment object. |
| “url” | URL | The API endpoint associated with this particular comment object. |
| “author” | Author Object | An Author Object which corresponds to the Author of the given Comment. See above for more information on Author Objects. |
| “content” | String | The content of the comment as it shows up on the web app. |
| “contentType” | String | Denotes the type of content contained within the comment. Will always be “text/plain” |
| “published” | Date and Time | The date and time when the given comment was published. |
| “entry” | URL | The API endpoint associated with the entry the given comment was published under. |
| “likes” | Likes Object |  |
| “web” | URL | The link to the comment’s web page. |

#### Example of Comment Object

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
        "count": 1,
        "src": [
            {
                "type": "like",
                "id": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/liked/82bfe2c3-6f8a-451e-bfe4-16a644f39d52/",
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
                "published": "2026-03-16T10:48:15.180115Z",
                "object": "http://127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/commented/e4fd8fea-1802-4a5d-b46b-f9db21c5d331/"
            }
        ]
    },
    "web": "http://127.0.0.1:8000/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/comments/e4fd8fea-1802-4a5d-b46b-f9db21c5d331"
}
```

___
## Like Object

Represents a single like on the Wheat Social Distribution Web App.

#### Associated Endpoint Pattern(s)

> N/A

There are no endpoints that directly relate to a like object, however, there are multiple other objects that contain like objects within them that do have related endpoints.

#### Associated HTTP Requests and Responses

> N/A

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For a like object this will always be set as “like”. |
| “id” | URL | The API endpoint associated with this particular like object. |
| “author” | Author Object | An Author Object which corresponds to the Author who gave out the like. See above for more information on Author Objects. |
| “published” | Date and Time | The date and time when the like was given. |
| “object” | URL | The id of the associated object the like was given to. Will be either an entry or comment. |

#### Example of Like Object

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

___
## Authors Object

Represents a set of Authors on the Wheat Social Distribution Web App. 

#### Associated Endpoint Pattern(s)

> \<Node Address\>/api/authors

#### Associated HTTP Requests and Responses

> GET returns 200

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For an authors object this will always be set as “authors”. |
| “authors” | Array | JSON array of Author Objects. |

#### Example of Authors Object

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

___
## Following Object

Represents a set of Authors who are followed by another specified author on the Wheat Social Distribution Web App. 

#### Associated Endpoint Pattern(s)

> \<Node Address\>/api/authors/\<Author Serial\>/following

#### Associated HTTP Requests and Responses

> GET returns 200, 401, 403, 404

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For a following object this will always be set as “following”. |
| “following” | Array | JSON array of Author Objects. Each author in this array is one who is followed by the author who was associated with the request. |

#### Example of Following Object

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

___
## Entries Object

Represents a set of Entries on the Wheat Social Distribution Web App. 

#### Associated Endpoint Pattern(s)

> \<Node Address\>/api/authors/\<Author Serial\>/entries/

#### Associated HTTP Requests and Responses

> GET returns 200, 404<br>
> POST returns 201, 400, 401, 403, 404<br>

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For an entries object this will always be set as “entries”. |
| “page_number” | Integer | The page number corresponding to the associated entries. |
| “size” | Integer | The number of entry objects contained within the entries object, as well as the number per page in respect to the page number. |
| “count” | Integer | The total number of entries under the given author. |
| “src” | Array | JSON array of Entry Objects. |

#### Example of Entries Object

```
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
```

___
## Comments Object

Represents a set of Entries on the Wheat Social Distribution Web App. 

#### Associated Endpoint Pattern(s)

I.<br>
> \<Node Address\>/api/authors/\<Author Serial\>/commented/

II.<br>
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/comments/

#### Associated HTTP Requests and Responses

I.<br>
> GET returns 200, 404<br>
> POST returns 201, 400, 401, 403, 404<br>

II.<br>
> GET returns 200, 403, 404

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For a comments object this will always be set as “comments”. |
| “page_number” | Integer | The page number corresponding to the associated comments |
| “size” | Integer | The number of comment objects contained within the comments object, as well as the number per page in respect to the page number. |
| “count” | Integer | The total number of comments under the given entry. |
| “src” | Array | JSON array of Comment Objects. |

#### Example of Comments Object

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

___
## Likes Object

Represents a set of Likes on the Wheat Social Distribution Web App. 

#### Associated Endpoint Pattern(s)

I.<br>
> \<Node Address\>/api/authors/\<Author Serial\>/liked/

II.<br>
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/likes/

III.<br>
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/comments/\<Comment Serial\>/likes/

#### Associated HTTP Requests and Responses

I.<br>
> GET returns 200, 404<br>
> POST returns 200, 201, 400, 401, 403, 404<br>

II.<br>
> GET returns 200, 401, 403, 404

III.<br>
> GET returns 200, 401, 403, 404

#### Object Fields

| Key | Field Type | Meaning |
| --------------- | --------------- | --------------- |
| “type” | String | Denotes the type of object. For a comments object this will always be set as “likes”. |
| “id” | URL | The API endpoint associated with this particular likes object. |
| “page_number” | Integer | The page number corresponding to the associated likes |
| “size” | Integer | The number of like objects contained within the likes object, as well as the number per page in respect to the page number. |
| “count” | Integer | The total number of likes under the given entry. |
| “src” | Array | JSON array of Like Objects. |

#### Example of Likes Object

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

# API Endpoints

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

> curl -X GET http:\//127.0.0.1:8000/api/authors

> **RETURNS “Authors Object” with Code=200**

Possible Error Codes: <br>NONE

___
## Author API - Retrieve an author. Edit information about an author through the API

___
#### Endpoint Pattern

> \<Node Address\>/api/authors/\<Author Serial\>/

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/

> **RETURNS “Author Object” with Code=200**

Possible Error Codes: <br>404 [Occurs if Author Serial does not exist in database]

___
#### PUT Request with curl

> curl --user example_username:example_password -X PUT http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/ -H "Content-Type: application/json" -d @/example/path/exampleFile.json

> **EDITS Author in database with Code=200**

Edits the Author with the corresponding serial in the database according to the “Author Object” contained in “exampleFile.json”. If successful returns Code=200

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to edit an author they do not have permission to], <br>404 [Occurs if Author Serial does not exist in database]

___
## Entries API - Retrieve a list of entries created by an author. Create a new entry through the API

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/

Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/

> **RETURNS “Entries Object” with Code=200**

Possible Error Codes: <br>404 [Occurs if Author Serial does not exist in database]

___
#### POST Request with curl

> curl --user example_username:example_password -X POST http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/ -H "Content-Type: application/json" -d @/example/path/exampleFile.json

> **CREATES Entry in database with Code=201**

Creates a new Entry in the database under the Author with the corresponding serial according to the “Entry Object” contained in “exampleFile.json”. If successful returns Code=201

Possible Error Codes: <br>400 [Occurs if the contentType is listed as “Image” but no ImageUrl is provided], <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to post an entry for an author they do not have permission to], <br>404 [Occurs if Author Serial does not exist in database]

___
## Entry API - Retrieve an entry. Edit an entry. Delete an entry.

___
#### Endpoint Pattern

> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/

___
#### GET Request with curl

> curl -X GET http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/

> **RETURNS “Entry Object” with Code=200**

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>404 [Occurs if Author Serial does not exist in database]

___
#### PUT Request with curl

> curl --user example_username:example_password -X PUT http://127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/ -H "Content-Type: application/json" -d @/example/path/exampleFile.json

> **EDITS Entry in database with Code=200**

Edits the Entry with the corresponding serial in the database according to the “Entry Object” contained in “exampleFile.json”. If successful returns Code=200

Possible Error Codes: <br>400 [Occurs if the contentType is listed as “Image” but no ImageUrl is provided], <br>401 [Occurs if user has not logged in], <br> 403 [Occurs if user attempts to edit an entry for an author they do not have permission to], <br> 404 [Occurs if Entry does not exist in database]

___
#### DELETE Request with curl

> curl -X DELETE http:\//127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/07f29235-2621-4f59-89dc-70c2f2cee588/

> **DELETES “Entry Object” with Code=204**

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to delete an entry for an author they do not have permission to]

___
## Follow Requests API - Get a list of follow requests for an author

___
#### Endpoint Pattern

> \<Node Address\>/api/authors/\<Author Serial\>/follow_requests
___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/follow_requests

> **RETURNS JSON Array of “Author Objects” with Code=200**

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to view follow requests of an author they do not have permission to], <br>404 [Occurs if Author Serial does not exist in database]

___
## Following API - Get the list of people an author is following

___
#### Endpoint Pattern

> \<Node Address\>/api/authors/\<Author Serial\>/following

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/following

> **RETURNS “Following Object” with Code=200**

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to view following list of an author they do not have permission to], <br>404 [Occurs if Author Serial does not exist in database]

___
## Commented API - Get a list of an author’s comments. Post a comment through the API.

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/commented/

Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/commented/?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/

> **RETURNS “Comments Object” with Code=200**

Possible Error Codes: <br>404 [Occurs if Author Serial does not exist in database]

___
#### POST Request with curl

> curl --user example_username:example_password -X POST http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/ -H "Content-Type: application/json" -d @/example/path/exampleFile.json

> **CREATES Comment in database with Code=201**

Creates a new Comment in the database under the Author with the corresponding serial according to the “Comment Object” contained in “exampleFile.json”. If successful returns Code=201

Possible Error Codes: <br>400 [Occurs if syntax is incorrect for provided Comment Object], <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to post a comment for an author they do not have permission to], <br>404 [Occurs if Author Serial does not exist in database]

___
## Comments API - Get a list of comments an author has made

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/comments/

Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/comments/?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/comments/

> **RETURNS “Comments Object” with Code=200**

Possible Error Codes: <br>403 [Occurs if user attempts to access comments for an entry they do not have permission to access], <br>404 [Occurs if Entry Serial does not exist in database]

___
## Comment API - Get a comment an author has made

___
#### Endpoint Pattern

> \<Node Address\>/api/authors/\<Author Serial\>/commented/\<Comment Serial\>/

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/commented/d379a3ed-734e-4419-b86f-3ba27af4d7d7

> **RETURNS “Comment Object” with Code=200**

Possible Error Codes: <br>403 [Occurs if user attempts to access a comment for an entry they do not have permission to access], <br>404 [Occurs if either Author or Comment Serial does not exist in database]

___
## Liked API - Get a list of an author’s liked entries/comments. Create new likes under entries/comments

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/liked/

Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/liked/?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/

> **RETURNS “Likes Object” with Code=200**

Possible Error Codes: <br>404 [Occurs if Author Serial does not exist in database]

___
#### POST Request with curl

> curl --user example_username:example_password -X POST http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/liked/ -H "Content-Type: application/json" -d @/example/path/exampleFile.json

> **CREATES Like in database with Code=201**

Creates a new Like in the database under the Author with the corresponding serial according to the “Like Object” contained in “exampleFile.json”. If successful, returns Code=201. If the author already has a like object for the given entry or comment, returns Code=200.

Possible Error Codes: <br>400 [Occurs if syntax is incorrect for provided Like Object], <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to make another author like an entry or comment], <br>404 [Occurs if Author Serial does not exist in database]

___
## Entry Likes API - Get the list of likes on an entry

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/likes/

Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/likes/?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/d379a3ed-734e-4419-b86f-3ba27af4d7d7/entries/07f29235-2621-4f59-89dc-70c2f2cee588/likes/

> **RETURNS “Likes Object” with Code=200**

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to make another author like an entry], <br>404 [Occurs if Author Serial does not exist in database]

___
## Comment Likes API - Get the List of Likes on a Comment

___
#### Endpoint Pattern

Non-Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/comments/\<Comment Serial\>/likes/

Paginated:
> \<Node Address\>/api/authors/\<Author Serial\>/entries/\<Entry Serial\>/comments/\<Comment Serial\>/likes/?page=\<Page Number\>&size=\<Results Per Page\>

___
#### GET Request with curl

> curl -X GET http:\//127.0.0.1:8000/api/authors/27e2ab6f-93f3-4680-8686-ce5f869ed3fb/entries/46704e66-a196-4536-919b-a736d55c7b61/comments/0db3fdc6-06fd-4afe-a39a-ca7c42dd3d1a/likes/

> **RETURNS “Likes Object” with Code=200**

Possible Error Codes: <br>401 [Occurs if user has not logged in], <br>403 [Occurs if user attempts to make another author like a comment], <br>404 [Occurs if Author Serial does not exist in database]

___
<br><br><br>
