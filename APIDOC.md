# Endpoints

## Author API

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

/api/entries/{ENTRY_FQID}/likes
**GET /api/entries/{entry_fqid}/likes*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/entries/{entry_fqid}/likes

**Description:** Retrieve a list of likes on an entry with an fqid

#### Auth
<example_username>: username of author (should be friend of author_serial for friends-only entries)
<example_password>: password for author (should be friend of author_serial for friends-only entries)

#### Parameters
entry_fqid (string): The FQID of an entry

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

**GET /api/authors/{author_serial}/liked*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/liked

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

**POST /api/authors/{author_serial}/liked*
> curl --user <example_username>:<example_password> -X POST http<nolink>:\//127.0.0.1:8000/api/authors/{author_serial}/liked

**Description:** Post a like to an author’s profile

#### Auth
<example_username>: username of author connected to author_serial *or* username of remote node of author_fqid
<example_password>: password for an author connected to author_serial *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author

#### Request Body

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
201 - Success<br>
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

**GET /api/authors/{author_fqid}/liked*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/authors/{author_fqid}/liked

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

**POST /api/authors/{author_fqid}/liked*
> curl --user <example_username>:<example_password> -X POST http<nolink>:\//127.0.0.1:8000/api/authors/{author_fqid}/liked

**Description:** Post a like to an author’s profile with their fqid

#### Auth
<example_username>: username of author connected to author_serial *or* username of remote node of author_fqid
<example_password>: password for an author connected to author_serial *or* password of remote node of author_fqid

#### Parameters
author_serial (string): The UUID of an author

#### Request Body

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
201 - Success<br>
400 - Invalid Request<br>
401 - Unauthorized<br>
403 - Forbidden Access<br>
404 - Object Does Not Exist<br>
500 - Internal Server Error<br>

**GET /api/liked/{like_fqid}*
> curl --user <example_username>:<example_password> -X GET http<nolink>:\//127.0.0.1:8000/api/liked/{like_fqid}

**Description:** Retrieve a like with its fqid

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
