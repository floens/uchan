/// <reference path="extra.ts" />
/// <reference path="draggable.ts" />
/// <reference path="persistence.ts" />

namespace uchan {
    class QRState implements Persistable {
        x: number = -1;
        y: number = -1;

        static fromDefaults() {
            return new QRState();
        }

        fromObject(obj: any) {
            this.x = obj['x'];
            this.y = obj['y'];
        }

        toObject() {
            return {
                'x': this.x,
                'y': this.y
            };
        }
    }

    export class QR {
        watcher: Watcher;
        persistence: Persistence;

        postEndpoint: string;
        filePostingEnabled: boolean;

        stateListeners: any[];
        state: QRState;
        showing: boolean = false;
        submitXhr: XMLHttpRequest = null;

        draggable: Draggable;

        element: HTMLDivElement;
        formElement: HTMLFormElement;
        closeElement: HTMLElement;
        nameElement: HTMLInputElement;
        passwordElement: HTMLInputElement;
        commentElement: HTMLInputElement;
        fileElement: HTMLInputElement;
        submitElement: HTMLInputElement;
        errorMessageElement: HTMLElement;

        constructor(watcher: Watcher, persistence: Persistence) {
            this.watcher = watcher;
            this.persistence = persistence;

            this.postEndpoint = uchan.context.postEndpoint;
            this.filePostingEnabled = uchan.context.filePostingEnabled;

            this.stateListeners = [];

            this.state = <QRState>persistence.retrieve('qr', QRState);
            if (this.state == null) {
                this.state = QRState.fromDefaults();
                persistence.persist('qr', this.state);
            }

            persistence.addCallback('qr', () => this.stateChanged());

            this.setupView();
        }

        private setupView() {
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
                '        <input type="file" name="file" multiple><input type="submit" value="Submit"/><br>' +
                '        <span class="error-message">Message</span>' +
                '        <input type="hidden" name="board" value="' + context.boardName + '"/>' +
                '        <input type="hidden" name="thread" value="' + context.threadRefno + '"/>' +
                '    </form>';

            this.draggable = new Draggable(this.element, this.element.querySelector('.handle'), false);
            this.draggable.bind(() => this.onDraggableMoved());

            this.formElement = <HTMLFormElement>this.element.querySelector('.qr-form');
            this.closeElement = <HTMLElement>this.element.querySelector('.handle-close');
            this.closeElement.addEventListener('click', this.onCloseClickedEvent.bind(this));

            this.nameElement = <HTMLInputElement>this.element.querySelector('input[name="name"]');
            this.passwordElement = <HTMLInputElement>this.element.querySelector('input[name="password"]');
            this.commentElement = <HTMLInputElement>this.element.querySelector('textarea[name="comment"]');
            this.fileElement = <HTMLInputElement>this.element.querySelector('input[name="file"]');
            this.fileElement.style.display = this.filePostingEnabled ? 'inline-block' : 'none';
            this.fileElement.addEventListener('change', this.onFileChangeEvent.bind(this));
            this.submitElement = <HTMLInputElement>this.element.querySelector('input[type="submit"]');
            this.errorMessageElement = <HTMLElement>this.element.querySelector('.error-message');

            this.commentElement.addEventListener('keydown', this.onCommentKeyDownEvent.bind(this));
            this.submitElement.addEventListener('click', this.onSubmitEvent.bind(this));

            document.body.appendChild(this.element);
        }

        insertFormElement(element) {
            this.formElement.insertBefore(element, this.commentElement.nextSibling);
        }

        addStateChangedListener(listener) {
            this.stateListeners.push(listener);
        }

        removeStateChangedListener(listener) {
            let index = this.stateListeners.indexOf(listener);
            if (index >= 0) {
                this.stateListeners.splice(index, 1);
            }
        }

        callStateChangedListeners(what) {
            for (let i = 0; i < this.stateListeners.length; i++) {
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

        onFileChangeEvent(event) {
            let overLimit = this.fileElement.files.length > context.fileMax;
            this.submitElement.disabled = overLimit;
            this.showErrorMessage(overLimit, 'Too many files selected, max ' + context.fileMax + ' files allowed');
        }

        onOpenEvent(event) {
            event.preventDefault();
            this.show();
        }

        onCloseClickedEvent(event) {
            event.preventDefault();
            this.hide();
        }

        onDraggableMoved() {
            this.state.x = this.draggable.x;
            this.state.y = this.draggable.y;

            this.persistence.persist('qr', this.state);
        }

        stateChanged() {
            this.state = <QRState>this.persistence.retrieve('qr', QRState);

            this.draggable.setPosition(this.state.x, this.state.y);
        }

        show() {
            if (!this.showing) {
                this.showing = true;

                this.element.style.display = 'inline-block';

                if (this.state.x == -1 && this.state.y == -1) {
                    let bb = this.element.getBoundingClientRect();
                    this.state.x = Math.min(1000, document.documentElement.clientWidth - bb.width - 100);
                    this.state.y = 100;
                }
                this.draggable.setPosition(this.state.x, this.state.y);

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
            let toInsert = '>>' + refno + '\n';

            let position = this.commentElement.selectionStart;
            let value = this.commentElement.value;
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
                let xhr = this.submitXhr = new XMLHttpRequest();
                xhr.open('POST', this.postEndpoint);
                xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
                xhr.onerror = this.submitXhrOnErrorEvent.bind(this);
                xhr.onload = this.submitXhrOnLoadEvent.bind(this);
                xhr.upload.onprogress = this.submitXhrOnProgressEvent.bind(this);

                let formData = new FormData(this.formElement);
                xhr.send(formData);

                this.submitElement.disabled = true;

                this.callStateChangedListeners('submitSent');
            }
        }

        submitXhrOnProgressEvent(event) {
            this.submitElement.value = Math.round((event.loaded / event.total) * 100) + '%';
        }

        submitXhrOnErrorEvent(event) {
            let responseData = null;
            try {
                responseData = JSON.parse(this.submitXhr.responseText);
            } catch (e) {
            }

            let responseMessage = 'Error submitting';
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
