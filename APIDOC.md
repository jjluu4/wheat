**API Documentation**

**---------- Authors API ----------**

~ GET api/authors

~~ GET: retrieves a json formatted list of all the authors in the database. Can be paginated by setting page and size variables as shown in the example below.

**EXAMPLES:**<br>
***Request:***<br>
GET /api/authors

***Response:***<br>
Code=200
````
{
    "type": "authors",
    "authors": [
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount",
            "github": "https://github.com/NewAccount",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
        },
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount2",
            "github": "https://github.com/NewAccount2",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/"
        }
    ]
}
````

[Returns all authors]

***Request:***<br>
GET /api/authors?page=2&size=1

***Response:***<br>
Code=200
````
{
    "type": "authors",
    "authors": [
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount2",
            "github": "https://github.com/NewAccount2",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/"
        }
    ]
}
````

[Can also be paginated. This returns the second page of size 1 from two total authors]<br><br><br>

**---------- Single Author API ----------**

~ GET/PUT api/authors/<uuid:author_serial>/

~~ GET: Retrieves a JSON formatted Author object according to the required author_serial. Returns a 404 if the relevant author does not exist.

~~ PUT: Edits the Author object corresponding to the required author_serial. Taken in with a JSON format which can contain fields for 'displayName', 'github', and 'profileImage'. Will update each of them accordingly. None of these fields are required. Returns a 401 if the user is not logged in, and a 403 if they are attempting to update a profile other than their own.

**EXAMPLES:**<br>
***Request:***<br>
GET /api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/

***Response:***<br>
Code=200
````
{
    "type": "author",
    "id": "http://127.0.0.1:8000/api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c",
    "host": "http://127.0.0.1:8000/api/",
    "displayName": "NewAccount2",
    "github": "https://github.com/NewAccount2",
    "profileImage": "https://placehold.co/150x150.png",
    "web": "http://127.0.0.1:8000/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/"
}
````

***Request:***<br>
PUT /api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/
````
{
    "displayName": "NewAccount2Edited"
}
````


***Response:***<br>
Code=200

[Successfully updated the display name of the corresponding author from “NewAccount2” to “NewAccount2Edited”]<br><br><br>

**---------- Following API ----------**

~ GET api/authors/<uuid:author_serial>/following

~~ GET: Retrieves in JSON formatting a list of all people the user is following corresponding to the required author_serial. Returns a 401 if the user is not logged in and a 403 if the user tries to access another user’s following list.

**EXAMPLES:**<br>
***Request:***<br>
GET /api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/following
````
***Response:***<br>
Code=200
{
    "type": "following",
    "following": [
        {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount",
            "github": "https://github.com/NewAccount",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
        }
    ]
}
````

[Logged in as author “f3c61a63-31ba-4129-b0a4-a85f37ae483c”]

***Request:***<br>
GET /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/following

***Response:***<br>
Code=403
"You don't have permission to view this following list."

[Logged in as author “f3c61a63-31ba-4129-b0a4-a85f37ae483c”. Cannot see other user’s following list]<br><br><br>

**---------- Follow Requests API ----------**

~ GET api/authors/<uuid:author_serial>/follow_requests

~~ GET: Retrieves in JSON formatting a list of all follow_requests for the user corresponding to the required author_serial. Returns a 401 if the user is not logged in and a 403 if the user tries to access another user’s follow requests.

**EXAMPLES:**<br>
***Request:***<br>
GET /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/follow_requests

***Response:***<br>
Code=200
````
[
    {
        "type": "follow",
        "summary": "NewAccount2Edited wants to follow NewAccount",
        "actor": {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount2Edited",
            "github": "https://github.com/NewAccount2",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/"
        },
        "object": {
            "type": "author",
            "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
            "host": "http://127.0.0.1:8000/api/",
            "displayName": "NewAccount",
            "github": "https://github.com/NewAccount",
            "profileImage": "https://placehold.co/150x150.png",
            "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
        }
    }
]
````

[Logged in as author “c6ede70c-0130-4b20-951c-d9bb8ad5a24e”]

***Request:***<br>
GET /api/authors/f3c61a63-31ba-4129-b0a4-a85f37ae483c/follow_requests

***Response:***<br>
Code=403
"You don't have permission to view these follow requests."

[Logged in as author “c6ede70c-0130-4b20-951c-d9bb8ad5a24e”. User cannot access the follow requests of another user]<br><br><br>

**---------- Entries API 1 ----------**

~ GET/POST /api/authors/<uuid:author_serial>/entries/ 

~~ GET: Retrieves a JSON representation of a list of entry objects created by the required author_serial. Can be paginated as seen below. Will show all entries based on the user’s relation to the author (friends/following/unaffiliated correspond to friends/unlisted/public). Will not show deleted posts. Will return a 401 if not logged in and a 404 if the requested author does not exist.

~~ POST: Creates a new entry based on the JSON object passed in under the author that exists with the required author_serial. Creates a new entry_serial and id for the new entry and fills in ‘content’, ‘content_type’, and ‘visibility with the values passed in from the JSON object. Will return a 403 if the user attempts to POST to an author other than themselves.

**EXAMPLES:**<br>
***Request:***<br>
GET /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/?page=2&size=2

***Response:***<br>
Code=200
````
{
    "type": "entries",
    "entries": [
        {
            "type": "entry",
            "title": "Title",
            "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/73852c06-cb9f-4205-8c60-b1a0c1bc6112",
            "web": "Web",
            "description": "Desc",
            "content_type": "text/plain",
            "content": "Content of the post.",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "NewAccount",
                "github": "https://github.com/NewAccount",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
            },
            "published": "2026-03-02T19:53:23.003883Z",
            "visibility": "PUBLIC"
        }
    ]
}
````

[Returns the “second page” of posts when there are three total posts]

***Request:***<br>
POST /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/
````
{
            "type": "entry",
            "title": "Title",
            "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/1",
            "web": "Web",
            "description": "Desc",
            "content_type": "text/plain",
            "content": "Content of the post.",
            "author": {
                "type": "author",
                "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
                "host": "http://127.0.0.1:8000/api/",
                "displayName": "NewAccount",
                "github": "https://github.com/NewAccount",
                "profileImage": "https://placehold.co/150x150.png",
                "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
            },
            "visibility": "PUBLIC"
        }
````

***Response:***<br>
Code=201<br><br><br>

**---------- Entries API 2 ----------**

~ GET/PUT/DELETE /api/authors/<uuid:author_serial>/entries/<uuid:entry_serial>/

~~ GET: Retrieves a JSON representation of an Entry object according to the required author_serial and entry_serial. Will only allow access to those with the correct permissions (friends/unlisted/public accordingly).

~~ PUT: Edits the Entry object corresponding to the required author_serial and entry_serial. Taken in with a JSON format which can contain fields for 'content', 'content_type', 'image_url', and 'visibility’. Will update each of them accordingly. None of these fields are required. A person can only access their own entries to edit.

~~ DELETE: Deletes the Entry object associated with the required author_serial and entry_serial. Only one’s own entries can be deleted, unless you are an admin.

**EXAMPLES:**<br>
***Request:***<br>
GET
/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/812ceb53-c4fe-4897-861c-9e672bf366f8/

***Response:***<br>
Code=200
````
{
    "type": "entry",
    "title": "Title",
    "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/0307d68b-a708-43aa-83d9-bda88577707a",
    "web": "Web",
    "description": "Desc",
    "content_type": "text/plain",
    "content": "test entry",
    "author": {
        "type": "author",
        "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
    },
    "published": "2026-03-02T17:40:25.624080Z",
    "visibility": "PUBLIC"
}
````

***Request:***<br>
DELETE /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/812ceb53-c4fe-4897-861c-9e672bf366f8/

***Response:***<br>
Code=204
````
{
    "deleted": "Entry has been deleted."
}
````

***Request:***<br>
PUT /api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/a9510b91-6a7b-4ecc-a2ac-fe6e76dca9e8/
````
{
    "content_type": "text/plain",
    "content": "new content",
    "visibility": "FRIENDS"
}
````

***Response:***<br>
Code=200
````
{
    "type": "entry",
    "title": "Title",
    "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/entries/a9510b91-6a7b-4ecc-a2ac-fe6e76dca9e8",
    "web": "Web",
    "description": "Desc",
    "content_type": "text/plain",
    "content": "new content",
    "author": {
        "type": "author",
        "id": "http://127.0.0.1:8000/api/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e",
        "host": "http://127.0.0.1:8000/api/",
        "displayName": "NewAccount",
        "github": "https://github.com/NewAccount",
        "profileImage": "https://placehold.co/150x150.png",
        "web": "http://127.0.0.1:8000/authors/c6ede70c-0130-4b20-951c-d9bb8ad5a24e/"
    },
    "published": "2026-03-02T18:46:05.453077Z",
    "visibility": "FRIENDS"
}
````

[Successfully changes the visibility of the post from “PUBLIC” to “FRIENDS” as well as editing the content.]