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
        }

        bind() {
            this.handleElement.addEventListener('mousedown', this.mouseDownBound);
            this.handleElement.addEventListener('touchstart', this.touchStartBound);
            this.handleElement.addEventListener('touchend', this.touchEndBound);
            this.handleElement.addEventListener('touchcancel', this.touchCancelBound);
            this.handleElement.addEventListener('touchmove', this.touchMoveBound);
        }

        unbind() {
            this.handleElement.removeEventListener('mousedown', this.mouseDownBound);
            this.handleElement.removeEventListener('touchstart', this.touchStartBound);
            this.handleElement.removeEventListener('touchend', this.touchEndBound);
            this.handleElement.removeEventListener('touchcancel', this.touchCancelBound);
            this.handleElement.removeEventListener('touchmove', this.touchMoveBound);
        }

        setPosition(x:number, y:number) {
            let minX = this.scrollX;
            let minY = this.scrollY;
            let maxX = document.documentElement.clientWidth - this.width + this.scrollX;
            let maxY = document.documentElement.clientHeight - this.height + this.scrollY;

            x = Math.max(Math.min(x, maxX), minX);
            y = Math.max(Math.min(y, maxY), minY);

            this.element.style.left = (x) + 'px';
            this.element.style.top = (y) + 'px';
        }

        touchStart(event:TouchEvent) {
            this.handleTouch(event, 'start');
        }

        touchEnd(event:TouchEvent) {
            this.handleTouch(event, 'end');
        }

        touchCancel(event:TouchEvent) {
            this.handleTouch(event, 'cancel');
        }

        touchMove(event:TouchEvent) {
            this.handleTouch(event, 'move');
        }

        handleTouch(event:TouchEvent, type:string) {
            let touches = event.touches;

            if (this.touchId >= 0) {
                let has = false;
                for (let i = 0; i < touches.length; i++) {
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

            for (let i = 0; i < touches.length; i++) {
                let touch = touches[i];
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
        }

        mouseDown(event:MouseEvent) {
            this.handleDownEvent(event.clientX, event.clientY);
            document.addEventListener('mousemove', this.mouseMoveBound);
            document.addEventListener('mouseup', this.mouseUpBound);
        }

        mouseMove(event:MouseEvent) {
            this.handleMoveEvent(event.clientX, event.clientY);
        }

        mouseUp(event:MouseEvent) {
            document.removeEventListener('mousemove', this.mouseMoveBound);
            document.removeEventListener('mouseup', this.mouseUpBound);
        }

        handleDownEvent(clientX:number, clientY:number) {
            let bb = this.element.getBoundingClientRect();
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

            let x = clientX - this.startDragX + this.scrollX;
            let y = clientY - this.startDragY + this.scrollY;

            this.setPosition(x, y);
        }
    }
}
