/// <reference path="extra.ts" />
/// <reference path="draggable.ts" />

namespace uchan {
    export class QR {
        watcher: Watcher;

        postEndpoint:string;
        filePostingEnabled:boolean;

        element:HTMLDivElement;

        draggable:Draggable;

        formElement:HTMLFormElement;
        closeElement:HTMLElement;
        nameElement:HTMLInputElement;
        passwordElement:HTMLInputElement;
        commentElement:HTMLInputElement;
        fileElement:HTMLInputElement;
        submitElement:HTMLInputElement;
        errorMessageElement:HTMLElement;
        stateListeners:any[];
        showing:boolean = false;
        submitXhr:XMLHttpRequest = null;

        constructor(watcher) {
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
                '        <input type="hidden" name="board" value="' + context.boardName + '"/>' +
                '        <input type="hidden" name="thread" value="' + context.threadId + '"/>' +
                '    </form>';

            document.body.appendChild(this.element);

            this.draggable = new Draggable(this.element, this.element.querySelector('.handle'), false);
            this.draggable.bind();

            this.formElement = <HTMLFormElement>this.element.querySelector('.qr-form');
            this.closeElement = <HTMLElement>this.element.querySelector('.handle-close');
            this.closeElement.addEventListener('click', this.onCloseClickedEvent.bind(this));

            this.nameElement = <HTMLInputElement>this.element.querySelector('input[name="name"]');
            this.passwordElement = <HTMLInputElement>this.element.querySelector('input[name="password"]');
            this.commentElement = <HTMLInputElement>this.element.querySelector('textarea[name="comment"]');
            this.fileElement = <HTMLInputElement>this.element.querySelector('input[name="file"]');
            this.fileElement.style.display = this.filePostingEnabled ? 'inline-block' : 'none';
            this.submitElement = <HTMLInputElement>this.element.querySelector('input[type="submit"]');
            this.errorMessageElement = <HTMLElement>this.element.querySelector('.error-message');

            this.commentElement.addEventListener('keydown', this.onCommentKeyDownEvent.bind(this));
            this.submitElement.addEventListener('click', this.onSubmitEvent.bind(this));

            this.stateListeners = [];
        }

        insertFormElement(element) {
            this.formElement.insertBefore(element, this.commentElement.nextSibling);
        }

        addStateChangedListener(listener) {
            this.stateListeners.push(listener);
        }

        removeStateChangedListener(listener) {
            var index = this.stateListeners.indexOf(listener);
            if (index >= 0) {
                this.stateListeners.splice(index, 1);
            }
        }

        callStateChangedListeners(what) {
            for (var i = 0; i < this.stateListeners.length; i++) {
                this.stateListeners[i](this, what);
            }
        }

        clear() {
            this.formElement.reset();
            this.callStateChangedListeners('clear');
        }

        addShowClickListener(element) {
            element.addEventListener('click', this.onOpenEvent.bind(this));
        }

        onCommentKeyDownEvent(event) {
            if (event.keyCode == 27) {
                this.hide();
            }
        }

        onOpenEvent(event) {
            event.preventDefault();
            this.show();
        }

        onCloseClickedEvent(event) {
            event.preventDefault();
            this.hide();
        }

        show() {
            if (!this.showing) {
                this.showing = true;

                this.element.style.display = 'inline-block';

                var bb = this.element.getBoundingClientRect();
                var x = Math.min(1000, document.documentElement.clientWidth - bb.width - 100);
                this.draggable.setPosition(x, document.documentElement.clientHeight - bb.height - 100);

                this.commentElement.focus();

                this.callStateChangedListeners('show');
            }
        }

        hide() {
            if (this.showing) {
                this.showing = false;

                this.element.style.display = 'none';

                this.callStateChangedListeners('hide');
            }
        }

        addRefno(refno) {
            var toInsert = '>>' + refno + '\n';

            var position = this.commentElement.selectionStart;
            var value = this.commentElement.value;
            this.commentElement.value = value.substring(0, position) + toInsert + value.substring(position);
            this.commentElement.selectionStart = this.commentElement.selectionEnd = position + toInsert.length;

            this.commentElement.focus();
        }

        onSubmitEvent(event) {
            event.preventDefault();

            this.submit();
        }

        submit() {
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
        }

        submitXhrOnProgressEvent(event) {
            this.submitElement.value = Math.round((event.loaded / event.total) * 100) + '%';
        }

        submitXhrOnErrorEvent(event) {
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

            this.callStateChangedListeners('submitError');

            this.resetAfterSubmit();
        }

        submitXhrOnLoadEvent(event) {
            if (this.submitXhr.status == 200) {
                this.showErrorMessage(false);

                this.callStateChangedListeners('submitDone');

                this.clear();
                this.hide();

                this.watcher.afterPost();
            } else {
                this.submitXhrOnErrorEvent(event);
            }

            this.resetAfterSubmit();
        }

        resetAfterSubmit() {
            this.submitElement.disabled = false;
            this.submitElement.value = 'Submit';
            this.submitXhr = null;
        }

        showErrorMessage(show, message = null) {
            this.errorMessageElement.style.display = show ? 'inline-block' : 'none';
            if (show) {
                this.errorMessageElement.innerHTML = message;
            }
        }
    }
}
