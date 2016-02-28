(function() {
    'use strict';

    var context = {};

    var escape = function(text) {
        text = text.toString();
        text = text.replace('&', '&amp;');
        text = text.replace('>', '&gt;');
        text = text.replace('<', '&lt;');
        text = text.replace("'", '&#39;');
        text = text.replace('"', '&#34;');
        return text;
    };

    var lpad = function(str, len, fill) {
        str = str.toString();
        while (str.length < len) {
            str = fill + str;
        }
        return str;
    };

    var round = function(num, digits) {
        var i = Math.pow(10, digits);
        return Math.round(num * i) / i;
    };

    var xhrJsonGet = function(endpoint, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', endpoint);
        xhr.send(null);
        xhr.onload = function(event) {
            if (xhr.status == 200) {
                var jsonData = null;
                var e = null;
                try {
                    jsonData = JSON.parse(xhr.responseText);
                } catch (err) {
                    e = err;
                }

                if (jsonData != null) {
                    callback(null, jsonData);
                } else {
                    callback(e, null);
                }
            } else {
                xhr.onerror(event);
            }
        };
        xhr.onerror = function(event) {
            callback(event, null);
        };
        return xhr;
    };

    var Draggable = function(element, handleElement, scrollWithPage) {
        this.element = element;
        this.handleElement = handleElement;
        this.scrollWithPage = scrollWithPage;

        this.startDragX = 0;
        this.startDragY = 0;
        this.scrollX = 0;
        this.scrollY = 0;
        this.width = 0;
        this.height = 0;

        this.mouseDownBound = this.mouseDown.bind(this);
        this.mouseMoveBound = this.mouseMove.bind(this);
        this.mouseUpBound = this.mouseUp.bind(this);
    };

    Draggable.prototype.bind = function() {
        this.handleElement.addEventListener('mousedown', this.mouseDownBound);
    };

    Draggable.prototype.unbind = function() {
        this.handleElement.removeEventListener('mousedown', this.mouseDownBound);
    };

    Draggable.prototype.setPosition = function(x, y) {
        var minX = this.scrollX;
        var minY = this.scrollY;
        var maxX = document.documentElement.clientWidth - this.width + this.scrollX;
        var maxY = document.documentElement.clientHeight - this.height + this.scrollY;

        x = Math.max(Math.min(x, maxX), minX);
        y = Math.max(Math.min(y, maxY), minY);

        this.element.style.left = (x) + 'px';
        this.element.style.top = (y) + 'px';
    };

    Draggable.prototype.mouseDown = function(event) {
        var bb = this.element.getBoundingClientRect();
        this.startDragX = event.clientX - bb.left;
        this.startDragY = event.clientY - bb.top;
        this.width = bb.width;
        this.height = bb.height;

        document.addEventListener('mousemove', this.mouseMoveBound);
        document.addEventListener('mouseup', this.mouseUpBound);
    };

    Draggable.prototype.mouseMove = function(event) {
        if (this.scrollWithPage) {
            this.scrollX = window.pageXOffset;
            this.scrollY = window.pageYOffset;
        } else {
            this.scrollX = this.scrollY = 0;
        }

        var x = event.clientX - this.startDragX + this.scrollX;
        var y = event.clientY - this.startDragY + this.scrollY;

        this.setPosition(x, y);
    };

    Draggable.prototype.mouseUp = function(event) {
        document.removeEventListener('mousemove', this.mouseMoveBound);
        document.removeEventListener('mouseup', this.mouseUpBound);
    };

    var QR = function(watcher, draggable) {
        this.watcher = watcher;

        this.postEndpoint = context.pageDetails.postEndpoint;
        this.filePostingEnabled = !!context.pageDetails.filePostingEnabled;

        this.element = document.createElement('div');
        this.element.className = 'qr';

        this.element.innerHTML = '' +
            '    <form class="qr-form" action="' + this.postEndpoint + '" method="post" enctype="multipart/form-data">' +
            '        <span class="handle">' +
            '            <span class="handle-text">Reply</span>' +
            '            <span class="handle-close">&#x2716;</span>' +
            '        </span><br>' +
            '        <input type="text" name="name" placeholder="Name"><br>' +
            '        <input type="password" name="password" placeholder="Password (for post deletion)"><br>' +
            '        <textarea name="comment" placeholder="Comment" rows="8"></textarea><br>' +
            '        <input type="file" name="file"><input type="submit" value="Submit"/><br>' +
            '        <span class="error-message">Message</span>' +
            '        <input type="hidden" name="board" value="' + context.pageDetails.boardName + '"/>' +
            '        <input type="hidden" name="thread" value="' + context.pageDetails.threadId + '"/>' +
            '    </form>';

        document.body.appendChild(this.element);

        this.draggable = new Draggable(this.element, this.element.querySelector('.handle'), false);
        this.draggable.bind();

        this.formElement = this.element.querySelector('.qr-form');
        this.closeElement = this.element.querySelector('.handle-close');
        this.closeElement.addEventListener('click', this.onCloseClickedEvent.bind(this));

        this.nameElement = this.element.querySelector('input[name="name"]');
        this.passwordElement = this.element.querySelector('input[name="password"]');
        this.commentElement = this.element.querySelector('textarea[name="comment"]');
        this.fileElement = this.element.querySelector('input[name="file"]');
        this.fileElement.style.display = this.filePostingEnabled ? 'inline-block' : 'none';
        this.submitElement = this.element.querySelector('input[type="submit"]');
        this.errorMessageElement = this.element.querySelector('.error-message');

        this.commentElement.addEventListener('keydown', this.onCommentKeyDownEvent.bind(this));
        this.submitElement.addEventListener('click', this.onSubmitEvent.bind(this));

        this.showing = false;
        this.submitXhr = null;
    };

    QR.prototype.clear = function() {
        this.formElement.reset();
    };

    QR.prototype.addShowListener = function(element) {
        element.addEventListener('click', this.onOpenEvent.bind(this));
    };

    QR.prototype.onCommentKeyDownEvent = function(event) {
        if (event.keyCode == 27) {
            this.hide();
        }
    };

    QR.prototype.onOpenEvent = function(event) {
        event.preventDefault();
        this.show();
    };

    QR.prototype.onCloseClickedEvent = function(event) {
        event.preventDefault();
        this.hide();
    };

    QR.prototype.show = function() {
        if (!this.showing) {
            this.showing = true;

            this.element.style.display = 'inline-block';

            var bb = this.element.getBoundingClientRect();
            var x = Math.min(1000, document.documentElement.clientWidth - bb.width - 100);
            this.draggable.setPosition(x, document.documentElement.clientHeight - bb.height - 100);

            this.commentElement.focus();
        }
    };

    QR.prototype.hide = function() {
        if (this.showing) {
            this.showing = false;

            this.element.style.display = 'none';
        }
    };

    QR.prototype.addRefno = function(refno) {
        var toInsert = '>>' + refno + '\n';

        var position = this.commentElement.selectionStart;
        var value = this.commentElement.value;
        this.commentElement.value = value.substring(0, position) + toInsert + value.substring(position);
        this.commentElement.selectionStart = this.commentElement.selectionEnd = position + toInsert.length;

        this.commentElement.focus();
    };

    QR.prototype.onSubmitEvent = function(event) {
        event.preventDefault();

        this.submit();
    };

    QR.prototype.submit = function() {
        if (this.submitXhr == null) {
            var xhr = this.submitXhr = new XMLHttpRequest();
            xhr.open('POST', this.postEndpoint);
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            xhr.onerror = this.submitXhrOnErrorEvent.bind(this);
            xhr.onload = this.submitXhrOnLoadEvent.bind(this);
            xhr.upload.onprogress = this.submitXhrOnProgressEvent.bind(this);

            var formData = new FormData(this.formElement);
            xhr.send(formData);

            this.submitElement.disabled = true;
        }
    };

    QR.prototype.submitXhrOnProgressEvent = function(event) {
        this.submitElement.value = Math.round((event.loaded / event.total) * 100) + '%';
    };

    QR.prototype.submitXhrOnErrorEvent = function(event) {
        var responseData = null;
        try {
            responseData = JSON.parse(this.submitXhr.responseText);
        } catch (e) {
        }

        var responseMessage = 'Error submitting';
        if (responseData && responseData['message']) {
            responseMessage = 'Error: ' + responseData['message'];
        } else {
            if (this.submitXhr.status == 400) {
                responseMessage = 'Error: bad request';
            }
        }

        console.error('Error submitting', this.submitXhr, event);
        this.showErrorMessage(true, responseMessage);

        this.resetAfterSubmit();
    };

    QR.prototype.submitXhrOnLoadEvent = function(event) {
        if (this.submitXhr.status == 200) {
            this.showErrorMessage(false);

            this.clear();
            this.hide();

            var self = this;
            setTimeout(function() {
                self.watcher.update();
            }, 500);
        } else {
            this.submitXhrOnErrorEvent(event);
        }

        this.resetAfterSubmit();
    };

    QR.prototype.resetAfterSubmit = function() {
        this.submitElement.disabled = false;
        this.submitElement.value = 'Submit';
        this.submitXhr = null;
    };

    QR.prototype.showErrorMessage = function(show, message) {
        this.errorMessageElement.style.display = show ? 'inline-block' : 'none';
        if (show) {
            this.errorMessageElement.innerText = message;
        }
    };

    var Watcher = function(threadId, postsElement, statusElement) {
        this.threadId = threadId;
        this.postsElement = postsElement;
        this.statusElement = statusElement;

        this.xhr = null;

        this.posts = [];
    };

    Watcher.prototype.addUpdateListener = function(element) {
        element.addEventListener('click', this.onUpdateElementClickEvent.bind(this));
    };

    Watcher.prototype.setStatus = function(status) {
        this.statusElement.textContent = status;
    };

    Watcher.prototype.onUpdateElementClickEvent = function(event) {
        event.preventDefault();
        this.update();
    };

    Watcher.prototype.update = function() {
        if (this.xhr == null) {
            this.setStatus('Updating...');
            this.xhr = xhrJsonGet('/api/thread/' + this.threadId, this.xhrDone.bind(this));
        }
    };

    Watcher.prototype.xhrDone = function(error, data) {
        if (error) {
            console.error('watcher error');
        } else {
            var thread = data.thread;
            var remotePosts = thread.posts;
            for (var i = 0; i < remotePosts.length; i++) {
                var remotePost = remotePosts[i];

                var has = false;
                for (var j = 0; j < this.posts.length; j++) {
                    var post = this.posts[j];
                    if (post.id == remotePost.id) {
                        has = true;
                        break;
                    }
                }

                if (!has) {
                    this.posts.push(remotePost);
                    var postElement = this.buildPostElement(remotePost);
                    this.postsElement.lastElementChild.classList.add('divider');
                    this.postsElement.appendChild(postElement);
                }
            }
        }

        this.setStatus('');
        this.xhr = null;
    };

    Watcher.prototype.buildPostElement = function(postData) {
        var postDiv = document.createElement('div');
        postDiv.className = 'post';
        postDiv.id = 'p#' + postData.refno;

        var postHtml = '<div class="header">';

        var file = postData.file;

        if (postData.subject) {
            postHtml += '<span class="subject">' + escape(postData.subject) + '</span><br>';
        }

        postHtml += '<a href="#p' + postData.refno + '" class="refno">#' + postData.refno + '</a> ' +
            '<span class="name">' + this.getPostNameHtml(postData.name) + '</span> ' +
            '<span class="date">' + this.getPostDateText(postData.date) + '</span> ' +
            '<span class="manage"><input type="checkbox" name="post_id" value="' + postData.id + '"></span>';

        if (file) {
            postHtml += '<br>File: <a href="' + escape(file.location) + '">' + escape(file.name) + '</a> ';
            postHtml += '(' + this.getPostFileSizeText(file.size) + ') , ' + file.width + 'x' + file.height + ')';
        }

        postHtml += '</div>\n';

        if (postData.html) {
            postHtml += '<div class="styled-text">' + postData.html + '</div>';
        }

        if (file) {
            postHtml += '<a class="file-link" href="' + escape(file.location) + '">';
            postHtml += '<img src="' + escape(file.thumbnailLocation) + '" width="' + file.thumbnailWidth + '" height="' + file.thumbnailHeight + '">';
            postHtml += '</a>'
        }

        postDiv.innerHTML = postHtml;

        return postDiv;
    };

    Watcher.prototype.getPostNameHtml = function(name) {
        var html = escape(name);
        var i = html.indexOf('!');
        if (i >= 0) {
            html = html.substring(0, i) + '<span class="trip">!' + html.substring(i + 1) + '</span>';
        }
        return html;
    };

    Watcher.prototype.getPostFileSizeText = function(bytes) {
        var prefixes = ['kB', 'MB', 'GB', 'TB'];
        if (bytes == 1) {
            return '1 Byte'
        } else if (bytes < 1000) {
            return bytes + ' Bytes';
        } else {
            for (var i = 0; i < prefixes.length; i++) {
                var unit = Math.pow(1000, i + 2);
                if (bytes < unit) {
                    return round((1000 * bytes / unit), 2) + ' ' + prefixes[i];
                }
            }
        }
    };

    Watcher.prototype.getPostDateText = function(postDate) {
        var date = new Date(postDate);

        // %Y-%m-%d %H:%M:%S
        var output = date.getUTCFullYear() + '-' + lpad(date.getUTCMonth() + 1, 2, '0') + '-' + lpad(date.getUTCDate(), 2, '0') + ' ';
        output += lpad(date.getUTCHours(), 2, '0') + ':' + lpad(date.getUTCMinutes(), 2, '0') + ':' + lpad(date.getUTCSeconds(), 2, '0');
        return output;
    };

    Watcher.prototype.bindPosts = function(posts) {
        for (var i = 0; i < posts.length; i++) {
            var postElement = posts[i];

            var postObj = {};

            postObj.id = parseInt(postElement.querySelector('input[type="checkbox"]').value);
            postObj.refno = parseInt(postElement.id.substr(1));
            postObj.date = parseInt(postElement.dataset.date);

            var textElement = postElement.querySelector('.styled-text');
            if (textElement) {
                var textHtml = textElement.innerHTML.trim();
                if (textHtml) {
                    postObj.html = textHtml;
                }
            }

            var nameText = postElement.querySelector('.header .name').textContent.trim();
            if (nameText) {
                postObj.name = nameText;
            }

            var subjectElement = postElement.querySelector('.header .subject');
            if (subjectElement) {
                var subjectText = subjectElement.textContent.trim();
                if (subjectText) {
                    postObj.subject = subjectText;
                }
            }

            var fileAnchorElement = postElement.querySelector('.file-link');
            if (fileAnchorElement) {
                var imgElement = fileAnchorElement.querySelector('img');
                postObj.file = {
                    'location': fileAnchorElement.getAttribute('href'),
                    'thumbnailLocation': imgElement.src,
                    'thumbnailWidth': imgElement.width,
                    'thumbnailHeight': imgElement.height,
                    'width': fileAnchorElement.dataset.filewidth,
                    'height': fileAnchorElement.dataset.fileheight,
                    'size': fileAnchorElement.dataset.filesize,
                    'name': fileAnchorElement.dataset.filename
                }
            }

            this.posts.push(postObj);
        }
    };

    var init = function() {
        var pageDetails = window.pageDetails;
        if (!pageDetails) {
            console.error('window.pageDetails not defined');
        } else {
            context.pageDetails = pageDetails;

            var replyButtons = document.querySelector('.thread-controls');
            replyButtons.innerHTML += '[<a id="open-qr" href="#">Reply</a>] [<a id="watch-update" href="#">Update</a>] ' +
                '<span id="watch-status"></span>';

            if (!context.pageDetails.locked) {
                var postForm = document.querySelector('.post-form');
                postForm.style.display = 'none';

                var postsElement = document.querySelector('.posts');
                var watchStatusElement = replyButtons.querySelector('#watch-status');
                var watcher = new Watcher(context.pageDetails.threadId, postsElement, watchStatusElement);
                var posts = postsElement.querySelectorAll('.post');
                watcher.bindPosts(posts);
                watcher.update();

                var qr = new QR(watcher);
                qr.addShowListener(replyButtons.querySelector('#open-qr'));

                watcher.addUpdateListener(replyButtons.querySelector('#watch-update'));

                var refnos = document.querySelectorAll('a.refno');
                for (var i = 0; i < refnos.length; i++) {
                    var refno = refnos[i];
                    refno.addEventListener('click', function(event) {
                        event.preventDefault();
                        var refnoText = this.textContent;
                        var refnoNumber = parseInt(refnoText.substring(refnoText.indexOf('#') + 1).trim());
                        qr.show();
                        qr.addRefno(refnoNumber);
                    });
                }
            }
        }
    };

    init();
})();
