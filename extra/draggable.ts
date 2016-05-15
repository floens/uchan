namespace uchan {
    export class Draggable {
        element:HTMLElement;
        handleElement:HTMLElement;
        scrollWithPage:boolean;

        startDragX:number;
        startDragY:number;
        scrollX:number;
        scrollY:number;
        width:number;
        height:number;

        mouseDownBound:any;
        mouseMoveBound:any;
        mouseUpBound:any;
        touchStartBound:any;
        touchEndBound:any;
        touchCancelBound:any;
        touchMoveBound:any;
        touchId = -1;

        constructor(element, handleElement, scrollWithPage) {
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
        };

        bind = function() {
            this.handleElement.addEventListener('mousedown', this.mouseDownBound);
            this.handleElement.addEventListener('touchstart', this.touchStartBound);
            this.handleElement.addEventListener('touchend', this.touchEndBound);
            this.handleElement.addEventListener('touchcancel', this.touchCancelBound);
            this.handleElement.addEventListener('touchmove', this.touchMoveBound);
        };

        unbind = function() {
            this.handleElement.removeEventListener('mousedown', this.mouseDownBound);
            this.handleElement.removeEventListener('touchstart', this.touchStartBound);
            this.handleElement.removeEventListener('touchend', this.touchEndBound);
            this.handleElement.removeEventListener('touchcancel', this.touchCancelBound);
            this.handleElement.removeEventListener('touchmove', this.touchMoveBound);
        };

        setPosition = function(x:number, y:number) {
            var minX = this.scrollX;
            var minY = this.scrollY;
            var maxX = document.documentElement.clientWidth - this.width + this.scrollX;
            var maxY = document.documentElement.clientHeight - this.height + this.scrollY;

            x = Math.max(Math.min(x, maxX), minX);
            y = Math.max(Math.min(y, maxY), minY);

            this.element.style.left = (x) + 'px';
            this.element.style.top = (y) + 'px';
        };

        touchStart = function(event:TouchEvent) {
            this.handleTouch(event, 'start');
        };

        touchEnd = function(event:TouchEvent) {
            this.handleTouch(event, 'end');
        };

        touchCancel = function(event:TouchEvent) {
            this.handleTouch(event, 'cancel');
        };

        touchMove = function(event:TouchEvent) {
            this.handleTouch(event, 'move');
        };

        handleTouch = function(event:TouchEvent, type:string) {
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
            } else if (touches.length > 0) {
                this.touchId = touches[0].identifier;
            }

            for (var i = 0; i < touches.length; i++) {
                var touch = touches[i];
                if (touch.identifier == this.touchId) {
                    if (type == 'start') {
                        this.handleDownEvent(touch.clientX, touch.clientY);
                    } else if (type == 'move') {
                        event.preventDefault();
                        this.handleMoveEvent(touch.clientX, touch.clientY);
                    } else if (type == 'end' || type == 'cancel') {
                    }
                    break;
                }
            }
        };

        mouseDown = function(event:MouseEvent) {
            this.handleDownEvent(event.clientX, event.clientY);
            document.addEventListener('mousemove', this.mouseMoveBound);
            document.addEventListener('mouseup', this.mouseUpBound);
        };

        mouseMove = function(event:MouseEvent) {
            this.handleMoveEvent(event.clientX, event.clientY);
        };

        mouseUp = function(event:MouseEvent) {
            document.removeEventListener('mousemove', this.mouseMoveBound);
            document.removeEventListener('mouseup', this.mouseUpBound);
        };

        handleDownEvent(clientX:number, clientY:number) {
            var bb = this.element.getBoundingClientRect();
            this.startDragX = clientX - bb.left;
            this.startDragY = clientY - bb.top;
            this.width = bb.width;
            this.height = bb.height;
        }

        handleMoveEvent(clientX:number, clientY:number) {
            if (this.scrollWithPage) {
                this.scrollX = window.pageXOffset;
                this.scrollY = window.pageYOffset;
            } else {
                this.scrollX = this.scrollY = 0;
            }

            var x = clientX - this.startDragX + this.scrollX;
            var y = clientY - this.startDragY + this.scrollY;

            this.setPosition(x, y);
        }
    }
}
