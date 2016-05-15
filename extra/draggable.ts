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
        };

        bind = function() {
            this.handleElement.addEventListener('mousedown', this.mouseDownBound);
        };

        unbind = function() {
            this.handleElement.removeEventListener('mousedown', this.mouseDownBound);
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

        mouseDown = function(event:MouseEvent) {
            var bb = this.element.getBoundingClientRect();
            this.startDragX = event.clientX - bb.left;
            this.startDragY = event.clientY - bb.top;
            this.width = bb.width;
            this.height = bb.height;

            document.addEventListener('mousemove', this.mouseMoveBound);
            document.addEventListener('mouseup', this.mouseUpBound);
        };

        mouseMove = function(event:MouseEvent) {
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
    
        mouseUp = function(event:MouseEvent) {
            document.removeEventListener('mousemove', this.mouseMoveBound);
            document.removeEventListener('mouseup', this.mouseUpBound);
        };
    }
}
