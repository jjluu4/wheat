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

function postUnlike(userSerial, objectUrl, csrfToken) {
    const localObjectUrl = toSameNodeApiPath(objectUrl);
    const str = objectUrl != null ? String(objectUrl) : '';
    const objectForBody =
        localObjectUrl != null
            ? localObjectUrl
            : /^https?:\/\//i.test(str)
              ? str
              : null;
    if (!objectForBody) {
        return Promise.reject(new Error('Rejected cross-node or non-api unlike target'));
    }

    return fetch(`/api/authors/${userSerial}/liked/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'unlike',
            object: objectForBody,
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

function postLike(userSerial, objectUrl, csrfToken) {
    const localObjectUrl = toSameNodeApiPath(objectUrl);
    const str = objectUrl != null ? String(objectUrl) : '';
    const objectForBody =
        localObjectUrl != null
            ? localObjectUrl
            : /^https?:\/\//i.test(str)
              ? str
              : null;
    if (!objectForBody) {
        return Promise.reject(new Error('Rejected cross-node or non-api like target'));
    }

    return fetch(`/api/authors/${userSerial}/liked/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': csrfToken,
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'like',
            object: objectForBody,
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

function toSameNodeApiPath(value) {
    if (!value) return value;
    const str = String(value);
    if (str.startsWith("/api/")) return str;

    try {
        const url = new URL(str, window.location.origin);
        if (url.origin !== window.location.origin) return null;
        if (!url.pathname.startsWith('/api/')) return null;
        return `${url.pathname}${url.search}${url.hash}`;
    } catch (_) {
        return null;
    }
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

    const button = entryNode.querySelector('.entry-like-button');
    const objectUrl = `/api/authors/${entryNode.dataset.author}/entries/${entrySerial}/`;
    const csrf = getCsrfToken(entryNode);
    const liked = button && button.dataset.liked === '1';
    const pending = button && button.dataset.pending === '1';

    if (!button || pending) return;

    button.dataset.pending = '1';
    button.disabled = true;

    const req = liked ? postUnlike(userSerial, objectUrl, csrf) : postLike(userSerial, objectUrl, csrf);
    req.then(({ response, data }) => {
            if (response.ok) {
                if (liked) {
                    button.textContent = 'Like';
                    button.dataset.liked = '0';
                } else {
                    button.textContent = 'Liked';
                    button.dataset.liked = '1';
                }
                refreshEntryLikeCount(entrySerial);
                return;
            }
            console.error('Entry like/unlike failed', response.status, data);
        })
        .catch((error) => {
            console.error('Entry like/unlike failed', error);
        })
        .finally(() => {
            button.dataset.pending = '0';
            button.disabled = false;
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
    const form = event.target;
    const formData = new FormData(form);
    const entryNode = form.closest('li');
    const auxiliaryButtons = Array.from(form.querySelectorAll('button[type="button"]'));

    if (window.beginPendingForm && !window.beginPendingForm(form)) return;
    auxiliaryButtons.forEach((button) => {
        if (button.disabled) return;
        button.dataset.pendingDisabledByComment = '1';
        button.disabled = true;
    });

    fetch(`/api/authors/${entryNode.dataset.user}/commented/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': formData.get('csrfmiddlewaretoken'),
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            type: 'comment',
            entry: entryNode.dataset.entryUrl,
            content: formData.get('content')
        })
    })
        .then(async (response) => {
            let data = {};
            try {
                data = await response.json();
            } catch (_) {
                data = {};
            }
            return { response, data };
        })
        .then(({ response, data }) => {
            if (!response.ok) {
                console.error('Comment submit failed', response.status, data);
                return;
            }

            form.reset();
            form.style.display = 'none';
            const commentsList = document.querySelector(`li[data-entry="${entryNode.dataset.entry}"] .comments`);
            if (commentsList.style.display === 'none') {
                toggleComments(entryNode.dataset.entry);
            } else {
                loadComments(entryNode.dataset.entry);
            }
        })
        .catch((error) => {
            console.error('Comment submit failed', error);
        })
        .finally(() => {
            auxiliaryButtons.forEach((button) => {
                if (button.dataset.pendingDisabledByComment === '1') {
                    button.disabled = false;
                    delete button.dataset.pendingDisabledByComment;
                }
            });
            if (window.endPendingForm) window.endPendingForm(form);
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
                    const viewerHasLiked = comment.likes?.viewer_has_liked === true;
                    likeButton.textContent = viewerHasLiked ? 'Liked' : 'Like';
                    likeButton.dataset.liked = viewerHasLiked ? '1' : '0';
                    likeButton.dataset.pending = '0';
                    const commentObjectUrl = comment.id || comment.url;
                    likeButton.onclick = () => {
                        if (likeButton.dataset.pending === '1') return;

                        const liked = likeButton.dataset.liked === '1';
                        const fn = liked ? postUnlike : postLike;
                        likeButton.dataset.pending = '1';
                        likeButton.disabled = true;

                        fn(currentUserSerial, commentObjectUrl, getCsrfToken(entryNode))
                            .then(({ response, data }) => {
                                if (response.ok) {
                                    loadComments(entrySerial, page);
                                    return;
                                }
                                console.error('Comment like failed', response.status, data);
                            })
                            .catch((error) => {
                                console.error('Comment like failed', error);
                            })
                            .finally(() => {
                                likeButton.dataset.pending = '0';
                                likeButton.disabled = false;
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
