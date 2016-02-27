(function() {
    'use strict';

    var context = {};

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

    var QR = function(element, draggable) {
        this.element = element;
        this.draggable = draggable;

        this.formElement = element.querySelector('.qr-form');
        this.closeElement = element.querySelector('.handle-close');
        this.closeElement.addEventListener('click', this.onCloseClickedEvent.bind(this));

        this.nameElement = element.querySelector('input[name="name"]');
        this.commentElement = element.querySelector('textarea[name="comment"]');
        this.fileElement = element.querySelector('input[name="file"]');
        this.submitElement = element.querySelector('input[type="submit"]');
        this.errorMessageElement = element.querySelector('.error-message');

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

    QR.prototype.onSubmitEvent = function(event) {
        event.preventDefault();

        this.submit();
    };

    QR.prototype.submit = function() {
        if (this.submitXhr == null) {
            var xhr = this.submitXhr = new XMLHttpRequest();
            xhr.open('POST', context.pageDetails.postEndpoint);
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

            // TODO
            location.reload();
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

    var init = function() {
        var pageDetails = window.pageDetails;
        if (!pageDetails) {
            console.error('window.pageDetails not defined');
        } else {
            context.pageDetails = pageDetails;

            var qrElement = document.querySelector('.qr');
            var qrHandleElement = document.querySelector('.qr .handle');
            var qrDraggable = new Draggable(qrElement, qrHandleElement, false);
            qrDraggable.bind();
            var qr = new QR(qrElement, qrDraggable);
            qr.addShowListener(document.querySelector('#open-qr'));

            qr.show();
        }
    };

    init();
})();
