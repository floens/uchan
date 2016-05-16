var uchan;
(function (uchan) {
    var Draggable = (function () {
        function Draggable(element, handleElement, scrollWithPage) {
            this.touchId = -1;
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
            this.touchStartBound = this.touchStart.bind(this);
            this.touchEndBound = this.touchEnd.bind(this);
            this.touchCancelBound = this.touchCancel.bind(this);
            this.touchMoveBound = this.touchMove.bind(this);
        }
        Draggable.prototype.bind = function () {
            this.handleElement.addEventListener('mousedown', this.mouseDownBound);
            this.handleElement.addEventListener('touchstart', this.touchStartBound);
            this.handleElement.addEventListener('touchend', this.touchEndBound);
            this.handleElement.addEventListener('touchcancel', this.touchCancelBound);
            this.handleElement.addEventListener('touchmove', this.touchMoveBound);
        };
        Draggable.prototype.unbind = function () {
            this.handleElement.removeEventListener('mousedown', this.mouseDownBound);
            this.handleElement.removeEventListener('touchstart', this.touchStartBound);
            this.handleElement.removeEventListener('touchend', this.touchEndBound);
            this.handleElement.removeEventListener('touchcancel', this.touchCancelBound);
            this.handleElement.removeEventListener('touchmove', this.touchMoveBound);
        };
        Draggable.prototype.setPosition = function (x, y) {
            var minX = this.scrollX;
            var minY = this.scrollY;
            var maxX = document.documentElement.clientWidth - this.width + this.scrollX;
            var maxY = document.documentElement.clientHeight - this.height + this.scrollY;
            x = Math.max(Math.min(x, maxX), minX);
            y = Math.max(Math.min(y, maxY), minY);
            this.element.style.left = (x) + 'px';
            this.element.style.top = (y) + 'px';
        };
        Draggable.prototype.touchStart = function (event) {
            this.handleTouch(event, 'start');
        };
        Draggable.prototype.touchEnd = function (event) {
            this.handleTouch(event, 'end');
        };
        Draggable.prototype.touchCancel = function (event) {
            this.handleTouch(event, 'cancel');
        };
        Draggable.prototype.touchMove = function (event) {
            this.handleTouch(event, 'move');
        };
        Draggable.prototype.handleTouch = function (event, type) {
            var touches = event.touches;
            if (this.touchId >= 0) {
                var has = false;
                for (var i = 0; i < touches.length; i++) {
                    if (touches[i].identifier == this.touchId) {
                        has = true;
                    }
                }
                if (!has) {
                    this.touchId = -1;
                }
            }
            else if (touches.length > 0) {
                this.touchId = touches[0].identifier;
            }
            for (var i = 0; i < touches.length; i++) {
                var touch = touches[i];
                if (touch.identifier == this.touchId) {
                    if (type == 'start') {
                        this.handleDownEvent(touch.clientX, touch.clientY);
                    }
                    else if (type == 'move') {
                        event.preventDefault();
                        this.handleMoveEvent(touch.clientX, touch.clientY);
                    }
                    else if (type == 'end' || type == 'cancel') {
                    }
                    break;
                }
            }
        };
        Draggable.prototype.mouseDown = function (event) {
            this.handleDownEvent(event.clientX, event.clientY);
            document.addEventListener('mousemove', this.mouseMoveBound);
            document.addEventListener('mouseup', this.mouseUpBound);
        };
        Draggable.prototype.mouseMove = function (event) {
            this.handleMoveEvent(event.clientX, event.clientY);
        };
        Draggable.prototype.mouseUp = function (event) {
            document.removeEventListener('mousemove', this.mouseMoveBound);
            document.removeEventListener('mouseup', this.mouseUpBound);
        };
        Draggable.prototype.handleDownEvent = function (clientX, clientY) {
            var bb = this.element.getBoundingClientRect();
            this.startDragX = clientX - bb.left;
            this.startDragY = clientY - bb.top;
            this.width = bb.width;
            this.height = bb.height;
        };
        Draggable.prototype.handleMoveEvent = function (clientX, clientY) {
            if (this.scrollWithPage) {
                this.scrollX = window.pageXOffset;
                this.scrollY = window.pageYOffset;
            }
            else {
                this.scrollX = this.scrollY = 0;
            }
            var x = clientX - this.startDragX + this.scrollX;
            var y = clientY - this.startDragY + this.scrollY;
            this.setPosition(x, y);
        };
        return Draggable;
    }());
    uchan.Draggable = Draggable;
})(uchan || (uchan = {}));
/// <reference path="extra.ts" />
/// <reference path="draggable.ts" />
var uchan;
(function (uchan) {
    var QR = (function () {
        function QR(watcher) {
            this.showing = false;
            this.submitXhr = null;
            this.watcher = watcher;
            this.postEndpoint = uchan.context.postEndpoint;
            this.filePostingEnabled = uchan.context.filePostingEnabled;
            this.element = document.createElement('div');
            this.element.className = 'qr';
            this.element.innerHTML = '' +
                '    <form class="qr-form" action="' + this.postEndpoint + '" method="post" enctype="multipart/form-data">' +
                '        <span class="handle">' +
                '            <span class="handle-text">Reply</span>' +
                '            <span class="handle-close">&#x2716;</span>' +
                '        </span><br>' +
                '        <input class="input" type="text" name="name" placeholder="Name"><br>' +
                '        <input class="input" type="password" name="password" placeholder="Password (for post deletion)"><br>' +
                '        <textarea class="input" name="comment" placeholder="Comment" rows="8"></textarea><br>' +
                '        <input type="file" name="file"><input type="submit" value="Submit"/><br>' +
                '        <span class="error-message">Message</span>' +
                '        <input type="hidden" name="board" value="' + uchan.context.boardName + '"/>' +
                '        <input type="hidden" name="thread" value="' + uchan.context.threadId + '"/>' +
                '    </form>';
            document.body.appendChild(this.element);
            this.draggable = new uchan.Draggable(this.element, this.element.querySelector('.handle'), false);
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
            this.stateListeners = [];
        }
        QR.prototype.insertFormElement = function (element) {
            this.formElement.insertBefore(element, this.commentElement.nextSibling);
        };
        QR.prototype.addStateChangedListener = function (listener) {
            this.stateListeners.push(listener);
        };
        QR.prototype.removeStateChangedListener = function (listener) {
            var index = this.stateListeners.indexOf(listener);
            if (index >= 0) {
                this.stateListeners.splice(index, 1);
            }
        };
        QR.prototype.callStateChangedListeners = function (what) {
            for (var i = 0; i < this.stateListeners.length; i++) {
                this.stateListeners[i](this, what);
            }
        };
        QR.prototype.clear = function () {
            this.formElement.reset();
            this.callStateChangedListeners('clear');
        };
        QR.prototype.addShowClickListener = function (element) {
            element.addEventListener('click', this.onOpenEvent.bind(this));
        };
        QR.prototype.onCommentKeyDownEvent = function (event) {
            if (event.keyCode == 27) {
                this.hide();
            }
        };
        QR.prototype.onOpenEvent = function (event) {
            event.preventDefault();
            this.show();
        };
        QR.prototype.onCloseClickedEvent = function (event) {
            event.preventDefault();
            this.hide();
        };
        QR.prototype.show = function () {
            if (!this.showing) {
                this.showing = true;
                this.element.style.display = 'inline-block';
                var bb = this.element.getBoundingClientRect();
                var x = Math.min(1000, document.documentElement.clientWidth - bb.width - 100);
                this.draggable.setPosition(x, document.documentElement.clientHeight - bb.height - 100);
                this.commentElement.focus();
                this.callStateChangedListeners('show');
            }
        };
        QR.prototype.hide = function () {
            if (this.showing) {
                this.showing = false;
                this.element.style.display = 'none';
                this.callStateChangedListeners('hide');
            }
        };
        QR.prototype.addRefno = function (refno) {
            var toInsert = '>>' + refno + '\n';
            var position = this.commentElement.selectionStart;
            var value = this.commentElement.value;
            this.commentElement.value = value.substring(0, position) + toInsert + value.substring(position);
            this.commentElement.selectionStart = this.commentElement.selectionEnd = position + toInsert.length;
            this.commentElement.focus();
        };
        QR.prototype.onSubmitEvent = function (event) {
            event.preventDefault();
            this.submit();
        };
        QR.prototype.submit = function () {
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
                this.callStateChangedListeners('submitSent');
            }
        };
        QR.prototype.submitXhrOnProgressEvent = function (event) {
            this.submitElement.value = Math.round((event.loaded / event.total) * 100) + '%';
        };
        QR.prototype.submitXhrOnErrorEvent = function (event) {
            var responseData = null;
            try {
                responseData = JSON.parse(this.submitXhr.responseText);
            }
            catch (e) {
            }
            var responseMessage = 'Error submitting';
            if (responseData && responseData['message']) {
                responseMessage = 'Error: ' + responseData['message'];
            }
            else {
                if (this.submitXhr.status == 400) {
                    responseMessage = 'Error: bad request';
                }
            }
            console.error('Error submitting', this.submitXhr, event);
            this.showErrorMessage(true, responseMessage);
            this.callStateChangedListeners('submitError');
            this.resetAfterSubmit();
        };
        QR.prototype.submitXhrOnLoadEvent = function (event) {
            if (this.submitXhr.status == 200) {
                this.showErrorMessage(false);
                this.callStateChangedListeners('submitDone');
                this.clear();
                this.hide();
                this.watcher.afterPost();
            }
            else {
                this.submitXhrOnErrorEvent(event);
            }
            this.resetAfterSubmit();
        };
        QR.prototype.resetAfterSubmit = function () {
            this.submitElement.disabled = false;
            this.submitElement.value = 'Submit';
            this.submitXhr = null;
        };
        QR.prototype.showErrorMessage = function (show, message) {
            if (message === void 0) { message = null; }
            this.errorMessageElement.style.display = show ? 'inline-block' : 'none';
            if (show) {
                this.errorMessageElement.innerHTML = message;
            }
        };
        return QR;
    }());
    uchan.QR = QR;
})(uchan || (uchan = {}));
var uchan;
(function (uchan) {
    var ImageExpansion = (function () {
        function ImageExpansion() {
        }
        ImageExpansion.prototype.bindImages = function () {
            var images = document.querySelectorAll('.post .file');
            for (var i = 0; i < images.length; i++) {
                var image = images[i];
                this.bindImage(image);
            }
        };
        ImageExpansion.prototype.bindImage = function (container) {
            var _this = this;
            var link = container.querySelector('a');
            var image = container.querySelector('img');
            image.addEventListener('click', function (event) {
                if (event.button == 0) {
                    event.preventDefault();
                    var expanded = link.dataset['expanded'] == 'true';
                    if (expanded) {
                        _this.close(container, link, image);
                    }
                    else {
                        _this.expand(container, link, image);
                    }
                }
            });
        };
        ImageExpansion.prototype.expand = function (container, link, image) {
            if (!link.dataset['thumbnail']) {
                link.dataset['thumbnail'] = image.src;
                link.dataset['thumbnailwidth'] = image.width.toString();
                link.dataset['thumbnailheight'] = image.height.toString();
            }
            var width = parseInt(link.dataset['filewidth']);
            var height = parseInt(link.dataset['fileheight']);
            var bb = container.getBoundingClientRect();
            var availableWidth = document.documentElement.clientWidth;
            var availableHeight = document.documentElement.clientHeight;
            if (width > availableWidth || height > availableHeight) {
                var ratio = Math.min(availableWidth / width, availableHeight / height);
                width *= ratio;
                height *= ratio;
            }
            var leftMargin = 0;
            if (width > availableWidth - bb.left) {
                leftMargin = -bb.left;
            }
            link.dataset['expanded'] = 'true';
            image.src = link.href;
            image.style.marginLeft = (leftMargin) + 'px';
            image.width = width;
            image.height = height;
        };
        ImageExpansion.prototype.close = function (container, link, image) {
            image.src = link.dataset['thumbnail'];
            image.width = parseInt(link.dataset['thumbnailwidth']);
            image.height = parseInt(link.dataset['thumbnailheight']);
            image.style.marginLeft = '0';
            link.dataset['expanded'] = 'false';
        };
        return ImageExpansion;
    }());
    uchan.ImageExpansion = ImageExpansion;
})(uchan || (uchan = {}));
var uchan;
(function (uchan) {
    var PageVisibility = (function () {
        function PageVisibility() {
        }
        PageVisibility.isVisible = function () {
            return !document.hidden;
        };
        PageVisibility.addListener = function (listener) {
            var _this = this;
            if (!this.eventListenerRegistered) {
                this.eventListenerRegistered = true;
                document.addEventListener('visibilitychange', function (e) {
                    var visible = _this.isVisible();
                    for (var i = 0; i < _this.listeners.length; i++) {
                        _this.listeners[i](visible);
                    }
                });
            }
            this.listeners.push(listener);
        };
        PageVisibility.removeListener = function (listener) {
            var index = this.listeners.indexOf(listener);
            if (index >= 0) {
                PageVisibility.listeners.splice(index, 1);
            }
        };
        PageVisibility.eventListenerRegistered = false;
        PageVisibility.listeners = [];
        return PageVisibility;
    }());
    uchan.PageVisibility = PageVisibility;
})(uchan || (uchan = {}));
/// <reference path="imageexpansion.ts" />
/// <reference path="pagevisibility.ts" />
var uchan;
(function (uchan) {
    var Watcher = (function () {
        function Watcher(threadId, postsElement, statusElement, imageExpansion) {
            var _this = this;
            this.delays = [10, 15, 20, 30, 60, 90, 120, 180, 240, 300];
            this.endPoint = '/api/thread/';
            this.xhr = null;
            this.error = false;
            this.posts = [];
            this.timeoutId = -1;
            this.statusTimeoutId = -1;
            this.currentDelay = 0;
            this.targetTime = 0;
            this.totalNewPosts = 0;
            this.threadId = threadId;
            this.postsElement = postsElement;
            this.statusElement = statusElement;
            this.imageExpansion = imageExpansion;
            this.documentTitle = document.title;
            document.addEventListener('scroll', function (e) { return _this.onScroll(e); }, false);
            uchan.PageVisibility.addListener(function (visible) { return _this.pageVisibilityChanged(visible); });
            this.updateTimerState(this.delays[0] * 1000);
            this.updateStatus();
        }
        Watcher.prototype.updateTimerState = function (delay) {
            var _this = this;
            if (this.timeoutId >= 0) {
                clearTimeout(this.timeoutId);
            }
            this.timeoutId = setTimeout(function () {
                _this.timeoutId = -1;
                _this.timerFired();
            }, delay);
            this.targetTime = Date.now() + delay;
        };
        Watcher.prototype.timerFired = function () {
            // console.log('timer fired');
            this.update();
            this.updateStatus();
        };
        Watcher.prototype.forceUpdate = function () {
            this.currentDelay = 0;
            this.update();
        };
        Watcher.prototype.update = function () {
            if (this.xhr == null) {
                this.xhr = uchan.xhrJsonGet(this.endPoint + this.threadId, this.xhrDone.bind(this));
                this.updateStatus();
            }
        };
        Watcher.prototype.resetTimer = function (newPosts) {
            this.totalNewPosts += newPosts;
            var delay;
            if (newPosts == 0 && this.currentDelay < this.delays.length - 1) {
                delay = this.delays[this.currentDelay];
                this.currentDelay++;
            }
            else {
                delay = this.delays[0];
                this.currentDelay = 0;
            }
            if (!uchan.PageVisibility.isVisible()) {
                delay = Math.max(60, delay);
            }
            this.updateTimerState(delay * 1000);
        };
        Watcher.prototype.pageVisibilityChanged = function (visible) {
            if (visible) {
                this.updateStatus();
            }
        };
        Watcher.prototype.afterPost = function () {
            var _this = this;
            setTimeout(function () { return _this.forceUpdate(); }, 500);
        };
        Watcher.prototype.addUpdateListener = function (element) {
            var _this = this;
            element.addEventListener('click', function (event) {
                event.preventDefault();
                _this.forceUpdate();
            });
        };
        Watcher.prototype.onScroll = function (event) {
            if (window.innerHeight + window.pageYOffset + 1 > document.documentElement.scrollHeight) {
                this.totalNewPosts = 0;
                this.updateStatus();
            }
        };
        Watcher.prototype.updateStatus = function () {
            var _this = this;
            var invalidate = false;
            var status = '';
            if (this.error) {
                status = 'Error';
            }
            else if (this.xhr != null) {
                status = 'Updating...';
            }
            else if (this.totalNewPosts > 0) {
                status = this.totalNewPosts + ' new post' + (this.totalNewPosts != 1 ? 's' : '');
            }
            else {
                status = Math.ceil((this.targetTime - Date.now()) / 1000).toString();
                invalidate = true;
            }
            this.statusElement.textContent = status;
            if (this.totalNewPosts > 0) {
                document.title = '(' + this.totalNewPosts + ') ' + this.documentTitle;
            }
            else {
                document.title = this.documentTitle;
            }
            if (uchan.PageVisibility.isVisible() && invalidate) {
                if (this.statusTimeoutId >= 0) {
                    clearTimeout(this.statusTimeoutId);
                }
                this.statusTimeoutId = setTimeout(function () {
                    // console.log('update status timer fired');
                    _this.updateStatus();
                }, 1000);
            }
        };
        Watcher.prototype.xhrDone = function (error, data) {
            if (error) {
                console.error('watcher error');
                this.error = true;
            }
            else {
                this.error = false;
                var previousLength = this.posts.length;
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
                this.resetTimer(this.posts.length - previousLength);
            }
            this.xhr = null;
            this.updateStatus();
        };
        Watcher.prototype.buildPostElement = function (postData) {
            var postDiv = document.createElement('div');
            postDiv.className = 'post';
            postDiv.id = 'p#' + postData.refno;
            var postHtml = '<div class="header">';
            var file = postData.file;
            if (postData.subject) {
                postHtml += '<span class="subject">' + uchan.escape(postData.subject) + '</span><br>';
            }
            postHtml += '<a href="#p' + postData.refno + '" class="refno">#' + postData.refno + '</a> ' +
                '<span class="name">' + this.getPostNameHtml(postData.name) + '</span> ';
            if (postData.modCode) {
                postHtml += '<span class="modcode">' + uchan.escape(postData.modCode) + '</span> ';
            }
            postHtml += '<span class="date">' + this.getPostDateText(postData.date) + '</span> ' +
                '<span class="manage"><input type="checkbox" name="post_id" value="' + postData.id + '"></span>';
            if (file) {
                postHtml += '<br>File: <a href="' + uchan.escape(file.location) + '">' + uchan.escape(file.name) + '</a> ';
                postHtml += '(' + this.getPostFileSizeText(file.size) + ', ' + file.width + 'x' + file.height + ')';
            }
            postHtml += '</div>\n';
            if (postData.html) {
                postHtml += '<div class="styled-text">' + postData.html + '</div>';
            }
            if (file) {
                postHtml += '<div class="file">';
                postHtml += '<a class="file-link" href="' + uchan.escape(file.location) + '" data-filewidth="' + file.width + '" data-fileheight="' + file.height + '" data-filename="' + uchan.escape(file.name) + '" data-filesize="' + file.size + '">';
                postHtml += '<img src="' + uchan.escape(file.thumbnailLocation) + '" width="' + file.thumbnailWidth + '" height="' + file.thumbnailHeight + '">';
                postHtml += '</a>';
                postHtml += '</div>';
            }
            postDiv.innerHTML = postHtml;
            this.bindRefno(postDiv.querySelector('a.refno'));
            if (file) {
                this.imageExpansion.bindImage(postDiv.querySelector('.file'));
            }
            return postDiv;
        };
        Watcher.prototype.getPostNameHtml = function (name) {
            var html = uchan.escape(name);
            var i = html.indexOf('!');
            if (i >= 0) {
                html = html.substring(0, i) + '<span class="trip">!' + html.substring(i + 1) + '</span>';
            }
            return html;
        };
        Watcher.prototype.getPostFileSizeText = function (bytes) {
            var prefixes = ['kB', 'MB', 'GB', 'TB'];
            if (bytes == 1) {
                return '1 Byte';
            }
            else if (bytes < 1000) {
                return bytes + ' Bytes';
            }
            else {
                for (var i = 0; i < prefixes.length; i++) {
                    var unit = Math.pow(1000, i + 2);
                    if (bytes < unit) {
                        return uchan.round((1000 * bytes / unit), 1) + ' ' + prefixes[i];
                    }
                }
            }
        };
        Watcher.prototype.getPostDateText = function (postDate) {
            var date = new Date(postDate);
            // %Y-%m-%d %H:%M:%S
            var output = date.getUTCFullYear() + '-' + uchan.lpad(date.getUTCMonth() + 1, 2, '0') + '-' + uchan.lpad(date.getUTCDate(), 2, '0') + ' ';
            output += uchan.lpad(date.getUTCHours(), 2, '0') + ':' + uchan.lpad(date.getUTCMinutes(), 2, '0') + ':' + uchan.lpad(date.getUTCSeconds(), 2, '0');
            return output;
        };
        Watcher.prototype.bindPosts = function (posts) {
            for (var i = 0; i < posts.length; i++) {
                var postElement = posts[i];
                var postObj = {
                    id: 0,
                    refno: 0,
                    date: 0,
                    html: null,
                    name: null,
                    modCode: null,
                    subject: null,
                    file: null
                };
                var checkbox = postElement.querySelector('input[type="checkbox"]');
                postObj.id = parseInt(checkbox.value);
                postObj.refno = parseInt(postElement.id.substr(1));
                postObj.date = parseInt(postElement.dataset['date']);
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
                var modCodeElement = postElement.querySelector('.header .modcode');
                if (modCodeElement) {
                    var modCodeText = modCodeElement.textContent;
                    if (modCodeText) {
                        postObj.modCode = modCodeText;
                    }
                }
                var subjectElement = postElement.querySelector('.header .subject');
                if (subjectElement) {
                    var subjectText = subjectElement.textContent.trim();
                    if (subjectText) {
                        postObj.subject = subjectText;
                    }
                }
                var fileAnchorElement = postElement.querySelector('.file');
                if (fileAnchorElement) {
                    var imgElement = fileAnchorElement.querySelector('img');
                    postObj.file = {
                        'location': fileAnchorElement.getAttribute('href'),
                        'thumbnailLocation': imgElement.src,
                        'thumbnailWidth': imgElement.width,
                        'thumbnailHeight': imgElement.height,
                        'width': fileAnchorElement.dataset['filewidth'],
                        'height': fileAnchorElement.dataset['fileheight'],
                        'size': fileAnchorElement.dataset['filesize'],
                        'name': fileAnchorElement.dataset['filename']
                    };
                }
                this.posts.push(postObj);
            }
        };
        Watcher.prototype.bindRefnos = function () {
            var refnos = document.querySelectorAll('a.refno');
            for (var i = 0; i < refnos.length; i++) {
                var refno = refnos[i];
                this.bindRefno(refno);
            }
        };
        Watcher.prototype.bindRefno = function (refno) {
            refno.addEventListener('click', function (event) {
                event.preventDefault();
                var refnoText = this.textContent;
                var refnoNumber = parseInt(refnoText.substring(refnoText.indexOf('#') + 1).trim());
                uchan.context.qr.show();
                uchan.context.qr.addRefno(refnoNumber);
            });
        };
        return Watcher;
    }());
    uchan.Watcher = Watcher;
})(uchan || (uchan = {}));
/// <reference path="qr.ts" />
/// <reference path="watcher.ts" />
/// <reference path="imageexpansion.ts" />
var uchan;
(function (uchan) {
    uchan.context = {
        mode: null,
        boardName: null,
        postEndpoint: null,
        filePostingEnabled: false,
        threadId: null,
        locked: false,
        sticky: false,
        qr: null
    };
    uchan.escape = function (text) {
        text = text.toString();
        text = text.replace('&', '&amp;');
        text = text.replace('>', '&gt;');
        text = text.replace('<', '&lt;');
        text = text.replace("'", '&#39;');
        text = text.replace('"', '&#34;');
        return text;
    };
    uchan.lpad = function (str, len, fill) {
        str = str.toString();
        while (str.length < len) {
            str = fill + str;
        }
        return str;
    };
    uchan.round = function (num, digits) {
        var i = Math.pow(10, digits);
        return Math.round(num * i) / i;
    };
    uchan.xhrJsonGet = function (endpoint, callback) {
        var xhr = new XMLHttpRequest();
        xhr.open('GET', endpoint);
        xhr.send(null);
        xhr.onload = function (event) {
            if (xhr.status == 200) {
                var jsonData = null;
                var e = null;
                try {
                    jsonData = JSON.parse(xhr.responseText);
                }
                catch (err) {
                    e = err;
                }
                if (jsonData != null) {
                    callback(null, jsonData);
                }
                else {
                    callback(e, null);
                }
            }
            else {
                xhr.onerror(event);
            }
        };
        xhr.onerror = function (event) {
            callback(new Error(event.type), null);
        };
        return xhr;
    };
    var init = function () {
        var pageDetails = window['pageDetails'];
        if (!pageDetails) {
            console.error('window.pageDetails not defined');
        }
        else {
            uchan.context.mode = pageDetails.mode;
            uchan.context.boardName = pageDetails.boardName;
            uchan.context.postEndpoint = pageDetails.postEndpoint;
            uchan.context.filePostingEnabled = pageDetails.filePostingEnabled || false;
            uchan.context.threadId = pageDetails.threadId || null;
            uchan.context.locked = pageDetails.locked || false;
            uchan.context.sticky = pageDetails.sticky || false;
            if (uchan.context.mode == 'thread') {
                var replyButtons = document.querySelector('.thread-controls');
                replyButtons.innerHTML += '[<a id="open-qr" href="#">Reply</a>] [<a id="watch-update" href="#">Update</a>] ' +
                    '<span id="watch-status"></span>';
            }
            if (uchan.context.mode == 'board' || uchan.context.mode == 'thread') {
                var imageExpansion = new uchan.ImageExpansion();
                imageExpansion.bindImages();
            }
            if (uchan.context.mode == 'thread' && !uchan.context.locked) {
                var postForm = document.querySelector('.post-form');
                //postForm.style.display = 'none';
                var postsElement = document.querySelector('.posts');
                var watchStatusElement = replyButtons.querySelector('#watch-status');
                var watcher = new uchan.Watcher(uchan.context.threadId, postsElement, watchStatusElement, imageExpansion);
                var posts = postsElement.querySelectorAll('.post');
                watcher.bindPosts(posts);
                uchan.context.qr = new uchan.QR(watcher);
                uchan.context.qr.addShowClickListener(replyButtons.querySelector('#open-qr'));
                watcher.addUpdateListener(replyButtons.querySelector('#watch-update'));
                watcher.bindRefnos();
            }
        }
    };
    init();
})(uchan || (uchan = {}));
