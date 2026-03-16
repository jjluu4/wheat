function getEntryNode(entrySerial) {
    return document.querySelector(`li[data-entry="${entrySerial}"]`);
}

function getCurrentUserSerial(entryNode) {
    return entryNode?.dataset.user || '';
}

function getCsrfToken(entryNode) {
    return (
        entryNode?.querySelector('[name=csrfmiddlewaretoken]')?.value ||
        document.querySelector('[name=csrfmiddlewaretoken]')?.value ||
        ''
    );
}

function updateEntryLikeCount(entryNode, count) {
    const likeCount = entryNode?.querySelector('.like-count');
    if (!likeCount) return;
    likeCount.textContent = `${count} like${count === 1 ? '' : 's'}`;
}

function postLike(userSerial, objectUrl, csrfToken) {
    return fetch(`/api/authors/${userSerial}/liked/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'like',
            object: objectUrl,
        }),
    }).then(async (response) => {
        let data = {};
        try {
            data = await response.json();
        } catch (_) {
            data = {};
        }
        return { response, data };
    });
}

function refreshEntryLikeCount(entrySerial) {
    const entryNode = getEntryNode(entrySerial);
    if (!entryNode) return;

    fetch(`/api/authors/${entryNode.dataset.author}/entries/${entrySerial}/likes/?page=1&size=1`)
        .then((response) => {
            if (!response.ok) throw new Error(`Failed to fetch entry likes (${response.status})`);
            return response.json();
        })
        .then((data) => {
            updateEntryLikeCount(entryNode, data.count || 0);
        })
        .catch((error) => console.error(error));
}

function toggleLike(entrySerial) {
    const entryNode = getEntryNode(entrySerial);
    if (!entryNode) return;

    const userSerial = getCurrentUserSerial(entryNode);
    if (!userSerial) return;

    const objectUrl = `${window.location.origin}/api/authors/${entryNode.dataset.author}/entries/${entrySerial}/`;
    postLike(userSerial, objectUrl, getCsrfToken(entryNode))
        .then(({ response, data }) => {
            if (response.ok) {
                const button = entryNode.querySelector('.entry-like-button');
                if (button) {
                    button.textContent = 'Liked';
                }
                refreshEntryLikeCount(entrySerial);
                return;
            }
            console.error('Entry like failed', response.status, data);
        })
        .catch((error) => {
            console.error('Entry like failed', error);
        });
}

function toggleCommentForm(entrySerial) {
    const form=document.querySelector(`li[data-entry="${entrySerial}"] form`);
    form.style.display=form.style.display==='none'?'flex':'none';
}

function toggleComments(entrySerial) {
    const commentsList = document.querySelector(`li[data-entry="${entrySerial}"] .comments`);

    if (commentsList.style.display==='none') {
        commentsList.style.display='flex';
        loadComments(entrySerial, 1);
    } else {
        commentsList.style.display='none';
    }
}

function submitComment(event) {
    event.preventDefault();
    const form=event.target;
    const formData=new FormData(form);

    //grab author and entry serials to construct the entryURL
    const entrySerial=form.closest('li').dataset.entry;
    const authorSerial=form.closest('li').querySelector('.profile-link').href.split('/').filter(part=>part!=='').pop();
    
    fetch(`/api/authors/${form.dataset.userSerial}/commented/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'comment',
            entry: `${window.location.origin}/api/authors/${authorSerial}/entries/${entrySerial}/`,
            content: formData.get('content')
        })

    }).then(() => {
        form.reset();
        form.style.display='none';
        const commentsList=document.querySelector(`li[data-entry="${entrySerial}"] .comments`);
        if(commentsList.style.display==='none')
            toggleComments(entrySerial);
        else
            loadComments(entrySerial);
    });
}

function loadComments(entrySerial, page=1) {
    const commentsList=document.querySelector(`li[data-entry="${entrySerial}"] .comments`);
    const entryNode = getEntryNode(entrySerial);
    const authorSerial=entryNode.dataset.author;
    const currentUserSerial = getCurrentUserSerial(entryNode);

    fetch(`/api/authors/${authorSerial}/entries/${entrySerial}/comments/?page=${page}&size=10`)
    .then(response => {
        if (!response.ok) throw new Error(`Failed to load comments (${response.status})`);
        return response.json();
    })
    .then(data => {
        commentsList.innerHTML='';

        if (data.src && data.src.length > 0) {
            data.src.forEach(comment => {
                const commentItem=document.createElement('li');
                commentItem.className='comment-item';

                const header=document.createElement('div');
                header.className='space-between';

                    const profile=document.createElement('a');
                    profile.className='profile-link';
                    profile.style.marginTop='0';
                    profile.href=`/authors/${encodeURIComponent(comment.author.serial)}/`;
                    profile.textContent=comment.author.displayName;

                    const date=document.createElement('div');
                    date.className='small';
                    const dateStrong=document.createElement('strong');
                    dateStrong.textContent=new Date(comment.published).toLocaleString();
                    date.appendChild(dateStrong);

                header.appendChild(profile);
                header.appendChild(date);

                const content = document.createElement('div');
                content.className = 'content markdown-source';
                content.style.margin = 0;
                content.textContent = comment.content || '';

                const actions = document.createElement('div');
                actions.className = 'small';

                const likeCount = document.createElement('span');
                const count = comment.likes?.count || 0;
                likeCount.textContent = `${count} like${count === 1 ? '' : 's'}`;
                actions.appendChild(likeCount);

                if (currentUserSerial && (comment.id || comment.url)) {
                    const likeButton = document.createElement('button');
                    likeButton.type = 'button';
                    likeButton.textContent = 'Like';
                    likeButton.onclick = () => {
                        postLike(currentUserSerial, comment.id || comment.url, getCsrfToken(entryNode))
                            .then(({ response, data }) => {
                                if (response.ok) {
                                    loadComments(entrySerial, page);
                                    return;
                                }
                                console.error('Comment like failed', response.status, data);
                            });
                    };
                    actions.appendChild(document.createTextNode(' '));
                    actions.appendChild(likeButton);
                }

                commentItem.appendChild(header);
                commentItem.appendChild(content);
                commentItem.appendChild(actions);
                commentsList.appendChild(commentItem);
            });
        } else {
            commentsList.innerHTML = '<li class="no-comments">No comments yet.</li>';
        }

        // Re-run markdown rendering for newly injected comment content
        if (typeof window.renderMarkdownContent === 'function') {
            window.renderMarkdownContent();
        }
    })
    .catch((error) => {
        console.error(error);
        commentsList.innerHTML = '<li class="no-comments">Unable to load comments.</li>';
    });
}
