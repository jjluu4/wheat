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
    const authorSerial=document.querySelector(`li[data-entry="${entrySerial}"] .profile-link`).href.split('/').filter(part=>part!=='').pop();

    fetch(`/api/authors/${authorSerial}/entries/${entrySerial}/comments/?page=${page}&size=10`)
    .then(response => response.json())
    .then(data => {
        commentsList.innerHTML = '';

        if (data.src && data.src.length > 0) {
            data.src.forEach(comment => {
                const commentItem = document.createElement('li');
                commentItem.className = 'comment-item';
                commentItem.innerHTML = `
                    <div class="space-between">
                        <a class="profile-link" style="margin-top: 0;" href="/authors/${comment.author.serial}/">${comment.author.displayName}</a>
                        <div class="small"><strong>${new Date(comment.published).toLocaleString()}</strong></div>
                    </div>
                    ${comment.content}
                `; //TODO: SECURITY BAD, LIKE SERIOUSLY THIS COULD NOT BE WORSE
                commentsList.appendChild(commentItem);
            });
        } else commentsList.innerHTML='<li class="no-comments">No comments yet.</li>';
    });
}