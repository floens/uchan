(function() {
    'use strict';

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

        this.submitElement = element.querySelector('input[type="submit"]');
        this.submitElement.addEventListener('click', this.onSubmitEvent.bind(this));

        this.showing = false;
    };

    QR.prototype.addOpenListener = function(element) {
        element.addEventListener('click', this.onOpenEvent.bind(this));
    };

    QR.prototype.onOpenEvent = function(event) {
        event.preventDefault();
        this.show();
    };

    QR.prototype.show = function() {
        if (!this.showing) {
            this.showing = true;

            this.element.style.display = 'inline-block';

            var x = Math.min(1000, document.documentElement.clientWidth - this.element.getBoundingClientRect().width);
            this.draggable.setPosition(x, 200);
        }
    };

    QR.prototype.hide = function() {
        if (this.showing) {
            this.showing = false;

            this.element.style.display = 'none';
        }
    };

    QR.prototype.onSubmitEvent = function(event) {
        console.log('submit!');
    };

    var init = function() {
        var qrElement = document.querySelector('.qr');
        var qrHandleElement = document.querySelector('.qr .handle');
        var qrDraggable = new Draggable(qrElement, qrHandleElement, false);
        qrDraggable.bind();
        var qr = new QR(qrElement, qrDraggable);
        qr.addOpenListener(document.querySelector('#open-qr'));
    };

    init();
})();
